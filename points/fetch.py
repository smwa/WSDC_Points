import requests
from bs4 import BeautifulSoup
import json
import re
import datetime
from dateutil.relativedelta import relativedelta
import msgpack
import gzip
from os import environ
import time

FULL_DANCER_CHECK = False
if "FULLDANCERCHECK" in environ:
  FULL_DANCER_CHECK = True
SKIP_FETCH = False
if "SKIPFETCH" in environ:
  SKIP_FETCH = True
COMPETITION_RECENCY_LIMIT_IN_MONTHS = 15
CHUNKED_DANCERS_SIZE = 20

LOCATION_CACHE_FILE = "./locations.json"
OPEN_WEATHER_MAP_API_KEY = ""
if "OPEN_WEATHER_MAP_API_KEY" in environ:
  OPEN_WEATHER_MAP_API_KEY = environ["OPEN_WEATHER_MAP_API_KEY"]

API_URL = "https://points.worldsdc.com/lookup2020/find"
NONE_SLIDE_LIMIT = 200
RAW_RESPONSE_FILE = './raw_responses.json.gz'
RAW_EVENTS_RESPONSE_FILE = './raw_events.html.gz'
LIMIT_TO_DANCE_STYLE = 'West Coast Swing'
ROLES_MAP = {
    1: 'Leader',
    2: 'Follower',
    3: 'Switch',
}
DIVISIONS_MAP = {
    12: 'Teacher',
    11: 'Invitational',
    10: 'Sophisticated',
    9: 'Professional',
    8: 'Champions',
    7: 'All-Stars',
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

SKILL_DIVISION_LIMITS = {DIVISIONS_MAP_INVERTED[d[0]]:(d[1], d[2]) for d in [
  ('Champions', 1, 10),
  ('All-Stars', 150, 225),
  ('Advanced', 60, 90),
  ('Intermediate', 30, 45),
  ('Novice', 16, 30),
  ('Newcomer', 0, 1),
]}

LEADER = ROLES_MAP_INVERTED["Leader"]
FOLLOWER = ROLES_MAP_INVERTED["Follower"]
SWITCH = ROLES_MAP_INVERTED["Switch"]

TEACHER = DIVISIONS_MAP_INVERTED['Teacher']
INVITATIONAL = DIVISIONS_MAP_INVERTED['Invitational']
SOPHISTICATED = DIVISIONS_MAP_INVERTED['Sophisticated']
PROFESSIONAL = DIVISIONS_MAP_INVERTED['Professional']
CHAMPIONS = DIVISIONS_MAP_INVERTED['Champions']
ALLSTARS = DIVISIONS_MAP_INVERTED['All-Stars']
ADVANCED = DIVISIONS_MAP_INVERTED['Advanced']
INTERMEDIATE = DIVISIONS_MAP_INVERTED['Intermediate']
NOVICE = DIVISIONS_MAP_INVERTED['Novice']
NEWCOMER = DIVISIONS_MAP_INVERTED['Newcomer']
MASTERS = DIVISIONS_MAP_INVERTED['Masters']
JUNIORS = DIVISIONS_MAP_INVERTED['Juniors']


# Why do you do this to us, WSDC?
LOCATION_PATCHES = {
   "Swing Fling": "Washington, D.C., US"
}

number_of_requests_to_wsdc = 0

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
with open(RAW_RESPONSE_FILE, "rb") as f:
  raw_response_dancers_json = gzip.decompress(f.read()).decode('utf-8')
  raw_response_dancers = json.loads(raw_response_dancers_json)

location_cache = {}
with open(LOCATION_CACHE_FILE, "r") as f:
  location_cache = json.load(f)

def get_location(name: str, location: str):
  if (location == "" or location is None) and name not in LOCATION_PATCHES:
     print("Location patch miss for '{}'".format(name))
  if (location == "" or location is None) and name in LOCATION_PATCHES:
     location = LOCATION_PATCHES[name]
  if location in location_cache:
     return location_cache[location]
  if SKIP_FETCH:
    return []
  time.sleep(1.1)
  splits = [s.strip() for s in location.split(",")]
  if len(splits) > 1 and len(splits[1]) == 2 and splits[1].isupper() and splits[1] != "UK":
    if len(splits) < 3:
      splits.append("US")
    else:
      splits[2] = "US"
  requestable_location = ",".join(splits)
  url = "http://api.openweathermap.org/geo/1.0/direct?q={}&limit=1&appid={}".format(requestable_location, OPEN_WEATHER_MAP_API_KEY)
  r = requests.get(url)
  if not r.ok:
    print("No results for location {}".format(location))
    location_cache[location] = []
    return []
  jsonResult = r.json()
  if len(jsonResult) < 1:
    print("No results for location {}".format(location))
    location_cache[location] = []
    return []
  ret = None
  latitude = jsonResult[0]["lat"]
  longitude = jsonResult[0]["lon"]
  ret = (latitude, longitude)
  location_cache[location] = ret
  return ret

def fetch_and_save_dancer(wsdc_id):
  res = get_dancer("{}".format(wsdc_id))
  if res is None:
    print("Empty result on {}".format(wsdc_id))
    return False
  else:
    raw_response_dancers[str(wsdc_id)] = res
    return True

def get_all_dancers(starting_wsdc_id=1):
    requests_made = 0
    current_wsdc_id = starting_wsdc_id
    none_slide = 0

    while True:
      if current_wsdc_id % 500 == 0:
        print("Getting", current_wsdc_id)
      success = fetch_and_save_dancer(current_wsdc_id)
      requests_made += 1
      if success:
        none_slide = 0
      else:
        none_slide += 1
        if none_slide >= NONE_SLIDE_LIMIT:
          print("Quitting")
          break
      current_wsdc_id += 1
    return requests_made

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

def get_dancers_abbreviated():
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
      fetch_and_save_dancer(dancer['dancer_wsdcid'])
      requests_made += 1
  return requests_made + get_all_dancers(max_wsdc_id + 1)

def parseEventsFromWsdcEventsPageHtml(html):
  soup = BeautifulSoup(html, 'html.parser')
  rows = soup.find("table").find_all("tr")[1:]
  ret = []
  for row in rows:
    tds = row.find_all('td')
    date = tds[0].get_text()
    location = tds[2].get_text()
    name = tds[1].find("div", class_="event_name").get_text().strip()
    url = tds[1].find("a")['href']
    event_type = tds[1].find("div", class_="event_type").get_text()

    start_date = None
    end_date = None

    try:
      year = re.findall('\d{4}', date)[0]
      month = re.findall('[a-zA-Z]{3}', date)[0]
      day = re.findall('\d{1,2}', date)[0]
      month = datetime.datetime.strptime(month, '%b').month
      start_date = datetime.datetime(int(year), month, int(day)).isoformat()

      year = re.findall('\d{4}', date)[-1]
      month = re.findall('[a-zA-Z]{3}', date)[-1]
      day = re.findall('\s(\d{1,2})[,\s]', date)[-1]
      month = datetime.datetime.strptime(month, '%b').month
      end_date = datetime.datetime(int(year), month, int(day)).isoformat()
    except Exception as e:
      raise e
    latlon = get_location(name, location)
    latitude = None
    longitude = None
    if len(latlon) >= 2:
      latitude = latlon[0]
      longitude = latlon[1]
    ret.append({
      "name": name,
      "location": location,
      "latitude": latitude,
      "longitude": longitude,
      "url": url,
      "type": event_type,
      "end_date": end_date,
      "start_date": start_date
    })
  return ret

eventsFromWsdc = []

if not SKIP_FETCH:
  if FULL_DANCER_CHECK:
    number_of_requests_to_wsdc = get_all_dancers(1)
  else:
    number_of_requests_to_wsdc = get_dancers_abbreviated()
  eventsPageResponse = requests.get("https://www.worldsdc.com/events/")
  number_of_requests_to_wsdc += 1
  if eventsPageResponse.status_code == 200:
    with open(RAW_EVENTS_RESPONSE_FILE, 'wb') as f:
      raw_events_html_compressed = gzip.compress(bytes(eventsPageResponse.text, 'utf-8'))
      f.write(raw_events_html_compressed)

with open(RAW_EVENTS_RESPONSE_FILE, "rb") as f:
  raw_events_html = gzip.decompress(f.read()).decode('utf-8')
  eventsFromWsdc = parseEventsFromWsdcEventsPageHtml(raw_events_html)

print("Made {} requests to WSDC".format(number_of_requests_to_wsdc))

raw_response_dancers = dict(sorted(raw_response_dancers.items()))
with open(RAW_RESPONSE_FILE, 'wb') as f:
  raw_response_dancers_json = json.dumps(raw_response_dancers)
  raw_response_dancers_json_compressed = gzip.compress(bytes(raw_response_dancers_json, 'utf-8'))
  f.write(raw_response_dancers_json_compressed)

def placementsToList(placements, raw_dancer):
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
            division_id = DIVISIONS_MAP_INVERTED[division_name]
            for competition in division["competitions"]:
                competition_date = None
                try:
                    competition_date = datetime.datetime.strptime(competition["event"]["date"], '%B %Y')
                except:
                    competition_date = datetime.datetime.strptime("January 1970", '%B %Y')
                if earliest_event is None or competition_date < earliest_event:
                   earliest_event = competition_date
                points = competition["points"]
                if points is None:
                   print("Found 'None' in points for dancer {}".format(dancer["dancer_wsdcid"]))
                   points = 0
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
                    "points": points,
                    "event": event['id'],
                    "date": event["date"],
                    "division": division_id,
                })
    return (final_placements, final_events, earliest_event)

