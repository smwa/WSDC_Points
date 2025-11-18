import requests
from bs4 import BeautifulSoup
import json
import re
import datetime
import gzip
import time

# Why do you do this to us, WSDC?
LOCATION_PATCHES = {
   "Swing Fling": "Washington, D.C., US",
   "Monterey Swing Fest": "Monterey, CA"
}

LOCATION_CACHE_FILE = "./locations.json"
RAW_EVENTS_RESPONSE_FILE = './raw_events.html.gz'

def _get_location(name: str, location: str, location_cache, OPEN_WEATHER_MAP_API_KEY):
  if (location == "" or location is None) and name not in LOCATION_PATCHES:
     print("Location patch miss for '{}'".format(name))
  if (location == "" or location is None) and name in LOCATION_PATCHES:
     location = LOCATION_PATCHES[name]
  if location in location_cache:
     return (location_cache[location], location_cache)
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
    return ([], location_cache)
  jsonResult = r.json()
  if len(jsonResult) < 1:
    print("No results for location {}".format(location))
    location_cache[location] = []
    return ([], location_cache)
  ret = None
  latitude = jsonResult[0]["lat"]
  longitude = jsonResult[0]["lon"]
  ret = (latitude, longitude)
  location_cache[location] = ret
  return (ret, location_cache)

def _parseEventsFromWsdcEventsPageHtml(html, OPEN_WEATHER_MAP_API_KEY):
  soup = BeautifulSoup(html, 'html.parser')
  rows = soup.find("table").find_all("tr")[1:]
  ret = []

  location_cache = {}
  with open(LOCATION_CACHE_FILE, "r") as f:
    location_cache = json.load(f)

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
    (latlon, location_cache) = _get_location(name, location, location_cache, OPEN_WEATHER_MAP_API_KEY)
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

  # Write out locations
  with open(LOCATION_CACHE_FILE, 'w') as f:
    json.dump(location_cache, f)

  return ret

def get_events(fetch_remote: bool, OPEN_WEATHER_MAP_API_KEY) -> list[dict]:
  if fetch_remote:
    eventsPageResponse = requests.get("https://www.worldsdc.com/events/")
    if eventsPageResponse.status_code == 200:
      with open(RAW_EVENTS_RESPONSE_FILE, 'wb') as f:
        raw_events_html_compressed = gzip.compress(bytes(eventsPageResponse.text, 'utf-8'))
        f.write(raw_events_html_compressed)
  with open(RAW_EVENTS_RESPONSE_FILE, "rb") as f:
    raw_events_html = gzip.decompress(f.read()).decode('utf-8')
    eventsFromWsdc = _parseEventsFromWsdcEventsPageHtml(raw_events_html, OPEN_WEATHER_MAP_API_KEY)
  return eventsFromWsdc
