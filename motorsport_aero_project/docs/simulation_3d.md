# Aero Lab — 3D simulation layer

The existing Analysis tab and its charts remain the analytical source of truth. The new **3D Simulation** tab replays those same saved baseline/candidate traces on original illustrative circuits. Everything runs locally with plain browser modules; no bundler, npm install, model download, or runtime CDN is needed.

## Run

From the `motorsport_aero_project` directory in PowerShell:

```powershell
..\.venv312\Scripts\python.exe -m src.viewer
```

Open http://127.0.0.1:8765/reports/dashboard.html and select **3D Simulation**. If the viewer is already running, refresh the existing page. An alternative on another machine is `python -m http.server 8765 --bind 127.0.0.1` from the project directory. Use HTTP, not a file:// URL, because browsers load JavaScript modules with origin checks. WebGL2 and hardware acceleration must be available; an initialization failure leaves Analysis accessible and displays a diagnostic.

Select **Downforce Circuit** to reproduce the values requested:

| Value | Display |
|---|---:|
| Front wing | 12.48° |
| Rear wing | 10.04° |
| Front ride height | 0.0384 m |
| Rear ride height | 0.0551 m |
| Candidate lap | 26.517 s |
| Baseline lap | 27.654 s |
| Candidate − baseline | −1.137 s |

The other two circuits retain their own saved recommendations. Calculations use full precision, while the HUD rounds only the display. Baseline settings come from the existing `Setup` defaults: 17.5° / 20°, 0.040 / 0.060 m. Wing angle and static ride-height/rake change the procedural model as well as the displayed setup. Force and performance values come from the saved run, not from the rendered wing geometry.

## Controls

- **Play / Pause / Reset:** start or stop the clock; Reset returns to the beginning of the saved flying lap and pauses.
- **Playback:** 0.25× through 4×; changes replay time, not model physics.
- **Focus run:** quick-switch baseline/candidate without resetting the shared clock. The HUD, follow camera, and aero overlay follow this selection.
- **Compare both cars:** display both runs at the same elapsed time. Small ±1.7 m lateral presentation offsets prevent overlapping bodies. They do not change distance, speed, or lap time. The HUD reports cumulative distance lead and lap count; each car wraps on its own duration.
- **Chase:** smoothly follows behind the focused car. **Cockpit-style:** looks over its nose. **TV / broadcast:** elevated trackside camera patches pan toward it. **Free orbit:** drag to rotate, scroll/pinch to zoom, right-drag to pan; this camera stays where you put it until another mode/run is selected.
- **Force arrows:** two downward axle arrows and one opposing drag arrow. All share a linear scale of 1 metre / 4 kN plus a 0.25 m visibility floor. Downforce shifts teal toward green with increasing force; drag shifts amber toward orange. Numeric force magnitudes remain visible in the HUD.
- **Airflow particles:** optional speed-driven visual cue. They are not fluid particles from a numerical flow solver.

## Data flow and timing

`src/reporting.py` embeds the existing six CSV traces and recommendations in one shared `AERO_DATA` object. Both tabs use the same `#circuit` selector. The 3D modules are imported only when the simulation tab opens. Returning to Analysis or hiding the browser document stops animation scheduling; returning resumes without accumulating background time.

The data are spatial cells, not frame samples. `time_s` and `distance_m` mark cell entry, and `dt_s`/`step_m` describe the interval. Binary search finds the active cell. The sum of the last entry timestamp and its duration is the exact lap time; no fabricated terminal sample is needed. Position within each cell uses a normalized integral of entry/exit speed. The source solver includes lumped shift losses in `dt_s`, so the replay stretches motion within those cells. Pose is approximate within a cell; the saved lap clock and distance boundaries are preserved exactly.

Speed interpolates between the saved entry and exit values. Downforce, drag, acceleration, tyre wear, and sector use the active saved cell. In particular, displayed forces are not claimed to be newly solved at every video frame. Tyre wear is the saved fractional value multiplied by 100 for display. Repeated laps loop the same qualifying trace, including tyre state; this is not a new multi-lap degradation simulation.

