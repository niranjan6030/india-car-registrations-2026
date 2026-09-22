# Tableau build guide — India Car Registrations 2026

For **Tableau Public** (free, macOS). Build time ~60 minutes.

Data file: `data/clean/tableau_cars_flat.csv` — one flat table, 5,686 rows, already cleaned.
Second file for the data-quality story: `data/clean/tableau_4w_segments.csv`.

---

## 0. The generated workbook

`India_Car_Registrations_2026.twbx` is built by `make_workbook.py` and already contains
the sheets and dashboards. Tableau Public shows "workbooks must use extracts" when it
opens: click OK, then **Data Source tab > Create Extract**, and it is ready to publish.
Two finishing touches are left to the UI, because Tableau's file format rejects them in a
hand-written workbook: sorting the bar charts (click the sort icon on any axis) and
setting the powertrain colours (green #22C55E for EV, blue #3B82F6 for the rest).

The steps below build the same thing by hand, if you would rather do it yourself.

## 1. Connect

1. Open Tableau Public → **Connect → Text file** → choose `tableau_cars_flat.csv`.
2. In the data grid, check the types Tableau guessed:
   - `Month` → **Date**
   - `Registrations`, `Days Covered`, `Month Number` → **Number (whole)**
   - `Is EV`, `Is Partial Month` → **Boolean**
   - `Map Location` → **Geographic role → State/Province** (right-click → Geographic Role)
   - `State` → also set **Geographic Role → State/Province**
3. Go to **Sheet 1**.

## 2. Calculated fields

Create each with **Analysis → Create Calculated Field**:

```
EV Registrations
IF [Is EV] THEN [Registrations] ELSE 0 END
```

```
EV Share
SUM([EV Registrations]) / SUM([Registrations])
```
→ Format as Percentage, 1 decimal.

```
Cars Per Day
SUM([Registrations]) / SUM([Days Covered])
```
Note: `Days Covered` repeats per row, so this only works at month level.
Safer version:
```
Cars Per Day (fixed)
SUM([Registrations]) / SUM({FIXED [Month Name] : MAX([Days Covered])})
```

```
Market Share
SUM([Registrations]) / TOTAL(SUM([Registrations]))
```
→ Compute using **Table (down)**.

```
Brand Rank
RANK(SUM([Registrations]))
```

## 3. Colour palette (keep it consistent)

- EV green `#22C55E`, Petrol/Diesel/CNG blue `#3B82F6`, accent saffron `#F59E0B`
- Background `#0B1220`, cards `#111A2E`, text `#E6ECF5`

Set a dark dashboard background: **Dashboard → Format → Dashboard Shading → More Colours → `#0B1220`**.
For each worksheet: **Format → Shading → Worksheet → `#111A2E`**, and set fonts to `#E6ECF5` via **Format → Font**.

## 4. Worksheets to build

| # | Sheet name | Marks | Shelves |
|---|---|---|---|
| 1 | `KPI Cars` | Text | Text = SUM(Registrations); format 22.9L via **Number (custom)**, 1 decimal, units = Lakhs |
| 2 | `KPI EV Share` | Text | Text = EV Share |
| 3 | `KPI Per Day` | Text | Text = Cars Per Day (fixed) |
| 4 | `Trend` | Area | Columns = MONTH(Month), Rows = Cars Per Day (fixed), Colour = Powertrain (green/blue) |
| 5 | `EV Curve` | Line | Columns = MONTH(Month), Rows = EV Share; Label ON, colour green, size 3 |
| 6 | `Top Brands` | Bar | Rows = Brand (sort desc by SUM Registrations), Columns = SUM(Registrations); Filter Brand → Top 10 by SUM(Registrations); Label = Market Share |
| 7 | `EV Brands` | Bar | Rows = Brand, Columns = SUM(EV Registrations); filter to top 8; colour green |
| 8 | `State Map` | Map | Detail = Map Location, Colour = EV Share (green gradient), Size = SUM(Registrations); Tooltip = brand leader |
| 9 | `State EV Bar` | Bar | Rows = State, Columns = EV Share; Filter: SUM(Registrations) ≥ 5000; sort desc |
| 10 | `Scatter` | Circle | Columns = SUM(Registrations), Rows = EV Share, Detail = State, Colour = Region |
| 11 | `Brand × State` | Square (heatmap) | Rows = State, Columns = Brand (top 8), Colour = Market Share, Label = Market Share |
| 12 | `Origin Mix` | Pie or Treemap | Colour = Origin Country, Size = SUM(Registrations) |
| 13 | `4W Bucket` | Bar | Second data source `tableau_4w_segments.csv`: Rows = segment, Columns = registrations; highlight that ~18 % is not cars |

## 5. Dashboards

**Dashboard 1 — "India's Car Market 2026"** (1200 × 800, Fixed size)
- Top: title text box "India's Car Market 2026 — 22.9 lakh cars, 1 Jan–17 Jun" on saffron rule
- Row of KPI sheets 1–3
- Middle: `Trend` (left, wide) + `State Map` (right)
- Bottom: `Top Brands` + `Origin Mix`
- Add a **Month** filter, apply to all sheets (right-click filter → Apply to Worksheets → All Using This Data Source)

**Dashboard 2 — "The EV Shift"**
- `EV Curve` across the top (the headline: 3.5 % → 7.5 %)
- `EV Brands` + `State EV Bar` side by side
- `Scatter` bottom, full width
- Region filter as a horizontal tile

**Dashboard 3 — "Behind the Data"**
- `4W Bucket` bar + `Brand × State` heatmap
- Text box with the cleaning story (from `reports/cleaning_log.md`)

## 6. Interactivity

- On each dashboard select a sheet → **Use as Filter** (funnel icon) so clicking a state or brand filters everything.
- Tooltips: add EV Share and Market Share to every sheet's Tooltip shelf.
- Device preview → check it doesn't break on laptop size.

## 7. Publish

**File → Save to Tableau Public As…** → sign in / create a free account → name it
`India Car Registrations 2026 — Vahan`.
Everything on Tableau Public is public. Copy the link for your CV, LinkedIn and the GitHub README.

---

## Talking points

- 22.9 lakh cars in 168 days ≈ 13,600/day; January peaks at 16,551/day (buyers want a 2026-model year car).
- EV share rose every month: 3.5 % → 7.5 %; overall 5.2 %.
- Tata 38.8 %, Mahindra 23.9 %, MG 21.6 % of EVs — but Maruti, with 37.6 % of the total market, has just 4.4 % of EVs.
- Chandigarh 12.7 % and Delhi 10.3 % lead EV adoption; Haryana's 0.4 % looks like under-reporting, not reality.
- ~18 % of Vahan's "4W" bucket is tractors, trailers and JCBs — cleaning changed every market-share number.

## Caveats to state up front

- Data ends 17 Jun 2026; June is partial, so compare per-day figures.
- State EV files total 2,990 fewer EVs than the national EV file (2.5 %).
- Vahan counts registrations, not factory dispatches (SIAM numbers differ).
