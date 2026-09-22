# Silverstone: five-page Power BI report

**Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.** Geometry © OpenStreetMap contributors, ODbL. Analytical sectors are not official timing sectors.

**Current result is not robust:** the nominal candidate delta is −0.036 s at 5 m but +0.035 s at 2.5 m. The sign reverses with mesh refinement. Include this note on presentation pages; the optimizer selects a discrete-grid minimum under a particular numerical resolution, not a validated improvement.

`Silverstone.pbip` is an authored Power BI project with five pages, native visuals, MySQL-backed Import partitions, seven model tables and DAX measures. It is not a PBIX captured from Desktop. Desktop loading, connector authentication, DAX execution and visual acceptance require the checks below; source authoring alone does not prove those steps passed.

## Windows connection

1. Run the Python pipeline with `--mysql`; it creates database `aero_lab_real`, normalized tables, and analytical views. See `../../docs/realtrack/README.md`.
2. Install Power BI Desktop and Oracle **MySQL Connector/NET**. Microsoft lists Import support and the Connector/NET prerequisite in its [MySQL connector documentation](https://learn.microsoft.com/en-us/power-query/connectors/mysql-database). Workbench installation alone is not this provider. Restart Desktop after installing the provider.
3. Open `Silverstone.pbip`. Enable the Power BI project feature if your installed Desktop version requires it. In Transform data → Manage parameters, set `MySQLServer` to your host/port and `MySQLDatabase` to `aero_lab_real`. This delivered workspace uses `127.0.0.1:3307`; a conventional installation uses `127.0.0.1:3306`.
4. In Data source settings, authenticate with **Database** credentials. Credentials belong in Desktop's credential store, never in M, DAX, source control or screenshots. Refresh.
5. If creating a PBIX manually: Get Data → MySQL database → the same server/database → Import. Select `dim_circuit`, `dim_setup`, `dim_sector`, `dim_run`, `fact_lap`, `fact_sector`, `fact_telemetry`. Use `queries.pq` as the exact M source for each query, and `measures.dax` for measures.
6. Save a PBIX after accepting the report. No Power BI Service publishing is performed. Scheduled cloud refresh would additionally need an appropriate standard gateway and connector installation; it is not part of this local release.

CSV fallback for demonstrations without MySQL: replace each M source with `Csv.Document(File.Contents(DataFolder & "/fact_telemetry.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])`, promote headers and retain the supplied type casts. Repeat with each corresponding CSV under `data/processed/realtrack`. Label this as CSV import, not a live MySQL connection.

## Relationships and grain

| Dimension key (one side) | Facts on the many side |
|---|---|
| dim_circuit[circuit_id] | fact_lap, fact_sector, fact_telemetry |
| dim_setup[setup_id] | fact_lap, fact_sector, fact_telemetry |
| dim_run[run_id] | fact_lap, fact_sector, fact_telemetry |
| dim_sector[sector_id] | fact_sector, fact_telemetry |

All relationships are active, single-direction from dimension to fact. Do **not** relate the facts to each other or add extra dimension-to-dimension relationships. The SQL storage is normalized; view projections repeat dimension keys deliberately for a star schema.

- `fact_lap`: one row per run. Never sum its lap time after joining to telemetry.
- `fact_sector`: one row per run × sector.
- `fact_telemetry`: one row per run × distance cell. Coordinates come from the referenced track point. Contains 11,780 rows in this release.
- `dim_run`: role, dataset hash and model version. Baseline, candidate and remaining grid runs are distinguishable.

Set numeric IDs and spatial fields to **Don't summarize**. Circuit and role selections should be visible on each page. Lap measures return blank where multiple runs make a single lap ambiguous. Baseline/candidate measures intentionally remove setup and run filters but retain circuit context, so their paired comparison remains stable when inspecting a grid setup. A sector selection changes telemetry/sector facts; it does not redefine a complete lap.

## Measures

All 19 measures are in `measures.dax` and the TMDL model. Important definitions:

| Measure | Definition and use |
|---|---|
| Lap Time s | Selected run's stored lap duration; blank when multiple runs are selected. |
| Baseline Lap s / Candidate Lap s | Matched role, one circuit; remove conflicting setup/run selections. |
| Lap Delta s | Candidate minus baseline; negative is faster. |
| Average Speed kmh | `SUM(step_m) / SUM(dt_s) * 3.6`; distance divided by elapsed time, not average of spatial speeds. |
| Max Speed kmh | Maximum entry speed × 3.6; the periodic trace includes every exit speed as the next entry. |
| Average Downforce N / Average Drag N | `SUMX(force * dt_s) / SUM(dt_s)`; time-weighted cell forces. |
| Tyre Wear Change pct | Sum of selected cell wear increments × 100, guarded to one run. This avoids dropping the final interval or counting gaps in disjoint selections. |
| Sector Time s / Sector Delta s | Sum of selected sector durations for one run / matched candidate minus baseline. |
| Setup Rank | Dense rank of nonblank selected setups by modelled lap time. Clear role/run filters to rank the full grid. |
| Model-generated share | Fraction of telemetry rows flagged synthetic; expected 1.000. This is not an accuracy score. |

For multiple runs, aggregate force and speed measures pool their selected time/distance; use a run/role legend or filter to one run to avoid an unintended pooled comparison.

## Exact five-page design

Every page contains slicers `dim_circuit[name]`, `dim_setup[name]`, `dim_run[comparison_role]`, and `dim_sector[name]`, plus cards `[Baseline Lap s]`, `[Candidate Lap s]`, `[Lap Delta s]`, `[Model-generated share]`. Select Silverstone explicitly. Keep the disclaimer visible. Use navy `#10263D`, teal `#176B91`, candidate green `#24CFBA`, baseline grey `#8695A4`.

| Page | Visual | Exact field binding |
|---|---|---|
| Executive Overview | Clustered column chart | Axis dim_setup[name]; Values [Lap Time s]. Clear run-role filters to compare the entire grid. |
| Executive Overview | Clustered bar chart | Axis dim_sector[name]; Values [Sector Delta s]. |
| Circuit Map & Sectors | Native scatter plot | Details fact_telemetry[point_index]; X [Map East m]; Y [Map North m]; Legend dim_sector[name]. Equal metre scales; small markers form a dense map. |
| Circuit Map & Sectors | Clustered column chart | Axis dim_sector[name]; Values [Baseline Sector s], [Candidate Sector s]. |
| Aero Trade-off | Line chart | X fact_telemetry[distance_m], continuous; Y [Average Downforce N]; Legend dim_run[comparison_role]. Filter role to baseline and candidate. |
| Aero Trade-off | Line chart | Same X/legend; Y [Average Drag N]. |
| Telemetry Analysis | Line chart | X fact_telemetry[distance_m], continuous; Y [Average Speed kmh]; Legend dim_run[comparison_role]. Filter to baseline/candidate. |
| Telemetry Analysis | Line chart | Same X/legend; Y [Average Acceleration mps2]. |
| Setup Optimizer | Table | dim_setup[name], front_wing_deg, rear_wing_deg; [Lap Time s], [Setup Rank], [Tyre Wear Change pct]. Sort rank ascending. |
| Setup Optimizer | Scatter plot | Details dim_setup[name]; X [Average Drag N]; Y [Lap Time s]. Clear role and sector filters for complete-run optimization. |

Recommended inspection additions in Desktop: distance-range slicer on Telemetry Analysis; tooltips with speed, force and wear on distance charts; conditional formatting on negative/positive deltas; model version/dataset ID tooltip. Page specifications matching the authored visuals are in `page_specifications.json`.

## A real x/y circuit map: two practical choices

**Native workaround (already authored):** dense scatter points reproduce the shape without a custom visual. Do not use the geographic Map visual with local metre coordinates—it expects latitude/longitude. Set X/Y min/max from the processed bounds and choose plot-area width/height proportional to the x/y ranges, or pad both axes to an equal square span. Choose one run to prevent duplicate point identities. Native scatter does not connect a racing-line polyline.

**Connected line with Deneb:** add Deneb through Desktop's visual marketplace if allowed. Add these columns to its Values field well: `point_index`, `x_m`, `y_m`, `distance_m`, `sector_id`, `speed_kmh`, `downforce_n` from fact_telemetry. Set Don't summarize and filter to exactly one run. Paste `circuit_map_deneb.json` into a Vega-Lite specification. It binds to Deneb's internal `dataset`, orders by point index and colors by analytical sector. See the [Deneb dataset contract](https://deneb.guide/docs/dataset).

The supplied specification fixes width and computes height from Silverstone's x/y spans. For an added circuit regenerate it or adjust its domains/aspect ratio; independent automatic axis scales can distort the track. Small gaps at the sector boundaries and lap closure represent separately colored line segments, not road discontinuities. This project does not install an unrequested marketplace visual automatically.

## Desktop acceptance checklist

- [ ] MySQL authentication and refresh complete with all seven views.
- [ ] Relationships remain one-to-many and single-direction, with no fact-to-fact links.
- [ ] Full baseline/candidate cards match `data/processed/realtrack/simulation_runs.csv` to 0.001 s.
- [ ] Sector totals equal lap durations; candidate sector deltas sum to lap delta.
- [ ] Choosing a setup changes its own lap and force metrics; paired baseline/candidate cards remain paired.
- [ ] Map uses equal metre scales; run filtering does not deform its shape.
- [ ] Baseline/candidate-only legends exclude pooled grid runs on telemetry charts.
- [ ] All five pages load, legends/labels are readable, and every disclaimer is visible.
- [ ] Exported screenshots show filters, units and data classification; no credentials appear.

JSON-schema validation, when recorded, checks PBIR structure only. It does not execute M or DAX or render visuals.
