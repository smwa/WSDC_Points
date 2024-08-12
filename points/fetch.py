import requests
import json
import json
import datetime
from dateutil.relativedelta import relativedelta
import msgpack
import gzip
from os import environ

FULL_DANCER_CHECK = False
if "FULLDANCERCHECK" in environ:
  FULL_DANCER_CHECK = True
COMPETITION_RECENCY_LIMIT_IN_MONTHS = 36

API_URL = "https://points.worldsdc.com/lookup2020/find"
NONE_SLIDE_LIMIT = 200
RAW_RESPONSE_FILE = './raw_responses.json.gz'
LIMIT_TO_DANCE_STYLE = 'West Coast Swing'
ROLES_MAP = {
    1: 'Leader',
    2: 'Follower',
    3: 'Switch',
}
DIVISIONS_MAP = {
    12: 'Teacher',
    11: 'All-Stars',
    10: 'Champions',
    9: 'Invitational',
    8: 'Sophisticated',
    7: 'Professional',
    6: 'Advanced',
    5: 'Intermediate',
    4: 'Novice',
    3: 'Newcomer',
    2: 'Masters',
    1: 'Juniors',
}
ROLES_MAP_INVERTED = dict((v, k) for k, v in ROLES_MAP.items())
DIVISIONS_MAP_INVERTED = dict((v, k) for k, v in DIVISIONS_MAP.items())

SKILL_DIVISION_PROGRESSION = [DIVISIONS_MAP_INVERTED[d] for d in [
  'Newcomer',
  'Novice',
  'Intermediate',
  'Advanced',
  'All-Stars',
  'Champions',
]]

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

# Load raw responses from a json file
raw_response_dancers = {} # Keyed by str(wsdc_id)
try:
  with open(RAW_RESPONSE_FILE, "rb") as f:
    raw_response_dancers_json = gzip.decompress(f.read()).decode('utf-8')
    raw_response_dancers = json.loads(raw_response_dancers_json)
except:
  pass

def fetch_and_save_dancer(wsdc_id):
  res = get_dancer("{}".format(wsdc_id))
  if res is None:
    print("Empty result on {}".format(wsdc_id))
    return False
  else:
    raw_response_dancers[str(wsdc_id)] = res
    return True

def get_all_dancers(starting_wsdc_id=1):
    current_wsdc_id = starting_wsdc_id
    none_slide = 0

    while True:
      if current_wsdc_id % 500 == 0:
        print("Getting", current_wsdc_id)
      success = fetch_and_save_dancer(current_wsdc_id)
      if success:
        none_slide = 0
      else:
        none_slide += 1
        if none_slide >= NONE_SLIDE_LIMIT:
          print("Quitting")
          break
      current_wsdc_id += 1

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
        competition_date = datetime.datetime.strptime(competition["event"]["date"], '%B %Y')
        if max_placement_date is None:
          max_placement_date = competition_date
        else:
          max_placement_date = max(max_placement_date, competition_date)
  return max_placement_date

def get_dancers_abbreviated():
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
      fetch_and_save_dancer(dancer['dancer_wsdcid'])
  get_all_dancers(max_wsdc_id + 1)

if FULL_DANCER_CHECK:
  get_all_dancers(1)
else:
  get_dancers_abbreviated()

raw_response_dancers = dict(sorted(raw_response_dancers.items()))
with open(RAW_RESPONSE_FILE, 'wb') as f:
  raw_response_dancers_json = json.dumps(raw_response_dancers)
  raw_response_dancers_json_compressed = gzip.compress(bytes(raw_response_dancers_json, 'utf-8'))
  f.write(raw_response_dancers_json_compressed)

def placementsToList(placements):
    final_placements = []
    final_events = []
    earliest_event = None
    if type(placements) is list:
        return (final_placements, final_events, earliest_event)
    for style_key in placements: # style_key is "West Coast Swing"
        if style_key != LIMIT_TO_DANCE_STYLE:
          continue
        style = placements[style_key] # style is {"NOV": {"division": {id: 3, name: newcomer, abbreviation: NEW}}}
        for division_key in style:
            division = style[division_key]
            division_name = division["division"]["name"].title()
            division_name = DIVISIONS_MAP_INVERTED[division_name]
            for competition in division["competitions"]:
                competition_date = datetime.datetime.strptime(competition["event"]["date"], '%B %Y')
                if earliest_event is None or competition_date < earliest_event:
                   earliest_event = competition_date
                event = {
                    **competition["event"],
                    "date": competition_date.date().isoformat()
                }
                final_events.append(event)
                role = competition["role"].title()
                role = ROLES_MAP_INVERTED[role]
                final_placements.append({
                    "role": role,
                    "result": competition["result"],
                    "points": competition["points"],
                    "event": event['id'],
                    "date": event["date"],
                    "division": division_name,
                })
    return (final_placements, final_events, earliest_event)

database = {
    "last_updated": datetime.datetime.now().isoformat(),
    'roles': ROLES_MAP,
    'divisions': DIVISIONS_MAP,
    'ordered_skill_divisions': SKILL_DIVISION_PROGRESSION,
    "dancers": [],
    "events": [],
    'top_dancers_by_points_gained_recently': {},
    'past_events_that_may_be_recurring': [],
    'new_dancers_over_time': [],
}

events = []

