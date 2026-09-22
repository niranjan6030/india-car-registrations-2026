"""Render the analysis charts used in the README and the LinkedIn carousel."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

import os

PROJ = Path(__file__).resolve().parent.parent
FIG = PROJ / "figures"
FIG.mkdir(exist_ok=True)
# BARE=1 renders the same charts without titles, for the LinkedIn carousel
# (the carousel page supplies its own heading)
BARE = os.environ.get("BARE") == "1"
PREFIX = "bare_" if BARE else ""

BG, CARD, TEXT, MUTED = "#0B1220", "#111A2E", "#E6ECF5", "#94A3B8"
EV, ICE, ACCENT, GRID = "#22C55E", "#3B82F6", "#F59E0B", "#1F2B45"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": CARD, "savefig.facecolor": BG,
    "text.color": TEXT, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": GRID, "grid.color": GRID, "font.family": "DejaVu Sans",
    "axes.titlesize": 15, "axes.titleweight": "bold", "figure.dpi": 130,
})

df = pd.read_csv(PROJ / "data/clean/tableau_cars_flat.csv", parse_dates=["Month"])
df["is_ev"] = df["Is EV"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]


def style(ax, title, sub=None):
    if BARE:
        title, sub = "", None
    ax.set_title(title, color=TEXT, pad=30 if sub else 12, loc="left")
    if sub:
        ax.text(0, 1.03, sub, transform=ax.transAxes, color=MUTED, fontsize=10.5, va="bottom")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.grid(axis="x", alpha=0.35)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / (PREFIX + name), bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print("wrote", PREFIX + name)


# 1. EV share climbing month by month -------------------------------------------------
m = df.groupby("Month Name", sort=False).apply(
    lambda g: pd.Series({"ev": g.loc[g.is_ev, "Registrations"].sum(),
                         "all": g.Registrations.sum(),
                         "days": g["Days Covered"].max()}), include_groups=False).reindex(MONTHS)
m["share"] = m.ev / m["all"] * 100

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(MONTHS, m.share, color=EV, linewidth=3, marker="o", markersize=9,
        markerfacecolor=EV, markeredgecolor=BG, markeredgewidth=2)
ax.fill_between(MONTHS, m.share, color=EV, alpha=0.12)
for x, y in zip(MONTHS, m.share):
    ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0, 12),
                ha="center", color=TEXT, fontsize=11, fontweight="bold")
ax.set_ylim(0, m.share.max() * 1.25)
ax.set_ylabel("EV share of new cars")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
style(ax, "Electric share of new cars doubled in six months",
      "India, 1 Jan – 17 Jun 2026 · Vahan registrations")
save(fig, "01_ev_share_trend.png")

# 2. Brand market share ---------------------------------------------------------------
b = df.groupby("Brand").Registrations.sum().sort_values(ascending=False)
top = b.head(10)[::-1]
fig, ax = plt.subplots(figsize=(9, 5.5))
colors = [ACCENT if i == len(top) - 1 else ICE for i in range(len(top))]
ax.barh(top.index, top / 1e5, color=colors, height=0.72)
for i, v in enumerate(top / 1e5):
    ax.text(v + 0.15, i, f"{v:.1f}L  ({v * 1e5 / b.sum() * 100:.1f}%)", va="center",
            color=TEXT, fontsize=10)
ax.set_xlim(0, (top / 1e5).max() * 1.25)
ax.set_xlabel("Cars registered (lakh)")
style(ax, "Maruti Suzuki takes 37.6% of the market",
      "Top 10 brands · 22.9 lakh passenger cars")
save(fig, "02_top_brands.png")

# 3. Who sells the EVs ----------------------------------------------------------------
ev = df[df.is_ev].groupby("Brand").Registrations.sum().sort_values(ascending=False).head(7)[::-1]
allb = df.groupby("Brand").Registrations.sum()
fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(ev.index, ev / ev.sum() * 100, color=EV, height=0.7)
ax.barh(ev.index, [allb[i] / allb.sum() * 100 for i in ev.index], color=ICE, height=0.3, alpha=0.9)
ax.set_xlabel("Share (%)")
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=EV),
                   plt.Rectangle((0, 0), 1, 1, color=ICE)],
          labels=["Share of India's EVs", "Share of all cars"],
          facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, loc="lower right")
style(ax, "Tata, Mahindra and MG sell 84% of India's electric cars",
      "Maruti leads the market overall but not the EV transition")
save(fig, "03_ev_brands.png")

# 4. State EV adoption ----------------------------------------------------------------
st = df.groupby("State").agg(total=("Registrations", "sum"))
st["ev"] = df[df.is_ev].groupby("State").Registrations.sum()
st = st[st.total >= 5000].dropna()
st["share"] = st.ev / st.total * 100
s = st.sort_values("share", ascending=False).head(12)[::-1]
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(s.index, s.share, color=[EV if v >= 8 else ICE for v in s.share], height=0.72)
for i, v in enumerate(s.share):
    ax.text(v + 0.15, i, f"{v:.1f}%", va="center", color=TEXT, fontsize=10)
ax.set_xlabel("EV share of new cars (%)")
ax.set_xlim(0, s.share.max() * 1.2)
style(ax, "Chandigarh and Delhi lead EV adoption",
      "States and UTs with more than 5,000 cars registered")
save(fig, "04_state_ev_share.png")

# 5. What the raw '4W' bucket actually contains ---------------------------------------
seg = pd.read_csv(PROJ / "data/clean/tableau_4w_segments.csv")
seg = seg.sort_values("registrations", ascending=False)
other = seg[~seg.segment.eq("Passenger car")]
fig, ax = plt.subplots(figsize=(9, 5))
wedges, *_ = ax.pie(
    [seg.registrations.iloc[0], other.registrations.sum()],
    labels=["Passenger cars\n22.9 lakh", "Not cars\n5.1 lakh"],
    colors=[ICE, ACCENT], startangle=90, counterclock=False,
    wedgeprops=dict(width=0.42, edgecolor=BG, linewidth=3),
    textprops=dict(color=TEXT, fontsize=12, fontweight="bold"))
ax.text(0, 0, "18%\nnot cars", ha="center", va="center", color=ACCENT,
        fontsize=16, fontweight="bold")
if not BARE:
    ax.set_title("Vahan's \"4-wheeler\" category is 18% tractors and trailers",
                 color=TEXT, loc="center", pad=18)
lines = "\n".join(f"{r.segment}: {r.registrations:,}" for r in other.head(5).itertuples())
ax.text(1.15, 0.5, "Removed during cleaning\n\n" + lines, transform=ax.transAxes,
        color=MUTED, fontsize=10, va="center")
save(fig, "05_data_quality.png")

# 6. Registrations per day, EV vs rest ------------------------------------------------
p = df.pivot_table(index="Month Name", columns="Powertrain", values="Registrations",
                   aggfunc="sum").reindex(MONTHS)
days = df.groupby("Month Name")["Days Covered"].max().reindex(MONTHS)
p = p.div(days, axis=0)
fig, ax = plt.subplots(figsize=(9, 5))
ax.stackplot(MONTHS, p["Petrol/Diesel/CNG/Hybrid"], p["Electric (EV)"],
             colors=[ICE, EV], alpha=0.9, labels=["Petrol / diesel / CNG", "Electric"])
ax.legend(facecolor=CARD, edgecolor=GRID, labelcolor=TEXT, loc="upper right")
ax.set_ylabel("Cars registered per day")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
style(ax, "January is the peak: 16,551 cars a day",
      "Per-day figures, because June holds only 17 days of data")
save(fig, "06_daily_trend.png")
