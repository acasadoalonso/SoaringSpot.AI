---
name: wgc2026-kronfeld-result
description: WGC 2026 (contest 5249) data location and the computed Robert Kronfeld Cup winner
metadata:
  type: reference
---

WGC 2026 = SoaringSpot contest **5249**, Częstochowa-Rudniki, Poland, 16–30 May 2026. Classes: Open (`10053`), 18 Metre (`10054`), 20 Metre Multi-Seat (`10055`). 10 competition days (2026-05-19 .. 2026-05-29).

**Saved MCP tool-results** (authoritative, used when MCP server on localhost:9009 is down):
`/home/angel/.claude/projects/-home-angel-SS/f95e2f75-3659-409f-8d8b-cc551ad9ac9a/tool-results/`
- `mcp-soaringspot-get_class_results-1780127963967.txt` = 20m
- `mcp-soaringspot-get_class_results-1780127964677.txt` = 18m
- `mcp-soaringspot-get_class_results-1780127965440.txt` = Open
`class_results` JSON: `_embedded["http://api.soaringspot.com/rel/class_results"]` = list of tasks; each task `_embedded[".../rel/results"]` = pilot results; each pilot `_embedded[".../rel/contestant"]`.

**Robert Kronfeld Cup winner (WGC 2026): Felipe Levin (GER, EB 29R, CN "FL"), Open class.**
Longest marking distance of the meet = 848.076 km on Task 9 (2026-05-28, Open, polygon/assigned task, status official). 14 Open pilots tied at that full distance; Levin won on highest speed 143.20 km/h (next: Kawa 139.40, Sommer 139.16). See [[kronfeld-cup-formula]].
