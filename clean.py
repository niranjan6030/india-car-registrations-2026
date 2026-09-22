"""
India Car Registrations 2026 - data cleaning pipeline
Source : Vahan 4 Dashboard (MoRTH, Govt. of India), 4-wheeler maker-wise monthly exports,
         mirrored daily by github.com/hrshlpnchl/Vahan_data
Input  : data/raw/vahan_4w/*.xlsx   (73 files per snapshot: 36 states/UTs + all-India, All-fuel + Pure-EV)
Output : data/clean/*.csv, data/clean/India_Car_Registrations_2026.xlsx, reports/cleaning_log.md
"""
import re
import glob
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/vahan_4w")
OUT = Path("data/clean")
REP = Path("reports")
OUT.mkdir(parents=True, exist_ok=True)
REP.mkdir(exist_ok=True)

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
# Undated files were uploaded on 14 Jun 2026; dated files carry their scrape date in the name.
UNDATED_SNAPSHOT = "2026-06-14"
log = []


def note(step, detail, rows=None):
    log.append((step, detail, rows))
    print(f"[{step}] {detail}" + (f"  ({rows:,} rows)" if rows is not None else ""))


# ---------------------------------------------------------------- 1. read raw files
def read_vahan(path):
    """Read one Vahan export. Handles both export layouts:
    A) title row, then 'S. No. | Maker | Jan 2026 ... | Total'
    B) title row, 'S No | Maker | Month Wise | TOTAL', blank row, then 'JAN | FEB ...' sub-header."""
    raw = pd.read_excel(path, header=None, dtype=str)
    header_row = raw.index[raw[1].astype(str).str.strip().str.upper() == "MAKER"][0]
    # month labels may sit on the header row (layout A) or a later sub-header row (layout B)
    month_cols = {}
    for r in range(header_row, min(header_row + 4, len(raw))):
        for c in raw.columns[2:]:
            tok = str(raw.iat[r, c]).strip().upper()[:3]
            if tok in MONTHS:
                month_cols[c] = MONTHS.index(tok) + 1
        if month_cols:
            break
    total_col = raw.columns[-1]
    body = raw[pd.to_numeric(raw[0], errors="coerce").notna()]  # keep only rows with a serial number
    df = pd.DataFrame({"maker_raw": body[1].astype(str)})
    for c, m in month_cols.items():
        df[m] = pd.to_numeric(body[c].str.replace(",", ""), errors="coerce").fillna(0).astype(int)
    df["file_total"] = pd.to_numeric(body[total_col].str.replace(",", ""), errors="coerce")
    return df, ("A" if header_row + 1 == raw.index[raw[1].notna()][1] else "B")


STATE_FIX = {
    "Andaman and Nicobar Island": "Andaman and Nicobar Islands",
    "UT of DNH and DD": "Dadra and Nagar Haveli and Daman and Diu",
    "All Vahan4 Running States": "ALL INDIA",
}

frames, layouts = [], {"A": 0, "B": 0}
files = sorted(glob.glob(str(RAW / "*.xlsx")))
for f in files:
    m = re.match(r"(.+)_4W_(AllFuel|PureEV)_2026(?:_(\d{8}))?\.xlsx", Path(f).name)
    state = STATE_FIX.get(m[1].replace("_", " "), m[1].replace("_", " "))
    snapshot = pd.to_datetime(m[3]).strftime("%Y-%m-%d") if m[3] else UNDATED_SNAPSHOT
    df, layout = read_vahan(f)
    layouts[layout] += 1
    df["state"], df["fuel_file"], df["snapshot"] = state, m[2], snapshot
    frames.append(df)
raw_all = pd.concat(frames, ignore_index=True)
note("Load", f"Read {len(files)} xlsx files ({layouts['A']} in layout A, {layouts['B']} in layout B)", len(raw_all))

# ---------------------------------------------------------------- 2. integrity checks
month_ids = [c for c in raw_all.columns if isinstance(c, int)]
raw_all[month_ids] = raw_all[month_ids].fillna(0).astype(int)
mismatch = raw_all[raw_all[month_ids].sum(axis=1) != raw_all.file_total]
note("Validate", f"Rows where Jan-Jun do not add up to the file's own Total column: {len(mismatch)}")

