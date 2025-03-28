import requests
import json
import datetime
from dateutil.relativedelta import relativedelta
import gzip

COMPETITION_RECENCY_LIMIT_IN_MONTHS = 15
API_URL = "https://points.worldsdc.com/lookup2020/find"
NONE_SLIDE_LIMIT = 200
RAW_RESPONSE_FILE = './raw_responses.json.gz'
LIMIT_TO_DANCE_STYLE = 'West Coast Swing'

def get_dancer(wsdc_id: str):
  r = requests.post(API_URL, data = {'num': wsdc_id})
  if r.status_code != 200:
    print("Bad status code: {}".format(r.status_code))
    return None
  json = r.json()
  if not json:
    print("Received no json but no 404")
    return None
  return json

def fetch_and_save_dancer(wsdc_id, raw_response_dancers):
  res = get_dancer("{}".format(wsdc_id))
  if res is None:
    print("Empty result on {}".format(wsdc_id))
    return (False, raw_response_dancers)
  else:
    raw_response_dancers[str(wsdc_id)] = res
    return (True, raw_response_dancers)

def get_all_dancers(starting_wsdc_id, raw_response_dancers):
    requests_made = 0
    current_wsdc_id = starting_wsdc_id
    none_slide = 0

    while True:
      if current_wsdc_id % 500 == 0:
        print("Getting", current_wsdc_id)
      (success, raw_response_dancers) = fetch_and_save_dancer(current_wsdc_id, raw_response_dancers)
      requests_made += 1
      if success:
        none_slide = 0
      else:
        none_slide += 1
        if none_slide >= NONE_SLIDE_LIMIT:
          print("Quitting")
          break
      current_wsdc_id += 1
    return (requests_made, raw_response_dancers)

def get_max_placement_date(dancer_role):
  placements = dancer_role['placements']
  if placements is None or type(placements) is list:
    return None
  max_placement_date = None
  for style_key in placements: # style_key is "West Coast Swing"
    if style_key != LIMIT_TO_DANCE_STYLE:
      continue
    style = placements[style_key] # style is {"NOV": {"division": {id: 3, name: newcomer, abbreviation: NEW}}}
    for division_key in style:
      division = style[division_key]
      for competition in division["competitions"]:
        competition_date = None
        try:
            competition_date = datetime.datetime.strptime(competition["event"]["date"], '%B %Y')
        except:
            competition_date = datetime.datetime.strptime("January 1970", '%B %Y')
        if max_placement_date is None:
          max_placement_date = competition_date
        else:
          max_placement_date = max(max_placement_date, competition_date)
  return max_placement_date

def get_dancers_abbreviated(raw_response_dancers):
  requests_made = 0
  max_wsdc_id = 1
  cutoff_date = datetime.datetime.now() - relativedelta(months=COMPETITION_RECENCY_LIMIT_IN_MONTHS)
  for wsdc_id in raw_response_dancers:
    dancer = raw_response_dancers[wsdc_id]
    max_wsdc_id = max(max_wsdc_id, dancer['dancer_wsdcid'])
    max_date = get_max_placement_date(dancer['leader'])
    max_follower_date = get_max_placement_date(dancer['follower'])
    if max_date is None or (max_follower_date is not None and max_follower_date > max_date):
      max_date = max_follower_date
    if max_date is not None and max_date > cutoff_date:
      (_, raw_response_dancers) = fetch_and_save_dancer(dancer['dancer_wsdcid'], raw_response_dancers)
      requests_made += 1
  next_wsdc_id = max_wsdc_id + 1
  requests_made += get_all_dancers(next_wsdc_id, raw_response_dancers)
  return (requests_made, raw_response_dancers)

def get_dancers(fetch_remote: bool, fetch_all):
  # Load raw responses from a json file
  raw_response_dancers = {} # Keyed by str(wsdc_id)
  with open(RAW_RESPONSE_FILE, "rb") as f:
    raw_response_dancers_json = gzip.decompress(f.read()).decode('utf-8')
    raw_response_dancers = json.loads(raw_response_dancers_json)

  number_of_requests_to_wsdc = 0
  if fetch_remote:
    if fetch_all:
      (number_of_requests_to_wsdc, raw_response_dancers) = get_all_dancers(1, raw_response_dancers)
    else:
      (number_of_requests_to_wsdc, raw_response_dancers) = get_dancers_abbreviated(raw_response_dancers)
  print("Made {} requests to WSDC".format(number_of_requests_to_wsdc))

  raw_response_dancers = dict(sorted(raw_response_dancers.items()))
  with open(RAW_RESPONSE_FILE, 'wb') as f:
    raw_response_dancers_json = json.dumps(raw_response_dancers)
    raw_response_dancers_json_compressed = gzip.compress(bytes(raw_response_dancers_json, 'utf-8'))
    f.write(raw_response_dancers_json_compressed)
  return raw_response_dancers
