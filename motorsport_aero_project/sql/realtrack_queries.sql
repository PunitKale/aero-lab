USE aero_lab_real;
-- Paired lap delta, candidate minus baseline. Faster is negative.
SELECT c.name,b.lap_time_s AS baseline_s,a.lap_time_s AS candidate_s,a.lap_time_s-b.lap_time_s AS delta_s
FROM simulation_runs b JOIN simulation_runs a ON a.circuit_id=b.circuit_id AND a.dataset_id=b.dataset_id
JOIN circuits c ON c.circuit_id=a.circuit_id WHERE b.comparison_role='baseline' AND a.comparison_role='candidate';
-- Time-weighted force metrics; do not average spatial samples without weights.
SELECT run_id,SUM(step_m)/SUM(dt_s)*3.6 AS average_speed_kmh,MAX(speed_mps)*3.6 AS max_speed_kmh,
 SUM(downforce_n*dt_s)/SUM(dt_s) AS average_downforce_n,SUM(drag_n*dt_s)/SUM(dt_s) AS average_drag_n,
 MAX(tyre_wear_end)-MIN(tyre_wear) AS tyre_wear_change FROM fact_telemetry GROUP BY run_id;
-- Sector deltas at a matched grain.
SELECT s.name,a.sector_time_s-b.sector_time_s AS sector_delta_s FROM fact_sector a
JOIN fact_sector b ON a.sector_id=b.sector_id JOIN dim_sector s ON a.sector_id=s.sector_id
JOIN dim_run ra ON ra.run_id=a.run_id JOIN dim_run rb ON rb.run_id=b.run_id
WHERE ra.comparison_role='candidate' AND rb.comparison_role='baseline' AND ra.dataset_id=rb.dataset_id;
-- Inspect every evaluated setup, not only the winner.
SELECT r.run_id,s.front_wing_deg,s.rear_wing_deg,r.lap_time_s,r.tyre_wear_change,
 DENSE_RANK() OVER(PARTITION BY r.circuit_id,r.dataset_id ORDER BY r.lap_time_s) AS lap_rank
FROM simulation_runs r JOIN aero_setups s ON s.setup_id=r.setup_id;
-- Reconciliation: this query should return no rows.
SELECT r.run_id,r.lap_time_s,SUM(t.dt_s) AS telemetry_seconds FROM simulation_runs r
JOIN telemetry_points t ON t.run_id=r.run_id GROUP BY r.run_id,r.lap_time_s
HAVING ABS(r.lap_time_s-SUM(t.dt_s))>0.00000001;
