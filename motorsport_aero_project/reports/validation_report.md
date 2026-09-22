# Validation report

All results concern a synthetic research model. Generated on the release date stored in the dataset metadata.

## Automated checks

39 passed; 0 failed; 0 skipped. See [test-case matrix](test_case_matrix.csv) and [JUnit evidence](tests.xml). Tests cover units, equations, zero speed, drag scaling, load transfer, tyre limits, DRS closure, continuity, repeated results, stint state, infeasible inputs, map bounds and convergence.

The generated run audit contains 1064 invariant checks; 1064 passed. These are implementation checks, not independent measured validation.

## MySQL

MySQL 8.0.46 was executed locally. 27/27 row-count and aggregate comparisons matched after two complete loads. The dedicated release snapshot is replaced in a transaction so changing sample resolution cannot leave stale rows. See [reconciliation](mysql_reconciliation.csv). Foreign keys remain enabled.

## Excel

5/5 checks passed after Microsoft Excel CalculateFullRebuild, followed by saving and reopening inspection. Independent checks cover dynamic pressure, downforce, drag, power and sector aggregation. See [reconciliation](excel_reconciliation.csv). This verifies scalar formulas and aggregates, not an independently implemented full Excel lap simulator.

## Numerical convergence

| step_m | setup | lap_time_s | top_speed_mps |
| --- | --- | --- | --- |
| 40 | baseline | 38.6125 | 84.1232 |
| 40 | recommended | 38.0820 | 88.8849 |
| 20 | baseline | 38.7850 | 84.2020 |
| 20 | recommended | 38.2660 | 89.0011 |
| 10 | baseline | 38.8693 | 84.1749 |
| 10 | recommended | 38.3484 | 89.0156 |
| 5 | baseline | 38.9053 | 84.2313 |
| 5 | recommended | 38.3856 | 89.0163 |

Production outputs use 10 m cells. Search and uncertainty use 25 m for screening, with finalist nominal re-evaluation at 10 m. On the displayed baseline/finalist, 10-to-5 m changes are below the 0.2% lap-time target. This is evidence for this scenario, not a universal solver-error bound. Spatial cells quantize DRS boundaries and braking-zone length; interpretation must respect that resolution.

## Power BI

186 project/report JSON files checked against Microsoft schemas, with 0 reported schema errors. The authored project has 18 pages and a TMDL semantic model. Power BI Desktop is unavailable here: TMDL loading, DAX execution, rendering, slicer interaction, bookmarks, tooltips, drill-through and service publication have not been accepted in Desktop. Python source-total checks do not stand in for executed DAX.

## Uncertainty and external accuracy

200/200 paired scenarios were feasible. Mean candidate-minus-baseline delta was -0.3780 s; empirical 95% range [-0.6567, 0.0849] s. Feasible-improvement frequency was 90.0%; Monte Carlo standard error of the mean delta was 0.0169 s. These results depend on assumed ranges and are not calibrated to a measured car. The range crosses zero, so the nominal recommendation does not improve every scenario.

No independent measured telemetry was provided. `fact_lap`, `fact_sector` and `fact_telemetry` are intentionally empty. Real-world MAE/RMSE and interval calibration remain unavailable. Surrogate residual plots compare a held-out set of synthetic simulator evaluations only.
