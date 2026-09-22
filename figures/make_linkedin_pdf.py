"""Build the LinkedIn carousel PDF (square pages, one idea per page)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

PROJ = Path(__file__).resolve().parent.parent
FIG = PROJ / "figures"
OUT = PROJ / "India_Car_Market_2026_LinkedIn.pdf"

BG, CARD, TEXT, MUTED = "#0B1220", "#111A2E", "#E6ECF5", "#94A3B8"
EV, ICE, ACCENT = "#22C55E", "#3B82F6", "#F59E0B"
SIZE = 10  # inches square -> 1080px at 108 dpi

plt.rcParams.update({"font.family": "DejaVu Sans"})


def page(pdf):
    fig = plt.figure(figsize=(SIZE, SIZE), facecolor=BG)
    return fig


def rule(fig, y=0.885):
    fig.add_artist(plt.Line2D([0.08, 0.2], [y, y], color=ACCENT, linewidth=5))


def title_page(pdf):
    fig = page(pdf)
    fig.text(0.08, 0.72, "India's car market,\nfirst half of 2026", color=TEXT,
             fontsize=44, fontweight="bold", va="top", linespacing=1.2)
    rule(fig, 0.78)
    fig.text(0.08, 0.45, "22.9 lakh cars.\n1.19 lakh of them electric.",
             color=ACCENT, fontsize=27, va="top", linespacing=1.4)
    fig.text(0.08, 0.28,
             "Cleaned from 146 raw government files\n"
             "Vahan Dashboard, Ministry of Road Transport & Highways\n"
             "1 January – 17 June 2026",
             color=MUTED, fontsize=16, va="top", linespacing=1.7)
    fig.text(0.08, 0.08, "Niranjan S  ·  BCA, Christ University", color=TEXT, fontsize=15)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def chart_page(pdf, image, heading, note):
    fig = page(pdf)
    fig.text(0.08, 0.93, heading, color=TEXT, fontsize=26, fontweight="bold", va="top")
    ax = fig.add_axes([0.05, 0.21, 0.90, 0.64])
    ax.imshow(mpimg.imread(FIG / ("bare_" + image)))
    ax.axis("off")
    fig.text(0.08, 0.15, note, color=MUTED, fontsize=15, va="top", linespacing=1.6)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def stat_page(pdf, heading, stats, footer):
    fig = page(pdf)
    fig.text(0.08, 0.90, heading, color=TEXT, fontsize=30, fontweight="bold", va="top")
    rule(fig, 0.845)
    y = 0.72
    for big, small in stats:
        fig.text(0.08, y, big, color=ACCENT, fontsize=40, fontweight="bold", va="top")
        fig.text(0.08, y - 0.075, small, color=TEXT, fontsize=17, va="top")
        y -= 0.175
    fig.text(0.08, 0.10, footer, color=MUTED, fontsize=14, va="top", linespacing=1.6)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


def closing_page(pdf):
    fig = page(pdf)
    fig.text(0.08, 0.88, "How it was built", color=TEXT, fontsize=30,
             fontweight="bold", va="top")
    rule(fig, 0.835)
    steps = [
        ("Collect", "146 raw .xlsx exports — 36 states and UTs, all-fuel and EV-only, two snapshots"),
        ("Clean", "Python + pandas: two export layouts, trade-certificate codes stripped from\n"
                  "maker names, 614 names normalised to 607"),
        ("Classify", "Rule-based mapping of legal entities to brands, parent groups and origin\n"
                     "countries; tractors, trailers and JCBs separated out"),
        ("Validate", "State totals reconciled against the national file — exact match on 27.9 lakh\n"
                     "four-wheelers"),
        ("Visualise", "Tableau workbook generated programmatically, plus a .hyper extract"),
    ]
    y = 0.72
    for label, body in steps:
        fig.text(0.08, y, label, color=EV, fontsize=19, fontweight="bold", va="top")
        fig.text(0.28, y, body, color=TEXT, fontsize=14, va="top", linespacing=1.5)
        y -= 0.125
    fig.text(0.08, 0.10, "Full pipeline, cleaning log and Tableau workbook on GitHub\n"
                         "github.com/niranjan6030/india-car-registrations-2026",
             color=MUTED, fontsize=14, va="top", linespacing=1.7)
    pdf.savefig(fig, facecolor=BG)
    plt.close(fig)


with PdfPages(OUT) as pdf:
    title_page(pdf)
    chart_page(pdf, "01_ev_share_trend.png", "EVs are winning, month by month",
               "3.5% of new cars in January. 7.5% by June.\n"
               "Every single month moved in the same direction.")
    chart_page(pdf, "03_ev_brands.png", "But not the brands you'd expect",
               "Maruti Suzuki sells 37.6% of India's cars — and just 4.4% of its EVs.\n"
               "Tata, Mahindra and MG own the electric transition.")
    chart_page(pdf, "04_state_ev_share.png", "Geography decides adoption",
               "Chandigarh 12.7%, Delhi 10.3%, Goa 9.5%.\n"
               "Haryana sits at 0.4% — low enough that reporting gaps are the likely cause.")
    chart_page(pdf, "02_top_brands.png", "Four brands, three quarters of the market",
               "Maruti, Tata, Mahindra and Hyundai together account for 78% of every\n"
               "new car registered in India this year.")
    chart_page(pdf, "05_data_quality.png", "The part nobody sees",
               "18% of the government's \"4-wheeler\" category is tractors, trailers and\n"
               "construction equipment. Skip the cleaning and every market-share number is wrong.")
    stat_page(pdf, "Six months in numbers",
              [("22.9 lakh", "passenger cars registered, 1 Jan – 17 Jun 2026"),
               ("13,600", "cars registered every single day"),
               ("5.2%", "were electric — rising to 7.5% by June"),
               ("84%", "of EVs come from just Tata, Mahindra and MG")],
              "Source: Vahan Dashboard, Ministry of Road Transport & Highways, Government of India.\n"
              "Registrations, not factory dispatches. June covers 1–17 only.")
    closing_page(pdf)

print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
