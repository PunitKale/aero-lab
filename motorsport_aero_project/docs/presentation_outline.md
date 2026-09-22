# Final presentation outline — 16 slides

1. **Title and research question:** Can circuit-specific aero choices be explained by a reproducible vehicle simulation?
2. **Motivation:** Drag, downforce, grip, balance and uncertainty interact. Use the force-speed figure.
3. **Scope and evidence:** Synthetic model; measured-car calibration unavailable. Distinguish implemented, assumed and future.
4. **Architecture:** Show architecture diagram and the four-tool data flow.
5. **Dataset:** Three circuit archetypes, setup/condition sweeps, explicit grains and source metadata.
6. **Aerodynamics:** SI equations, positive-downforce convention, map limits and ride-height heatmap.
7. **Digital car:** RWD traction, axle transfer, brake bias, tyres and powertrain.
8. **Lap solver:** Forward/backward envelope, periodic boundary and state continuity.
9. **DRS:** Zone/eligibility state machine; paired speed traces and time gain.
10. **Optimization:** Baseline, grid, random, DE and Powell with actual budgets. Explain rejected candidates.
11. **Results:** Use the current recommendation table; compare sectors rather than only a headline lap.
12. **Race and wet:** Stint state evolution and candidate-bank objective differences; state search scope.
13. **Robustness:** Paired uncertainty histogram, interval crossing zero and improvement frequency.
14. **Validation:** Unit/integration tests, 10-to-5 m convergence, actual MySQL and Excel reconciliation.
15. **Demonstration:** Open workbook, change scalar input, show query and local viewer. Power BI source project requires Desktop acceptance.
16. **Conclusion and next experiment:** Calibrate against independently measured aero/coast-down/braking/corner data.

Each quantitative slide must cite the source CSV or run IDs. Use report figures without removing the synthetic-data captions. Presenter notes should distinguish the current nominal result from the conditional uncertainty distribution. Rehearse the twelve-minute script in user_manual.md.
