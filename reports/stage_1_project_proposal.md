# Stage 1 — Project proposal and implementation plan

Version 1.0 | 17 September 2026 | Status: proposed design

This document covers the twenty Stage 1 deliverables requested in the original brief and integrates sections 21–23 of the simulation supplement. Numerical values below are proposed project assumptions or acceptance targets, not experimental results. Implementation begins in Stage 2 after the requested stage review.

## 1. Refined project title

**Simulation-Based Motorsport Aerodynamic Setup Optimization: An Integrated Python, MySQL, Excel and Power BI Decision-Support Platform**

Subtitle: A simplified digital vehicle model for circuit-specific performance, uncertainty and engineering trade-off analysis.

The term “digital vehicle model” is deliberate: without continuous measured-car calibration, this project should not claim a validated digital twin or a professional racing simulator.

## 2. Abstract

Aerodynamic setup selection requires balancing cornering and braking benefits against straight-line drag, tyre loading and sensitivity to operating conditions. Maximizing downforce or aerodynamic efficiency alone does not establish the fastest or most consistent setup for a particular circuit. This project proposes an integrated decision-support platform that evaluates aerodynamic configurations through a simplified vehicle-performance simulation.

Python will generate traceable synthetic aerodynamic maps, model vehicle forces and tyre behaviour, simulate circuit segments and race stints, and perform constrained setup optimization. The digital car model will connect front and rear wing settings, ride heights and aerodynamic balance to acceleration, braking, cornering, fuel consumption and tyre-state evolution. A configurable drag-reduction state machine will restrict activation to permitted zones and operating conditions. MySQL will preserve normalized inputs, simulation lineage and optimization results; Excel will provide transparent engineering calculations and reconciliation; Power BI will support interactive comparison of setups, sectors, uncertainty and model quality.

The study will compare baseline configurations, grid and random search, differential evolution, local refinement and Pareto selection. Robustness will be assessed through paired uncertainty scenarios involving weather, aerodynamic coefficients and tyre grip. Verification will combine analytical cases, physical invariants, convergence tests and cross-tool reconciliation. Independent measured-data validation will remain conditional on suitable telemetry becoming available. Expected contributions are a reproducible simulation pipeline, interpretable setup recommendations and an explicit account of uncertainty and model validity. No claim of real-world lap-time accuracy will be made from synthetic-data agreement alone.

## 3. Background and motivation

Aerodynamic force depends on air density, reference area, coefficient and the square of air-relative speed. This makes aerodynamic changes particularly consequential at high speed, while power, traction and mechanical grip remain important across the lap. The force equations provide a foundation, but their coefficients require evidence or explicit assumptions; the equations alone cannot establish a credible aero map. See NASA's [lift equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation/) and [drag equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/).

The practical research problem is to connect these forces to vehicle performance and make the reasoning inspectable across engineering and analytics tools. A wing change can improve one sector and worsen another. Its value can also change with fuel, tyres, wind or the availability of drag reduction.

The initial study will use a generic rear-wheel-drive, high-downforce single-seater with a configurable legacy-style DRS research policy. This is not a claim of compliance with current Formula 1. FIA's [2026 regulations overview](https://www.fia.com/news/new-era-competition-fia-showcases-future-focused-formula-1-regulations-2026-and-beyond) describes active aerodynamics, so a historical-style DRS rule must not silently be treated as a current championship rule. Any championship-specific extension must select and version the applicable technical and sporting regulations.

The academic contribution is the integration and verification methodology, not a claim to have discovered a new aerodynamic law or a championship-winning configuration.

## 4. Problem statement

Develop a reproducible system that selects feasible aerodynamic setups for a specified circuit and objective using simulated vehicle performance, while explaining sector trade-offs and sensitivity to uncertain inputs. The system must retain data provenance, prevent invalid extrapolation and ensure that Python, MySQL, Excel and Power BI use consistent definitions.

The central challenge is that aerodynamic load, drag, tyre grip, balance and vehicle state are coupled. Independent force calculations or a dashboard of average values cannot establish a defensible lap-time optimum. A second challenge is evidential: synthetic consistency must be distinguished from agreement with an independently measured car.

## 5. Aim

Design, implement and verify a research-grade decision-support prototype that recommends circuit-specific aerodynamic setups through a constrained digital vehicle simulation and communicates the resulting performance, uncertainty and engineering trade-offs through four reconciled tools.

## 6. SMART objectives

These targets apply to the sixteen-week schedule; they are not current achievements.

