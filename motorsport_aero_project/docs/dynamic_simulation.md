# Interactive Aero Lab

The dashboard view is now owned by `src/realtrack/dashboard_view.py` and served directly by Python at `/reports/dashboard`. The previous `/reports/dashboard.html` address remains a compatible Python route. Existing HTML files are compatibility snapshots. Browser HTML/CSS/JavaScript and Three.js remain necessary for the unchanged interactive interface. Display times use minutes:seconds.milliseconds; API, exported data and physics retain seconds.

Run from the project folder on Windows:

```powershell
python -m pip install -r requirements.txt
python -m src.realtrack.api --port 8765
```

Open http://127.0.0.1:8765/reports/dashboard.html. The Python process serves the API and browser assets on one origin. Stop any older static viewer using that port first. The interactive page requires this API, not `python -m http.server`. All JavaScript libraries and geometry are local; no build step or network is required for normal use.

## Files and flow

- `config/circuits.json`: five attributed circuits; geographic `[longitude, latitude]` centreline, calculated length, 5 m corner classifications, analytical sector boundaries, assumed weather.
- `data/raw/catalogue/`: cached GeoJSON and upstream MIT licence/README. Silverstone retains its existing OSM cache and ODbL attribution.
- `scripts/build_circuit_catalogue.py`: rebuilds catalogue from those caches (`python scripts/build_circuit_catalogue.py`). Add a source entry and expected length bounds here to support another circuit.
- `src/realtrack/api.py`: validated same-origin HTTP endpoint and atomic paired simulations.
- `src/realtrack/dynamic_model.py`: version 2 educational model, separate from the archived research model.
- `reports/dynamic.js`: draft controls, presets, browser-local save, circuit selection, API state and JSON export.
- `reports/dynamic-render.js`: KPIs, six distance charts, circuit map, sector and run tables.
- `src/realtrack/dashboard.html` and `reports/dashboard.html`: dashboard template and delivered page.
- `reports/simulation/{boot,replay,telemetry,ui}.js` (telemetry is `.mjs`): data-change events, geometry rebuild/reset and interpolated replay.
- `tests/test_dynamic_api.py`: all circuits, calculation reconciliation, grip envelope, input rejection and parameter sensitivity.

The same successful API response feeds every analysis view and the two-car replay. Circuit changes load default weather, retain candidate vehicle/aero choices, recalculate the full pair, rebuild track geometry and reset to a paused flying lap. Form edits, Reset Setup and Load Preset change only draft values. Save Setup stores one preset in this browser; it does not submit a simulation. Invalid fields cannot be submitted. An API failure retains and labels the last successful circuit/result. Only one simulation is allowed at a time; other requests receive HTTP 429.

Live runs are exploratory and are **not silently written to MySQL or Power BI**. Export run JSON records both parameter sets, source checksums, processed geometry and telemetry. The existing saved research pipeline and database remain available separately. Candidate is the user's requested setup, not an automatically selected optimum. Very small deltas may reverse under finer spatial sampling.

## API

`GET /api/circuits` returns the catalogue, defaults, numeric bounds/steps/labels and tyre choices.

`POST /api/simulate`, `Content-Type: application/json`:

```json
{"circuit_id":"monza","parameters":{"front_wing_deg":12,"rear_wing_deg":15,"diffuser_efficiency":1.1,"tyre_compound":"soft","fuel_load_kg":20,"wind_speed_mps":5,"wind_direction_deg":90}}
```

Missing fields use API defaults. The optional `centerline_lonlat` must match the selected catalogue entry, preserving source attribution. Unsupported circuits, mismatched geometry, unknown keys, wrong types, nonfinite or out-of-range values return HTTP 400 with an `error` message. The full body is limited to 1 MB. This is a loopback-only development server, not a public deployment service.

Response has `recommendations[name]` (baseline/candidate summaries, parameters, sector times, delta), `traces[name][role]` (column arrays) and `geometry[name]` (distance/x/y points, actual length, source, metadata, sectors). Distances are 0,5,10,…; the final cell is shorter and closes the loop. `time_s`/`dt_s`, `speed_mps`/`exit_speed_mps`, acceleration, forces, wear and sector IDs describe each cell. Lap time is sum(dt), sector time is sum(dt) within that sector, delta is candidate minus baseline. Both runs start on the same origin with the same elapsed clock.