def addEvents(_events, new_events):
  for new_event in new_events:
    event = None
    for e in _events:
        if e['id'] == new_event['id']:
            event = e
            break
    if event is None:
        event = {
          "id": new_event["id"],
          "name": new_event['name'],
          "location": new_event['location'],
          "url": new_event['url'],
          'dates': [],
        }
        _events.append(event)
    event['dates'].append(new_event['date'])
    event['dates'] = list(set(event['dates']))
    event['dates'].sort()
    if event['dates'][-1] == new_event['date']:
        # This is the most recent, so update info
        event["name"] = new_event['name']
        event["location"] = new_event['location']
        event["url"] = new_event['url']
  return _events

new_dancers_by_date = {}

def addEarliestPlacement(dateOne: datetime.datetime|None, dateTwo: datetime.datetime|None):
  if dateOne is None and dateTwo is None:
    return
  d = dateOne
  if d is None:
    d = dateTwo
  if dateOne is not None and dateTwo is not None:
    d = min(dateOne, dateTwo)

  date_string = d.date().replace(month=1).isoformat() # Group by year only
  if date_string not in new_dancers_by_date:
    new_dancers_by_date[date_string] = 0
  new_dancers_by_date[date_string] += 1

for raw_response_dancer_wsdc_id in raw_response_dancers:
    datum = raw_response_dancers[raw_response_dancer_wsdc_id]
    leader = placementsToList(datum["leader"]["placements"])
    follower = placementsToList(datum["follower"]["placements"])
    addEarliestPlacement(leader[2], follower[2])
    dancer_placements = leader[0] + follower[0]
    dancer_placements.sort(key=lambda p: p["date"], reverse=True)
    res = {
      'id': datum['dancer_wsdcid'],
      'pro': datum["is_pro"] == 1,
      'primary_role': ROLES_MAP_INVERTED[datum["short_dominate_role"]],
      'first': datum["dancer_first"],
      'last': datum["dancer_last"],
      'placements': dancer_placements,
    }
    if len(res['placements']) > 0:
        database["dancers"].append(res)
        database["events"] = addEvents(database["events"], leader[1])
        database["events"] = addEvents(database["events"], follower[1])

# Get how many new dancers by month
new_dancers_over_time = [{'key': k, 'value': new_dancers_by_date[k]} for k in new_dancers_by_date.keys()]
new_dancers_over_time.sort(key=lambda kv: datetime.date.fromisoformat(kv['key']))
for kv in new_dancers_over_time:
  kv['key'] = "{:'%y}".format(datetime.date.fromisoformat(kv['key']))
database['new_dancers_over_time'] = new_dancers_over_time

# Find "rising stars", top 5 for each role/division by points received in the last 3 months

min_date = (datetime.date.today().replace(day=1) - datetime.timedelta(days=90)).replace(day=1) # 3 months ago
from_each_group = 5

divisions = {} # [novice/beginner/advanced][leader/follower] = {wscid: int, points: int}[]

for dancer in database["dancers"]:
    for placement in dancer["placements"]:
        if datetime.date.fromisoformat(placement["date"]) < min_date:
            continue
        _points = placement["points"]
        _division = placement["division"]
        _role = placement["role"]
        if _division not in divisions:
            divisions[_division] = {}
        if _role not in divisions[_division]:
            divisions[_division][_role] = {}
        if dancer['id'] not in divisions[_division][_role]:
            divisions[_division][_role][dancer['id']] = 0
        divisions[_division][_role][dancer['id']] += _points

sorted_divisions = {}
for division in divisions:
    sorted_divisions[division] = {}
    for role in divisions[division]:
        chunked_sorted = sorted(divisions[division][role].items(), key=lambda item: item[1], reverse=True)[0:from_each_group]
        sorted_divisions[division][role] = {d[0]: d[1] for d in chunked_sorted}

unkeyed_by_division = []
for division in sorted_divisions:
  unkeyed_division = {
    'division': division,
    'roles': [],
  }
  for role in sorted_divisions[division]:
    unkeyed_role = {
      'role': role,
      'dancers': [],
    }
    for dancer_id in sorted_divisions[division][role]:
      unkeyed_dancer = {
        'points': sorted_divisions[division][role][dancer_id],
        'wscdid': dancer_id,
      }
      unkeyed_role['dancers'].append(unkeyed_dancer)
    unkeyed_role['dancers'] = sorted(unkeyed_role['dancers'], key=lambda dancer: dancer['points'], reverse=True)
    unkeyed_division['roles'].append(unkeyed_role)
  unkeyed_division['roles'] = sorted(unkeyed_division['roles'], key=lambda role: role['role'])
  unkeyed_by_division.append(unkeyed_division)
unkeyed_by_division = sorted(unkeyed_by_division, key=lambda division: division['division'], reverse=True)

database["top_dancers_by_points_gained_recently"] = unkeyed_by_division


# Past events that may be coming back up
min_date = (datetime.date.today().replace(day=1) - datetime.timedelta(days=(30 * 11))).replace(day=1) # 11 months ago
max_date = (datetime.date.today().replace(day=1) - datetime.timedelta(days=(30 * 10))).replace(day=1) # 10 months ago

for event in database['events']:
  valid_dates = [d for d in event['dates'] if datetime.date.fromisoformat(d) >= min_date and datetime.date.fromisoformat(d) <= max_date]
  if len(valid_dates) > 0:
    database["past_events_that_may_be_recurring"].append(event['id'])

# Write to file, leave at bottom of this script
with open("../spa/src/assets/database.txt", 'bw') as f:
    contents = msgpack.packb(database)
    f.write(contents)