# keep the latest snapshot per state + fuel file; older snapshot only used to measure back-fill
latest = raw_all.groupby(["state", "fuel_file"]).snapshot.transform("max")
old = raw_all[raw_all.snapshot != latest]
cur = raw_all[raw_all.snapshot == latest].copy()
bf = (cur[cur.state == "ALL INDIA"].query("fuel_file=='AllFuel'")[[1, 2, 3, 4, 5]].sum()
      - old[old.state == "ALL INDIA"].query("fuel_file=='AllFuel'")[[1, 2, 3, 4, 5]].sum())
note("Snapshot", f"Kept latest snapshot {cur.snapshot.max()}; dropped older {old.snapshot.max()}. "
     f"Late back-filled registrations for Jan-May between snapshots: {int(bf.sum()):,}", len(cur))

# ---------------------------------------------------------------- 3. clean maker names
def clean_name(s):
    s = s.upper().strip()
    s = re.sub(r"^M/S\.?\s*", "", s)                       # 'M/S ' business prefix
    s = re.sub(r"[, ]*(?:KURNOOL|KADAPA|ANANTHAPUR)?\s*AP\d[\dV]{6,}$", "", s)  # AP trade-certificate numbers glued to names
    s = re.sub(r"\s*-\s*", "-", s)                         # 'MERCEDES -BENZ' -> 'MERCEDES-BENZ'
    s = re.sub(r"\s+", " ", s).strip(" ,.")
    return s


cur["maker_clean"] = cur.maker_raw.map(clean_name)
changed = (cur.maker_raw.str.strip().str.upper() != cur.maker_clean).sum()
note("Clean names", f"Normalised {cur.maker_raw.nunique()} raw maker names -> {cur.maker_clean.nunique()} clean names "
     f"({changed} rows had GST/trade-cert codes, 'M/S' prefixes or bad spacing)")

