# Aero Lab: real circuit data analytics and simulation

**Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.**

This final-year project follows one dataset from public Silverstone coordinates through Python, MySQL, Power BI and an interactive Three.js replay. The older fictional-circuit project remains available under `reports/legacy_dashboard.html`; its recommendations are separate historical examples.

## Quick start on Windows

Run commands from `motorsport_aero_project` in PowerShell. Python 3.12 is recommended. The existing delivered CSVs, database seed SQL and browser data can be explored before rerunning the model.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# Create .env only if you do not already have one. Preserve existing credentials.
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Run offline from the included source snapshot:
.\.venv\Scripts\python.exe -m src.realtrack.pipeline
.\.venv\Scripts\python.exe scripts/realtrack_sensitivity.py
.\.venv\Scripts\python.exe -m src.viewer
```

Open http://127.0.0.1:8765/reports/dashboard.html. Choose Analysis or 3D Simulation. Play, pause, reset, change camera, switch baseline/candidate or compare both cars. The local server is read-only and blocks dotfiles. Do not open the HTML with file:// because browser module loading needs HTTP.

In this existing workspace, the already working interpreter is `..\.venv312\Scripts\python.exe`; it can replace `.\.venv\Scripts\python.exe` in those commands. The model does not require a GPU, but Three.js requires WebGL2.

## MySQL Server and Workbench

Install MySQL Server 8.0.16+ or a compatible newer release and Workbench. Workbench is a client, not the database server. Start the MySQL service and connect in Workbench.

Set this variable in the project `.env`, using your own password and port:

```dotenv
REALTRACK_MYSQL_URL=mysql+pymysql://aero_user:YOUR_PASSWORD@127.0.0.1:3306/aero_lab_real
```

URL-encode reserved password characters in a SQLAlchemy URL. Never commit `.env`. The user must have schema-creation and table/view CRUD privileges for this dedicated database. A database administrator can first execute `sql/realtrack_schema.sql`, create a local user and grant privileges scoped to `aero_lab_real.*`. The loader may reuse the already configured `MYSQL_URL` credentials if the dedicated variable is absent, but always targets `aero_lab_real`; it does not replace the legacy database.

```powershell
.\.venv\Scripts\python.exe -m src.realtrack.pipeline --mysql
```

The Python loader creates/updates schema and views, loads one atomic data snapshot for configured circuit IDs, and checks rows, lap totals and geometry/performance equality. Rerunning does not append duplicate telemetry. Do not store unrelated manual data under those managed circuit IDs. DDL and data transactions are separate because MySQL DDL commits implicitly.

Alternatively, use Workbench: execute `sql/realtrack_schema.sql`, then `sql/realtrack_seed.sql` **once on an empty schema**. The seed file contains actual delivered records in insert batches and a transaction. It intentionally fails on duplicate keys; use the Python loader for repeatable refreshes. Run `sql/realtrack_queries.sql` for comparisons and reconciliation. This path needs no `LOCAL INFILE` server setting.

## Power BI Desktop

The complete setup, exact fields/visuals, DAX and map instructions are in [the five-page Power BI guide](../../powerbi/Silverstone/README.md). Open `powerbi/Silverstone/Silverstone.pbip`, set MySQL host/port parameters, authenticate and Refresh. Connector/NET is required in addition to Workbench. Import mode is used. The native map workaround needs no custom visual; an optional Deneb specification provides connected lines.

Regenerate the authored Power BI files after schema changes:

```powershell
.\.venv\Scripts\python.exe scripts/build_realtrack_powerbi.py
.\.venv\Scripts\python.exe scripts/validate_realtrack_powerbi.py
.\.venv\Scripts\python.exe scripts/verify_realtrack_mysql.py
```

The project is source-authored; Desktop execution, M/DAX evaluation and visual acceptance are tracked separately from JSON-schema checks. Do not claim a successful Power BI connection simply because Python loaded MySQL.

## File-by-file code map

| File/folder | Purpose |
|---|---|
| `config/realtrack.json` | Circuit registry, source relation/start way, spacing, smoothing, vehicle assumptions and setup grid. |
| `src/realtrack/ingest.py` | Download/cache OSM relation, exclude pit lane, deduplicate ways, assemble directed closed route and record provenance. |
| `src/realtrack/geometry.py` | WGS84 → east/north metres, cleaning, periodic smoothing, arc length, heading, curvature, classification and analytical sectors. |
| `src/realtrack/model.py` | Aero assumptions, curvature/grip/power/braking limits, periodic speed envelope, time and tyre proxy. |
| `src/realtrack/database.py` | SQL inserts, atomic MySQL data refresh, row/time/coordinate/force reconciliation. |
| `src/realtrack/pipeline.py` | Orchestrates all circuits and setup runs; exports normalized and star-shaped CSVs, replay JSON, SQL seed and validation. |
| `src/realtrack/dashboard.py` and `dashboard.html` | Builds the real-track browser analysis from the same payload, retaining the legacy page. |
| `reports/simulation/processed-curve.js` | Distance-indexed adapter over processed x/y; no new fictional spline. |
| `reports/simulation/circuits.js` | Builds track scenery from the adapter; preserves legacy layouts separately. |
| `reports/simulation/replay.js` | Uses the processed curve and existing time-driven baseline/candidate replay. |
| `reports/simulation/ui.js` | Same live HUD and controls, with real-geometry/model-performance provenance. |
| `reports/simulation/car.js`, `scene.js`, `telemetry.mjs`, `boot.js`, CSS | Reused procedural car, cameras, force cues, data sampling and layer controls. |
| `data/raw/silverstone/` | Raw OSM response, extracted longitude/latitude CSV, provenance and licence attribution. |
| `data/processed/realtrack/` | Six normalized CSVs, seven Power BI view projections, replay JSON and verification records. |
| `sql/realtrack_schema.sql` | Six tables, primary/foreign keys, constraints, indexes and seven analytical views. |
| `sql/realtrack_seed.sql`, `realtrack_queries.sql` | Complete sample load and useful analysis/reconciliation queries. |
| `scripts/build_realtrack_powerbi.py` | Generates the five-page PBIP/PBIR/TMDL project, M, DAX and Deneb map spec. |
| `scripts/validate_realtrack_powerbi.py` | Validates authored report JSON against cached Microsoft schemas. |
| `tests/test_realtrack.py`, `tests/realtrack-replay.test.mjs` | Source/geometry, all-run physics invariants, cross-output equality and exact 3D point binding. |
| `docs/realtrack/methodology.md` | Equations, limitations, result interpretation and future improvements. |
| `docs/realtrack/screenshots_checklist.md` | Evidence to capture for GitHub and final-year demonstration. |

## Reproduction and extension

The default uses the shipped source snapshot. Use `--download` only when intentionally updating public geometry; it replaces the snapshot and records a new checksum. OSM is editable, so source changes may require route inspection. Network failures do not create substitute geometry.

For another circuit add a unique circuit ID, slug, OSM circuit relation ID, directed start way ID and expected length range to `config/realtrack.json`. Ensure the selected relation contains a single directed closed main route. The ingester rejects disconnected/ambiguous topology. Run the pipeline to obtain separate circuit/run/point keys and a shared selector entry, then rebuild Power BI. Sector boundaries default to analytical equal-distance thirds for every circuit; do not rename them official sectors without a documented source. The original 10 m fictional simulation remains independent.

Run the checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_realtrack.py -q
node --experimental-loader ./tests/three-loader.mjs --test tests/realtrack-replay.test.mjs
```

Use Node.js 22+ only for JavaScript development checks; the browser itself needs no Node build. The geometry loader is test-only. A successful test establishes numerical/software consistency under assumptions, not measured-car validation.

## GitHub delivery

Commit code, config, `.env.example`, attributed source snapshot, sample outputs, SQL, Power BI source and documentation. Exclude `.env`, venvs, caches, logs, MySQL runtime directories and credentials. Do not publish a database URL containing a password. Keep OSM and Three.js attribution/licence files in every redistributed archive. Describe the project as an educational data engineering and simulation system. See the screenshot checklist before claiming browser or Desktop acceptance.
