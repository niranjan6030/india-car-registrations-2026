# Power BI build guide — India Car Registrations 2026

Built for **Power BI in the browser (app.powerbi.com)** with a Christ University Microsoft 365 login.
Total build time: ~60–90 minutes.

---

## 0. Files you need (all in this project)

| File | Use |
|---|---|
| `data/clean/India_Car_Registrations_2026.xlsx` | The only file you upload. 4 sheets = 4 tables. |
| `powerbi/measures.dax` | Copy-paste DAX measures |
| `powerbi/theme_india_autos.json` | Dark "Midnight" colour theme |
| `reports/cleaning_log.md` | Numbers for the Data Quality page |

## 1. Upload the data

1. Go to **app.powerbi.com** → sign in with your `@christuniversity.in` account.
2. Open **My workspace** → **Upload** (or **New item → Get data / Excel**, depending on your screen) → pick `India_Car_Registrations_2026.xlsx`.
3. If asked, choose **Import** (not "Upload to OneDrive / view workbook") and tick all four tables:
   `fact_registrations`, `dim_maker`, `dim_state`, `dim_date`.
4. You now have a **semantic model** called *India_Car_Registrations_2026*.

> If you get "your organisation hasn't enabled Power BI", ask the IT help desk to enable **Power BI (free)** for your account, or use a college-lab PC with Power BI Desktop — every step below also works there.

## 2. Model: relationships (star schema)

Open the semantic model → **Open data model** (top ribbon). Power BI usually auto-detects these; check them in **Manage relationships** and add any missing ones:

| From (many) | To (one) | Cardinality | Filter direction |
|---|---|---|---|
| `fact_registrations[month_date]` | `dim_date[month_date]` | Many-to-one | Single |
| `fact_registrations[state]` | `dim_state[state]` | Many-to-one | Single |
| `fact_registrations[maker]` | `dim_maker[maker]` | Many-to-one | Single |

Then, still in the data model view:
- `dim_date[month_name]` → **Sort by column** → `month_num` (otherwise months sort alphabetically).
- `dim_state[map_location]` → **Data category** → *Place*; `dim_state[state]` → *State or Province*.
- Hide the technical columns from report view: `dim_date[month_num]`, `dim_maker[is_passenger_car]`.

## 3. Measures

Select `fact_registrations` → **New measure** → paste each measure from `measures.dax` **one at a time**.
Set formats (Measure tools / Properties pane):

| Measure | Format |
|---|---|
| Car Registrations, EV Registrations, ICE Registrations, Avg Daily … | Whole number, thousands separator |
| EV Share %, Market Share %, EV Market Share %, Non-Car Share of 4W % | Percentage, 1 decimal |
| EV Share MoM (pp), EV Share Jan to Latest (pp) | Decimal, 1 decimal |

## 4. Create the report + apply the theme

Semantic model → **Create report → Start from scratch**.
Then **View → Themes → Browse for themes** → pick `theme_india_autos.json`.
Set page size: **Format page → Canvas settings → 16:9 (1280 × 720)**.

> If your editor has no *Browse for themes*, pick the built-in **"Innovate"** or **"Storm"** theme and set page background to `#0B1220`, visual background to `#111A2E` manually.