# ---------------------------------------------------------------- 4. classify makers
# brand, parent group, country of origin - ordered rules, first match wins
BRANDS = [
    (r"MARUTI", "Maruti Suzuki", "Suzuki", "Japan"),
    (r"TATA (MOTORS|PASSENGER)", "Tata", "Tata Motors", "India"),
    (r"MAHINDRA & MAHINDRA LIMITED$|MAHINDRA ELECTRIC AUTOMOBILE", "Mahindra", "Mahindra", "India"),
    (r"HYUNDAI", "Hyundai", "Hyundai", "South Korea"),
    (r"^KIA", "Kia", "Hyundai", "South Korea"),
    (r"TOYOTA", "Toyota", "Toyota", "Japan"),
    (r"LEXUS", "Lexus", "Toyota", "Japan"),
    (r"HONDA CARS", "Honda", "Honda", "Japan"),
    (r"SKODA|VOLKSWAGEN", "Skoda-VW", "Volkswagen Group", "Germany"),
    (r"^AUDI", "Audi", "Volkswagen Group", "Germany"),
    (r"PORSCHE", "Porsche", "Volkswagen Group", "Germany"),
    (r"LAMBORGHINI", "Lamborghini", "Volkswagen Group", "Italy"),
    (r"BENTLEY", "Bentley", "Volkswagen Group", "UK"),
    (r"JSW MG", "MG", "JSW-SAIC", "India / China"),
    (r"RENAULT", "Renault", "Renault", "France"),
    (r"NISSAN", "Nissan", "Nissan", "Japan"),
    (r"^BMW|^MINI", "BMW", "BMW Group", "Germany"),
    (r"ROLLS-ROYCE", "Rolls-Royce", "BMW Group", "UK"),
    (r"MERCEDES", "Mercedes-Benz", "Mercedes-Benz", "Germany"),
    (r"STELLANTIS", "Stellantis (Jeep/Citroen)", "Stellantis", "Netherlands"),
    (r"JAGUAR LAND ROVER", "Jaguar Land Rover", "Tata Motors", "UK"),
    (r"^VOLVO", "Volvo", "Geely", "Sweden"),
    (r"LOTUS", "Lotus", "Geely", "UK"),
    (r"^BYD", "BYD", "BYD", "China"),
    (r"VINFAST", "VinFast", "Vingroup", "Vietnam"),
    (r"TESLA", "Tesla", "Tesla", "USA"),
    (r"FERRARI", "Ferrari", "Ferrari", "Italy"),
    (r"MASERATI", "Maserati", "Stellantis", "Italy"),
    (r"FORCE MOTORS", "Force", "Force Motors", "India"),
    (r"ISUZU", "Isuzu", "Isuzu", "Japan"),
]
SEGMENTS = [  # everything that is NOT a passenger car but sits in Vahan's 4W bucket
    (r"CONSTRUCTION|EARTHMOVER|JCB|CASE NEW HOLLAND|ACTION CONSTRUCTION|AJAX|SCHWING|CRANE|FIELDTRACK|BOBCAT|DOOSAN|MINING", "Construction equipment"),
    (r"TRACTOR|SWARAJ|TAFE|ESCORTS KUBOTA|KUBOTA|JOHN DEERE|EICHER TRACTORS|CNH INDUSTRIAL|MASSEY|SAME DEUTZ|"
     r"TILLER|ZETOR|AGRI|AGRO|KRUSHI|KRISHI|KISAN|FARM|GROMAX|SONALIKA|INTERNATIONAL TRACTORS|PREET|CAPTAIN|KARTAR|"
     r"INDO FARM|DASMESH|NEW HOLLAND|HARVEST|ROTAVATOR|SHETKARI|TIRTH", "Tractor & Farm equipment"),
    (r"TRAIL|TROLL", "Trailer"),
    (r"ASHOK LEYLAND|VE COMMERCIAL|SML|EICHER MOTORS|BHARATBENZ|DAIMLER INDIA|PIAGGIO|ATUL|MAHINDRA ELECTRIC MOBILITY|"
     r"MAHINDRA LAST MILE", "Commercial vehicle"),
    (r"ATHER|TVS|REVOLT|HONDA MOTORCYCLE|HERO|BAJAJ|OLA ELECTRIC|ROYAL ENFIELD|KINETIC|YAMAHA|SUZUKI MOTORCYCLE",
     "2W/3W maker (misfiled)"),
    (r"^OTHERS$|^XYZ\d*$|^NA$|^-$", "Placeholder / unknown"),
    (r"ENG(G|INEERING|NEERING)?\.? ?WORKS?|WELDING|INDUSTR|ENTERPRISE|FABRICATION|FEBRICATION|STEEL|MACHINE|MECHANI|LORRY ?BODY|ENGG|DIESELS", "Small fabricator / workshop"),
]


def classify(name):
    for pat, brand, group, country in BRANDS:
        if re.search(pat, name):
            return pd.Series(["Passenger car", brand, group, country])
    for pat, seg in SEGMENTS:
        if re.search(pat, name):
            return pd.Series([seg, None, None, None])
    return pd.Series(["Other / unclassified", None, None, None])


makers = pd.DataFrame({"maker_clean": sorted(cur.maker_clean.unique())})
makers[["segment", "brand", "parent_group", "origin_country"]] = makers.maker_clean.apply(classify)
makers["is_passenger_car"] = makers.segment.eq("Passenger car")
cur = cur.merge(makers, on="maker_clean", how="left")

india_all = cur[(cur.state == "ALL INDIA") & (cur.fuel_file == "AllFuel")]
seg_mix = india_all.groupby("segment").file_total.sum().sort_values(ascending=False)
note("Classify", "4W bucket split by segment (all-India): " +
     ", ".join(f"{k} {v:,}" for k, v in seg_mix.items()))