database = {
    "last_updated": datetime.datetime.now().isoformat(),
    'roles': ROLES_MAP,
    'divisions': DIVISIONS_MAP,
    'ordered_skill_divisions': SKILL_DIVISION_PROGRESSION,
    "dancers": [],
    "dancers_count": 0,
    "events": [],
    "events_count": 0,
    'top_dancers_by_points_gained_recently': {},
    'upcoming_events': eventsFromWsdc,
    'new_dancers_over_time': [],
    'division_progression': {"labels": [], "data": []},
}

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
    event['dates'].sort(reverse=True)
    if event['dates'][-1] == new_event['date']:
        # This is the most recent, so update info
        event["name"] = new_event['name']
        event["location"] = new_event['location']
        event["url"] = new_event['url']
  return _events

new_dancers_by_date = {}

def getCompetableDivisions(role_id, placements, primary_role_competable_divisons = None):
  is_primary_role = primary_role_competable_divisons is None
  points_per_division = {}
  for placement in placements:
    if placement["role"] != role_id:
      continue
    if placement["division"] not in points_per_division:
      points_per_division[placement["division"]] = 0
    points_per_division[placement["division"]] += placement["points"]
  competableDivisions = []

  if CHAMPIONS in points_per_division:
    competableDivisions.append(CHAMPIONS)
    if points_per_division[CHAMPIONS] < SKILL_DIVISION_LIMITS[CHAMPIONS][1]:
      competableDivisions.append(ALLSTARS)

  elif ALLSTARS in points_per_division:
    if points_per_division[ALLSTARS] >= SKILL_DIVISION_LIMITS[ALLSTARS][0]:
      competableDivisions.append(CHAMPIONS)
    if points_per_division[ALLSTARS] < SKILL_DIVISION_LIMITS[ALLSTARS][1]:
      competableDivisions.append(ALLSTARS)

  elif ADVANCED in points_per_division:
    if points_per_division[ADVANCED] >= SKILL_DIVISION_LIMITS[ADVANCED][0]:
      competableDivisions.append(ALLSTARS)
    if points_per_division[ADVANCED] < SKILL_DIVISION_LIMITS[ADVANCED][1]:
      competableDivisions.append(ADVANCED)

  elif INTERMEDIATE in points_per_division:
    if points_per_division[INTERMEDIATE] >= SKILL_DIVISION_LIMITS[INTERMEDIATE][0]:
      competableDivisions.append(ADVANCED)
    if points_per_division[INTERMEDIATE] < SKILL_DIVISION_LIMITS[INTERMEDIATE][1]:
      competableDivisions.append(INTERMEDIATE)

  elif NOVICE in points_per_division:
    if points_per_division[NOVICE] >= SKILL_DIVISION_LIMITS[NOVICE][0]:
      competableDivisions.append(INTERMEDIATE)
    if points_per_division[NOVICE] < SKILL_DIVISION_LIMITS[NOVICE][1]:
      competableDivisions.append(NOVICE)

  elif NEWCOMER in points_per_division:
    competableDivisions.append(NOVICE)

  else:
    competableDivisions.append(NOVICE)
    competableDivisions.append(NEWCOMER)

  # Filter competable divions for secondary role
  ## This is done in a "practical" way, in that if they are a champion in their primary role and never competed
  ## in their secondary role, they technically can compete in advanced, but we really doubt that they actually will.
  if not is_primary_role:
    if NOVICE not in primary_role_competable_divisons:
      competableDivisions = [c for c in competableDivisions if c != NEWCOMER]
    if NOVICE not in primary_role_competable_divisons and INTERMEDIATE not in primary_role_competable_divisons and ADVANCED not in primary_role_competable_divisons:
      competableDivisions = [c for c in competableDivisions if c != NOVICE]
    if INTERMEDIATE not in primary_role_competable_divisons and ADVANCED not in primary_role_competable_divisons and ALLSTARS not in primary_role_competable_divisons:
      competableDivisions = [c for c in competableDivisions if c != INTERMEDIATE]

  return competableDivisions

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
    leader = placementsToList(datum["leader"]["placements"], datum)
    follower = placementsToList(datum["follower"]["placements"], datum)
    addEarliestPlacement(leader[2], follower[2])
    dancer_placements = leader[0] + follower[0]
    dancer_placements.sort(key=lambda p: p["date"], reverse=True)

    primary_role_id = ROLES_MAP_INVERTED[datum["short_dominate_role"]]
    competable_roles = [LEADER, FOLLOWER]
    primary_role_competable_divisons = getCompetableDivisions(primary_role_id, dancer_placements)
    competable_roles = [r for r in competable_roles if r != primary_role_id]
    divisions = {
      primary_role_id: primary_role_competable_divisons
    }
    for cr in competable_roles:
      divisions[cr] = getCompetableDivisions(cr, dancer_placements, primary_role_competable_divisons)

    res = {
      'id': datum['dancer_wsdcid'],
      # 'pro': datum["is_pro"] == 1,
      'primary_role': primary_role_id,
      'name': "{} {}".format(datum["dancer_first"], datum["dancer_last"]),
      'placements': dancer_placements,
      'divisions': divisions,
    }
    if len(res['placements']) > 0:
        database["dancers"].append(res)
        database["events"] = addEvents(database["events"], leader[1])
        database["events"] = addEvents(database["events"], follower[1])