**Colour rules used across all pages** (be consistent — it's what makes it look professional):
- EV = green `#22C55E`, Petrol/Diesel/CNG = blue `#3B82F6`, highlight/accent = saffron `#F59E0B`.
- Card titles in grey, numbers in white. Rounded corners 12 px (already in the theme).

---

## Page 1 — "Overview"

Layout (1280 × 720):

```
┌───────────────────────────────────────────────────────────────────────┐
│  [Title Overview measure as a Card – large]          [Month slicer]  │
├──────────┬──────────┬──────────┬──────────┬───────────────────────────┤
│ Cars     │ EV share │ Avg/day  │ Top brand│                           │
│ 22.9 L   │ 5.2 %    │ 13.6 K   │ Maruti   │   Azure Map / bubble map  │
├──────────┴──────────┴──────────┴──────────┤   size = Car Registrations │
│  Area chart: Avg Daily Registrations       │   colour = EV Share %      │
│  by month (EV vs ICE stacked)              │                           │
├────────────────────────────┬───────────────┴───────────────────────────┤
│ Bar: Top 10 brands          │ Donut: Car Registrations by origin_country │
│ by Market Share %           │                                            │
└────────────────────────────┴────────────────────────────────────────────┘
```

| Visual | Fields |
|---|---|
| 4 × **Card (new)** | `Car Registrations`, `EV Share %`, `Avg Daily Registrations`, `Top Brand` |
| **Stacked area chart** | X = `dim_date[month_name]`, Y = `Avg Daily Registrations`, Legend = `fact_registrations[powertrain]` |
| **Clustered bar chart** | Y = `dim_maker[brand]`, X = `Market Share %`; Filters pane → `brand` → Top N = 10 by `Car Registrations`; filter `dim_maker[is_passenger_car]` = True |
| **Donut chart** | Legend = `dim_maker[origin_country]`, Values = `Car Registrations` |
| **Azure Map** (or *Map*) | Location = `dim_state[map_location]`, Size = `Car Registrations`, Tooltips = `EV Share %` |
| **Slicer** | `dim_date[month_name]`, style = Tile |

> Why "Avg Daily" instead of monthly totals? The data ends on **17 June**, so June's raw total looks like a crash. Per-day numbers compare months fairly — mention this in your viva.

## Page 2 — "The EV Shift"

| Visual | Fields |
|---|---|
| **Card** | `Title EV` (big headline) |
| **Line chart** | X = `month_name`, Y = `EV Share %`, data labels ON, line colour green, markers ON |
| **Clustered bar** | Y = `brand`, X = `EV Market Share %`, filter `powertrain` = Electric; top 8 |
| **Bar chart** | Y = `dim_state[state]`, X = `EV Share %`; visual filter `Car Registrations` > 5000; sort desc; conditional-format bars green gradient |
| **Scatter chart** | X = `Car Registrations`, Y = `EV Share %`, Values = `state`, Legend = `dim_state[region]` — shows big markets vs green markets |
| **Card** | `Top EV State` |

## Page 3 — "State Explorer"

| Visual | Fields |
|---|---|
| **Slicers** | `dim_state[region]` (dropdown), `dim_state[state]` (dropdown, search on), `powertrain` (tile) |
| **Matrix (heatmap)** | Rows = `state`, Columns = `brand` (top 8 brands via filter), Values = `Market Share %` → Conditional formatting → Background colour → gradient `#0F1B2E` → `#F59E0B` |
| **Treemap** | Category = `region`, Details = `state`, Values = `Car Registrations` |
| **Ribbon chart** | X = `month_name`, Y = `Car Registrations`, Legend = `brand` (top 6) — shows ranking changes month to month |

## Page 4 — "Data Quality" (the cleaning story — examiners love this)

| Visual | Fields / content |
|---|---|
| **Cards** | `146` raw files · `614 → 607` maker names · `Non-Car Share of 4W %` (~18 %) · `8,603` late back-filled records |
| **Donut** | Legend = `dim_maker[segment]`, Values = `All 4W Registrations` (no passenger-car filter!) |
| **Table** | `dim_maker[maker]`, `segment`, `All 4W Registrations`; filter `is_passenger_car` = False; top 15 |
| **Text box** | 5–6 bullets copied from `reports/cleaning_log.md` (two export layouts, GST codes stripped, EV split, June partial month, EV reconciliation gap) |

## 5. Finishing touches (what makes it look "premium")

1. Put a thin saffron rectangle (`#F59E0B`, 4 px high) under each page title.
2. Add **page navigator** buttons (Insert → Buttons → Navigator → Page navigator) at the top.
3. Turn on **Edit interactions** so the map filters everything and the slicers filter all visuals.
4. Tooltips: set `EV Share %` and `Market Share %` as tooltip fields on every chart.
5. Align everything to a grid: 24 px outer margin, 16 px gap between visuals.
6. Save → **Share** or **Export → PDF** for submission.

---

## Headline insights (use these in your presentation)

- **22.9 lakh passenger cars** registered on Vahan between 1 Jan and 17 Jun 2026 (≈13,600 a day).
- **EV share doubled in six months: 3.5 % (Jan) → 7.5 % (Jun)**, rising every single month. Overall 5.2 %.
- **Tata (38.8 %), Mahindra (23.9 %) and JSW MG (21.6 %)** make ~84 % of India's electric cars; Maruti has 37.6 % of all cars but only 4.4 % of EVs.
- **Chandigarh (12.7 %) and Delhi (10.3 %)** lead EV adoption; Kerala, Karnataka, Goa, Andhra Pradesh are all above 8 %.
- **Maruti Suzuki alone = 37.6 %** of the market; the top 4 (Maruti, Tata, Mahindra, Hyundai) = 78 %.
- **Japanese-origin brands** sell more cars in India (46 %) than Indian brands (29 %).
- **January is the peak** (16,551 cars/day vs ~13,000 later) — buyers wait for the new calendar year so the car is "a 2026 model".
- **~18 % of Vahan's "4W" category isn't cars at all** — tractors, trailers, construction equipment. Without cleaning, every market-share number would be wrong.

## Caveats (say these before the examiner asks)

- Data ends 17 Jun 2026 (scraper's last snapshot 18 Jun) → June is partial; per-day measures handle it.
- State-level EV files sum to 2,990 fewer EVs than the all-India EV file (2.5 %). Haryana's very low EV share (0.4 %) is probably partly this reporting gap.
- Vahan counts **registrations**, not factory sales (SIAM). Registrations lag sales by days/weeks.
