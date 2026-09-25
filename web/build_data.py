"""Pack the cleaned data into a compact JSON bundle for the web dashboard."""
import json
from pathlib import Path

import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
OUT = PROJ / "web/data.json"

df = pd.read_csv(PROJ / "data/clean/tableau_cars_flat.csv")
seg = pd.read_csv(PROJ / "data/clean/tableau_4w_segments.csv")

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
days = df.groupby("Month Name")["Days Covered"].max().reindex(MONTHS).astype(int).tolist()

states = sorted(df.State.unique())
brands = sorted(df.Brand.unique())
regions = sorted(df.Region.unique())
origins = sorted(df["Origin Country"].unique())

state_ix = {s: i for i, s in enumerate(states)}
brand_ix = {b: i for i, b in enumerate(brands)}

state_region = df.groupby("State").Region.first().reindex(states).map(
    {r: i for i, r in enumerate(regions)}).tolist()
brand_origin = df.groupby("Brand")["Origin Country"].first().reindex(brands).map(
    {o: i for i, o in enumerate(origins)}).tolist()
state_ut = df.groupby("State")["State or UT"].first().reindex(states).eq("Union Territory").astype(int).tolist()

rows = []
grp = df.groupby(["Month Number", "State", "Brand", "Is EV"], as_index=False).Registrations.sum()
for r in grp.itertuples():
    rows.append([int(r._1) - 1, state_ix[r.State], brand_ix[r.Brand],
                 1 if r._4 else 0, int(r.Registrations)])

bundle = {
    "months": MONTHS,
    "days": days,
    "states": states,
    "brands": brands,
    "regions": regions,
    "origins": origins,
    "stateRegion": state_region,
    "brandOrigin": brand_origin,
    "stateIsUT": state_ut,
    "rows": rows,
    "segments": [[r.segment, int(r.registrations)] for r in seg.itertuples()],
    "meta": {
        "from": "1 Jan 2026", "to": "17 Jun 2026",
        "files": 146, "makersRaw": 614, "makersClean": 607,
        "backfilled": 8603, "evGap": 2990,
        "all4w": int(seg.registrations.sum()),
    },
}

OUT.write_text(json.dumps(bundle, separators=(",", ":")))
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB, {len(rows):,} rows)")
