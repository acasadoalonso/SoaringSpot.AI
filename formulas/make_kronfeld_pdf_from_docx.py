#!/usr/bin/env python3
"""Render the Robert Kronfeld Challenge Cup report to PDF, mirroring the .docx layout.
Uses fpdf2 + DejaVu (Unicode) so emoji-free glyphs and accents render correctly."""
from fpdf import FPDF
from fpdf.enums import XPos, YPos

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
NAVY = (31, 58, 95); GOLD = (184, 134, 11); GREY = (85, 85, 85)
DARK = (33, 41, 54); LINE = (210, 215, 222)
HEAD_BG = (31, 58, 95); WINROW = (252, 243, 214)

# Standings: rank, pilot, CN, team, glider, dist_km, speed_kmh
rows = [
    (1,  "Felipe Levin",          "FL",  "GER", "EB 29R",      "848.076", "143.20"),
    (2,  "Sebastian Kawa",        "YY",  "POL", "JS5",         "848.076", "139.40"),
    (3,  "Michael Sommer",        "OR",  "GER", "EB 29R",      "848.076", "139.16"),
    (4,  "Laurent Aboulin",       "5",   "FRA", "JS5",         "848.076", "139.11"),
    (5,  "Sylvain Gerbaud",       "72",  "FRA", "EB 29R",      "848.076", "138.56"),
    (6,  "David Jansen",          "4D",  "AUS", "JS5",         "848.076", "137.70"),
    (7,  "Max Leenders",          "UFO", "NED", "EB 29DR",     "848.076", "134.13"),
    (8,  "Bas Seijffert",         "XR",  "NED", "EB 29R",      "848.076", "134.10"),
    (9,  "Oscar Goudriaan",       "OG",  "RSA", "JS5",         "848.076", "133.30"),
    (10, "Pierre de Broqueville", "IP3", "BEL", "EB 29DR",     "848.076", "133.07"),
    (11, "Russell Cheetham",      "1E",  "GBR", "JS5",         "848.076", "132.41"),
    (12, "Tomas Rendla",          "EX",  "CZE", "EB 29R",      "848.076", "132.11"),
    (13, "Jiri Kusbach",          "ZFI", "CZE", "JS1C TJ 21m", "848.076", "128.39"),
    (14, "Jan Buch-Madsen",       "B",   "DEN", "JS3 RES 18m", "848.076", "126.17"),
]
MEDAL = {1: "1st", 2: "2nd", 3: "3rd"}

class PDF(FPDF):
    def footer(self):
        self.set_y(-12); self.set_font("DejaVu", "", 8); self.set_text_color(*GREY)
        self.cell(0, 6, f"Page {self.page_no()}/{{nb}}", align="C")

pdf = PDF(orientation="P", unit="mm", format="A4")
pdf.add_font("DejaVu", "", f"{FONT_DIR}/DejaVuSans.ttf")
pdf.add_font("DejaVu", "B", f"{FONT_DIR}/DejaVuSans-Bold.ttf")
pdf.add_font("DejaVu", "I", f"{FONT_DIR}/DejaVuSans.ttf")
pdf.set_auto_page_break(True, margin=16)
pdf.alias_nb_pages()
pdf.add_page()
W = pdf.w - pdf.l_margin - pdf.r_margin

# ---- Title ----
pdf.set_font("DejaVu", "B", 20); pdf.set_text_color(*NAVY)
pdf.cell(0, 11, "Robert Kronfeld Challenge Cup", align="C"); pdf.ln(11)
pdf.set_font("DejaVu", "B", 12); pdf.set_text_color(*GOLD)
pdf.cell(0, 7, "Final Result", align="C"); pdf.ln(11)

