# SoaringSpot — Context

## What is SoaringSpot

**SoaringSpot** is the central repository of gliding (sailplane) championships. It
holds the complete record of competitions, from local contests to world
championships, and serves as the authoritative source for scoring, tasks, and
participant data in the gliding community.

## Governing rules

World and Continental gliding championships are run under the FAI Sporting Code.
The authoritative ruleset is **Annex A to Section 3 — FAI Rules for World and
Continental Gliding Championships**:

- [SC3A 2025a (PDF)](https://www.fai.org/sites/default/files/document/file/SC3A_2025a.pdf)

These rules define class definitions, eligibility, task setting, scoring, and the
team competition — the framework behind the contests, tasks, and results stored in
SoaringSpot.

## What it contains

SoaringSpot stores, for every championship, the full competition dataset:

- **Contests** — each gliding championship or competition event, including
  location, dates, organizing body, and the classes being flown.
- **Classes** — the competition categories within a contest (e.g. Club, Standard,
  15-Metre, 18-Metre, Open, Two-Seater), each with its own contestants, tasks,
  and results.
- **Tasks** — the daily flight assignments set for each class: turnpoints,
  task type (Assigned/AAT/etc.), distances, opening/closing times, and the
  task geometry. Tasks can be downloaded (e.g. as XML) for flight computers.
- **Pilots / Contestants** — the competitors entered in each class, with their
  details, glider type, competition number, and nationality.
- **Results** — scored outcomes at every level: per-task points and rankings,
  cumulative class standings, contest winners, and individual flight scores.
- **Flights** — individual recorded flights tied to a pilot and a task, with
  the scoring data and downloadable artifacts.
- **Locations & Images** — venue/location data and associated imagery for
  contests and tasks.

## Data hierarchy

```
Contest
 └── Class
      ├── Contestants (pilots)
      ├── Tasks
      │    └── Task points / Task results
      └── Class results (overall standings)
```

## How to access it using an scrapper

In the case that the user is asking to use an scrapper, use the following URL

https://www.soaringspot.com/en_gb/ + competition ID

after that get the pilot list and Tasks & Results

## How to access it (MCP tools)

A `soaringspot` MCP server is available to query the platform. The general
workflow is to discover competitions, then drill down into classes, tasks, and
results:

1. `list_contests` — discover available championships.
2. `get_contest` / `get_contest_classes` — inspect a contest and its classes.
3. `get_class` / `get_class_contestants` / `get_class_tasks` / `get_class_results`
   — drill into a class.
4. `get_task` / `get_task_points` / `get_task_results` / `get_task_download_xml`
   — inspect individual tasks and their scoring.
5. `get_contestant` / `get_flight` — look up individual pilots and flights.
6. `get_contest_winners` — retrieve final standings.

Supporting tools include `get_location`, `get_image`, `get_task_images`,
`get_contest_downloads`, and `get_server_time`.

### Credentials are per-competition

The API credentials (`SOARINGSPOT_CLIENT_ID` / `SOARINGSPOT_SECRET`) are issued by a
single competition's admin panel and are **valid only for that one competition** —
they are *not* universal keys for all of SoaringSpot. The client ID is even prefixed
with the contest ID (e.g. `5249_…` for WGC 2026). Querying a different competition
requires that competition's own credentials.
The credentials for an specific competitions are under the directory SoaringSpot 
and within that directory on a subdirectory that matches the name with the 
competition name, for example SoaringSpot/wgc2026/clientid or
SoaringSpot/wgc2026/secretkey

### If the MCP server is down

If the `soaringspot` MCP server is unreachable, start it locally by running the
provided script, which exports the credentials and launches the server:

```bash
./run.sh
```

It serves on `http://0.0.0.0:9009/soaringspot`. Point the MCP client at that URL and
retry the query.

## A real example — WGC 2026, Poland

To make the hierarchy concrete, here is a live contest pulled straight from the
`soaringspot` MCP — the **40th FAI World Gliding Championships** (contest `5249`).

- **Contest** — *40th FAI World Gliding Championships*, 16–30 May 2026,
  Częstochowa-Rudniki, Poland (`PL`), time zone `Europe/Warsaw`, location `12563`.
  Public page: <http://www.soaringspot.com/en_gb/wgc2026/>
- **Classes** — three were flown, each with its own contestant field, tasks, and standings:

  | Class | ID | Type | Contestants |
  |-------|----|------|------------:|
  | 20 Metre Multi-Seat | `10055` | `double_seater` | 16 |
  | 18 Metre            | `10054` | `18_meter`      | 42 |
  | Open                | `10053` | `open`          | 15 |

- **Tasks** — the final day (task 10, 29 May 2026) was an Assigned Area Task in every
  class, e.g. Open's *"TASK A - AAT - OPEN"* (task `10541334541`): ~444 km nominal,
  315–611 km min/max, 3-hour window — `result_status: official`.
- **Results (overall class champions)** — cumulative standings after all scored days:

  | Class | 🥇 Champion | Team | Glider | Total |
  |-------|-----------|------|--------|------:|
  | Open                | Felipe Levin     | GER | EB 29R    | 8945 |
  | 18 Metre            | Victor Mallick   | FRA | JS3 18m   | 8440 |
  | 20 Metre Multi-Seat | Leucker & Omsels | GER | Arcus T   | 8338 |

  In Open, Sebastian Kawa (POL, JS5) took silver on 8938 — just 7 points behind.

### How this was retrieved

```
get_contest(5249)              → name, dates, location 12563, 3 classes
get_contest_classes(5249)      → classes 10055 / 10054 / 10053
get_class_results(10053)       → Open cumulative standings (champion: Levin)
get_contest_winners(5249)      → per-class final-day podiums
```

This is also the dataset behind `reports/SS.WGC2026_teamcup_standings.md`, where the
same per-task points are aggregated into the FAI Team Cup score.

## Summary

SoaringSpot is the single source of truth for gliding championships — a complete,
queryable archive of **contests, classes, tasks, pilots, and results**.

## Helpers
You can find some python scripts helpers on the utils directory, like compute_teamcup.py
or make_pdf.py
check it before to generate a new ones