# ---------------------------------------------------------------- 5. reconcile states vs all-India
states = cur[cur.state != "ALL INDIA"]
for ff in ["AllFuel", "PureEV"]:
    s = states[states.fuel_file == ff].file_total.sum()
    a = cur[(cur.state == "ALL INDIA") & (cur.fuel_file == ff)].file_total.sum()
    note("Reconcile", f"{ff}: sum of 36 state files {s:,} vs all-India file {a:,} (diff {a - s:,})"
         + (" - state-level EV exports under-report; state visuals use state files, national EV KPI can use the "
            "all-India figure" if ff == "PureEV" and a != s else ""))

# ---------------------------------------------------------------- 6. reshape wide -> long, split EV / non-EV
long = states.melt(id_vars=["state", "fuel_file", "maker_clean", "brand"], value_vars=month_ids,
                   var_name="month", value_name="registrations")
long = (long.groupby(["state", "maker_clean", "month", "fuel_file"]).registrations.sum()
        .unstack("fuel_file", fill_value=0).reset_index())
long["PureEV"] = long.get("PureEV", 0)
long["non_ev"] = long.AllFuel - long.PureEV
neg = long[long.non_ev < 0]
note("EV split", f"Non-EV = All-fuel minus Pure-EV. Cells where EV > All-fuel (source inconsistency): {len(neg)} "
     f"-> clipped to 0, EV kept")
long["non_ev"] = long.non_ev.clip(lower=0)

fact = long.melt(id_vars=["state", "maker_clean", "month"], value_vars=["PureEV", "non_ev"],
                 var_name="powertrain", value_name="registrations")
fact["powertrain"] = fact.powertrain.map({"PureEV": "Electric (EV)", "non_ev": "Petrol/Diesel/CNG/Hybrid"})
before = len(fact)
fact = fact[fact.registrations > 0]
note("Sparsity", f"Dropped zero-registration cells from the long table", before - len(fact))
fact["month_date"] = pd.to_datetime("2026-" + fact.month.astype(str) + "-01")

# ---------------------------------------------------------------- 7. dimensions
snap = pd.Timestamp(cur.snapshot.max())
days_in_data = {m: pd.Period(f"2026-{m:02d}").days_in_month for m in month_ids}
days_in_data[snap.month] = snap.day - 1  # scraped at 04:00 on snapshot day -> data runs to the previous day
dim_date = pd.DataFrame({"month_date": pd.to_datetime([f"2026-{m:02d}-01" for m in month_ids])})
dim_date["month_name"] = dim_date.month_date.dt.strftime("%b")
dim_date["month_num"] = dim_date.month_date.dt.month
dim_date["quarter"] = "Q" + dim_date.month_date.dt.quarter.astype(str)
dim_date["days_covered"] = dim_date.month_num.map(days_in_data)
dim_date["is_partial_month"] = dim_date.days_covered < dim_date.month_date.dt.days_in_month
note("Partial month", f"{snap:%B} only has {days_in_data[snap.month]} days of data - flagged for per-day DAX measures")

REGION = {
    "North": ["Chandigarh", "Delhi", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Ladakh", "Punjab",
              "Rajasthan", "Uttarakhand", "Uttar Pradesh"],
    "South": ["Andhra Pradesh", "Karnataka", "Kerala", "Tamil Nadu", "Telangana", "Puducherry", "Lakshadweep",
              "Andaman and Nicobar Islands"],
    "West": ["Goa", "Gujarat", "Maharashtra", "Dadra and Nagar Haveli and Daman and Diu"],
    "East": ["Bihar", "Jharkhand", "Odisha", "West Bengal"],
    "Central": ["Chhattisgarh", "Madhya Pradesh"],
    "North-East": ["Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Sikkim", "Tripura"],
}
ISO = {"Andaman and Nicobar Islands": "AN", "Andhra Pradesh": "AP", "Arunachal Pradesh": "AR", "Assam": "AS",
       "Bihar": "BR", "Chandigarh": "CH", "Chhattisgarh": "CT", "Dadra and Nagar Haveli and Daman and Diu": "DH",
       "Delhi": "DL", "Goa": "GA", "Gujarat": "GJ", "Haryana": "HR", "Himachal Pradesh": "HP",
       "Jammu and Kashmir": "JK", "Jharkhand": "JH", "Karnataka": "KA", "Kerala": "KL", "Ladakh": "LA",
       "Lakshadweep": "LD", "Madhya Pradesh": "MP", "Maharashtra": "MH", "Manipur": "MN", "Meghalaya": "ML",
       "Mizoram": "MZ", "Nagaland": "NL", "Odisha": "OR", "Puducherry": "PY", "Punjab": "PB", "Rajasthan": "RJ",
       "Sikkim": "SK", "Tamil Nadu": "TN", "Telangana": "TG", "Tripura": "TR", "Uttar Pradesh": "UP",
       "Uttarakhand": "UK", "West Bengal": "WB"}