| ID / deadline | Measurable success criterion | Inputs and implementation | Validation and evidence |
|---|---|---|---|
| O1 / W3 | Version one data contract covering all core entities, units and provenance; zero undocumented model inputs | Both briefs; YAML configuration and data dictionary | Schema review, assumption register and requirement mapping |
| O2 / W4 | Generate 3 synthetic circuit archetypes, 3 sectors each, 3 weather profiles, 3 compounds and at least 12 setups; deterministic values for a fixed seed | Configured geometry and physically linked aero/tyre functions | Hashes excluding volatile timestamps; range, uniqueness and relationship checks |
| O3 / W5 | Load all core dimensions and at least one complete run transactionally into MySQL; duplicate import creates no duplicate records | Generated files; migrations, keys and import manifest | Integration tests, orphan counts of zero and reconciliation query outputs |
| O4 / W6 | Pass all scalar force, axle-load, unit and limiting-case tests | Car inputs and aerodynamic coefficients | Independent hand calculations and automated tests |
| O5 / W8 | Complete continuous laps on all 3 circuits; sector sums agree within 1e-6 s; timestep halving changes lap time by less than 0.2% | Track, powertrain, tyres, weather; coupled simulation | Speed/force traces, continuity and convergence evidence |
| O6 / W9 | Produce paired DRS-on/off runs and a 10-lap stint; zero illegal activations and no negative fuel | Zone policy, fuel and tyre state | Event audit, monotonic fuel checks and stint report |
| O7 / W11 | Compare 5 single-objective search methods under declared budgets; output only feasible recommendations plus a Pareto set | Simulator, setup bounds and constraints | Search logs, baseline deltas and full-model re-evaluation |
| O8 / W12 | Evaluate finalists on at least 200 paired uncertainty draws and 5 optimization seeds | Declared distributions and common scenario seeds | Quantiles, probability of improvement and Monte Carlo convergence report |
| O9 / W13 | Deliver formula-based Excel engineering checks with every required sheet; reconciliation meets declared tolerances | Canonical inputs and frozen run exports | Actual spreadsheet recalculation evidence, formula audit and residual table |
| O10 / W14 | Deliver 18 named Power BI pages with valid relationships and matching source aggregates | Dimensions, facts and measure contract | Saved report, screenshots, filter tests and exported visual totals |
| O11 / W15 | Execute every mandatory test case, documenting passed, failed and unavailable external-validation cases | Automated suite and independent references if available | Validation report; no synthetic result labelled measured |
| O12 / W16 | Deliver reproducible installation, research report, presentation outline and a 10–15 minute demonstration | Released artifacts and environment lock | Clean-environment rehearsal, manifest and submission checklist |

## 7. Research questions

1. How do front and rear wing settings change sector performance, lap time and balance across contrasting circuit archetypes?
2. Under which conditions does the straight-line benefit of drag reduction outweigh its transient loss of rear aerodynamic load?
3. How do qualifying-optimal and race-stint-optimal setups differ as tyre state and fuel mass evolve?
4. How sensitive are setup rankings to wind, density, grip, ride-height uncertainty and aero-map error?
5. Can simulation-based search improve upon a declared baseline while satisfying balance, clearance, braking and load constraints?
6. Which input uncertainties dominate the probability that a candidate outperforms the baseline?
7. Can independently calculated engineering quantities and aggregate results reconcile across Python, MySQL, Excel and Power BI?
8. What conclusions remain unsupported until independent measured telemetry is available?

Hypotheses will be conditional. Higher downforce may benefit an aero-sensitive circuit; it is not assumed to reduce lap time universally. Search failure or no feasible improvement is a legitimate result.

## 8. Scope and maturity levels

| Level | Included capability | Completion evidence |
|---|---|---|
| Minimum viable research prototype | Synthetic data and provenance; scalar aerodynamics; longitudinal, braking and corner limits; continuous sector/lap solution; baseline/grid search; MySQL; basic Excel checks and BI pages | One reproducible end-to-end circuit comparison by W8 |
| Complete major-project implementation | Three circuits; configurable DRS; gears; load-sensitive tyres; fuel/tyre evolution; quasi-static pitch/roll and axle balance; all search methods and objectives; uncertainty; complete workbook/report; documentation | O1–O12 and requirements matrix satisfied by W16 |
| Advanced research extension | Calibrated measured aero/tyre maps; transient suspension; richer slip and thermal models; validated wake/traffic effects; safety car; CFD or hardware integration | Separate future-work proposal and validation dataset |

All implementation features are currently planned. Synthetic circuit archetypes will represent low-drag, balanced and high-downforce demands without borrowing real circuit names or implying surveyed geometry. Track width will constrain an assumed path, not automatically solve an optimal racing line. Elevation and banking are supported inputs; absent measurements default to documented synthetic values or zero.

Cooling, brake ducts, flap families, floor and diffuser configurations will be categorical scenarios with separate aero maps. Continuous optimization initially varies four quantities: front/rear wing angle and front/rear static ride height. Rake is derived, avoiding a redundant independent variable. DRS is a policy-controlled state, not a freely selectable optimizer variable at each sample.

## 9. Assumptions and model contract

Every value below must move to a versioned configuration file in Stage 2. They are illustrative generic-car assumptions, not sourced vehicle specifications.