database["events"].sort(key=lambda kv: kv["id"], reverse=True)

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

database["dancers"].sort(key=lambda kv: kv["id"], reverse=True)

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


# Division Progression
divisions_plus_top = database['ordered_skill_divisions']
data_all_by_key = {}

for dancer in database["dancers"]:
  earliest_date_by_division = {}

  for placement in dancer["placements"]:
    if dancer["primary_role"] != placement["role"]:
      continue

    placement_date = datetime.date.fromisoformat(placement["date"])
    if not placement["division"] in earliest_date_by_division:
      earliest_date_by_division[placement["division"]] = placement_date
    elif placement_date < earliest_date_by_division[placement["division"]]:
        earliest_date_by_division[placement["division"]] = placement_date

  for i in range(1, len(divisions_plus_top)):
    from_division = divisions_plus_top[i-1]
    to_division = divisions_plus_top[i]
    if not (from_division in earliest_date_by_division and to_division in earliest_date_by_division):
      continue
    from_division_date = earliest_date_by_division[from_division]
    to_division_date = earliest_date_by_division[to_division]
    days = abs((to_division_date - from_division_date).days)
    if from_division not in data_all_by_key:
      data_all_by_key[from_division] = []
    data_all_by_key[from_division].append(days)

for i in range(0, len(divisions_plus_top) - 1):
  from_division = divisions_plus_top[i]
  database["division_progression"]["labels"].append(database["divisions"][from_division])
  database["division_progression"]["data"].append(data_all_by_key[from_division])