# ---- Meta block ----
meta = [
    ("Competition", "40th FAI World Gliding Championships (WGC 2026)"),
    ("Location", "Częstochowa-Rudniki, Poland"),
    ("Dates", "16–30 May 2026"),
    ("Eligible classes", "Open · 18 Metre · 20 Metre Multi-Seat"),
    ("Award rule", "Longest single-task Marking Distance of the WGC, any task type"),
    ("Tie-breaks", "(c) highest speed on that task, then (d) earliest outlanding time"),
    ("Data source", "SoaringSpot (contest 5249), retrieved live via the soaringspot MCP"),
]
for k, v in meta:
    pdf.set_x(pdf.l_margin)
    pdf.set_font("DejaVu", "B", 9.5); pdf.set_text_color(*NAVY)
    pdf.cell(38, 5.6, k + ":", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("DejaVu", "", 9.5); pdf.set_text_color(*DARK)
    pdf.cell(W - 38, 5.6, v, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
pdf.ln(2)
pdf.set_draw_color(*LINE); pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + W, pdf.get_y())
pdf.ln(4)

# ---- Winner callout ----
pdf.set_font("DejaVu", "B", 13); pdf.set_text_color(*GOLD)
pdf.cell(0, 7, "WINNER", align="C"); pdf.ln(8)
pdf.set_font("DejaVu", "B", 17); pdf.set_text_color(*NAVY)
pdf.cell(0, 8, "Felipe Levin (GER)", align="C"); pdf.ln(8)
pdf.set_font("DejaVu", "", 10); pdf.set_text_color(*GREY)
pdf.cell(0, 6, "EB 29R · comp. no. FL · Open class", align="C"); pdf.ln(6)
pdf.set_font("DejaVu", "B", 12); pdf.set_text_color(*DARK)
pdf.cell(0, 7, "848.076 km  @  143.20 km/h  —  Task 9, 28 May 2026", align="C"); pdf.ln(11)

# ---- How the Cup was decided ----
pdf.set_font("DejaVu", "B", 13); pdf.set_text_color(*NAVY)
pdf.cell(0, 7, "How the Cup was decided"); pdf.ln(8)
pdf.set_font("DejaVu", "", 9.5); pdf.set_text_color(*DARK)
pdf.multi_cell(W, 5.2,
    "The Robert Kronfeld Cup is not a cumulative-points ranking. It is awarded to the pilot — "
    "across the Open, 18 Metre and 20 Metre Multi-Seat classes — who flew the single longest "
    "Marking Distance on any one task of the championship, regardless of task type. The longest "
    "task of the meet was the Open-class racing (polygon) task on 28 May 2026 (Task 9), "
    "848.076 km, status official. Fourteen Open pilots completed the full marked distance and "
    "therefore tie on Marking Distance, so tie-break (c) — highest speed on that task — decides "
    "the Cup. Felipe Levin's 143.20 km/h was clear of the field, so the outlanding-time "
    "tie-break (d) was not required.")
pdf.ln(4)

# ---- Standings table ----
pdf.set_font("DejaVu", "B", 11.5); pdf.set_text_color(*NAVY)
pdf.multi_cell(W, 6, "Standings — pilots who flew the longest Marking Distance "
                     "(848.076 km), ranked by speed")
pdf.ln(1)
cols = [("Rank", 16, "C"), ("Pilot", 46, "L"), ("CN", 14, "C"), ("Team", 16, "C"),
        ("Glider", 32, "L"), ("Marking dist.", 28, "R"), ("Speed (km/h)", 26, "R")]
tw = sum(c[1] for c in cols); x0 = pdf.l_margin + (W - tw) / 2
pdf.set_x(x0); pdf.set_fill_color(*HEAD_BG)
pdf.set_font("DejaVu", "B", 9); pdf.set_text_color(255, 255, 255)
for label, w, al in cols:
    pdf.cell(w, 7, label, align="C", fill=True)
pdf.ln(7)
for r in rows:
    rank, pilot, cn, team, glider, dist, speed = r
    win = (rank == 1)
    rank_txt = MEDAL.get(rank, "") + (" " if rank in MEDAL else "") + str(rank)
    pdf.set_x(x0)
    pdf.set_fill_color(*(WINROW if win else (255, 255, 255)))
    pdf.set_text_color(*DARK)
    vals = [rank_txt, pilot, cn, team, glider, f"{dist} km", speed]
    for (label, w, al), txt in zip(cols, vals):
        pdf.set_font("DejaVu", "B" if win else "", 9)
        pdf.cell(w, 6.4, txt, align=al, fill=True, border=0)
    pdf.ln(6.4)
pdf.set_draw_color(*LINE); pdf.set_x(x0); pdf.line(x0, pdf.get_y(), x0 + tw, pdf.get_y())
pdf.ln(4)

# ---- Notes ----
pdf.set_font("DejaVu", "B", 11); pdf.set_text_color(*NAVY)
pdf.cell(0, 6, "Notes"); pdf.ln(7)
notes = [
    "Marking Distance is taken from SoaringSpot's scored_distance field; speed from scored_speed "
    "(stored in m/s and converted to km/h). On a fully completed racing task, scored distance "
    "equals the task distance for all finishers — which is exactly why the 14-way tie arises and "
    "the speed tie-break is decisive.",
    "Next-best Marking Distance anywhere in the championship was 778.076 km (also Open Task 9, "
    "Christian Hynek, who did not finish for speed). The longest 18 Metre distance was 755.198 km "
    "(Karol Staryszak), confirming Open as the deciding class.",
    "Practice days were excluded. Result based on the official Task 9 results "
    "(result_status: official), re-pulled live from the soaringspot MCP server.",
]
pdf.set_font("DejaVu", "", 9); pdf.set_text_color(*GREY)
for n in notes:
    pdf.multi_cell(W, 4.8, "•  " + n); pdf.ln(0.8)

out = "/home/angel/SS/reports/SS.WGC2026_kronfeld_cup.pdf"
pdf.output(out); print("WROTE", out)
