# Simulation-Based Motorsport Aerodynamic Setup Optimization

Technical report — executed synthetic research prototype, model 1.0.0.

## 1. Abstract

**Purpose:** Present the complete research contribution.

A reproducible Python–MySQL–Excel–Power BI platform connects aerodynamic setup to a simplified digital car. The implemented solver combines a continuous spatial speed envelope, rear-axle traction, braking bias, corner limits, tyre degradation, fuel and restricted DRS. Synthetic circuit experiments compare search algorithms and quantify conditional uncertainty. Results are internally verified; independent measured validation and Power BI Desktop acceptance remain separate limitations.

**Implementation and evidence:** [recommendations.json](recommendations.json). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for introduction.

## 2. Introduction

**Purpose:** Define the engineering decision.

A setup is selected for a circuit and driving objective. Downforce alone is insufficient: the same change affects drag, axle load, braking and tyre use. The software records the conditions under which a recommendation is made and compares matched baseline/candidate runs.

**Implementation and evidence:** [README.md](../README.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for background and motivation.

## 3. Background and motivation

**Purpose:** Connect aerodynamics to circuit performance.

Dynamic pressure scales with air-relative speed squared. In still air, aerodynamic drag power scales approximately with speed cubed when coefficients are fixed. Ride-height and yaw dependence modify simple scaling. Force equations are necessary but do not identify a lap optimum without a vehicle and circuit model.

**Implementation and evidence:** [figure_notes.md](figures/figure_notes.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for problem statement.

## 4. Problem statement

**Purpose:** State what the system must solve.

Select feasible aerodynamic configurations by simulated performance while retaining provenance, consistent units and interpretable trade-offs. Avoid independent segment restarts, unlimited driven-wheel force and arbitrary DRS activation. The model must also be honest about the lack of independently measured calibration.

**Implementation and evidence:** [user_manual.md](../docs/user_manual.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for aim and objectives.

## 5. Aim and objectives

**Purpose:** Define measurable delivery goals.

The aim is a reproducible decision-support implementation, not professional simulator equivalence. Objectives cover a normalized dataset, live MySQL import, modular physics, continuous laps and stints, five search methods, Pareto and robust analysis, independent Excel checks, a BI source project and a transparent validation report. The proposal retains the original SMART targets; the final status matrix records partial acceptance explicitly.

**Implementation and evidence:** [delivery_status.csv](delivery_status.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for research questions.

## 6. Research questions

**Purpose:** Make hypotheses testable.

Investigate circuit dependence of wing/height choices, DRS benefit, qualifying versus stint objectives, sensitivity to grip/weather, robustness of rankings and cross-tool reconciliation. All hypotheses are conditional on the synthetic response surface. A failed search, infeasible optimum or uncertainty interval crossing zero is an informative result.

**Implementation and evidence:** [recommendations.json](recommendations.json). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for scope of the project.

## 7. Scope of the project

**Purpose:** Separate implemented model from extensions.

Implemented: synthetic three-circuit experiments, bounded aero response, load-sensitive tyres, quasi-static balance, gears with lumped shift cost, spatial laps, stints, search and uncertainty. Beyond scope: resolved CFD, transient suspension, full tyre slip/thermal physics, traffic wakes, safety-car strategy and current championship active-aero compliance.

**Implementation and evidence:** [assumption_changes.md](assumption_changes.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for project limitations.

## 8. Project limitations

**Purpose:** Bound the conclusions.

All coefficient surfaces and tyre parameters are assumed. Corner speed has a 5% reserve below the standalone lateral limit. Shift time is lumped. Roll and pitch are quasi-static approximations, crosswind yaw is regularized at low speed, and braking distance is cell-quantized in lap summaries. No claim of safe real-car handling or real-world prediction accuracy follows from these runs.

**Implementation and evidence:** [validation_report.md](validation_report.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for literature-review plan.

## 9. Literature-review plan

**Purpose:** Separate checked sources from reading candidates.

NASA Glenn lift/drag pages establish force and coefficient conventions. FIA official 2026 overview distinguishes current active aerodynamics from the generic historical-style research DRS policy. Katz, Milliken and Pacejka books are reading candidates whose editions and page-specific claims must be checked before citing detailed conclusions. The project does not invent reviewed papers or experimental benchmarks.

**Implementation and evidence:** [references.md](references.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for existing-system analysis.

## 10. Existing-system analysis

**Purpose:** Explain the integration gap without invented comparisons.

Spreadsheet-only analysis exposes equations but does not automatically provide continuous stateful laps. Telemetry dashboards describe observed runs but cannot alone evaluate unseen setups. A physics model supports counterfactuals but is only as credible as its inputs. The proposed architecture integrates these roles; no commercial-product performance benchmark was conducted.

**Implementation and evidence:** [README.md](../README.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for proposed-system analysis.

## 11. Proposed-system analysis

**Purpose:** Show the implemented workflow.

Configuration and synthetic data feed validation, aero coefficients, car forces and the circuit solver. Search invokes the same simulator and stores feasibility. The release flows into MySQL, CSV snapshots, Excel and the Power BI model. Run IDs and manifests link charts and recommendations to their source records.

**Implementation and evidence:** [architecture.md](architecture.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for functional requirements.

## 12. Functional requirements

**Purpose:** Map requirements to executable features.

Generate inputs; validate units and ranges; simulate laps and stints; enforce map/DRS/physical constraints; compare setups and objectives; evaluate uncertainty; persist normalized facts; export engineering and BI artifacts; and provide an explanation for each recommendation. Measured-data ingestion requires an authorized reference dataset and mapping.

**Implementation and evidence:** [delivery_status.csv](delivery_status.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for non-functional requirements.

## 13. Non-functional requirements

**Purpose:** Define operational quality.

Fixed seeds, dependency locks, explicit versions and source hashes support repeatability. Transactions and foreign keys support database integrity. Configuration and typed objects isolate assumptions. Tests and source-linked results support auditability. The local MySQL service binds only to localhost and credentials are excluded from the release.

**Implementation and evidence:** [test_case_matrix.csv](test_case_matrix.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for system architecture.

## 14. System architecture

**Purpose:** Describe data and control flow.

The optimizer calls the digital car through the same CarModel interface used for direct experiments. Raw/configured inputs are distinct from simulated outputs. MySQL stores normalized entities; the Power BI CSV projection adds dimension keys to facts without joining facts to facts. A single-direction star avoids ambiguous filter paths.

**Implementation and evidence:** [architecture.md](architecture.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for methodology.

## 15. Methodology

**Purpose:** Explain the executed experimental design.

Twelve input setups are evaluated across three synthetic circuits and three weather profiles. Separate tyre, DRS, repeatability and stint experiments use matched conditions. Qualifying search runs on all circuits, with five seeds on Apex Ring. Other objectives use an explicitly limited candidate bank; robust selection screens three alternatives. Finalists receive fine-mesh nominal re-evaluation.

**Implementation and evidence:** [search_method_benchmark.csv](search_method_benchmark.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for dataset design.

## 16. Dataset design

**Purpose:** Describe grain and provenance.

Each dimension has an explicit key; each state is a run/sample pair; each sector result is a run/sector pair. The release contains synthetic inputs and simulated outputs, not measured facts. Generation timestamps, random seed, source type and versions are stored on source/run records; child facts inherit provenance through the run key. The column-level dictionary records units and examples.

**Implementation and evidence:** [data_dictionary.csv](data_dictionary.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for aerodynamic theory.

## 17. Aerodynamic theory

**Purpose:** State force definitions and sign convention.

q=0.5ρv_air² in Pa; F_down=q A Cl_down and F_drag=q A Cd in N. Cl_down is positive downforce and all coefficients share the 1.5 m² reference area. Front fraction is F_front/F_down; center of pressure measured behind the front axle is L times rear fraction. Undefined zero-load ratios remain unavailable. At ρ=1.225 kg/m³ and v=50 m/s, Cl=3 and Cd=0.9 give 6890.625 N downforce and 2067.1875 N drag.

**Implementation and evidence:** [physics.py](../src/physics.py). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for vehicle-dynamics model.

## 18. Vehicle-dynamics model

**Purpose:** Explain force capacity and balance.

Mass includes fuel. Engine force is the maximum valid-gear wheel torque capped by crank power times efficiency, then constrained by rear-axle tyre capacity. Longitudinal transfer m ax h/L shifts normal load rearward during acceleration. Per-wheel capacity is μ(Fz,wear,T)Fz. Braking is limited by front/rear capacity divided by brake-bias fractions. Lateral transfer and banking alter the wheel loads used in corner solving.

**Implementation and evidence:** [vehicle_model.py](../src/vehicle_model.py). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for lap-time simulation model.

## 19. Lap-time simulation model

**Purpose:** Explain continuity and numerical solution.

Track cells partition each segment. Corner limits constrain endpoint speeds; backward braking sweeps communicate downstream limits and forward sweeps enforce available drive acceleration. Periodic start/end speed creates a flying lap. Iteration couples the speed envelope with tyre/fuel and load state. Cell time is 2Δs/(v_in+v_out), plus declared shift loss. DRS closes on braking, zone exit or failed eligibility.

**Implementation and evidence:** [convergence.csv](convergence.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for optimization methodology.

## 20. Optimization methodology

**Purpose:** Define search methods and objective scope.

A baseline, 16-point grid, seeded random search, SciPy differential evolution and bounded Powell refinement share a cached evaluator. Actual unique evaluation counts are reported; budgets are not falsely described as equal. Pareto filtering minimizes lap time, wear and mean drag. Race sums ten laps, overtaking targets top speed, high-downforce targets high-speed corner performance and wet minimizes mean+SD under grip perturbations. Robust selection uses paired uncertain scenarios.

**Implementation and evidence:** [optimization.py](../src/optimization.py). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for mysql database design.

## 21. MySQL database design

**Purpose:** Explain relational integrity and analytical use.

The schema contains 26 managed tables, explicit primary/foreign keys, nonnegative checks and unique run/sample or run/sector indexes. Snapshot replacement runs in one transaction with foreign keys enabled. Analytical views expose matched comparisons. Scalar and force ratios use NULLIF for undefined division. Large telemetry workloads should use indexed run queries and downsampled analytical projections before considering partitioning.

**Implementation and evidence:** [schema.sql](../sql/schema.sql). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for python implementation.

## 22. Python implementation

**Purpose:** Describe modules and execution.

Modules separate configuration, schemas, units, generation, ingestion, physics, aero maps, tyres, vehicle, circuit, simulation, search, uncertainty, explanation, database, export and reporting. Public objects use dataclasses and explicit exceptions. The CLI is python -m src.pipeline. A separate reporting stage consumes frozen outputs instead of silently rerunning selected favourable experiments.

**Implementation and evidence:** [README.md](../README.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for excel implementation.

## 23. Excel implementation

**Purpose:** Describe independent calculation and snapshots.

The 31-sheet workbook includes editable blue inputs, named ranges, structured tables, locked formulas, validation, charts and reconciliation sheets. Force equations and simple straight/brake/corner limiting cases are live formulas. Integrated speed traces and optimization results are explicitly snapshots. Microsoft Excel recalculates the workbook; cached generator numbers alone are not counted as verification.

**Implementation and evidence:** [excel_reconciliation.csv](excel_reconciliation.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for power bi implementation.

## 24. Power BI implementation

**Purpose:** Describe the authored model and acceptance boundary.

The project contains PBIP, public-schema PBIR JSON, TMDL partitions, DAX and 18 pages. CSV import partitions use a portable DataFolder parameter. Facts have dimension keys and one-direction relationships. Measures include weighted force averages, paired DRS gains, lap/sector comparisons and feasibility counts. Power BI Desktop execution/rendering remains unverified; publication was not performed.

**Implementation and evidence:** [powerbi_schema_validation.json](powerbi_schema_validation.json). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for validation and testing.

## 25. Validation and testing

**Purpose:** Report evidence without overstating it.

The test suite records 39 passing cases. MySQL counts and lap sums reconcile after repeated loads. Excel independently recalculates five checks. Mesh refinement is measured rather than assumed. Surrogate residuals are held-out synthetic comparisons, and real-world error metrics are unavailable without independent telemetry.

**Implementation and evidence:** [validation_report.md](validation_report.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for results and discussion.

## 26. Results and discussion

**Purpose:** Interpret actual run results.

| Circuit | Baseline (s) | Candidate (s) | Delta (s) | DRS gain (s) |
| --- | --- | --- | --- | --- |
| Velocity Park | 49.5975 | 49.2322 | -0.3653 | 0.3893 |
| Apex Ring | 38.8693 | 38.3484 | -0.5209 | 0.2948 |
| Downforce Circuit | 27.6544 | 26.5174 | -1.1370 | 0.2565 |

On Apex Ring, the nominal candidate improves the baseline by 0.5209 s. Across 200 paired assumed scenarios, mean delta is -0.3780 s and the 95% empirical range is [-0.6567, 0.0849] s. Improvement frequency is 90.0%. The interval crosses zero: the candidate is not universally superior. Candidate settings favour less wing drag on this synthetic geometry; sector tables reveal the corner/straight trade-off.

**Implementation and evidence:** [recommendations.json](recommendations.json). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for risk analysis.

## 27. Risk analysis

**Purpose:** Record technical and delivery risks.

Primary risks are synthetic-model bias, optimizer exploitation of smooth assumed surfaces, incorrect units, map extrapolation, insufficient mesh resolution, missing measured validation and unavailable BI authoring runtime. The release mitigates these through explicit domains, numerical tests, assumptions, matched runs and honest integration status. Production-car safety and regulatory conformity are not inferred.

**Implementation and evidence:** [risk_register.csv](../../planning/risk_register.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for ethical and data-quality considerations.

## 28. Ethical and data-quality considerations

**Purpose:** Preserve source meaning and access boundaries.

Synthetic data is labelled throughout. Empty measured tables are not filled with invented telemetry. A failed evaluation is retained with an unavailable objective and reason. Credentials remain in ignored environment files. Future measured data requires authorization, license review, quality checks and a documented matching/calibration protocol before sharing.

**Implementation and evidence:** [data_quality.csv](data_quality.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for conclusion.

## 29. Conclusion

**Purpose:** State the supported contribution.

The delivered numerical/data prototype executes continuous laps, comparisons, constrained searches, uncertainty experiments, database loads and independent spreadsheet checks. It demonstrates the value of a reproducible engineering pipeline and exposes the uncertainty of its own recommendations. It does not establish measured-car predictive accuracy or a fully accepted Power BI deployment.

**Implementation and evidence:** [delivery_status.csv](delivery_status.csv). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for future work.

## 30. Future work

**Purpose:** Prioritize extensions by evidence value.

First obtain independent coast-down, braking, corner and aero-map observations with matching setup/environment metadata. Calibrate on one subset and test on held-out sessions. Next replace surrogate tyre and compliance assumptions, add transient pitch/roll and current championship policies, test more circuits and expand robust search. Complete Desktop acceptance before distributing the BI report.

**Implementation and evidence:** [future_work.md](../docs/future_work.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for references.

## 31. References

**Purpose:** Give traceable checked sources.

The bibliography lists official NASA and FIA pages checked during the project, Microsoft PBIP/PBIR/TMDL documentation, and clearly marked reading candidates. It does not invent papers or claim that listed textbooks were consulted page by page.

**Implementation and evidence:** [references.md](references.md). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for appendices.

## 32. Appendices

**Purpose:** Make the work reproducible.

Appendices comprise the schema, actual seed data, dictionary, source code, configuration, tests, traceability, dataset manifests, workbook generator, PBIR/TMDL files, execution logs, figure notes, demonstration script and dependency lock. File-level hashes identify the shareable release. Secrets and isolated database runtime files are excluded.

**Implementation and evidence:** [release_manifest.json](release_manifest.json). The linked artifact is the chapter’s inspectable code, table, diagram or output.

**Connection:** This establishes the basis for reproduction and independent validation.

