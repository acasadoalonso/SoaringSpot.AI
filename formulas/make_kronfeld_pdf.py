#!/usr/bin/env python3
"""Render the Robert-Kronfeld-Challenge Cup result to a PDF using fpdf2 + DejaVu (Unicode)."""
from fpdf import FPDF

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
DARK = (33, 41, 54); GREY = (90, 100, 115); LINE = (210, 215, 222)
HEAD_BG = (33, 41, 54); ZEBRA = (244, 246, 249)
GOLD = (212, 175, 55); SILVER = (160, 168, 178); BRONZE = (176, 124, 78)

# Open Task 9 (28 May 2026, task 10541334540) — 848.08 km racing task.
# All finishers scored the full task distance -> tie on Marking Distance,
# broken by highest speed (rule c). Sorted by scored_speed descending.
DIST_M = 848075.6875
finishers = [  # (number, name, team, glider, speed_m_s, finish_local)
    ("FL",  "Felipe Levin",       "GER", "EB 29R",        39.7765, "17:25:43"),
    ("YY",  "Sebastian Kawa",     "POL", "JS5",           38.7214, "17:23:11"),
    ("OR",  "Michael Sommer",     "GER", "EB 29R",        38.6561, "17:48:01"),
    ("5",   "Laurent Aboulin",    "FRA", "JS5",           38.6420, "17:39:01"),
    ("72",  "Sylvain Gerbaud",    "FRA", "EB 29R",        38.4894, "17:40:27"),
    ("4D",  "David Jansen",       "AUS", "JS5",           38.2499, "17:54:14"),
    ("UFO", "Max Leenders",       "NED", "EB 29DR",       37.2584, "17:39:33"),
    ("XR",  "Bas Seijffert",      "NED", "EB 29R",        37.2502, "17:39:30"),
    ("OG",  "Oscar Goudriaan",    "RSA", "JS5",           37.0290, "18:01:38"),
    ("IP3", "Pierre de Broqueville","BEL","EB 29DR",      36.9645, "18:02:04"),
    ("1E",  "Russell Cheetham",   "GBR", "JS5",           36.7801, "17:32:16"),
    ("EX",  "Tomas Rendla",       "CZE", "EB 29R",        36.6973, "17:30:19"),
    ("ZFI", "Jiri Kusbach",       "CZE", "JS1C TJ 21m",   35.6634, "17:41:20"),
    ("B",   "Jan Buch-Madsen",    "DEN", "JS3 RES 18m",   35.0459, "17:47:48"),
]

def kmh(v): return v * 3.6

class PDF(FPDF):
    def footer(self):
        self.set_y(-12); self.set_font("DejaVu","",8); self.set_text_color(*GREY)
        self.cell(0,6,f"Page {self.page_no()}/{{nb}}",align="C")

pdf = PDF(orientation="P", unit="mm", format="A4")
pdf.add_font("DejaVu","",f"{FONT_DIR}/DejaVuSans.ttf")
pdf.add_font("DejaVu","B",f"{FONT_DIR}/DejaVuSans-Bold.ttf")
pdf.add_font("DejaVu","I",f"{FONT_DIR}/DejaVuSans.ttf")  # no oblique file; reuse regular
pdf.set_auto_page_break(True, margin=16)
pdf.alias_nb_pages()
pdf.add_page()
W = pdf.w - pdf.l_margin - pdf.r_margin

def h(txt,size,color=DARK,style="B",sp=2,align="L"):
    pdf.set_font("DejaVu",style,size); pdf.set_text_color(*color)
    pdf.multi_cell(W,size*0.5+1,txt,align=align); pdf.ln(sp)

# ---- Title block ----
h("Robert-Kronfeld-Challenge Cup",18,DARK,"B",1)
h("40th FAI World Gliding Championships (WGC 2026)",12,GREY,"B",3)
pdf.set_font("DejaVu","",9.5); pdf.set_text_color(*DARK)
meta = [
 ("Location","Częstochowa-Rudniki, Poland"),
 ("Dates","16–30 May 2026"),
 ("Eligible classes","Open · 18 Metre · 20 Metre Multi-Seat"),
 ("Award","Pilot who flew the longest Marking Distance during the WGC"),
 ("Data source","SoaringSpot (contest 5249), via soaringspot MCP"),
]
for k,v in meta:
    pdf.set_font("DejaVu","B",9.5); pdf.cell(34,5.4,k)
    pdf.set_font("DejaVu","",9.5); pdf.multi_cell(W-34,5.4,v)
pdf.ln(3)