## Transparent model assumptions

All performance values are model estimates, not CFD or official telemetry.

For wing angles F/R in degrees and heights hf/hr in metres:

```
floor = clip(1 - 3*abs(hf-.04) - 2*abs(hr-.06), .7, 1)
Cl = (1.5*diffuser_efficiency + .045*F + .060*R)*floor
Cd = .55 + .0007*F² + .001*R² + .08*(1-floor) + .02*(diffuser_efficiency-1)²
rho = 101325 / (287.05*(air_temperature_C + 273.15))
downforce = .5*rho*air_speed²*1.5*Cl
drag = .5*rho*air_speed²*1.5*Cd
mass = vehicle_mass_excluding_fuel + fuel_load
```

Coefficients are assumed response curves, not fits to measured data. Wind direction is meteorological FROM north clockwise. With east-counterclockwise track heading h, longitudinal headwind is `wind_speed*sin(h+direction)`; `air_speed=max(ground_speed+headwind,0)`. Crosswind side forces/yaw effects are omitted. Cell aero values average squared relative speed at both endpoints. Solver capacity/drag bounds use conservative endpoint wind and speed envelopes.

Dry compound friction coefficients are soft1.65, medium1.55, hard1.45, multiplied by `max(.75,1-.00025*(track_temperature-30)²)`. Steady corner speed reserves longitudinal grip for resistance, sharing `mu*(mass*g+downforce)` through a friction circle with lateral demand `mass*v²*abs(curvature)`. Forward power-limited and backward braking passes converge around a periodic flying lap. Caps: 480 kW wheel power, 95 m/s, 39.24 m/s² lateral, 28 m/s² braking; rolling coefficient .015, area1.5 m². No hard-coded lap target.

`dt=2*ds/(v_start+v_end)` and `a=(v_end²-v_start²)/(2*ds)`. Tyre wear is an arbitrary dimensionless proxy: `ds*1e-6*(1+.2*v²*abs(curvature)/g+.08*max(-a,0)/g)` times compound factors soft1.3/medium1/hard.75 and `1+.01*abs(track_temperature-30)`. Wear does not reduce grip during the lap. Fuel adds constant mass; consumption is omitted. There are no gear shifts, suspension transients, temperature evolution, DRS, rain or racing-line optimization.

WGS84 coordinates are converted to local east/north metres, smoothed over4m and resampled by distance. Length is recalculated rather than forced to a published lap length. Sector boundaries are analytical equal-distance thirds, not official timing sectors. Geometry is approximate; flat elevation ignores hills and Suzuka's overpass height. Tarmac width, kerbs, trees and car are procedural illustrations. Monaco does not include a city model.

Replay integrates speed within each 5m cell for position and interpolates speed, force overlays and wear. Analysis/export keep original numerical cell values. Car comparison lane offsets and airflow particles are visual aids, not alternative racing lines or fluid calculations.

## Sources

- Silverstone: OpenStreetMap relation51160, https://www.openstreetmap.org/relation/51160; © OpenStreetMap contributors, ODbL1.0.
- Monaco, Monza, Spa-Francorchamps, Suzuka: https://github.com/bacinger/f1-circuits, © Tomislav Bacinger; MIT licence cached at `data/raw/catalogue/LICENSE.md`. Upstream map-derived geometry is approximate and may not represent the latest surveyed modifications. Per-file SHA256 and source URLs are in the catalogue. No real performance telemetry is used.

## Verification

```powershell
python -m pytest tests/test_dynamic_api.py tests/test_realtrack.py -q
node --experimental-loader ./tests/three-loader.mjs --test tests/simulation.test.mjs tests/simulation-geometry.test.mjs tests/realtrack-replay.test.mjs
```

Browser acceptance: edit without running (old lap stays), submit (all views change), switch all five circuits, change while replay is playing (pause/reset), test camera/focus/compare/flow, invalid numeric input, Save/Reset/Load Preset, and narrow viewport. Exported JSON must reconcile lap=sum(dt), sector sums and total length=sum(step_m).


## Research comparison upgrade

