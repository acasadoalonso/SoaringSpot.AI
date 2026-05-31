#!/usr/bin/env python3
"""Render the WGC 2026 Team Cup standings to a PDF using fpdf2 + DejaVu (Unicode)."""
from fpdf import FPDF

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
DARK = (33, 41, 54); GREY = (90, 100, 115); LINE = (210, 215, 222)
HEAD_BG = (33, 41, 54); ZEBRA = (244, 246, 249)
GOLD = (212, 175, 55); SILVER = (160, 168, 178); BRONZE = (176, 124, 78)

standings = [
    (1,"GER",928.46),(2,"FRA",909.78),(3,"POL",883.48),(4,"HUN",879.10),
    (5,"BEL",839.63),(6,"GBR",835.92),(7,"NED",834.58),(8,"SUI",814.90),
    (9,"AUS",811.33),(10,"CZE",803.90),(11,"FIN",797.10),(12,"AUT",795.52),
    (13,"ITA",765.60),(14,"SVK",765.43),(15,"LTU",760.03),(16,"DEN",691.47),
]
dates = ["05-19","05-20","05-21","05-22","05-23","05-24","05-26","05-27","05-28","05-29"]
daily = {
 "GER":[948.80,945.40,963.80,955.80,987.00,915.60,946.20,903.00,923.00,796.00],
 "FRA":[885.40,799.40,962.40,947.00,930.20,914.00,935.20,909.40,923.00,891.80],
 "POL":[841.75,912.75,916.50,896.75,943.00,933.50,726.00,821.25,921.50,921.75],
 "HUN":[857.33,820.00,969.67,864.67,904.33,910.67,904.67,953.67,897.67,708.33],
 "BEL":[903.00,695.33,916.67,868.00,894.00,904.67,890.33,716.67,918.33,689.33],
 "GBR":[843.50,919.50,861.25,858.00,854.50,829.00,713.25,828.00,883.50,768.75],
 "NED":[808.40,783.00,866.20,881.00,845.20,855.60,822.20,874.80,868.00,741.40],
 "SUI":[872.00,653.00,766.50,855.00,901.50,737.50,798.50,837.50,867.50,860.00],
 "AUS":[806.00,801.50,746.33,892.67,715.00,772.75,844.00,845.25,877.75,812.00],
 "CZE":[793.00,796.00,878.00,806.00,847.50,714.50,794.50,836.33,820.33,752.83],
 "FIN":[928.67,563.67,828.33,893.00,580.33,833.33,805.67,810.67,849.33,878.00],
 "AUT":[852.00,697.00,865.00,802.75,841.25,756.00,887.25,757.00,777.50,719.50],
 "ITA":[859.67,813.00,747.67,852.33,757.33,709.33,784.00,753.67,854.00,525.00],
 "SVK":[848.67,683.67,749.00,786.67,628.33,821.67,834.67,791.00,701.67,809.00],
 "LTU":[907.00,888.00,822.33,808.67,604.33,666.67,782.33,845.33,612.33,663.33],
 "DEN":[664.67,611.67,809.67,751.67,728.33,523.33,664.33,802.67,788.67,569.67],
}

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1: return
        self.set_font("DejaVu","",8); self.set_text_color(*GREY)
        self.cell(0,6,"FAI Team Cup — WGC 2026",align="L")
        self.ln(8)
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
h("FAI Team Cup — Final Standings",18,DARK,"B",1)
h("40th FAI World Gliding Championships (WGC 2026)",12,GREY,"B",3)
pdf.set_font("DejaVu","",9.5); pdf.set_text_color(*DARK)
meta = [
 ("Location","Częstochowa-Rudniki, Poland"),
 ("Dates","16–30 May 2026"),
 ("Classes","20 Metre Multi-Seat · 18 Metre · Open"),
 ("Valid days","10 (19–24 & 26–29 May) — all official in every class"),
 ("Scoring","FAI Sporting Code §8.5 (Team Cup)"),
 ("Data source","SoaringSpot (contest 5249), via soaringspot MCP"),
]
for k,v in meta:
    pdf.set_font("DejaVu","B",9.5); pdf.cell(28,5.4,k)
    pdf.set_font("DejaVu","",9.5); pdf.multi_cell(W-28,5.4,v)
pdf.ln(3)

# ---- Medals ----
h("Medals",13,DARK,"B",1)
medal_rows=[("Gold","GER (Germany)","928.46",GOLD),
            ("Silver","FRA (France)","909.78",SILVER),
            ("Bronze","POL (Poland)","883.48",BRONZE)]
cw=[34,W-34-30,30]
for place,team,score,col in medal_rows:
    y=pdf.get_y()
    pdf.set_fill_color(*col); pdf.rect(pdf.l_margin,y,3,8,"F")
    pdf.set_x(pdf.l_margin+5)
    pdf.set_font("DejaVu","B",11); pdf.set_text_color(*DARK)
    pdf.cell(cw[0]-5,8,place,border=0)
    pdf.set_font("DejaVu","",11); pdf.cell(cw[1],8,team)
    pdf.set_font("DejaVu","B",11); pdf.cell(cw[2],8,score,align="R")
    pdf.ln(8.5)
