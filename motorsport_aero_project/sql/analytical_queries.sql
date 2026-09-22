USE motorsport_aero;
-- Best/average lap within comparable circuit, tyre, weather and session conditions.
SELECT circuit_id,weather_id,tyre_id,session_id,MIN(lap_time_s) best_lap_s,AVG(lap_time_s) average_lap_s
FROM fact_simulation_lap JOIN run_registry USING(run_id) WHERE comparison_group='setup_sweep' GROUP BY circuit_id,weather_id,tyre_id,session_id;
SELECT sector_id,MIN(sector_time_s) best_sector_s FROM fact_simulation_sector GROUP BY sector_id;
-- Candidate minus matched baseline; negative is faster.
SELECT r.run_id,r.setup_id,l.lap_time_s-b.lap_time_s setup_delta_s FROM run_registry r JOIN fact_simulation_lap l USING(run_id)
JOIN run_registry br ON br.circuit_id=r.circuit_id AND br.weather_id=r.weather_id AND br.tyre_id=r.tyre_id AND br.session_id=r.session_id AND br.setup_id=1 AND br.comparison_group='setup_sweep'
JOIN fact_simulation_lap b ON b.run_id=br.run_id WHERE r.comparison_group='setup_sweep';
SELECT * FROM vw_aero_efficiency WHERE speed_mps=70;
SELECT * FROM vw_drs_comparison;
SELECT run_id,MAX(speed_mps) top_speed_mps,SUM(front_downforce_n*dt_s)/NULLIF(SUM(downforce_n*dt_s),0) front_balance FROM fact_vehicle_state GROUP BY run_id;
SELECT * FROM fact_optimization_result WHERE feasible=0;
SELECT * FROM vw_model_validation;
SELECT r.setup_id,r.circuit_id,r.weather_id,STDDEV_SAMP(l.lap_time_s) repeated_lap_sd_s,COUNT(*) n FROM fact_simulation_lap l JOIN run_registry r USING(run_id) WHERE r.comparison_group='repeatability' GROUP BY r.setup_id,r.circuit_id,r.weather_id;
SELECT * FROM (SELECT o.*,ROW_NUMBER() OVER(PARTITION BY optimization_run_id ORDER BY objective_value) ranking FROM fact_optimization_result o WHERE feasible=1) ranked WHERE ranking<=5;