The Python API adds reproducible descriptive evidence via `src/realtrack/comparison.py`:
- cumulative delta at each cell boundary is cumsum(candidate dt − baseline dt), including the lap endpoint;
- sector and straight/fast-corner/corner differences sum to the same lap delta;
- average speed is lap distance / lap time; mean forces are weighted by cell duration;
- downforce impulse is sum(downforce × dt), N·s; drag work is sum(drag × ds), J;
- tyre degradation remains an arbitrary wear proxy, with no grip feedback.

Insights explain observed model differences and coefficient changes. They do not assign an isolated causal contribution to a wing or fuel change. Identical parameters produce the explicit no-change message. Winner is nominal and ties use the displayed 0.001 s precision. Confidence is “Unvalidated model estimate — uncertainty not quantified” for each lap; it is not a probability or measured error band.

`reports/research.js` supplies six responsive comparison charts, a winner card, metric table, assumption warnings, accessible parameter help, change marking and circuit-aware preset notes. Preset recommendations are circuit-character heuristics, not optimization or engineering advice. Reset candidate to baseline keeps the current shared weather; Reset Setup also restores circuit-default weather. Neither executes the simulator until submission.

`reports/research-exports.js` provides reusable CSV row generation and quoting. Lap, sector and telemetry exports repeat scalar metadata on each row: circuit, UTC timestamp, model version, dataset ID, both setups (including shared weather), assumptions, source URL/licence/checksum and disclaimer. JSON retains the complete structured metadata. Calculations/exports use seconds; time cards use minutes:seconds.milliseconds. CSV files are UTF-8 and use quoted RFC-style fields. Existing MySQL and Power BI snapshots are not overwritten.

Focused changed files: `src/realtrack/api.py`, `comparison.py`, `dashboard_view.py`; `reports/dynamic.js`, `dynamic-render.js`, `research.js`, `research-exports.js`; synchronized HTML compatibility snapshots. No vehicle solver equations or 3D controls were removed. Sample JSON and three CSVs are under `reports/research-sample.json` and `reports/sample-*.csv`.

Validation: `python -m pytest tests/test_dynamic_api.py tests/test_comparison.py -q`. Comparison tests reconcile cumulative, sector and classification deltas and load integrals. CSV checks verify metadata, quoting, row counts and lap-time reconciliation after parsing with Python.


## Efficiency and prediction checks

The server keeps a bounded 16-lap in-memory LRU cache keyed by normalized parameters, circuit, geometry source checksum, solver/API revision and spacing. Identical baseline and candidate runs share one calculation. Cached arrays are copied before use so callers cannot mutate future results. Restarting clears the cache. Changing weather invalidates both lap keys. JSON uses compact serialization and gzip when accepted. Charts outside the viewport defer SVG creation and retain the newest run definition until scrolled into view. Numerical fidelity is unchanged.

The optional **Verify prediction at finer spacing** button checks the committed result, not draft edits, through `POST /api/verify` with the same circuit/parameter body. It repeats at 5 m and 2.5 m, reports each lap's shift and both deltas, and stores the check in JSON metadata / CSV verification fields. The displayed production replay remains 5 m. A ranking is labelled consistent in this limited check only when both signed deltas agree and the smaller gain exceeds their difference plus 0.0005 s. Otherwise the winner card is inconclusive; identical setups are a tie. This conservative display rule is not a calibrated statistical threshold or proof of convergence.

For the Silverstone rear-wing24° example, a nominal -0.059 s delta at5m becomes +0.014 s at2.5m, so the gain is not numerically robust. This is why small simulated gains must not be treated as real engineering conclusions. Both resolutions still use the same approximate geometry, flat elevation and uncalibrated coefficients. Real-world prediction accuracy requires a documented measured dataset, separate calibration/holdout sessions and error assessment; no such accuracy claim is made here.

Local benchmark before caching: ~0.277 s for a changed rear wing and ~0.271 s repeated. After caching: ~0.146 s changed and ~0.012 s repeated (Python call only; excludes browser rendering/network). A representative compact response decreased from ~1.02MB to~0.39MB with gzip level1. Timings vary by laptop and cache state. `tests/test_efficiency.py` checks cache isolation, weather invalidation and distinct-resolution checks.