pdf.ln(3)

# ---- Full standings table ----
h("Full standings (16 eligible teams)",13,DARK,"B",1)
cols=[("Rank",18,"C"),("Team",30,"L"),("Team Cup Score",40,"R"),("Days scored",30,"C")]
tw=sum(c[1] for c in cols); x0=pdf.l_margin+(W-tw)/2
def row(cells,fill=None,bold=False,tc=DARK,hcol=None):
    pdf.set_x(x0); y=pdf.get_y()
    for (label,w,al),txt in zip(cols,cells):
        if fill: pdf.set_fill_color(*fill)
        pdf.set_font("DejaVu","B" if bold else "",9.5)
        pdf.set_text_color(*(hcol or tc))
        pdf.cell(w,6.6,str(txt),border=0,align=al,fill=bool(fill))
    pdf.ln(6.6)
# header
pdf.set_x(x0); pdf.set_fill_color(*HEAD_BG)
pdf.set_font("DejaVu","B",9.5); pdf.set_text_color(255,255,255)
for label,w,al in cols: pdf.cell(w,7,label,align="C",fill=True)
pdf.ln(7)
for i,(r,t,s) in enumerate(standings):
    z = ZEBRA if i%2 else (255,255,255)
    accent = {1:GOLD,2:SILVER,3:BRONZE}.get(r)
    row([r,t,f"{s:.2f}","10"],fill=z,bold=(r<=3),
        hcol=accent if accent else DARK)
pdf.set_draw_color(*LINE); pdf.set_x(x0); pdf.line(x0,pdf.get_y(),x0+tw,pdf.get_y())
pdf.ln(4)

# ---- Daily scores (landscape page) ----
pdf.add_page(orientation="L")
Wl = pdf.w - pdf.l_margin - pdf.r_margin
h("Daily Team Scores",13,DARK,"B",1)
tcol=20; dcol=(Wl-tcol-22)/len(dates); acol=22
pdf.set_fill_color(*HEAD_BG); pdf.set_text_color(255,255,255); pdf.set_font("DejaVu","B",8.5)
pdf.cell(tcol,7,"Team",align="L",fill=True)
for d in dates: pdf.cell(dcol,7,d,align="R",fill=True)
pdf.cell(acol,7,"Avg",align="R",fill=True); pdf.ln(7)
for i,(r,t,s) in enumerate(standings):
    z = ZEBRA if i%2 else (255,255,255)
    pdf.set_fill_color(*z); pdf.set_text_color(*DARK)
    pdf.set_font("DejaVu","B",8.5); pdf.cell(tcol,6,t,align="L",fill=True)
    pdf.set_font("DejaVu","",8.5)
    for v in daily[t]: pdf.cell(dcol,6,f"{v:.2f}",align="R",fill=True)
    pdf.set_font("DejaVu","B",8.5); pdf.cell(acol,6,f"{s:.2f}",align="R",fill=True); pdf.ln(6)
pdf.ln(4)

# ---- Methodology / notes ----
h("Methodology (FAI Sporting Code §8.5)",12,DARK,"B",1)
pdf.set_font("DejaVu","",9); pdf.set_text_color(*DARK)
notes=[
 "§8.5.3  Competitor's Team Cup Score = own day score − class winner's day score + 1000, for each pilot with a valid launch in a class that had a valid competition day.",
 "§8.5.4(a)  Team's Daily Score = mean of its competitors' Team Cup Scores across all classes that flew that day (2 dp). Pilots without a valid launch are excluded.",
 "§8.5.5  Team Cup Score = (sum of Team's Daily Scores) ÷ (days the team scored), to 2 dp.",
 "§8.5.6  Gold / Silver / Bronze awarded to the three highest Team Cup Scores.",
]
for n in notes: pdf.multi_cell(Wl,5,"•  "+n); pdf.ln(0.5)
pdf.ln(2)
h("Eligibility & edge cases",12,DARK,"B",1)
pdf.set_font("DejaVu","",9)
notes2=[
 "§8.5.2 (2-class minimum): Excluded as ineligible — ARG, RSA (one class only) and ESP, EST, JAP, NOR, SLO, SWE, USA (18 Metre only). 16 teams qualified.",
 "§8.5.4(b) zero-score backfill: never triggered — every eligible team had a valid launch in ≥2 classes on all 10 days.",
 "Non-launchers (given no score): 18 Metre day 10 (4 pilots); Open days 3 & 4 (1 each).",
 "No not_competing entries appeared in the scored results.",
]
for n in notes2: pdf.multi_cell(Wl,5,"•  "+n); pdf.ln(0.5)
pdf.ln(1)
pdf.set_font("DejaVu","I",8); pdf.set_text_color(*GREY)
pdf.multi_cell(Wl,4.5,"Standings reflect the currently published official scores. If any day is later rescored, re-running compute_teamcup.py will update these figures.")

out="/home/angel/SS/SS.WGC2026_teamcup_standings.pdf"
pdf.output(out); print("WROTE",out)
