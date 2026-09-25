"""Render the one-page executive dashboard (KPI cards, trend, breakdowns, insights)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "figures/00_dashboard.png"

BG, CARD, EDGE = "#0B0B0D", "#17171C", "#2A2A33"
TEXT, MUTED = "#F2F2F5", "#9A9AA6"
ORANGE, ORANGE_D, GREEN, RED = "#F97316", "#C2410C", "#22C55E", "#EF4444"

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT})

df = pd.read_csv(PROJ / "data/clean/tableau_cars_flat.csv", parse_dates=["Month"])
seg = pd.read_csv(PROJ / "data/clean/tableau_4w_segments.csv")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
ev = df[df["Is EV"]]

days = df.groupby("Month Name")["Days Covered"].max().reindex(MONTHS)
by_month = df.groupby("Month Name").Registrations.sum().reindex(MONTHS)
ev_month = ev.groupby("Month Name").Registrations.sum().reindex(MONTHS)
per_day = by_month / days
ev_share_month = ev_month / by_month * 100

TOTAL = int(df.Registrations.sum())
EV_TOTAL = int(ev.Registrations.sum())
PER_DAY = TOTAL / days.sum()
BRANDS = df.Brand.nunique()
states = df.groupby("State").Registrations.sum().sort_values(ascending=False)

fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG)
gs = fig.add_gridspec(nrows=100, ncols=100, left=0.012, right=0.988, top=0.985, bottom=0.015,
                      hspace=0, wspace=0)


def card(x, y, w, h, fill=CARD):
    """Draw a rounded card in figure coordinates and return an axes inside it."""
    fig.patches.append(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.012",
        linewidth=1.2, edgecolor=EDGE, facecolor=fill,
        transform=fig.transFigure, zorder=-5))


def inner(x, y, w, h):
    ax = fig.add_axes([x, y, w, h], zorder=10)
    ax.set_facecolor("none")
    ax.patch.set_alpha(0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    return ax


# ------------------------------------------------------------------ header
card(0.012, 0.902, 0.62, 0.083)
fig.text(0.030, 0.958, "INDIA CAR REGISTRATIONS", fontsize=24, fontweight="bold",
         va="center", color=TEXT)
fig.text(0.318, 0.958, "2026", fontsize=24, fontweight="bold", va="center", color=ORANGE)
fig.text(0.030, 0.920,
         "Vahan Dashboard, MoRTH   |   1 Jan – 17 Jun 2026   |   36 states and UTs   |   "
         "146 raw files cleaned", fontsize=10.5, va="center", color=MUTED)

for i, (label, value) in enumerate([("Segment", "Passenger cars"), ("Powertrain", "All"),
                                    ("Period", "Jan – Jun")]):
    x = 0.645 + i * 0.118
    card(x, 0.902, 0.110, 0.083)
    fig.text(x + 0.010, 0.962, label, fontsize=9.5, va="center", color=MUTED)
    fig.text(x + 0.010, 0.930, value, fontsize=13, va="center", fontweight="bold", color=TEXT)
    fig.text(x + 0.099, 0.930, "▾", fontsize=10, va="center", color=ORANGE)

# ------------------------------------------------------------------ KPI cards
def kpi(x, w, title, value, series, delta, delta_good, note):
    y, h = 0.775, 0.115
    card(x, y, w, h)
    fig.text(x + 0.012, y + h - 0.025, title, fontsize=10.5, color=MUTED, va="center")
    fig.text(x + 0.012, y + h - 0.062, value, fontsize=23, fontweight="bold",
             color=TEXT, va="center")
    colour = GREEN if delta_good else RED
    fig.text(x + 0.012, y + 0.018, ("▲ " if delta_good else "▼ ") + delta,
             fontsize=10.5, color=colour, va="center", fontweight="bold")
    fig.text(x + 0.072, y + 0.018, note, fontsize=8.5, color=MUTED, va="center")
    ax = inner(x + w - 0.082, y + 0.030, 0.070, h - 0.055)
    ax.plot(range(len(series)), series, color=ORANGE, linewidth=2)
    ax.fill_between(range(len(series)), series, min(series) * 0.97, color=ORANGE, alpha=0.18)
    ax.set_xticks([]); ax.set_yticks([])


W, GAP = 0.1876, 0.0075
jun_vs_may = (per_day["Jun"] / per_day["May"] - 1) * 100
ev_pp = ev_share_month["Jun"] - ev_share_month["May"]
ev_growth = (ev_month["Jun"] / days["Jun"]) / (ev_month["May"] / days["May"]) * 100 - 100

kpi(0.012, W, "TOTAL CARS REGISTERED", f"{TOTAL / 1e5:.1f} lakh", by_month.values,
    f"{jun_vs_may:+.1f}%", jun_vs_may > 0, "cars/day, Jun vs May")
kpi(0.012 + (W + GAP), W, "ELECTRIC CARS", f"{EV_TOTAL / 1e5:.2f} lakh", ev_month.values,
    f"{ev_growth:+.1f}%", ev_growth > 0, "EVs/day, Jun vs May")
kpi(0.012 + 2 * (W + GAP), W, "EV SHARE OF NEW CARS", f"{EV_TOTAL / TOTAL * 100:.2f}%",
    ev_share_month.values, f"{ev_pp:+.2f} pp", ev_pp > 0, "Jun vs May")
kpi(0.012 + 3 * (W + GAP), W, "CARS PER DAY", f"{PER_DAY:,.0f}", per_day.values,
    f"{jun_vs_may:+.1f}%", jun_vs_may > 0, "Jun vs May")
kpi(0.012 + 4 * (W + GAP), W, "BRANDS TRACKED", f"{BRANDS}",
    df.groupby("Month Name").Brand.nunique().reindex(MONTHS).values,
    "37.6%", True, "Maruti share of market")

# ------------------------------------------------------------------ row 2
def panel_title(x, y, text, sub=None):
    fig.text(x, y, text, fontsize=12, fontweight="bold", color=TEXT, va="center")
    if sub:
        fig.text(x, y - 0.024, sub, fontsize=9, color=MUTED, va="center")


# monthly trend: bars = cars/day, line = EV share
card(0.012, 0.485, 0.392, 0.272)
panel_title(0.028, 0.735, "Monthly registrations and EV share",
            "bars: cars per day   ·   line: EV share of new cars")
ax = inner(0.040, 0.520, 0.318, 0.155)
ax.bar(MONTHS, per_day.values, color=ORANGE, width=0.62)
for i, v in enumerate(per_day.values):
    ax.text(i, v + 250, f"{v / 1000:.1f}k", ha="center", color=TEXT, fontsize=8.5)
ax.set_ylim(0, per_day.max() * 1.60)
ax.set_yticks([])
ax.tick_params(axis="x", colors=MUTED, labelsize=9)
ax2 = ax.twinx()
ax2.plot(MONTHS, ev_share_month.values, color=GREEN, linewidth=2.4, marker="o", markersize=5)
for i, v in enumerate(ev_share_month.values):
    ax2.text(i, v + 0.20, f"{v:.1f}%", ha="center", color=GREEN, fontsize=8.5,
             fontweight="bold",
             bbox=dict(facecolor=BG, edgecolor="none", alpha=0.80, pad=1.5))
ax2.set_ylim(0, ev_share_month.max() * 1.18)
ax2.set_yticks([])
for s in ax2.spines.values():
    s.set_visible(False)

# brand bars
card(0.412, 0.485, 0.322, 0.272)
panel_title(0.428, 0.735, "Top brands by registrations", "share of the passenger-car market")
brands = df.groupby("Brand").Registrations.sum().sort_values(ascending=False).head(8)[::-1]
ax = inner(0.480, 0.510, 0.232, 0.180)
ax.barh(brands.index, brands.values / 1e5, color=ORANGE, height=0.66)
for i, v in enumerate(brands.values / 1e5):
    ax.text(v + 0.12, i, f"{v:.1f}L", va="center", color=TEXT, fontsize=8.5)
ax.set_xlim(0, (brands.values / 1e5).max() * 1.22)
ax.set_xticks([])
ax.tick_params(axis="y", colors=TEXT, labelsize=9)

# region donut
card(0.742, 0.485, 0.246, 0.272)
panel_title(0.758, 0.735, "Registrations by region")
region = df.groupby("Region").Registrations.sum().sort_values(ascending=False)
ax = inner(0.752, 0.505, 0.130, 0.195)
cols = [ORANGE, "#FB923C", ORANGE_D, "#7C2D12", "#FDBA74", "#9A3412"]
ax.pie(region.values, colors=cols[:len(region)], startangle=90, counterclock=False,
       wedgeprops=dict(width=0.40, edgecolor=BG, linewidth=2))
ax.text(0, 0, f"{TOTAL / 1e5:.1f}L", ha="center", va="center", fontsize=13,
        fontweight="bold", color=TEXT)
for i, (name, val) in enumerate(region.items()):
    yy = 0.700 - i * 0.030
    fig.add_artist(plt.Rectangle((0.896, yy - 0.006), 0.009, 0.013, color=cols[i],
                                 transform=fig.transFigure))
    fig.text(0.910, yy, f"{name}  {val / region.sum() * 100:.1f}%", fontsize=8.8,
             color=MUTED, va="center")

# ------------------------------------------------------------------ row 3
# EV brand split
card(0.012, 0.192, 0.392, 0.278)
panel_title(0.028, 0.448, "Who sells India's electric cars",
            "EV registrations by brand, Jan – Jun 2026")
evb = ev.groupby("Brand").Registrations.sum().sort_values(ascending=False).head(6)[::-1]
ax = inner(0.090, 0.218, 0.290, 0.190)
ax.barh(evb.index, evb.values / 1000, color=GREEN, height=0.62)
for i, v in enumerate(evb.values / 1000):
    ax.text(v + 0.7, i, f"{v:,.0f}k  ({v * 1000 / EV_TOTAL * 100:.1f}%)", va="center",
            color=TEXT, fontsize=8.5)
ax.set_xlim(0, (evb.values / 1000).max() * 1.34)
ax.set_xticks([])
ax.tick_params(axis="y", colors=TEXT, labelsize=9)

# top states
card(0.412, 0.192, 0.322, 0.278)
panel_title(0.428, 0.448, "Top states by registrations", "and their EV share")
top_states = states.head(7)[::-1]
ev_by_state = ev.groupby("State").Registrations.sum()
ax = inner(0.510, 0.218, 0.202, 0.190)
ax.barh(top_states.index, top_states.values / 1e5, color=ORANGE, height=0.62)
for i, (name, v) in enumerate(top_states.items()):
    share = ev_by_state.get(name, 0) / v * 100
    ax.text(v / 1e5 + 0.05, i, f"{v / 1e5:.2f}L   EV {share:.1f}%", va="center",
            color=TEXT, fontsize=8.2)
ax.set_xlim(0, (top_states.values / 1e5).max() * 1.55)
ax.set_xticks([])
ax.tick_params(axis="y", colors=TEXT, labelsize=8.5)

# what is inside the 4W bucket
card(0.742, 0.192, 0.246, 0.278)
panel_title(0.758, 0.448, "What the raw 4W data holds", "before cleaning")
notcar = seg[seg.segment != "Passenger car"].registrations.sum()
ax = inner(0.752, 0.212, 0.130, 0.200)
ax.pie([seg.registrations.iloc[0], notcar], colors=[ORANGE, "#3F3F46"], startangle=90,
       counterclock=False, wedgeprops=dict(width=0.40, edgecolor=BG, linewidth=2))
ax.text(0, 0, "18%\nnot cars", ha="center", va="center", fontsize=11,
        fontweight="bold", color=TEXT)
rows = seg[seg.segment != "Passenger car"].head(4)
for i, r in enumerate(rows.itertuples()):
    yy = 0.400 - i * 0.030
    fig.text(0.892, yy, f"{r.segment[:26]}", fontsize=8.2, color=MUTED, va="center")
    fig.text(0.892, yy - 0.014, f"{r.registrations:,}", fontsize=8.2, color=ORANGE,
             va="center")

# ------------------------------------------------------------------ row 4: insights
card(0.012, 0.015, 0.722, 0.162)
panel_title(0.028, 0.155, "What the data says")
lines = [
    f"EV share climbed every month: {ev_share_month['Jan']:.1f}% in January to "
    f"{ev_share_month['Jun']:.1f}% in June, ending at {EV_TOTAL / TOTAL * 100:.2f}% overall.",
    "Maruti Suzuki holds 37.6% of the market but only 4.4% of EVs; Tata, Mahindra and "
    "MG together sell 84% of every electric car.",
    f"January is the peak at {per_day['Jan']:,.0f} cars a day against a "
    f"{PER_DAY:,.0f} average, as buyers wait for the new model year.",
    "Chandigarh (12.7%) and Delhi (10.3%) lead EV adoption; Haryana's 0.4% points to "
    "a reporting gap rather than low demand.",
    f"{notcar / (notcar + seg.registrations.iloc[0]) * 100:.0f}% of the raw 4-wheeler "
    "category is tractors, trailers and construction equipment, removed before analysis.",
]
for i, line in enumerate(lines):
    yy = 0.122 - i * 0.0235
    fig.text(0.030, yy, "•", fontsize=10, color=ORANGE, va="center")
    fig.text(0.040, yy, line, fontsize=9.6, color=TEXT, va="center")

# ------------------------------------------------------------------ row 4: origin mix
card(0.742, 0.015, 0.246, 0.162)
panel_title(0.758, 0.155, "Where the brands come from")
origin = df.groupby("Origin Country").Registrations.sum().sort_values(ascending=False).head(5)
ax = inner(0.790, 0.035, 0.150, 0.088)
ax.barh(origin.index[::-1], origin.values[::-1] / 1e5, color=ORANGE, height=0.6)
for i, v in enumerate(origin.values[::-1] / 1e5):
    ax.text(v + 0.15, i, f"{v:.1f}L", va="center", color=TEXT, fontsize=8)
ax.set_xlim(0, (origin.values / 1e5).max() * 1.45)
ax.set_xticks([])
ax.tick_params(axis="y", colors=TEXT, labelsize=8.5)

fig.savefig(OUT, facecolor=BG)
print(f"wrote {OUT}")
