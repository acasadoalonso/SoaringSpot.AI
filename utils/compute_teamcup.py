#!/usr/bin/env python3
"""Compute the FAI Team Cup (Sporting Code 8.5) for WGC 2026 (contest 5249)
from the three get_class_results JSON files retrieved via the SoaringSpot MCP."""
import json, glob, os
from collections import defaultdict

TR = "/home/angel/.claude/projects/-home-angel-SS/f95e2f75-3659-409f-8d8b-cc551ad9ac9a/tool-results"
FILES = {
    "20m":  f"{TR}/mcp-soaringspot-get_class_results-1780127963967.txt",
    "18m":  f"{TR}/mcp-soaringspot-get_class_results-1780127964677.txt",
    "Open": f"{TR}/mcp-soaringspot-get_class_results-1780127965440.txt",
}
RES_KEY = "http://api.soaringspot.com/rel/class_results"
PILOT_RES_KEY = "http://api.soaringspot.com/rel/results"
CON_KEY = "http://api.soaringspot.com/rel/contestant"

# data[cls][date] = {"winner": float, "pilots": {team: [points,...launched]}, "nolaunch": {team:count}}
data = defaultdict(dict)
team_classes = defaultdict(set)      # team -> set of classes it has entries in (any day)
notcomp = 0
all_dates = set()

for cls, fn in FILES.items():
    j = json.load(open(fn))
    for task in j["_embedded"][RES_KEY]:
        if task["task_number"] < 1:        # skip practice days
            continue
        date = task["task_date"]
        all_dates.add(date)
        results = task["_embedded"][PILOT_RES_KEY]
        launched = []          # (team, points)
        nolaunch = []          # team (entered but no valid launch)
        for r in results:
            con = r["_embedded"][CON_KEY]
            team = con["team"]
            if con.get("not_competing"):
                globals().__setitem__("notcomp", notcomp+1)
            team_classes[team].add(cls)
            has_start = "scored_start" in r and r["scored_start"]
            if has_start:
                launched.append((team, r["points"]))
            else:
                nolaunch.append(team)
        winner = max((p for _, p in launched), default=0)
        bteam = defaultdict(list)
        for team, p in launched:
            bteam[team].append(p)
        bnl = defaultdict(int)
        for team in nolaunch:
            bnl[team] += 1
        data[cls][date] = {"winner": winner, "pilots": dict(bteam), "nolaunch": dict(bnl)}

dates = sorted(all_dates)
classes = list(FILES.keys())
all_teams = sorted(team_classes)
eligible = {t for t in all_teams if len(team_classes[t]) >= 2}

print(f"Dates (valid competition days): {len(dates)} -> {dates}")
print(f"not_competing pilot-entries encountered: {notcomp}")
print("\nTeam class membership (entries):")
for t in all_teams:
    mark = "" if t in eligible else "   <-- INELIGIBLE (only 1 class)"
    print(f"  {t}: {sorted(team_classes[t])}{mark}")

def tcs(points, winner):            # Competitor's Team Cup Score, 8.5.3.b
    return points - winner + 1000

# ---- per team per day ----
exception_log = []
team_daily = defaultdict(dict)      # team -> {date: daily_score}
for t in sorted(eligible):
    for d in dates:
        entries = []                       # competitor team-cup scores this day
        classes_rep = []                   # classes with a valid launch
        for cls in classes:
            cell = data[cls].get(d)
            if not cell:
                continue
            for p in cell["pilots"].get(t, []):
                entries.append(tcs(p, cell["winner"]))
                classes_rep.append(cls)
        # 8.5.4.b narrow exception: representation reduced below 2 classes
        if len(set(classes_rep)) < 2:
            # add zero-day-score entries from unrepresented classes where team
            # entered but had no valid launch, until 2 classes are represented
            reps = set(classes_rep)
            for cls in classes:
                if len(reps) >= 2:
                    break
                if cls in reps:
                    continue
                cell = data[cls].get(d)
                if cell and cell["nolaunch"].get(t):
                    entries.append(tcs(0, cell["winner"]))   # day score = 0
                    reps.add(cls)
                    exception_log.append((t, d, cls))
        if entries:
            team_daily[t][d] = round(sum(entries) / len(entries), 2)

# ---- Team Cup Score, 8.5.5 ----
final = []
for t in sorted(eligible):
    ds = team_daily[t]
    if not ds:
        continue
    score = round(sum(ds.values()) / len(ds), 2)
    final.append((t, score, len(ds)))

final.sort(key=lambda x: -x[1])

print("\n8.5.4.b exception triggered:", exception_log if exception_log else "never")
print("\n================ TEAM CUP STANDINGS (WGC 2026) ================")
print(f"{'Rank':<5}{'Team':<6}{'TeamCupScore':>14}{'Days':>6}")
medals = {1:"GOLD", 2:"SILVER", 3:"BRONZE"}
for i, (t, s, n) in enumerate(final, 1):
    m = medals.get(i, "")
    print(f"{i:<5}{t:<6}{s:>14.2f}{n:>6}   {m}")

# ---- detail for medal teams ----
print("\n---- Daily Team Scores (all eligible teams) ----")
hdr = "Team  " + "".join(f"{d[5:]:>9}" for d in dates) + "   Avg"
print(hdr)
for t, s, n in final:
    row = f"{t:<6}" + "".join(f"{team_daily[t].get(d,'-'):>9}" for d in dates) + f"   {s:.2f}"
    print(row)