| Parameter | Proposed default / domain | Rationale and limitation |
|---|---|---|
| Dry operating mass including driver | 800 kg | Fuel added separately; mass definition prevents double counting |
| Fuel | 10 kg qualifying; 60 kg initial race scenario | Illustrative; fuel consumption initially 0.0005 kg/m |
| Geometry | Wheelbase 3.6 m; track 1.6 m; CG height 0.30 m | Quasi-static transfer only; no claim of specific chassis geometry |
| Static front weight fraction | 0.45 | CG position derived from fraction and wheelbase |
| Reference frontal area | 1.50 m² | All aero coefficients use the same declared reference area |
| Powertrain | 450 kW crank-power cap; efficiency 0.92; tyre radius 0.33 m | Torque curve and six gear ratios specified and reviewed in Stage 2 |
| Environment | 101325 Pa absolute, 288.15 K; dry-air gas constant 287.05 J/(kg K) | Density from local pressure/temperature; do not apply altitude twice |
| Gravity / rolling resistance | 9.80665 m/s²; coefficient 0.015 | Rolling resistance depends on normal load in the chosen model |
| Front / rear wing angle | 10–25° / 10–30° | Assumed map domain, not regulatory limits |
| Static front / rear ride height | 0.025–0.055 m / 0.040–0.085 m | Dynamic minimum clearance initially 0.015 m |
| Nominal dry tyre friction | 1.60 at a defined reference tyre load | Load exponent, compound, temperature and wet factors documented separately |
| Initial reference aero point | Downforce coefficient 3.0; drag coefficient 0.9; front aero fraction 0.44 | Seed values for a synthetic response surface, not constants across setups |
| Illustrative DRS effect | 18% drag reduction and 25% rear-downforce reduction | Front coefficient initially unchanged; map-dependent in complete model |
| Integration / speed cap | Initial timestep 0.02 s; numerical/model cap 100 m/s | Confirm convergence; results at a cap receive a validity warning |
| Random seed | 42 | Separate deterministic streams for generation, search and uncertainty |

Provisional feasibility thresholds: front aero fraction 0.35–0.55, change from baseline at matched state at most 0.06, positive wheel loads, valid map coordinates, clearance at least 0.015 m, and 80-to-30 m/s braking distance no more than 105% of baseline under matched conditions. Drag, tyre-load and sensitivity limits must be quantified in Stage 2 before optimization; an unset safety constraint is not silently treated as passed.

### Equations and conventions to freeze

- SI storage: m, s, kg, N, W, Pa and K. Presentation may use km/h and degrees with explicit conversion; internal angles use radians.
- `cl_down` is positive for downward aerodynamic load; it is the negative of a conventional upward-positive lift coefficient.
- `q_pa = 0.5 * rho_kg_m3 * v_air_mps²`; `downforce_n = q_pa * reference_area_m2 * cl_down`; `drag_n = q_pa * reference_area_m2 * cd`.
- Aerodynamics uses air-relative velocity; wheel kinematics and distance use ground-relative velocity. Wind direction is resolved into longitudinal and lateral components; yaw must remain within map support.
- `front_aero_fraction = front_downforce_n / downforce_n`; undefined at zero total load. `aero_efficiency = downforce_n / drag_n`; undefined at zero drag. Return null plus a quality flag, not an invented zero ratio.
- Aero center of pressure measured behind the front axle is `wheelbase_m * rear_aero_fraction`, assuming only the represented vertical aerodynamic loads.
- At 50 m/s in still air, rho=1.225 kg/m³, area=1.5 m², cl_down=3 and cd=0.9: q=1531.25 Pa, downforce=6890.625 N, drag=2067.1875 N and drag power=103359.375 W. These are analytical examples only.
- In still air, drag power is `drag_n * speed_mps`; with wind, distinguish vehicle mechanical power from energy relative to the airflow.
- `m * dv/dt = engine_force_n - drag_longitudinal_n - rolling_force_n - brake_force_n - m*g*sin(grade)`.
- Engine force comes from wheel torque, gearing and efficiency, bounded by power at nonzero speed and rear driven-axle traction. Avoid division by zero at launch; total-car normal load cannot be used as rear-wheel-drive traction.
- Static front/rear loads sum to `m*g`. Longitudinal transfer magnitude is `m*abs(ax)*cg_height/wheelbase`, with front loading under braking and rear loading under acceleration. Aerodynamic axle loads are added separately; pitch requires a compliance model and is not identical to load transfer.
- Lateral load transfer requires a stated front/rear roll-stiffness split. Banking and load-sensitive tyre capacity enter the corner limit; the speed-dependent aero/tyre equation is solved implicitly, not by inserting an arbitrary speed once.
- A combined-slip friction envelope prevents simultaneous maximum longitudinal and lateral force. A braking/turn-in segment cannot receive both full standalone braking and full standalone cornering grip.
- Fuel and tyre states update at each segment or finer integration step. Segment exit state becomes the next segment's entry state. Flying laps use a periodic speed-boundary solution; standing-start laps are explicitly separate.
- `lap_delta_s = candidate_lap_s - baseline_lap_s` (negative is faster); `drs_time_gain_s = matched_no_drs_lap_s - drs_lap_s` (positive is beneficial).

Provisional uncertainty inputs: density multiplier 0.98–1.02, wind components −5 to +5 m/s, grip multiplier 0.95–1.05, aero multipliers 0.95–1.05 and ride-height offset ±0.002 m. These are sensitivity scenarios, not measured distributions. Correlated front/rear aero and shared weather must be sampled coherently. Invalid map states remain infeasible rather than being silently clipped. Driver and residual uncertainty are separately labelled assumed until measured residuals exist.

