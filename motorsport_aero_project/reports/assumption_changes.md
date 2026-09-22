# Assumption changes from the proposal

The proposal is preserved as a planning record. The executed model uses these explicit changes:

1. Integration uses a distance step (10 m nominal), rather than a 0.02 s primary timestep. A mesh study showed 20-to-10 m lap changes slightly above the proposed 0.2% tolerance; 10-to-5 m is below 0.1% on the tested Apex Ring baseline and finalist. Search and uncertainty screening use 25 m and finalists are re-evaluated at 10 m. The independent braking test remains time-domain at 0.005 s.
2. Maximum individual tyre load is set to 15,000 N. The initial 9,500 N draft rejected the generic baseline (11,276 N on Apex Ring). This is an assumed research screening limit, not a tyre manufacturer's approved load. Unvalidated load limits must not support a real-car safety claim.
3. Roll follows an assumed progressive compliance: 4*tanh(0.025*ay/4) degrees. Pitch/heave are quasi-static, not transient suspension simulation. Heave load-transfer correction uses 810 kg nominal mass; physical axle loads use actual mass.
4. Six ordered geometry segments per circuit partition the distance. Acceleration and braking zones emerge from the speed solution within those segments, rather than adding overlapping lengths.
5. Gear changes use optimal valid-gear selection and a declared 0.04 s lumped time loss. The model does not resolve shift torque interruption or clutch transients.
6. Yaw is regularized below 15 m/s for crosswinds; parked-car side force is outside scope. Coefficients are evaluated directly from the synthetic bounded response surface in simulation. A separately tested interpolator is supplied for gridded map experiments.
7. Corner speed uses 95% of the standalone lateral limit to reserve tyre capacity for overcoming drag. The combined-slip envelope is applied separately. This explicit driver/model assumption prevents claiming simultaneous full lateral and longitudinal capacity.

These changes are implementation decisions, not hidden calibrations against measured performance.