# ---- Winner ----
h("Winner",13,DARK,"B",1)
y=pdf.get_y()
pdf.set_fill_color(*GOLD); pdf.rect(pdf.l_margin,y,3,9,"F")
pdf.set_x(pdf.l_margin+5)
pdf.set_font("DejaVu","B",13); pdf.set_text_color(*DARK)
pdf.cell(0,9,"Felipe Levin  (GER) — EB 29R")
pdf.ln(11)
pdf.set_font("DejaVu","",9.5); pdf.set_text_color(*DARK)
pdf.multi_cell(W,5.2,
 "Flew the longest Marking Distance of the championship — 848.08 km on Open Task 9 "
 "(28 May 2026) — and, in the tie among all finishers of that task, attained it at the "
 "highest speed: 143.2 km/h (39.78 m/s). He also won the day with 1000 points.")
pdf.ln(3)

# ---- The decisive task ----
h("The decisive task",13,DARK,"B",1)
pdf.set_font("DejaVu","",9.5); pdf.set_text_color(*DARK)
task_meta = [
 ("Task","Open — TASK A · RACING (task 10541334540)"),
 ("Date","28 May 2026 (contest day 9)"),
 ("Task distance","848.08 km (848,075.69 m) — the longest task of the entire WGC"),
 ("Type","Racing task: every finisher is scored the full task distance"),
 ("Result","14 pilots completed → tie on Marking Distance → decided on speed (rule c)"),
]
for k,v in task_meta:
    pdf.set_font("DejaVu","B",9.5); pdf.cell(30,5.4,k)
    pdf.set_font("DejaVu","",9.5); pdf.multi_cell(W-30,5.4,v)
pdf.ln(2)
pdf.set_font("DejaVu","I",8.5); pdf.set_text_color(*GREY)
pdf.multi_cell(W,4.6,
 "Why this task decides the Cup: across all three eligible classes, no other task — "
 "racing or AAT — produced a longer marking distance. The next-longest racing tasks were "
 "18 m Task 9 (755 km) and 20 m Task 9 (616 km); the longest AAT maximum (Open Task 10) "
 "was only ~611 km. So 848.08 km is the unique championship maximum.")
pdf.ln(3)

# ---- Tie-break table ----
h("Tie-break — finishers of the 848.08 km task, by speed (rule c)",12,DARK,"B",1)
cols=[("#",12,"C"),("Pilot",50,"L"),("Team",16,"C"),("Glider",34,"L"),
      ("Speed (km/h)",26,"R"),("Finish",20,"R")]
tw=sum(c[1] for c in cols); x0=pdf.l_margin+(W-tw)/2
# header
pdf.set_x(x0); pdf.set_fill_color(*HEAD_BG)
pdf.set_font("DejaVu","B",9); pdf.set_text_color(255,255,255)
for label,w,al in cols: pdf.cell(w,7,label,align="C",fill=True)
pdf.ln(7)
for i,(num,name,team,glider,sp,fin) in enumerate(finishers):
    z = ZEBRA if i%2 else (255,255,255)
    win = (i==0)
    pdf.set_x(x0)
    for (label,w,al),txt in zip(cols,[num,name,team,glider,f"{kmh(sp):.1f}",fin]):
        pdf.set_fill_color(*z)
        pdf.set_font("DejaVu","B" if win else "",9)
        pdf.set_text_color(*(GOLD if win else DARK))
        pdf.cell(w,6.4,str(txt),align=al,fill=True)
    pdf.ln(6.4)
pdf.set_draw_color(*LINE); pdf.set_x(x0); pdf.line(x0,pdf.get_y(),x0+tw,pdf.get_y())
pdf.ln(2)
pdf.set_font("DejaVu","I",8.5); pdf.set_text_color(*GREY)
pdf.multi_cell(W,4.6,
 "All 14 pilots were scored the same Marking Distance of 848,075.69 m. Felipe Levin holds "
 "the highest speed, so the tie is settled at rule (c); the rule (d) earliest-outlanding "
 "tiebreak is not needed. (A 15th starter, C. Hynek/AUT, was scored 778.08 km under "
 "SC3A 1.4.5.3 and so did not reach the full task distance.)")
pdf.ln(3)

# ---- Methodology ----
h("Award rules (Robert-Kronfeld-Challenge Cup)",12,DARK,"B",1)
pdf.set_font("DejaVu","",9); pdf.set_text_color(*DARK)
notes=[
 "a.  The Cup is presented to a pilot flying at the WGC in the Open, 18 m or 20 m Multi-Seat classes.",
 "b.  The winner flew the longest Marking Distance during the WGC, regardless of task type (taken directly from the results).",
 "c.  Tie on longest Marking Distance → won by the pilot who attained it at the highest speed.",
 "d.  Tie with no highest speed → broken by the earliest out-landing time.",
]
for n in notes: pdf.multi_cell(W,5,"•  "+n); pdf.ln(0.5)
pdf.ln(1)
pdf.set_font("DejaVu","I",8); pdf.set_text_color(*GREY)
pdf.multi_cell(W,4.5,
 "Result reflects the currently published official scores on SoaringSpot (contest 5249). "
 "Marking Distance = each pilot's scored task distance; speed = scored task speed.")

out="/home/angel/SS/reports/SS.WGC2026_kronfeld_cup.pdf"
pdf.output(out); print("WROTE",out)
