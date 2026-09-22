# Methodology, assumptions and limits

**Real circuit geometry; model-generated vehicle performance. Not CFD or official telemetry.**

## Source and legal reuse

The implementation uses [OpenStreetMap relation 51160](https://www.openstreetmap.org/relation/51160), Silverstone Grand Prix. The raw response is included in `data/raw/silverstone/osm_relation_51160.json`; `provenance.json` records source/version, checksum, ordered way IDs, duplicate removal and source warnings. © OpenStreetMap contributors, [ODbL 1.0](https://www.openstreetmap.org/copyright). OSM-derived geographic records, centreline CSVs and database extracts are provided with ODbL attribution and share-alike terms; retain attribution and make the derivative data available when redistributing them. No Google map imagery, paid circuit asset, proprietary telemetry, team logo or licensed vehicle model is used.

The mapped route is geographically based, not survey-certified. Six included ways carry OSM's `note=Estimate`; this limitation is retained rather than hidden. The relation currently repeats members and includes a pit-lane member. The pipeline deduplicates by way ID, excludes the pit lane, follows directed endpoint connectivity and requires closure. Shorter layouts are not substituted. The lap origin is the first node of the configured Hamilton Straight way, not a claim to reproduce an official timing line.

Practical alternative sources considered: TUMFTM's racetrack database provides smoothed metre coordinates with its own licence and OSM attribution, but would not demonstrate the requested raw lon/lat transformation as directly. A documented future public telemetry adapter should keep its licence, source and observation flags separate from these generated records. No public telemetry has been imported in this release.

## Geometry

Longitude/latitude use WGS84. With semimajor axis `a=6378137 m` and eccentricity squared `e²=0.00669437999014`, compute `N=a/sqrt(1-e² sin²(lat))` and Earth-centred Earth-fixed coordinates at assumed altitude zero:

```text
X = N cos(lat) cos(lon)
Y = N cos(lat) sin(lon)
Z = N (1-e²) sin(lat)
```

Subtract the first point's ECEF coordinate. Project the difference onto local east `[-sin(lon0), cos(lon0), 0]` and north `[-sin(lat0)cos(lon0), -sin(lat0)sin(lon0), cos(lat0)]`. Output x=east and y=north in metres. This local tangent-plane treatment omits elevation and banking.

Remove consecutive points separated by less than 0.05 m; reject a nonclosed route. Fit a periodic cubic interpolant to raw chord distance, sample at approximately 1 m, apply a wrap-around Gaussian filter with 4 m sigma, and recompute arc length. Fit the smoothed curve and export every 5 m. The final cell is shorter to close the lap exactly; no rescaling to a published lap length is applied.

```text
distance = cumulative sqrt(dx² + dy²)
heading = atan2(dy/ds, dx/ds)
curvature = (x' y'' - y' x'') / (x'² + y'²)^(3/2)
```

Absolute curvature below 1/700 m⁻¹ is classified straight; between 1/700 and 1/160 is a fast corner; larger values are corners. These are heuristic classes, not named or official corners. Analytical sectors split the processed lap into approximately equal-distance thirds, snapped to sample boundaries. Sector flags therefore indicate synthetic definitions even though the underlying map is real.

The delivered initial geometry has raw chord length 5891.04 m and smoothed length 5887.33 m; maximal smoothing displacement on the dense comparison grid is approximately 0.52 m. These are computed source-processing quantities, not official certification. The exact values and source checksum are in validation JSON.

## Vehicle assumptions

All values below are assumptions in `config/realtrack.json`: 820 kg constant mass, 480 kW wheel power, tyre friction coefficient 1.55, air density 1.225 kg/m³, reference area 1.5 m², rolling coefficient 0.015, braking cap 28 m/s², lateral acceleration cap 39.24 m/s², speed cap 95 m/s. No claim is made that these represent a particular racing car or regulations.

Front/rear wing angles `f,r` are degrees. The aero map is an explicitly invented rule:

```text
floor = clip(1 - 3 abs(h_front - 0.04) - 2 abs(h_rear - 0.06), 0.7, 1)
CL_down = (1.5 + 0.045 f + 0.06 r) floor
CD = 0.55 + 0.0007 f² + 0.001 r²
qA = 0.5 rho A
downforce = qA CL_down v²       # positive downward
drag = qA CD v²
rolling = Crr m g
```

The baseline uses 16°/20° and 0.040/0.060 m ride heights. Nine alternatives use front angles {10,14,18} and rear angles {12,18,24}, with the same ride heights and vehicle conditions. Candidate means the minimum lap time in those nine alternatives; the pipeline never forces a prescribed lap delta or assumes an alternative beats the baseline. This is discrete grid search, not a global optimizer.

## Speed envelope and consistency

At steady speed, lateral tyre force is `m v² |curvature|`. Longitudinal force must also balance drag and rolling resistance. The corner cap solves this combined constraint by bisection:

```text
hypot(m v² k_bound, drag(v) + rolling) <= mu (m g + downforce(v))
```

`k_bound` includes adjacent samples, conservatively bounding cell endpoints. Also enforce the lateral acceleration and terminal power limits. The terminal speed solves `(drag+rolling)*v <= power`; this prevents a constant-speed segment from exceeding available power.

For each spatial cell, remaining longitudinal tyre force comes from a friction circle. Lateral demand uses the greater endpoint speed and greater endpoint curvature; available normal load uses the lower endpoint speed. This conservative choice shares grip between cornering and braking/acceleration rather than granting maximum longitudinal force while already at full cornering grip.

```text
remaining_Fx = sqrt(max(0, [mu(mg + downforce(v_low))]² - [m v_high² k_cell]²))
a_drive <= (min(remaining_Fx, power/v_high) - drag(v_high) - rolling) / m
a_brake <= min(braking_cap, [remaining_Fx + drag(v_low) + rolling] / m)
v_next² <= v_entry² + 2 a_drive ds
v_entry² <= v_next² + 2 a_brake ds
```

Forward/backward passes only reduce speeds, with periodic lap closure. Bisection solves reachable endpoints in each constrained interval. Export requires convergence. Neutral/coasting cells remain subject to the steady-state cap. Tests independently check combined tyre force, power, braking, lateral acceleration and kinematics on every delivered run.

Constant acceleration within a spatial cell gives:

```text
dt = 2 ds / (v_entry + v_exit)
acceleration = (v_exit² - v_entry²)/(2 ds)
time_s = cumulative previous dt
```

Saved force is evaluated at the mean endpoint squared speed, a spatial-cell mean for this interpolation. Force summaries in SQL and Power BI weight these saved cell values by `dt`; they are approximations to continuous time means, improving with a finer mesh.

The wear proxy increments by `ds * 1e-6 * (1 + 0.2*v²*k/g + 0.08*max(-acceleration,0)/g)`. It is dimensionless, starts at zero, and is not calibrated. It does not feed back into grip during this qualifying lap. There is no fuel-burn, thermal, hybrid, gearshift, suspension, transient slip or aerodynamic flow solution in this new model.

## Shared outputs and replay

MySQL stores x/y once in `track_points`; `telemetry_points` references it. The analytical `fact_telemetry` view and corresponding CSV join coordinates with performance, setup and sector keys. The replay JSON is projected from the same DataFrames. Dataset hashes identify the source/config/model combination. Live MySQL checks compare all exported positions/speeds/forces and every lap duration back to Python.

The Three.js `ProcessedCurve` uses piecewise interpolation of the **processed distance-indexed coordinates**, mapping east→+X and north→−Z. It does not fit a second decorative circuit. Animation integrates the saved speed cell and uses its exact distance fraction. Road width (12 m), kerbs, pit building, trees and barriers remain illustrative; they do not represent surveyed track boundaries or Silverstone facilities. Both cars share elapsed time; optional lateral offsets only prevent overlap. Each repeated lap loops the same tyre state.

## Results, uncertainty and honest conclusions

Use the current `simulation_runs.csv` and `mesh_sensitivity.json`, not earlier provisional values, for the final presentation. Negative candidate delta means faster **within this model**. Small gains are sensitive to grid spacing, smoothing and assumed aero/tyre coefficients. A finer-mesh comparison is numerical sensitivity, not calibration, measured validation, or a confidence interval. Do not tune the coefficients to make the candidate appear to win.

No measured vehicle telemetry, CFD, wind-tunnel measurement or validated vehicle dynamics is present. OpenStreetMap geometry improves geographical fidelity but does not confer physical accuracy on model-generated speed or lap time. Baseline/candidate results should support discussion of the pipeline, trade-offs and uncertainty, not real-world setup recommendations.

## Future improvements

1. Surveyed or better documented centreline, elevation, banking, widths and official timing-line coordinates with reusable licences.
2. Convergence across multiple distance meshes and smoothing scales, plus uncertainty sweeps over grip/aero/power.
3. Racing-line optimization inside documented boundaries, rather than driving the centreline.
4. Load-sensitive tyres, longitudinal/lateral slip, transient yaw, suspension and thermal/fuel state.
5. Independently sourced telemetry for calibration with whole-session holdouts and reported residuals; retain source licences and real/generated flags.
6. Immutable database history by geometry/config version, migrations, CI, and a small read-only API if browser data grow beyond static exports.
7. Power BI Desktop acceptance, presentation screenshots and optional locally configured refresh automation.