UT = {"Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
      "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"}
dim_state = pd.DataFrame({"state": sorted(fact.state.unique())})
dim_state["region"] = dim_state.state.map({s: r for r, ss in REGION.items() for s in ss})
dim_state["state_code"] = "IN-" + dim_state.state.map(ISO)
dim_state["state_or_ut"] = dim_state.state.map(lambda s: "Union Territory" if s in UT else "State")
dim_state["map_location"] = dim_state.state + ", India"  # unambiguous geocoding for Power BI map visuals
assert dim_state.region.notna().all() and dim_state.state_code.notna().all(), "unmapped state"

dim_maker = makers.rename(columns={"maker_clean": "maker"})
dim_maker["brand"] = dim_maker.brand.fillna("(not a car maker)")
fact = fact.rename(columns={"maker_clean": "maker"})[["month_date", "state", "maker", "powertrain", "registrations"]]

# ---------------------------------------------------------------- 8. write outputs
fact.to_csv(OUT / "fact_registrations.csv", index=False)
dim_maker.to_csv(OUT / "dim_maker.csv", index=False)
dim_state.to_csv(OUT / "dim_state.csv", index=False)
dim_date.to_csv(OUT / "dim_date.csv", index=False)
with pd.ExcelWriter(OUT / "India_Car_Registrations_2026.xlsx", engine="openpyxl") as xw:  # one workbook -> one Power BI semantic model
    for name, d in [("fact_registrations", fact), ("dim_maker", dim_maker),
                    ("dim_state", dim_state), ("dim_date", dim_date)]:
        d.to_excel(xw, sheet_name=name, index=False)
        # Power BI service reads Excel *tables*, not plain ranges
        ws = xw.sheets[name]
        from openpyxl.worksheet.table import Table, TableStyleInfo
        ref = f"A1:{ws.cell(row=len(d) + 1, column=d.shape[1]).coordinate}"
        t = Table(displayName=name, ref=ref)
        t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(t)

cars = fact.merge(dim_maker[["maker", "is_passenger_car"]], on="maker").query("is_passenger_car")
note("Output", f"fact {len(fact):,} rows, dim_maker {len(dim_maker)}, dim_state {len(dim_state)}, dim_date {len(dim_date)}. "
     f"Passenger cars: {cars.registrations.sum():,} registrations, "
     f"of which EV {cars[cars.powertrain.str.startswith('Electric')].registrations.sum():,}")

with open(REP / "cleaning_log.md", "w") as fh:
    fh.write("# Cleaning log - India Car Registrations 2026 (Vahan)\n\n| # | Step | What happened | Rows |\n|---|---|---|---|\n")
    for i, (s, d, r) in enumerate(log, 1):
        fh.write(f"| {i} | {s} | {d} | {'' if r is None else f'{r:,}'} |\n")
    fh.write("\n## Makers that are not passenger cars (all-India, latest snapshot)\n\n")
    top = (india_all[~india_all.is_passenger_car].groupby(["segment", "maker_clean"]).file_total.sum()
           .reset_index().sort_values("file_total", ascending=False).head(25))
    fh.write("| Segment | Maker | Registrations |\n|---|---|---:|\n")
    for r in top.itertuples():
        fh.write(f"| {r.segment} | {r.maker_clean} | {r.file_total:,} |\n")
