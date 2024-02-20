import requests
import json
from time import sleep
from os import walk
from pathlib import Path
import json
import datetime

API_URL = "https://points.worldsdc.com/lookup2020/find"
NONE_SLIDE_LIMIT = 10
RAW_RESPONSE_DIR = './raw'
LIMIT_TO_DANCE_STYLE = 'West Coast Swing'
ROLES_MAP = {
    1: 'Leader',
    2: 'Follower',
    3: 'Switch',
}
DIVISIONS_MAP = {
    12: 'Teacher',
    11: 'Advanced',
    10: 'Masters',
    9: 'Novice',
    8: 'Intermediate',
    7: 'Champions',
    6: 'Invitational',
    5: 'All-Stars',
    4: 'Sophisticated',
    3: 'Professional',
    2: 'Juniors',
    1: 'Newcomer',
}
ROLES_MAP_INVERTED = dict((v, k) for k, v in ROLES_MAP.items())
DIVISIONS_MAP_INVERTED = dict((v, k) for k, v in DIVISIONS_MAP.items())

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

def get_all_dancers():
    current_wsdc_id = 0
    none_slide = 0

    while True:
      if current_wsdc_id % 500 == 0:
        print("Getting", current_wsdc_id)
      res = get_dancer("{}".format(current_wsdc_id))
      if res is None:
        print("Empty result on {}".format(current_wsdc_id))
        none_slide += 1
        if none_slide >= NONE_SLIDE_LIMIT:
          print("Quitting")
          break
      else:
        none_slide = 0
        with open("{}/{:05d}.json".format(RAW_RESPONSE_DIR, current_wsdc_id), 'w') as f:
          json.dump(res, f)
      current_wsdc_id += 1
      sleep(1)

# get_all_dancers() # TODO Uncomment

filenames = next(walk('{}/'.format(RAW_RESPONSE_DIR)), (None, None, []))[2]
filenames.sort()

raw_response_dancers = []

for f in filenames:
    dancer = json.load(open("{}/{}".format(RAW_RESPONSE_DIR, f), "r"))
    raw_response_dancers.append(dancer)

def placementsToList(placements):
    final_placements = []
    final_events = []
    if type(placements) is list:
        return (final_placements, final_events)
    for style_key in placements: # style_key is "West Coast Swing"
        if style_key != LIMIT_TO_DANCE_STYLE:
          continue
        style = placements[style_key] # style is {"NOV": {"division": {id: 3, name: newcomer, abbreviation: NEW}}}
        for division_key in style:
            division = style[division_key]
            division_name = division["division"]["name"].title()
            division_name = DIVISIONS_MAP_INVERTED[division_name]
            for competition in division["competitions"]:
                event = {
                    **competition["event"],
                    "date": datetime.datetime.strptime(competition["event"]["date"], '%B %Y').date().isoformat()
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
    return (final_placements, final_events)

database = {
    "last_updated": datetime.datetime.now().isoformat(),
    'roles': ROLES_MAP,
    'divisions': DIVISIONS_MAP,
    "dancers": [],
    "events": [],
    'top_dancers_by_points_gained_recently': {},
    'past_events_that_may_be_recurring': [],
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

for datum in raw_response_dancers:
    leader = placementsToList(datum["leader"]["placements"])
    follower = placementsToList(datum["follower"]["placements"])
    res = {
      'id': datum['dancer_wsdcid'],
      'pro': datum["is_pro"] == 1,
      'first': datum["dancer_first"],
      'last': datum["dancer_last"],
      'placements': leader[0] + follower[0],
    }
    if len(res['placements']) > 0:
        database["dancers"].append(res)
        database["events"] = addEvents(database["events"], leader[1])
        database["events"] = addEvents(database["events"], follower[1])


# Find "rising stars", top 5 for each role/division by points received in the last 6 months

min_date = (datetime.date.today().replace(day=1) - datetime.timedelta(days=180)).replace(day=1) # 6 months ago
from_each_group = 5

roles = {} # [leader/follower][novice/beginner/advanced][wscdid] = points

for dancer in database["dancers"]:
    for placement in dancer["placements"]:
        if datetime.date.fromisoformat(placement["date"]) < min_date:
            continue
        _points = placement["points"]
        _division = placement["division"]
        _role = placement["role"]
        if _role not in roles:
            roles[_role] = {}
        if _division not in roles[_role]:
            roles[_role][_division] = {}
        if dancer['id'] not in roles[_role][_division]:
            roles[_role][_division][dancer['id']] = 0
        roles[_role][_division][dancer['id']] += _points

sorted_roles = {}
for role in roles:
    sorted_roles[role] = {}
    for division in roles[role]:
        chunked_sorted = sorted(roles[role][division].items(), key=lambda item: item[1], reverse=True)[0:from_each_group]
        sorted_roles[role][division] = [d[0] for d in chunked_sorted]

database["top_dancers_by_points_gained_recently"] = sorted_roles


# Past events that may be coming back up
min_date = (datetime.date.today().replace(day=1) - datetime.timedelta(days=(30 * 12))).replace(day=1) # 12 months ago
max_date = (datetime.date.today().replace(day=1) - datetime.timedelta(days=(30 * 10))).replace(day=1) # 10 months ago

for event in database['events']:
  valid_dates = [d for d in event['dates'] if datetime.date.fromisoformat(d) >= min_date and datetime.date.fromisoformat(d) <= max_date]
  if len(valid_dates) > 0:
    database["past_events_that_may_be_recurring"].append(event['id'])

# Write to file, leave at bottom of this script
with open("../spa/src/assets/database.json", 'w') as f:
    json.dump(database, f)