Spline progress uses the sampled distance fraction with Three.js arc-length parameterization. The circuits are original centripetal closed Catmull–Rom splines, sized approximately to the saved lap distance. Velocity Park has broad sweeping sections, Apex Ring mixed corners, and Downforce Circuit more direction changes. **These layouts do not reproduce the solver's radius sequence.** Local visual corner tightness therefore does not establish a speed/curvature/grip relationship. The source synthetic setup can run a high speed through a visually tight section. A future physically coupled version should derive solver radii and track sectors from the same spline, then rerun all optimizations; this upgrade intentionally preserves the existing results.

## File-by-file implementation

| File | Responsibility |
|---|---|
| `src/reporting.py` | Adds the two layers and import map; embeds baseline setup; preserves the analysis generator and shared data. |
| `reports/dashboard.html` | Regenerated complete runnable dashboard entry point. |
| `reports/simulation/boot.js` | Lazy module loading, layer switching, shared circuit binding, visibility handling and startup error UI. |
| `reports/simulation/scene.js` | WebGL renderer, sunlight, shadow camera, fog, resizing, chase/cockpit/TV/orbit cameras. |
| `reports/simulation/car.js` | Original procedural body, open wheels, wings, cockpit, force arrows and optional airflow. |
| `reports/simulation/circuit-definitions.mjs` | Three original closed-spline control-point layouts and circuit character labels. |
| `reports/simulation/circuits.js` | Spline generation, tarmac/runoff ribbons, kerbs, start line, instanced trees/barriers, pit building and GPU disposal. |
| `reports/simulation/telemetry.mjs` | Pure trace validation and time-to-state sampling, independent of DOM/WebGL. |
| `reports/simulation/replay.js` | Shared clock, run comparison, vehicle placement, rendering loop and resource lifecycle. |
| `reports/simulation/ui.js` | Controls, lap comparison, live telemetry, setup binding and circuit minimap. |
| `reports/simulation/simulation.css` | Scoped dark motorsport styling and responsive controls/HUD. |
| `reports/vendor/three/` | Pinned Three.js 0.180.0 core/module, OrbitControls, MIT license and source/archive checksum. |
| `tests/simulation.test.mjs` | Actual-trace timing, boundaries, sectors, setup values, lead, layout closure/intersections and analytics integration checks. |
| `tests/simulation-geometry.test.mjs` | Procedural mesh indices/finite vertices and car update checks. |
| `tests/three-loader.mjs` | Node import-map equivalent used only for geometry tests. |

## Performance and validation

Pixel ratio is capped at 1.5, shadows use a 1024² map centered on the focused car, repeated scenery uses instancing, kerbs use combined geometry, and the HUD refreshes at roughly 12 Hz. There is no bloom/postprocessing pipeline. Hidden simulation layers stop rendering. Circuit replacement disposes the old geometry/materials. These are performance choices, not a measured laptop frame-rate guarantee.

Run checks with Node.js 22 or newer:

```powershell
node --test tests/simulation.test.mjs
node --experimental-loader ./tests/three-loader.mjs --test tests/simulation-geometry.test.mjs
```

The loader warning is expected for Node's experimental-loader API. Validation checks cover all six saved traces, exact requested rounded values, lap wrap and geometric integrity. They do not constitute a WebGL screenshot, browser interaction, or frame-rate acceptance test. For manual acceptance: try all circuits and cameras, compare both cars through one full lap, pause/reset/switch focus, resize the page, return to Analysis and change a chart metric. Confirm Downforce Circuit's displayed values against the table above.

To regenerate only the dashboard after updating saved traces:

```powershell
python -c "import json; from pathlib import Path; from src.reporting import build_dashboard; build_dashboard(json.loads(Path('reports/recommendations.json').read_text()), {})"
```

The simulation modules remain separate and are not overwritten by regeneration.

## Attribution and scope

Three.js is MIT licensed; its license and download provenance are in `reports/vendor/three/`. Implementation references: [WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer.html), [CatmullRomCurve3](https://threejs.org/docs/pages/CatmullRomCurve3.html), [OrbitControls](https://threejs.org/docs/pages/OrbitControls.html). No external 3D model files or licensed vehicle designs are used.

**All vehicle, circuit, and performance data are synthetic. This visualization is a conceptual digital-vehicle model, not CFD or real telemetry.**
