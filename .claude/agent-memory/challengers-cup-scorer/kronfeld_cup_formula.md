---
name: kronfeld-cup-formula
description: How to compute the Robert Kronfeld Challenge Cup (a Challengers Cup) from SoaringSpot WGC data
metadata:
  type: project
---

The Robert-Kronfeld-Challenge Cup is awarded at a World Gliding Championships across the **Open, 18m, and 20m Multi-Seat** classes combined.

Rule (from `/home/angel/SS/robert.kronfeld.challenge.cup.formula.md`):
- Winner = pilot who flew the **longest Marking Distance** on any single task during the WGC, regardless of task type. It is NOT a cumulative sum — it is the single longest scored distance.
- Tie-break c): if tie on marking distance, highest **speed** on that task wins.
- Tie-break d): if still tied (no speed, e.g. outlandings), earliest **outlanding/finish time** wins.

**Data mapping in `get_class_results`** (the authoritative fields):
- Marking Distance = pilot result `scored_distance` (meters).
- Speed = `scored_speed` (m/s; ×3.6 for km/h).
- Outlanding/finish time = `scored_finish` (ISO timestamp). Used for tie-break d.
- Skip practice days: `task_number < 1` (or None).

**Why:** the formula explicitly says it can be read off the results list, no special recomputation needed.
**How to apply:** load all three classes' `get_class_results`, collect every (pilot, task) `scored_distance`, take the global max; resolve ties by speed then finish time. A full Assigned/polygon task day typically produces many pilots tied at the exact task distance, so the speed tie-break usually decides it.

See [[wgc2026-kronfeld-result]] for the WGC 2026 outcome.