# End Division Progression

database["dancers_count"] = len(database["dancers"])
database["events_count"] = len(database["events"])

# Write out locations
with open(LOCATION_CACHE_FILE, 'w') as f:
  json.dump(location_cache, f)

# Write to file, leave at bottom of this script
with open("../assets/database.txt", 'bw') as f:
    contents = msgpack.packb(database)
    f.write(contents)

# Write only events to file, leave at bottom of this script
with open("../assets/events.txt", 'bw') as f:
    contents = msgpack.packb({ "events": database["events"] })
    f.write(contents)

# Write to json for jekyll, leave at bottom of this script
with open("../_data/database.json", 'w') as f:
    json.dump(database, f)

# Write out chunked dancers # WARNING THIS MODIFIES THE DATABASE OBJECT
i = 0
max_wsdc_id = database["dancers"][0]["id"]
while i <= max_wsdc_id:
  top = i + CHUNKED_DANCERS_SIZE
  chunk_ingress = [d for d in database["dancers"] if d["id"] >= i and d["id"] < top]
  for dancer in chunk_ingress:
      dancer["primary_role"] = database["roles"][dancer["primary_role"]]
      for placement in dancer["placements"]:
        placement["division"] = database["divisions"][placement["division"]]
        placement["role"] = database["roles"][placement["role"]]
        placement["event"] = [e for e in database["events"] if e["id"] == placement["event"]][0]
        if "dates" in placement["event"]:
          del placement["event"]["dates"]
        if "url" in placement["event"]:
          del placement["event"]["url"]
      dancer["divisions"] = {database["roles"][k]:[database["divisions"][d] for d in v] for k,v in dancer["divisions"].items()}
  with open("../assets/chunks/dancers_{}-{}.txt".format(i, i+CHUNKED_DANCERS_SIZE), 'bw') as f:
    contents = msgpack.packb({"dancers": chunk_ingress},)
    f.write(contents)
  i += CHUNKED_DANCERS_SIZE
