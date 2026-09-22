# Interactive multi-circuit upgrade

Run `python -m src.realtrack.api --port 8765` from this folder, then open http://127.0.0.1:8765/reports/dashboard.html. Supports Silverstone, Monaco, Monza, Spa-Francorchamps and Suzuka with draft setup controls and Python-generated paired telemetry. See [dynamic simulation guide](docs/dynamic_simulation.md) for API, formulas, sources and tests. Live runs are separate from the archived MySQL / Power BI dataset.

# Motorsport Aerodynamic Setup Optimization

## Silverstone real-geometry extension — start here

The current Aero Lab entry point now follows a public OpenStreetMap Silverstone centreline through Python, a dedicated MySQL database, five-page Power BI source and the shared Three.js replay. **Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.**

- [Windows quick start and complete file guide](docs/realtrack/README.md)
- [Methodology, equations and limitations](docs/realtrack/methodology.md)
- [Power BI MySQL setup and five-page report](powerbi/Silverstone/README.md)
- [Screenshot and demonstration checklist](docs/realtrack/screenshots_checklist.md)

Run `python -m src.realtrack.pipeline --mysql`, then `python scripts/realtrack_sensitivity.py`, then `python -m src.viewer`. Open `http://127.0.0.1:8765/reports/dashboard.html`. The source snapshot supports offline reruns; omit `--mysql` for CSV/browser-only output. Baseline/candidate gain reverses sign between 5 m and 2.5 m meshes, so no robust performance improvement is claimed.

The sections below describe the retained legacy fictional-circuit release. Its browser page is now `reports/legacy_dashboard.html`.

A runnable research project joining a synthetic aerodynamic map, a digital vehicle model, constrained setup search, MySQL, Excel and a Power BI project.

**All car, track, aero and tyre data are synthetic or assumed.** This is a simplified quasi-static model, not a calibrated racing simulator. No measured-car accuracy is claimed.

## Start here

- `reports/technical_report.md`: research report and results.
- `reports/recommendations.json`: circuit-specific recommendations and matched baselines.
- `outputs/aero-release/Motorsport_Aero_Engineering.xlsx`: 31-sheet engineering workbook.
- `powerbi/Aero.pbip`: 18-page authored Power BI project. Open with compatible Power BI Desktop, update `DataFolder` if moved, then Refresh.
- `reports/dashboard.html`: Aero Lab analysis plus a separate interactive Three.js simulation layer, supplementary to Power BI. Run `python -m src.viewer` and open `http://127.0.0.1:8765/reports/dashboard.html#simulation`.
- `docs/simulation_3d.md`: 3D controls, file-by-file code guide, exact data binding, local run instructions and modelling limitations.
- `reports/validation_report.md`: executed checks and limitations.
- `docs/user_manual.md`: controls, interpretation and demonstration.

## Reproduce

Use Python 3.12 and the locked dependency list. From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
# Edit MYSQL_URL for your own MySQL database before the load step.
.\.venv\Scripts\python.exe -m src.pipeline --draws 200 --search-seeds 5
.\.venv\Scripts\python.exe scripts/add_experiments.py
.\.venv\Scripts\python.exe -m src.visualization
.\.venv\Scripts\python.exe scripts/build_workbook.py
.\scripts\recalculate_excel.ps1 -WorkbookPath .\outputs\aero-release\Motorsport_Aero_Engineering.xlsx
.\.venv\Scripts\python.exe scripts/build_powerbi.py
.\.venv\Scripts\python.exe scripts/validate_powerbi.py
.\.venv\Scripts\python.exe -m pytest -q --junitxml=reports/tests.xml
.\.venv\Scripts\python.exe -m src.reporting
```

The current workspace also has a tested Python environment at `../.venv312/Scripts/python.exe`. The isolated MySQL instance uses localhost port 3307; its generated connection is in ignored `.env`. No credentials are included in the shareable project.

`scripts/run_release.ps1` automates the generation sequence using the available environment. MySQL uses a **dedicated release-snapshot database**: the loader transactionally replaces only its managed tables. Do not point it at an unrelated production database.

## Model

The spatial solver iterates a backward braking and forward drive envelope with periodic flying-lap speed. It carries tyre wear, temperature and fuel between cells and laps; uses rear-axle traction, load sensitivity, brake bias and a combined-slip envelope; and closes DRS when braking or outside the defined zone. Wing/height effects use a bounded synthetic coefficient surface. The standalone gridded interpolator rejects extrapolation.

Nominal spatial step is 10 m; search and uncertainty screening use 25 m. A 5 m convergence run checks the finalist. Gear shifts add an explicit lumped time cost. Dynamic balance is quasi-static, with assumed compliance and roll stiffness. See `reports/assumption_changes.md` for changes from the proposal.

## Evidence and limitations

The release includes executable tests, a live MySQL reconciliation, recalculated Excel checks, public-schema validation of Power BI JSON, search logs and a dataset manifest. Power BI Desktop is not installed in the execution environment, so TMDL/DAX execution, report rendering, bookmarks, drill-through behaviour and service publication are **not verified**. A source project is not a claim of a published or Desktop-tested report.

Independent measured tables are intentionally empty. Surrogate residuals compare against the synthetic simulator. Uncertainty distributions are assumed and their intervals are not real-car calibrated confidence intervals.

Do not infer a globally optimal or safe real-car setup from a finite-budget search. Failed candidates and no-improvement outcomes are legitimate.
