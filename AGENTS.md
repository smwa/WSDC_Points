# WSDC Points — Project Reference

## Project Overview

A Jekyll static site deployed at **wsdc.mechstack.dev** that mirrors and enriches West Coast Swing (WCS) competition data from the [WSDC (World Swing Dance Council)](https://worldsdc.com) registry. It lets dancers look up their points, track division eligibility, explore competition history, and see upcoming sanctioned events.

There is also a companion Android TWA app on Google Play backed by the same URL.

---

## Technical Overview

| Layer | Technology |
|---|---|
| Static site generator | Jekyll |
| Data pipeline | Python 3.13 |
| Frontend JS | Vanilla JS (no framework) |
| Data serialization | MessagePack (`msgpack`) for binary assets; JSON for Jekyll |
| Charts | Chart.js + chartjs-chart-boxplot |
| Search / list | list.min.js |
| Icons | Feather icons |
| Analytics | Matomo (self-hosted at mat.mechstack.dev) |
| CI/CD | GitHub Actions |
| Geocoding | OpenWeatherMap Geocoding API |

### Data Flow

```
WSDC API (points.worldsdc.com)       worldsdc.com/events/
         |                                   |
   dancer_repository.py             event_repository.py
         |                                   |
  raw_responses.json.gz           raw_events.html.gz
         \                               /
          \                             /
                    fetch.py
                       |
        ┌──────────────┼─────────────────┐
        |              |                 |
assets/database.txt  assets/events.txt  assets/chunks/dancers_N-M.txt
(full msgpack)       (events msgpack)   (per-dancer msgpack, 20/file)
        |
  _data/database.json  (Jekyll template data)
        |
  Jekyll build → _site/ → GitHub Pages
```

The data pipeline runs before every Jekyll build. On push to `master`, it runs with `SKIPFETCH=1` (no network calls to WSDC, just re-processes existing cached data). Scheduled GitHub Actions workflows handle actual data refreshes.

---

## Python Data Pipeline (`points/`)

### `dancer_repository.py`

Manages fetching and caching raw dancer data from the WSDC points API.

- **API endpoint**: `POST https://points.worldsdc.com/lookup2020/find` with `num=<wsdc_id>`
- **Cache file**: `points/raw_responses.json.gz` — gzip-compressed JSON dict keyed by `str(wsdc_id)`
- **`get_dancers(fetch_remote, fetch_all)`**: Main entry point.
  - If `fetch_all=True`: Scans every integer WSDC ID from 1 upward until 200 consecutive misses (`get_all_dancers`).
  - If `fetch_all=False`: Re-fetches only dancers with placements in the last 15 months, then scans IDs beyond the current maximum (`get_dancers_abbreviated`).
  - Always loads from `raw_responses.json.gz` first and writes back to it after fetching.

### `event_repository.py`

Fetches upcoming sanctioned events from the WSDC events calendar page.

- **Source**: `GET https://www.worldsdc.com/events/` (HTML table)
- **Cache file**: `points/raw_events.html.gz` — gzip-compressed HTML
- **Location cache**: `points/locations.json` — maps location strings to `(lat, lon)` tuples via OpenWeatherMap API
- Parses the events HTML table with BeautifulSoup, geocodes each event location (with a 1.1 s rate-limit sleep), and returns a list of event dicts including `start_date`, `end_date`, `latitude`, `longitude`.
- Has hardcoded location patches for venues with missing/wrong location strings (e.g., "Swing Fling" → "Washington, D.C., US").

### `fetch.py`

The main processing script. Orchestrates everything.

**Key constants:**
- `LIMIT_TO_DANCE_STYLE = 'West Coast Swing'` — ignores all other dance styles
- `CHUNKED_DANCERS_SIZE = 20` — dancers per chunk file
- `SKILL_DIVISION_PROGRESSION` — ordered list of skill divisions: Newcomer → Novice → Intermediate → Advanced → All-Stars → Champions
- `SKILL_DIVISION_LIMITS` — per-division thresholds for promotion (`can_compete_at`, `must_leave_at`, `min_pts_for_secondary`)

**Processing steps:**
1. Load events (upcoming) and raw dancer responses.
2. For each raw dancer, call `placementsToList()` to flatten the nested API response into a list of `{role, result, points, event, date, division}` placement dicts (WCS only).
3. Compute `divisions` (which division(s) a dancer is eligible to compete in for each role) via `getCompetableDivisions()` and `getSecondaryRoleCompetableDivisions()`.
4. Build the `database` dict with: dancers, events (de-duplicated by ID), division tiers, new dancer counts over time, top rising dancers (last 3 months), and division progression statistics.
5. Derive **event tiers** from first-place points: 3 pts = Tier 1 (5–10 competitors), 6 = Tier 2, 10 = Tier 3, 15 = Tier 4, 20 = Tier 5, 25 = Tier 6.
6. Write `assets/database.txt` (full msgpack, no competitors).
7. Build an **event competitors index** (`event_id → date → [competitor]`) by scanning all dancer placements. Attach the sorted competitor list to each event occurrence date object.
8. Write `assets/events.txt` (events + competitors per occurrence).
9. Strip competitors from the in-memory events list, then write `_data/database.json` (JSON for Jekyll; competitors omitted because they are too large and not needed by any template).
10. Write `assets/chunks/dancers_N-M.txt` — per-dancer msgpack chunks that also include **`points_by_division`** (total points per division per role, precomputed so the dancer page never needs to reduce placements client-side).

**Environment variables:**
- `FULLDANCERCHECK=1` — enables full rescan of all WSDC IDs
- `SKIPFETCH=1` — skips all network calls to WSDC (re-processes cached data only)
- `OPEN_WEATHER_MAP_API_KEY` — required for geocoding new event locations

---

## GitHub Actions Workflows (`.github/workflows/`)

| Workflow | Trigger | Behavior |
|---|---|---|
| `fetch.yml` | Weekly (Thursday 6 AM UTC) + manual | Incremental fetch: re-fetches active dancers + scans new IDs. Rebuilds and commits. |
| `fetchall.yml` | Bi-monthly (1st of every 2nd month, 2 AM UTC) + manual | Full rescan of every WSDC ID (`FULLDANCERCHECK=1`). Slow. |
| `buildnofetch.yml` | Every push + manual | Skips WSDC fetch (`SKIPFETCH=1`), re-processes cached data and commits output. |
| `jekyll.yml` | (standard Jekyll pages deploy) | Builds the Jekyll site for GitHub Pages. |

All fetch workflows use `EndBug/add-and-commit@v9` to commit the generated data files back to the repo.

---

## Web Pages (`pages/`)

All pages use the `default` or `javascripted` layout from `_layouts/default.html`. The layout provides: HTML boilerplate, Matomo analytics, service worker registration, and left/right navigation arrow buttons (using `previous_page`/`next_page` frontmatter).

Client-side data loading is done by `assets/js/index.js`, which fetches msgpack binary files and decodes them with `msgpack.min.js`.

### Navigation Order
Events → Home (/) → Upcoming Events → Dancers On The Rise → Dancers Over Time → Division Progression → About → Dancers → Events

---

### `/` — Home (`pages/index.html`)

Displays last-updated date, total dancer and event counts, and the user's starred/favorite dancers (filtered to those who competed in the last 90 days). Links to the Google Play TWA app.

Favorites are stored in `localStorage.wsdcpoints.favoriteDancers` (array of WSDC IDs).

---

### `/dancer` — Dancer Profile (`pages/dancer.html`)

Shows an individual dancer by WSDC ID (from URL hash `#<id>`). Loads data from the relevant chunk file via `getDancer(id)`.

Displays:
- Name and WSDC ID, with a star/favorite button
- **Can Compete** table: which division(s) the dancer is eligible for, per role
- **Points** table: reads `dancer.points_by_division` (precomputed in chunk files as `{division: {role: total_points}}`)
- **Placements** list: all competition results (date, event link, division, role, placement, points)

---

### `/dancers` — Dancer List (`pages/dancers.html`)

Searchable list of all dancers, powered by list.min.js. Loaded from `assets/database.txt`. Each item links to `/dancer#<id>`.

---

### `/dancers-on-the-rise` — Rising Dancers (`pages/dancers-on-the-rise.html`)

Shows the top 5 dancers per division per role by points earned in the most recent 3 months, rendered server-side from `_data/database.json` via Jekyll Liquid templates. No client-side data loading.

---

### `/dancers-over-time` — New Dancer Growth Chart (`pages/dancers-over-time.html`)

A Chart.js line chart showing the count of new dancers (by earliest competition year) over time. Data is embedded into the page at build time from `site.data.database.new_dancers_over_time`.

---

### `/division-progression` — Division Transition Box Plot (`pages/division-progression.html`)

A chartjs-chart-boxplot box-and-whisker chart showing the distribution of days it took dancers to move from each skill division to the next. Data is embedded at build time. Reveals a "spinner" loading indicator while the chart renders.

---

### `/event` — Single Event (`pages/event.html`)

Displays a single event by WSDC event ID (from URL hash `#<id>`). Loads from `assets/events.txt`.

Shows: event name, location, URL, all dates hosted, and per-date tier information (division × role breakdown). Each date links to the `/event-competitors` page.

---

### `/event-competitors` — Event Competitors (`pages/event-competitors.html`)

Shows competitors at a specific event on a specific date. URL hash format: `#<event_id>:<YYYY-MM-DD>`. Reads directly from `assets/events.txt` (already loaded for the event header); competitor lists are precomputed per event occurrence so no full-database scan is needed.

---

### `/events` — Event List (`pages/events.html`)

Searchable list of all past events, powered by list.min.js. Loaded from `assets/events.txt`. Each item links to `/event#<id>`.

---

### `/upcoming-events` — Upcoming Events (`pages/upcoming-events.html`)

Lists upcoming sanctioned events from `worldsdc.com/events/`. Includes a "Sort By Distance" button that uses the browser's Geolocation API to sort events by proximity. Offers ICS calendar subscription and URL copy. Powered by list.min.js.

---

### `/about` — About (`pages/about.html`)

Static informational page. Contact email and Mechstack.dev attribution.

---

## Raw WSDC API Response Structure

The WSDC points API returns one JSON object per dancer (POST to `/lookup2020/find` with `num=<id>`):

```
Dancer
├── dancer_wsdcid: int           — WSDC registry ID
├── dancer_first: str
├── dancer_last: str
├── is_pro: 0 | 1
├── short_dominate_role: "Leader" | "Follower" | "Switch"
├── short_non_dominate_role: str
├── dominate_required: str       — division abbrev (e.g. "ALS")
├── dominate_allowed: str        — division abbrev (e.g. "CHMP")
├── dominate_role_highest_level: str       — division name
├── dominate_role_highest_level_points: int | "N/A"
├── non_dominate_role_highest_level: str
├── non_dominate_role_highest_level_points: int | "N/A"
├── recent_year: str
├── points_message: str
├── show_chmp_warning: bool
├── leader: RoleObject
├── follower: RoleObject
├── dominate_data: RoleObject
├── non_dominate_data: RoleObject
└── non_dominate_lookup: list

RoleObject
├── type: "dancer"
├── dancer: { id, first_name, last_name, wscid }
├── level: { required, allowed, reason }   — division abbreviations
├── recent_year: str | 0
└── placements: dict | []
    └── "West Coast Swing"
        └── <DIV_ABBREV>   (e.g. "CHMP", "ALS", "ADV", "INT", "NOV", "NEW", ...)
            ├── division: { id: int, name: str, abbreviation: str }
            ├── total_points: int
            ├── wscid: int
            ├── adv_sliding: any
            ├── as_sliding: any
            └── competitions: [ Competition ]

Competition
├── role: "leader" | "follower"
├── points: int
├── result: "1" | "2" | "3" | "4" | "5" | "F"   — F = finalist, did not place top 5
└── event: { id: int, name: str, location: str, url: str, date: "Month YYYY" }
```

**Division IDs and abbreviations:**

| ID | Abbreviation | Name |
|---|---|---|
| 1 | JRS | Juniors |
| 2 | MSTR | Masters |
| 3 | NEW | Newcomer |
| 4 | NOV | Novice |
| 5 | INT | Intermediate |
| 6 | ADV | Advanced |
| 7 | ALS | All-Stars |
| 8 | CHMP | Champions |
| 9 | INV | Invitational |
| 10 | PRO | Professional |
| 12 | SPH | Sophisticated |
| 13 | TCH | Teacher |

Only divisions 3–8 (Newcomer through Champions) are part of the skill progression ladder. The rest are special/invitational categories.

---

## Relational Database Design

If this data were stored in a relational database rather than flat files, a natural schema would be:

```sql
-- Reference tables
CREATE TABLE roles (
    id   INTEGER PRIMARY KEY,  -- 1=Leader, 2=Follower, 3=Switch
    name TEXT NOT NULL
);

CREATE TABLE divisions (
    id           INTEGER PRIMARY KEY,
    abbreviation TEXT NOT NULL,
    name         TEXT NOT NULL,
    is_skill_division BOOLEAN  -- TRUE for the Newcomer→Champions ladder
);

-- Dancer registry
CREATE TABLE dancers (
    id              INTEGER PRIMARY KEY,  -- dancer_wsdcid
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    is_pro          BOOLEAN NOT NULL DEFAULT FALSE,
    primary_role_id INTEGER REFERENCES roles(id)
);

-- Past sanctioned events (recurring events have one row per unique event)
CREATE TABLE events (
    id       INTEGER PRIMARY KEY,  -- WSDC event ID
    name     TEXT NOT NULL,
    location TEXT,
    url      TEXT
);

-- Each time an event was held (events recur annually)
CREATE TABLE event_occurrences (
    id       INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    date     DATE NOT NULL          -- stored as first of month (YYYY-MM-01)
);


-- Competition tier per division/role for each event occurrence
-- Derived from first-place points: 3→Tier1, 6→T2, 10→T3, 15→T4, 20→T5, 25→T6
CREATE TABLE event_occurrence_tiers (
    id                  INTEGER PRIMARY KEY,
    event_occurrence_id INTEGER NOT NULL REFERENCES event_occurrences(id),
    division_id         INTEGER NOT NULL REFERENCES divisions(id),
    role_id             INTEGER NOT NULL REFERENCES roles(id),
    tier                TEXT NOT NULL,
    UNIQUE (event_occurrence_id, division_id, role_id)
);

-- Individual competition placements (core fact table)
CREATE TABLE placements (
    id                  INTEGER PRIMARY KEY,
    dancer_id           INTEGER NOT NULL REFERENCES dancers(id),
    event_occurrence_id INTEGER NOT NULL REFERENCES event_occurrences(id),
    role_id             INTEGER NOT NULL REFERENCES roles(id),
    division_id         INTEGER NOT NULL REFERENCES divisions(id),
    result              TEXT NOT NULL,   -- "1","2","3","4","5","F"
    points              INTEGER NOT NULL
);

-- Upcoming events (sourced from worldsdc.com/events/, refreshed weekly)
CREATE TABLE upcoming_events (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    location   TEXT,
    latitude   REAL,
    longitude  REAL,
    url        TEXT,
    event_type TEXT,
    start_date TIMESTAMP,
    end_date   TIMESTAMP
);
```

**Key relationships:**
- A `dancer` has many `placements`, each linked to an `event_occurrence`, a `role`, and a `division`.
- An `event` has many `event_occurrences` (one per year the event was held).
- `event_occurrence_tiers` is derived from the maximum first-place points seen across `placements` for that occurrence/division/role combination.
- Division eligibility (which division a dancer "can compete in") is computed on-the-fly from aggregated `placements` points using the thresholds in `SKILL_DIVISION_LIMITS` — it is not stored, only derived.

**Recommended indexes:**
```sql
-- Fast lookup of all competitors at an event occurrence (roles/divisions are tiny
-- reference tables; no denormalized competitors table needed)
CREATE INDEX idx_placements_occurrence ON placements(event_occurrence_id);

-- Fast lookup of all placements for a dancer (dancer profile page)
CREATE INDEX idx_placements_dancer ON placements(dancer_id);

-- Fast aggregation of points by dancer+division+role (covering index)
CREATE INDEX idx_placements_dancer_div_role ON placements(dancer_id, division_id, role_id);
```

**Precomputed vs. derived:**

| Data | Where stored | How computed |
|---|---|---|
| Dancer division eligibility | `dancer.divisions` (chunk files) | `getCompetableDivisions()` at pipeline time |
| Points totals per division/role | `dancer.points_by_division` (chunk files) | SUM over placements at pipeline time |
| Event competitors per occurrence | `event.dates[].competitors` (events.txt) | Index over placements at pipeline time; in a relational DB this is just `placements` filtered by `event_occurrence_id` with an index — no separate table needed |
| Rising dancers (last 3 months) | `top_dancers_by_points_gained_recently` (database) | Aggregated at pipeline time |
| New dancers over time | `new_dancers_over_time` (database) | Counted at pipeline time |
| Division progression (days) | `division_progression.data` (database) | Raw day-arrays at pipeline time; box stats computed by Chart.js in browser |
| Event tiers | `event.dates[].divisions` (events.txt + database) | Derived from first-place points at pipeline time |

**Useful derived queries:**
```sql
-- Total points per dancer per division per role
-- (also stored precomputed as dancer.points_by_division in chunk files)
SELECT dancer_id, division_id, role_id, SUM(points) AS total_points
FROM placements
GROUP BY dancer_id, division_id, role_id;

-- Rising dancers: points in last 90 days
SELECT dancer_id, division_id, role_id, SUM(points) AS recent_points
FROM placements p
JOIN event_occurrences eo ON p.event_occurrence_id = eo.id
WHERE eo.date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY dancer_id, division_id, role_id
ORDER BY recent_points DESC;

-- Earliest date a dancer competed in each division (for progression analysis)
SELECT dancer_id, division_id, MIN(eo.date) AS first_competed
FROM placements p
JOIN event_occurrences eo ON p.event_occurrence_id = eo.id
GROUP BY dancer_id, division_id;

-- Event competitors (also stored precomputed in event_occurrence_competitors)
SELECT d.id, d.first_name, d.last_name, r.name AS role, dv.name AS division,
       p.result, p.points
FROM placements p
JOIN dancers d ON p.dancer_id = d.id
JOIN roles r ON p.role_id = r.id
JOIN divisions dv ON p.division_id = dv.id
WHERE p.event_occurrence_id = ?
ORDER BY dv.name, r.name;
```
