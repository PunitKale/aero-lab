# Aero Lab — Geometry-Driven Research

**Live dashboard: [aero-lab.onrender.com](https://aero-lab.onrender.com/reports/dashboard)**

Hosted on Render's free Python service. After inactivity, the first load may take 50 seconds or more while the service wakes up.

A complete final-year Python analytics and simulation project: five mapped circuits, interactive aero setup comparison, Three.js replay, MySQL and Power BI source reports.

**Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.** The vehicle model is uncalibrated. The finer-spacing check measures numerical sensitivity, not real-world accuracy.

## Run on Windows

```powershell
cd motorsport_aero_project
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-web.txt
.\.venv\Scripts\waitress-serve --host=127.0.0.1 --port=8765 src.realtrack.web:app
```

Open http://127.0.0.1:8765/reports/dashboard. MySQL is not required for the live dashboard. Install `requirements.txt` as well for the full research pipeline.

## Explore the project

- [Deployment guide](motorsport_aero_project/docs/deployment.md): Python hosting with the root `render.yaml`.
- [Interactive model, sources and limitations](motorsport_aero_project/docs/dynamic_simulation.md).
- [Full project guide](motorsport_aero_project/README.md).
- [Real-geometry pipeline and Power BI setup](motorsport_aero_project/docs/realtrack/README.md).

Code is in `motorsport_aero_project/src`, browser assets and results in `reports`, public source snapshots and generated data in `data`, schemas in `sql`, report sources in `powerbi`, and research in `notebooks`, `docs` and `tests`. Root `planning` preserves the original proposal.

The deployment/API/model regression selection passes 36 tests locally. Power BI Desktop refresh remains unverified. Secrets, local database/runtime files, virtual environments and release ZIPs are excluded from Git. Source geometry and vendored library licenses are retained. Earlier reports below describe historical stages; their numerical results are not live or measured telemetry.

## Historical project notes

# Motorsport Aerodynamic Setup Optimization

**Current project:** [Silverstone real-geometry analytics and simulation](motorsport_aero_project/docs/realtrack/README.md), with public OSM coordinates, Python, MySQL, five-page Power BI source and Three.js sharing one processed dataset. [Methodology and limits](motorsport_aero_project/docs/realtrack/methodology.md). Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.

Research implementation release, dated 17 September 2026.

Aero Lab now includes a separate procedural Three.js simulation layer sharing the analysis circuit selector and saved telemetry. See the [3D simulation guide and file-by-file changes](motorsport_aero_project/docs/simulation_3d.md). Twelve replay/geometry checks pass; browser visual acceptance and GPU frame-rate benchmarking remain unmeasured.

Start with [the implemented project](motorsport_aero_project/README.md), [technical report](motorsport_aero_project/reports/technical_report.md), or [interactive results viewer](motorsport_aero_project/reports/dashboard.html).

The release includes the Python vehicle simulator and optimization engine, 133 simulation runs, a live-tested MySQL schema and seed data, a recalculated 31-sheet workbook, 19 engineering figures, two executed notebooks, 39 passing tests, and an authored 18-page Power BI source project.

**Acceptance boundary:** Power BI Desktop is not installed here. Its JSON schemas pass, but Desktop loading, DAX execution, visual acceptance and publishing remain unverified. Independent measured-car validation is unavailable because no measured dataset was supplied. See [validation evidence](motorsport_aero_project/reports/validation_report.md).

The original [Stage 1 proposal](reports/stage_1_project_proposal.md) is retained as a planning record.

Planning files:

- [16-week schedule](planning/implementation_schedule.csv)
- [Risk register](planning/risk_register.csv)
- [Requirements and acceptance matrix](planning/requirements_traceability.csv)

All car parameters, circuits, aero maps and tyre models are explicitly synthetic or assumed. No real-world accuracy or regulatory-compliance claim is made.