## 10. Limitations

The model uses quasi-steady coefficients and simplified tyre, suspension and driver behaviour. It will not resolve turbulent flow, full transient handling, porpoising, structural loads, aquaplaning, tyre carcass physics or detailed energy deployment. Stall behaviour can only reflect the supplied synthetic map. Stability indicators are screening metrics, not proof that a real car is safe to drive.

Synthetic reference data tests implementation and internal consistency. It does not independently validate the underlying physical model. No real-world MAE, accuracy percentage or uncertainty coverage will be claimed without an independent dataset. Optimization is confined to the model domain and may expose model weaknesses rather than real improvements.

A deployable MySQL database and an authored Power BI report require available runtimes. SQL scripts, CSV exports and DAX specifications alone do not count as a running database or completed dashboard. Availability is checked early and any unexecuted integration is recorded explicitly.

## 11. Proposed methodology

1. **Establish evidence and contracts.** Create an assumption register, source ledger, data dictionary, research questions and test plan. Separate measured, synthetic, simulated, estimated and analytical-reference records.
2. **Generate traceable inputs.** Define synthetic aero surfaces with coherent wing, height, rake and yaw responses; constrain interpolators to their support. Generate circuit geometry, weather and tyres independently of optimizer results. Keep pristine raw files with hashes.
3. **Build and verify physical components.** Develop scalar forces, powertrain, tyre capacity, brake-bias limits, corner solving and quasi-static axle/wheel loads. Reject invalid values before integration.
4. **Assemble the simulator.** Use backward braking feasibility and forward traction/acceleration passes to construct a continuous speed envelope, followed by stateful evaluation. Iterate state-dependent limits to convergence. Avoid independently restarting each segment or double-counting braking-zone distance.
5. **Add scenario logic.** State-based DRS requires a permitted zone, session/policy eligibility, availability and operating conditions; braking, zone exit or ineligibility closes it. Pair DRS comparisons under identical initial states. Define speed gain at matched distance and distance gain at matched time.
6. **Integrate optimization.** Evaluate every candidate with the vehicle simulator. Compare manual baseline, grid, random, differential evolution and bounded local refinement under recorded evaluation budgets. Search categorical aero packages separately. Retain non-dominated candidates for lap time, stint degradation and robustness; label this as Pareto filtering unless an evolutionary multi-objective solver is actually implemented.
7. **Quantify uncertainty.** Use common random scenarios for candidate/baseline pairs and independent scenarios to evaluate finalists. Report mean, median, SD, 2.5th/97.5th percentiles, observed extremes and probability of improvement. A simulation uncertainty interval is not automatically a confidence interval for a measured car.
8. **Reconcile and communicate.** Export frozen run IDs to MySQL, Excel and Power BI. Recalculate independent spreadsheet formula checks, query database totals and inspect filtered BI outputs. Publish limitations alongside recommendations.

Objective definitions: qualifying minimizes flying-lap time; race minimizes a declared 10-lap stint subject to tyre constraints; overtaking maximizes terminal speed on a selected straight with whole-lap and braking constraints; high-downforce mode minimizes designated high-speed-sector time with whole-lap/drag constraints; wet mode minimizes scenario mean lap time plus a configurable SD penalty, subject to balance and traction constraints. Robust default risk multiplier is 1.0, varied in sensitivity analysis. Stability is not reduced to a claim based on lap time alone.

Surrogate models are optional accelerators after the direct simulator works. Hold out entire setups or circuits to prevent telemetry-row leakage. Re-evaluate every proposed optimum with the direct simulator and retain surrogate errors as a separate validation category.

### Research and literature plan

