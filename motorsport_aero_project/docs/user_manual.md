# Installation, user guide and demonstration

## Installation

1. Install Python 3.12 and MySQL 8.0 or use the tested local environment described in README. Install `requirements-lock.txt` into a virtual environment.
2. Copy `.env.example` to `.env` and supply a connection to a dedicated `motorsport_aero` database. The loader creates its managed schema and transactionally refreshes the release tables. Credentials stay outside Git.
3. Run the commands in README. For a quick numerical smoke run use `--draws 20 --search-seeds 1`; this deliberately does not satisfy the full uncertainty/seed targets.
4. Excel must be available for the supplied COM recalculation script. On other platforms, recalculate the workbook in an installed spreadsheet engine and repeat the five numerical checks. Merely opening cached values is not verification.
5. Open `powerbi/Aero.pbip` in a Desktop version supporting PBIP/PBIR/TMDL. Enable project-format features if required by that version. Set the `DataFolder` M parameter to the absolute `powerbi/data` directory, then Refresh. Check source permissions and CSV encoding. Desktop acceptance remains outstanding in this release.

## Run a custom setup

```python
from src.schemas import Setup, Weather, Tyre, VehicleState
from src.vehicle_model import CarModel
from src.circuit_model import circuits
from src.optimization import constraint_reasons

car = CarModel(Setup(18, 22, .040, .065), Weather(), Tyre())
result = car.simulate_lap(circuits()['Apex Ring'], state=VehicleState(40, 10, 0, 85))
print(result.summary)
print(constraint_reasons(car, result))
result.trace.to_csv('custom_trace.csv', index=False)
```

Settings and thresholds live in `config/project.json`. Changing them requires a new model/data version and regenerated exports. `Setup` validates static bounds. The aero model additionally validates operating heights, yaw and roll. An exception or infeasible result must not be replaced with a plausible lap time.

## Interpret outputs

- Negative candidate-minus-baseline lap delta is faster. Positive DRS gain means the no-DRS reference took longer.
- Match circuit, weather, tyre, fuel, session and objective. Never compare the fastest wet lap directly with the fastest dry lap as a setup-only effect.
- `braking_distance_m` in a full lap is the summed distance of cells with braking. The independent 80-to-30 m/s braking experiment in recommendations is the comparable stopping-distance metric.
- A Pareto point is non-dominated across lap time, wear and mean drag among evaluated feasible candidates; it is not proof of global optimality.
- The uncertainty report counts invalid scenarios and gives both conditional improvement probability and feasible-improvement probability. The 95% interval is the 2.5th–97.5th percentile of assumed scenarios.
- The workbook's blue inputs drive independent scalar equations. Changing those cells does not rerun the Python vehicle simulator. Integrated traces and comparisons are labelled snapshots and require regeneration.

## Data lifecycle

`data/raw` retains generation configuration and source manifests. `data/synthetic` contains generated inputs. `data/processed/tables` contains canonical normalized exports. `powerbi/data` is a flattened analytical projection with the same run keys. SHA-256 manifests identify file releases; source timestamps are excluded when comparing numeric reproducibility.

The database schema and dictionary provide keys, types and units. No stored procedure is required: transformations are versioned Python and analytical SQL. Measured facts remain empty until licensed independent data can be imported and matched to simulated conditions.

## Database backup and restore

Use `mysqldump --single-transaction --routines --triggers -h 127.0.0.1 -P 3307 -u root -p motorsport_aero > backup.sql` for the isolated instance. Enter the password securely when prompted; do not place it in command history. Restore into a separate test database/instance, verify row counts and lap sums, then retain the restore log. The delivered `schema.sql` and `seed.sql` also reconstruct the synthetic release. Seed restore uses inserts/upserts in dependency order; it is not a migration of unknown production data.

The isolated instance can be restarted with `scripts/start_local_mysql.ps1`. It is bound only to localhost. Do not change the user's unrelated MySQL service or install a new Windows service for this project.

## Power BI model and acceptance

Facts receive circuit/setup/weather/tyre/session/car/date keys through a many-to-one run merge. Dimensions filter facts in one direction. Do not also activate redundant run-registry relationships. `fact_aero_map` is setup-grain/operating-point data, so weather/session slicers do not govern it unless an explicit scenario projection is created.

Import mode is used for reproducible CSV snapshots. For a live MySQL source, replace each CSV partition with an approved connector query to its view and retain the same column contract. Verify connector support, gateway placement, credentials and refresh ownership. DirectQuery is an optional separate deployment exercise, not an implemented refresh mode.

Single-user synthetic data needs no row-level security. If proprietary data is added, define team/circuit entitlement tables and test roles before sharing. No report is publicly published by this project.

Desktop checks: load all tables; inspect relationships; verify lap totals under circuit/setup/weather/tyre/session filters; select one run for trace plots; inspect missing/empty-reference measures; check pages at normal zoom; save/reopen; export visual totals; document screenshots. Any unimplemented bookmarks, tooltip pages and drill-through are tracked as remaining presentation extensions.

## Twelve-minute demonstration

1. **0–1 min:** State the research question and synthetic-data limitation.
2. **1–3 min:** Show the circuit-specific recommendations and explain a straight/corner trade-off using sector deltas.
3. **3–5 min:** Show speed, braking, downforce and DRS traces. Explain continuous states and legal-zone closure.
4. **5–7 min:** Compare search methods, feasible candidates, Pareto membership and the baseline. Show actual evaluation budgets.
5. **7–8 min:** Show uncertainty; explain why nominal improvement is not guaranteed under all scenarios.
6. **8–10 min:** Change the workbook speed or coefficient input, observe its force formula and inspect reconciliation. Run a MySQL analytical view.
7. **10–11 min:** Show test output, convergence and missing measured-reference status.
8. **11–12 min:** Summarize limitations and the next measured-data validation experiment.

## Troubleshooting

DLL import failures: use the tested Python 3.12 versions in the lock file. A Python 3.14 dependency combination was rejected by host application control; no security policy was changed. Database connection failures: verify the configured port and credentials, then run `scripts/load_database.py` without repeating simulation. Excel COM failure: close only the generated workbook if it is already open and retry; do not terminate unrelated user Excel sessions. Map errors: reduce the setup/operating excursion or expand the map only with documented evidence, never enable silent extrapolation.
