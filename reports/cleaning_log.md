# Cleaning log - India Car Registrations 2026 (Vahan)

| # | Step | What happened | Rows |
|---|---|---|---|
| 1 | Load | Read 146 xlsx files (73 in layout A, 73 in layout B) | 6,087 |
| 2 | Validate | Rows where Jan-Jun do not add up to the file's own Total column: 0 |  |
| 3 | Snapshot | Kept latest snapshot 2026-06-18; dropped older 2026-06-14. Late back-filled registrations for Jan-May between snapshots: 8,603 | 3,050 |
| 4 | Clean names | Normalised 614 raw maker names -> 607 clean names (529 rows had GST/trade-cert codes, 'M/S' prefixes or bad spacing) |  |
| 5 | Classify | 4W bucket split by segment (all-India): Passenger car 2,285,905, Tractor & Farm equipment 468,266, Trailer 15,841, Placeholder / unknown 13,607, 2W/3W maker (misfiled) 5,373, Small fabricator / workshop 5,003, Construction equipment 1,640, Commercial vehicle 1,268, Other / unclassified 601 |  |
| 6 | Reconcile | AllFuel: sum of 36 state files 2,797,504 vs all-India file 2,797,504 (diff 0) |  |
| 7 | Reconcile | PureEV: sum of 36 state files 118,593 vs all-India file 121,583 (diff 2,990) - state-level EV exports under-report; state visuals use state files, national EV KPI can use the all-India figure |  |
| 8 | EV split | Non-EV = All-fuel minus Pure-EV. Cells where EV > All-fuel (source inconsistency): 0 -> clipped to 0, EV kept |  |
| 9 | Sparsity | Dropped zero-registration cells from the long table | 15,017 |
| 10 | Partial month | June only has 17 days of data - flagged for per-day DAX measures |  |
| 11 | Output | fact 9,343 rows, dim_maker 607, dim_state 36, dim_date 6. Passenger cars: 2,285,905 registrations, of which EV 118,577 |  |

## Makers that are not passenger cars (all-India, latest snapshot)

| Segment | Maker | Registrations |
|---|---|---:|
| Tractor & Farm equipment | MAHINDRA & MAHINDRA LIMITED (TRACTOR) | 105,426 |
| Tractor & Farm equipment | MAHINDRA & MAHINDRA LIMITED (SWARAJ DIVISION) | 87,995 |
| Tractor & Farm equipment | INTERNATIONAL TRACTORS LIMITED | 63,212 |
| Tractor & Farm equipment | TAFE LIMITED | 54,645 |
| Tractor & Farm equipment | ESCORTS KUBOTA LIMITED (AGRI MACHINERY GROUP) | 52,939 |
| Tractor & Farm equipment | JOHN DEERE INDIA PVT LTD(TRACTOR DEVISION) | 34,235 |
| Tractor & Farm equipment | EICHER TRACTORS | 29,205 |
| Tractor & Farm equipment | CNH INDUSTRIAL (INDIA) PVT LTD | 23,463 |
| Trailer | LOCAL TRAILER MANUFACTURER | 15,329 |
| Placeholder / unknown | OTHERS | 13,604 |
| 2W/3W maker (misfiled) | KINETIC MOTOR COMPANY LIMITED | 5,301 |
| Tractor & Farm equipment | JOHN DEERE INDIA PVT LTD(CROP SOLUTION DIV) | 4,790 |
| Tractor & Farm equipment | GROMAX AGRI EQUIPMENT LTD | 2,130 |
| Tractor & Farm equipment | V.S.T. TILLERS TRACTORS LIMITED | 1,419 |
| Tractor & Farm equipment | CAPTAIN TRACTORS PVT. LTD | 1,253 |
| Tractor & Farm equipment | INDO FARM EQUIPMENT LIMITED | 1,147 |
| Tractor & Farm equipment | KUBOTA AGRICULTURAL MACHINERY INDIA PVT.LTD | 923 |
| Small fabricator / workshop | AWACHAT INDUSTRIES LTD | 881 |
| Construction equipment | ACTION CONSTRUCTION EQUIPMENT LTD | 844 |
| Commercial vehicle | MAHINDRA ELECTRIC MOBILITY LIMITED | 830 |
| Tractor & Farm equipment | PREET TRACTORS PVT LTD | 798 |
| Tractor & Farm equipment | ADICO ESCORTS AGRI EQUIPMENTS PVT. LTD | 507 |
| Tractor & Farm equipment | SWARAJ AUTOMOTIVES LTD | 405 |
| Small fabricator / workshop | JAI BHAVANI ENGINEERING WORKS | 383 |
| Tractor & Farm equipment | SAME DEUTZ-FAHR INDIA (P) LTD | 373 |