| Source | Verification status on 17 September 2026 | Intended use |
|---|---|---|
| NASA Glenn lift and drag equation pages linked above | Web pages located and content checked | Force definitions, coefficient/reference-area conventions |
| FIA 2026 overview linked above | Web page located and content checked | Establish that current active aerodynamics must not be conflated with legacy DRS |
| [FIA technical regulations index](https://www.fia.com/regulation/fia-formula-1-technical-regulations) | Index located; applicable full rule clauses not audited | Select championship/year and archive precise version if compliance is studied |
| Joseph Katz, *Race Car Aerodynamics* | Reading candidate; edition, pages and claims to verify | Ground effect, wing interactions and aerodynamic balance |
| Milliken and Milliken, *Race Car Vehicle Dynamics* | Reading candidate; edition, pages and claims to verify | Load transfer, tyres and handling assumptions |
| Hans Pacejka, *Tire and Vehicle Dynamics* | Reading candidate; edition, pages and claims to verify | Limits of simplified tyre approximations |
| Peer-reviewed lap simulation and robust optimization papers | Search and screen in W1–W2; none claimed reviewed yet | Solver verification and uncertainty methodology |

The review will record research question, model fidelity, input provenance, independent validation, reproducibility and limitations for each accepted source. Use university-library/publisher copies where available. Do not create paper titles, DOIs or claimed numerical findings without checking the source. Compare spreadsheet-only calculations, telemetry-only analytics and physics simulation as approaches; do not invent competitor-system benchmark results.

## 12. System architecture

```text
Synthetic configs / optional measured files / circuit & rule versions
                              |
                  Immutable raw files + SHA-256 manifest
                              |
                 Ingestion -> validation -> quarantine
                              |
                  Clean SI data + versioned dictionaries
                              |
                 Aero interpolation + derived features
                              |
        CarModel <-> tyre/fuel/weather/DRS state <-> track solver
                              ^
                              |
              Constrained optimizer + uncertainty scenarios
                              |
                   Results + constraints + provenance
                              |
           MySQL canonical tables -> versioned analytical views
                              |
        CSV snapshots / Excel engineering checks / Power BI model
                              |
          Verified charts + recommendation + technical report
```

Every simulation run has a unique ID and links to car, setup, circuit, session, tyre, weather, rule version, model version, data version and configuration hash. An optimization run owns candidate evaluations; an evaluation may own multiple scenario simulations. File ingestion is idempotent by hash and source identity. Failed imports or infeasible evaluations remain auditable.

Operational input tables are normalized. Analytical views expose a star schema without forcing the transactional model to duplicate descriptive attributes. Facts are never joined directly at mismatched grains. Simulation and measured results remain separate; comparison requires an explicit matched-reference mapping.

Functional requirements include ingestion, quality checks, reproducible simulation, objective selection, constrained optimization, uncertainty, export and explanation. Non-functional requirements include reproducibility, explicit units, transactional integrity, testability, configuration-based assumptions and access-controlled credentials. Initial performance target: one nominal lap in at most 5 seconds and 500 candidate laps in at most 45 minutes on the recorded development machine; benchmark and revise transparently before large searches.

## 13. Technology justification

| Component | Role and justification | Boundary |
|---|---|---|
| Python + NumPy / pandas | Numerical modelling and tabular pipelines | Canonical simulation logic; no duplicate independent lap simulator inside BI |
| SciPy | Interpolation, roots and constrained search | Bound checks and solver convergence required |
| scikit-learn | Optional surrogate and held-out metrics | Deferred until direct-model verification |
| MySQL + SQLAlchemy | Relational integrity, transactional loading and analytical views | Pin and test actual server/driver versions in Stage 2 |
| Excel + openpyxl or XlsxWriter | Visible equations, engineering checks and scenario comparison | Writing formulas is not recalculating them; verify in an available spreadsheet engine |
| Power BI | Interactive star-schema analytics and recommendations | Desktop/service access assessed before claiming authored or published reports |
| matplotlib / seaborn; optional Plotly | Inspectable engineering plots and selected interaction | Every plot includes units, context and synthetic status |
| pytest | Unit, integration, regression and invariant tests | Independent expected values, not merely copied implementation outputs |
| YAML/JSON, dotenv and logging | Configuration, environment separation and audit trail | Never commit database passwords or proprietary raw data |
| Git and file hashes | Source and dataset lineage | Large generated telemetry excluded from routine source commits |

These are design selections, not an assertion that dependencies are installed. Pin compatible versions from the tested environment instead of claiming an untested “latest” stack.

## 14. Major-project work breakdown

| Work package | Core work | Required evidence |
|---|---|---|
| WP1 Research | Literature matrix, problem definition and measurable hypotheses | Verified source ledger and proposal |
| WP2 Architecture | Interfaces, data grains, unit contracts and acceptance tests | Architecture diagram and requirements matrix |
| WP3 Data | Synthetic generator, QA, provenance and examples | Data dictionary, manifest and quality report |
| WP4 Storage | Tables, keys, migrations, views and import pipeline | Schema diagram, load log and SQL tests |
| WP5 Physics | Aerodynamics, powertrain, tyres and axle loads | Analytical examples and component tests |
| WP6 Simulation | Continuous laps, braking, corners, gears and DRS | State traces, convergence and event audit |
| WP7 Optimization | Search benchmarks, objectives, constraints and uncertainty | Feasible candidates, Pareto chart and scenario results |
| WP8 Excel | Required sheets, formulas, protection and checks | Recalculated workbook and reconciliation table |
| WP9 BI | Semantic model, 18 pages and measure validation | Report artifact, screenshots and exported totals |
| WP10 Verification | Full test matrix and conditional measured validation | Test report and limitation register |
| WP11 Reporting | Chapters, results, management and future work | Technical report and result provenance |
| WP12 Delivery | Install, user guide, demonstration and presentation | Release manifest and clean-run evidence |

The final report will retain the requested 32 chapters. Each chapter will include purpose, concepts, diagrams/tables, implementation links, expected or observed outputs and connection to the next chapter. Results chapters are written only after execution; literature, limitations and references distinguish reviewed evidence from planned investigation.

## 15. Database and Python implementation roadmap

### Stage 2: contracts and repository foundation

Create the requested `motorsport_aero_project/` structure, configuration files, `.env.example`, structured logging, schema validators, unit functions, generator skeleton and initial tests. Freeze column names and SI units. Define example records, permissible nulls, relationships, source flags and grains before creating dashboards.

Canonical metadata: `data_source_type`, `synthetic_flag`, `model_version`, `data_version`, `generation_timestamp` in UTC, `random_seed` and `validation_status`. “Validated” must carry a scope such as `schema_checked`, `analytical_verified` or `measured_compared`; it must not be an ambiguous blanket certification.

### Stage 3: data and MySQL

Core dimensions: `dim_car`, `dim_circuit`, `dim_sector`, `dim_corner`, `dim_session`, `dim_driver`, `dim_weather`, `dim_tyre`, `dim_setup`, `dim_date`. Add `dim_track_segment`, a run registry and a versioned rule-policy entity because segment ordering and lineage need explicit keys.

| Fact / group | Planned grain |
|---|---|
| `fact_aero_map` | One map version, setup/configuration and operating-coordinate combination |
| `fact_telemetry` | One source run and timestamp/sample index |
| `fact_lap`, `fact_sector` | One source run/lap; one such lap/sector |
| `fact_drs_event` | One activation interval per simulation or source run |
| `fact_tyre_state` | One run/sample/tyre or explicitly axle-aggregated state |
| `fact_optimization_run` | One search configuration and objective |
| `fact_optimization_result` | One candidate evaluation with scenario aggregation identified |
| `fact_model_validation` | One model/test/reference/metric result |
| `fact_vehicle_state` | One simulation run/lap/sample index |
| `fact_simulation_segment` | One simulation run/lap/track segment |
| `fact_simulation_sector` | One simulation run/lap/sector |
| `fact_simulation_lap` | One simulation run/lap |
| `fact_simulation_warning` | One warning occurrence with entity/time and severity |

Write executable schema/seed/view/quality/query scripts. Views cover best setup by circuit and objective, sectors, paired DRS, efficiency, Pareto status, matched weather scenarios, prediction/reference comparison and data quality. Rank only within compatible objective, condition and model versions; do not select “best” laps across unmatched weather or fuel states.

Index telemetry by `(run_id, sample_index)` and common time lookup patterns. Use batch inserts, avoid text repetition at sample grain, and provide downsampled BI views. Partitioning is considered only after query profiling and checking MySQL foreign-key restrictions; it is not a default promise. Backup guidance will cover consistent dumps, separately retained raw files and a tested restore.

### Stages 4–5: physical model and simulator

Modules: `config`, `logging_config`, `schemas`, `units`, `synthetic_data`, `ingestion`, `validation`, `physics`, `aero_map`, `telemetry`, `circuit_model`, `tyre_model`, `vehicle_model`, `lap_simulator`, `database`. Use type hints, public docstrings and explicit exceptions.

`CarModel` will expose `calculate_mass`, `calculate_aero_forces`, `calculate_engine_force`, `calculate_traction_limit`, `calculate_braking_force`, `calculate_corner_speed`, `update_tyre_state`, `update_fuel_state`, `simulate_segment`, `simulate_sector`, `simulate_lap` and `compare_setups`. Inputs include car, setup, tyres, weather, track, initial state and timestep. Outputs include state history, segment/sector/lap results, warnings, constraint violations and metadata.

Implement the supplement's ten levels in order: static model; longitudinal simulation; braking; cornering; combined vehicle; tyre/fuel; dynamic balance; DRS; unified interface; integrated validation. Quasi-static balance uses declared suspension compliance and roll distribution. Full transient pitch/roll physics remains an extension.

### Stage 6: search and reporting

Modules: `optimization`, `uncertainty`, `surrogate_models`, `explainability`, `export`, `visualization`, `reporting`. Every candidate invokes the simulator, checks feasibility and persists the reason for rejection where applicable. Store no-feasible-solution outcomes explicitly. Re-run finalists with finer integration and fresh uncertainty draws.

The recommendation record contains setup, objective, baseline/candidate lap and sector times, delta, top speed, high-speed corner speed, braking distance, DRS gain, tyre/fuel effects, uncertainty, constraint status and limitations. An explanation must identify which sectors produce the trade-off and when the ranking changes.

## 16. Excel and Power BI roadmap

### Excel engineering workbook

Retain the 22 requested sheets: README; Project Scope; Assumptions; Unit Reference; Car Inputs; Circuit Inputs; Sector Inputs; Corner Inputs; Tyre Inputs; Weather Inputs; Aero Map; Setup Scenarios; Aero Calculations; Lap-Time Model; Sector Comparison; DRS Analysis; Sensitivity Analysis; Optimization Results; Data Quality; Python Reconciliation; MySQL Reconciliation; Charts.

Add all nine simulation sheets: Vehicle Inputs; Simulation Settings; Segment Simulation; Speed Trace; Force Breakdown; Tyre State; Fuel State; Lap Summary; Setup Comparison. `Car Inputs` owns editable parameters; `Vehicle Inputs` links to those cells rather than creating a conflicting second source.

Use structured tables, named ranges, SI labels, blue editable inputs, protected formulas, validation lists and conditional warnings. Include independent scalar equations, constant-acceleration straight/braking examples, a documented corner solution, segment/sector sums and paired setup deltas. Imported integrated speed traces remain labelled simulation outputs; they are not evidence that Excel independently reproduced the full simulator.

Example named-range formula: `=0.5*AirDensity*AirSpeed^2*ReferenceArea*ClDown`. Reconciliation compares values after actual formula recalculation, with a separate check that formulas exist. Cached Python values do not count as independent spreadsheet validation.

### Power BI semantic model and report

Display names may use `DimCircuit` and `FactLap`, but a mapping file must identify their canonical SQL sources. Keep measured/source lap facts and simulation lap facts visibly distinct. Use one-to-many single-direction dimension filters. Avoid fact-to-fact relationships, ambiguous sector/circuit paths and bidirectional filters that multiply results. Weather and tyre state variation may require sample-grain foreign keys rather than one misleading constant per run.

Ten analytical pages: Project Overview; Setup Recommendation; Aero Performance; Sector and Lap Analysis; DRS Analysis; Setup Optimization; Pareto Analysis; Sensitivity and Uncertainty; Model Validation; Data Quality.

Eight simulation pages: Digital Car Overview; Speed and Acceleration; Force Breakdown; Cornering Performance; Tyre and Fuel Evolution; DRS Simulation; Setup Simulation Comparison; Simulation Validation.

Measure groups cover every requested KPI: lap/sector best and averages, deltas, downforce/drag and balance, paired DRS gains, top/corner speed, rank/Pareto status, robustness, constraints, model errors, validation counts and synthetic share. Simulation measures additionally cover braking distance, fuel/tyre effects and maximum forces. Prefer ratios of appropriate aggregated forces over an unweighted average of sample ratios; distinguish time-weighted and distance-weighted averages.

Use source-computed Pareto membership within a declared comparison set. DAX handles filter-context reporting, not vehicle integration. Comparison measures require matched run IDs; subtracting unrelated minima is not a DRS benefit. Sensitivity and uncertainty visuals consume stored scenario summaries.

Start with import mode and refreshable snapshot exports; test a configured MySQL connector when available. Evaluate DirectQuery only if profiling justifies it and the chosen connector supports the intended environment. Specify refresh ownership, credentials, gateway needs where applicable and stable versioned views. Row-level security is optional for a single-user synthetic project and required if later data ownership demands it.

All visualizations require units, setup/session context, sample size, source type and an explanation. Track plots use real supplied coordinates or explicitly synthetic geometry. Publication, custom visuals and service deployment are separate verified deliverables, not implied by a DAX file.

## 17. Risk register

The machine-readable [risk register](../planning/risk_register.csv) records likelihood, impact, mitigation, owner and trigger.

Highest-priority risks are unsupported real-world accuracy claims, optimistic synthetic maps, inconsistent units, discontinuous lap integration, optimizer exploitation of model weaknesses, absence of MySQL/Power BI access, and schedule expansion. Each has an explicit acceptance gate. The complete project requires a sustained part-time workload; a reduced workload requires a declared scope revision rather than relabelling a partial dashboard as complete.

Privacy and ethics: only use authorized measured data, preserve licensing/source metadata, and avoid publishing proprietary telemetry. Synthetic circuit and car names must remain clearly identifiable as invented.

## 18. Final deliverables and staged release plan

| Stage | Deliverables | Exit gate |
|---|---|---|
| 1 — Proposal (current) | Refined title, abstract, proposal, architecture, objectives, assumptions, risks, roadmap and schedule | Review scope and authorize Stage 2 |
| 2 — Research/data contract | Literature plan, requirements, dictionary, configuration, repository foundation and traceability | Units, grains and assumption version frozen |
| 3 — Dataset/storage | Generator, versioned dataset, schema, seeds, views, queries and ingestion | Clean import and database checks |
| 4 — Engineering components | Physics, aero maps, car/tyre/track modules, component notebook and tests | Analytical checks pass |
| 5 — Digital vehicle | Lap/stint simulator, state histories, DRS and dynamic balance | Continuity, legality and convergence pass |
| 6 — Optimization | Search engine, uncertainty, sensitivity and recommendation reports | Feasible finalists independently re-evaluated |
| 7 — Excel/BI | Engineering workbook, generation code, data exports, DAX/model specifications and authored report | Recalculated workbook and observed report totals reconcile |
| 8 — Validation/submission | Validation report, results/discussion, technical report, user manual, installation guide, notebooks, README, presentation outline, demonstration and future work | Clean release rehearsal and explicit limitations |

This covers the original 26 final deliverables; the proposal and abstract are supplied here, while subsequent artifacts remain planned. Digital-car outputs include every requested state trace, force trace, tyre/fuel trace, corner/sector/lap table, constraint-warning table and uncertainty summary.

## 19. Evaluation criteria and quality gates

| Test family | Acceptance rule | Evidence boundary |
|---|---|---|
| Scalar physics | Relative tolerance 1e-9, with absolute tolerance 1e-8 for near-zero SI scalar examples | Verifies formula implementation only |
| Units and inputs | All documented invalid, missing and nonfinite cases rejected or quarantined | No silent unit guessing or unrecorded imputation |
| Aerodynamic invariants | Zero force at zero airspeed; speed doubling gives 4x force for fixed coefficients; axle aero sums agree | Hold setup and coefficients fixed |
| Interpolation | Reproduce grid nodes; bound-check every axis; outside-map request rejected and logged | No extrapolated recommendation |
| Vehicle limits | Traction respects driven-axle load; brake bias respects each axle; combined-slip envelope holds | Include low grip and off-camber cases |
| Directional checks | More mass reduces acceleration for a matched power-limited case; more drag reduces net acceleration; reduced grip lowers corner limit | Do not assert universal monotonicity across changing states |
| Lap consistency | Continuous boundary speeds/states; positive dt; segment/sector/lap sums within 1e-6 s | Includes periodic flying-lap solution |
| Numerical convergence | Halving timestep and spatial resolution changes lap time by <0.2% and top speed by <0.5% | Revisit tolerances if setup gains are smaller than numerical error |
| DRS | Zero activations outside policy; immediate brake/zone-exit closure within integration resolution | Matched on/off cases and unavailable-state equivalence |
| Fuel/tyres | Nonnegative fuel, correct distance-based burn, bounded grip/temperature and reproducible states | Degradation follows documented model, not random noise |
| Optimization | No infeasible recommended setup; budget and seeds logged; candidate re-evaluated; no improvement is reportable | No assumed global-optimum proof |
| Reproducibility | Same config/seed produces identical IDs/values or documented floating-point tolerance; timestamps excluded | Environment and algorithm versions retained |
| MySQL round trip | Row counts/keys exact; numeric values within 1e-8 relative or documented DECIMAL precision | Live server test required; mock tests do not substitute |
| Excel reconciliation | Scalars within 1e-6 relative or 0.01 N absolute; imported lap/sector aggregates within 0.001 s | Actual recalculation required |
| BI reconciliation | Counts exact; aggregate lap times within 0.001 s; force ratios within 1e-6 before display rounding | Verify exported visuals under at least 5 filter combinations |
| External accuracy | Report lap/sector MAE, RMSE, bias and residuals only on independent matched references | Real-world accuracy target set after suitable data is obtained |
| Uncertainty | >=200 finalist draws, paired baseline scenarios, convergence check and assumption disclosure | Quantiles reflect input assumptions, not proven calibration |

Proposed assessment weighting: engineering/model transparency 25%; data/database integrity 15%; optimization/uncertainty 20%; Excel/BI consistency 15%; verification 15%; documentation/reproducibility 10%. Data provenance, feasibility and no fabricated validation are mandatory gates regardless of score.

The test matrix must include all twelve simulator cases from the supplement, plus brake-bias/load-transfer, combined-slip, invalid data, missing data, database idempotence, independent spreadsheet formulas and BI filter-context tests. Tests use analytical limiting cases where possible. Model-versus-generator agreement is explicitly a synthetic regression test.

Versioning: semantic model versions; immutable dataset releases with SHA-256 manifests; run configuration hashes; migration versions; export timestamps and source run IDs. Use `main` for reviewed releases and short-lived `codex/<feature>` branches. Keep secrets in environment variables, raw proprietary inputs outside Git and generated artifacts in versioned release storage. Perform daily source/data backup, weekly database dump and a restore rehearsal before submission; synchronization alone is not a tested backup.

## 20. Sixteen-week implementation schedule

The [Gantt-ready schedule](../planning/implementation_schedule.csv) includes tasks, dependencies, effort, risks, acceptance criteria and report evidence. Weeks are relative to the approved project start.

| Phase | Weeks | Estimated hours | Main exit condition |
|---|---|---:|---|
| 1 Literature and definition | 1–2 | 24 | Sources and research questions reviewed |
| 2 Requirements and architecture | 2–3 | 24 | Model/data contracts frozen |
| 3 Synthetic dataset and dictionary | 3–4 | 32 | Generator deterministic and QA complete |
| 4 MySQL | 4–5 | 28 | Transactional import and reconciliation pass |
| 5 Python physics | 5–6 | 36 | Independent component tests pass |
| 6 Vehicle and lap simulation | 6–9 | 64 | Continuous lap/stint, DRS and convergence verified |
| 7 Optimization and uncertainty | 9–12 | 56 | Search comparison and robust finalists completed |
| 8 Excel | 12–13 | 24 | Recalculated workbook reconciles |
| 9 Power BI | 13–14 | 28 | All pages and filter tests complete |
| 10 Validation | 14–15 | 32 | Full evidence matrix and limitations issued |
| 11 Results and discussion | 15–16 | 24 | Claims tied to actual runs |
| 12 Documentation and demonstration | 16 | 20 | Clean-run rehearsal and release manifest |

Total estimated effort: 392 hours, approximately 24.5 hours per week. Overlapping tasks represent staged work by one student, not assumed parallel staffing. Phase 6 carries the largest engineering risk; reserve part of its allocation for integration and convergence repairs. If the available weekly effort is lower, extend the calendar or explicitly choose the minimum viable prototype scope.

Stage 1 produces plans and acceptance targets only. No lap-time improvement, optimum setup or validation score has yet been observed.
