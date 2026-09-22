USE motorsport_aero;
CREATE OR REPLACE VIEW vw_best_setup_per_circuit AS
SELECT x.* FROM (SELECT l.*,r.circuit_id,r.setup_id,r.weather_id,r.tyre_id,
ROW_NUMBER() OVER(PARTITION BY r.circuit_id,r.weather_id,r.tyre_id,r.session_id ORDER BY l.lap_time_s) AS position
FROM fact_simulation_lap l JOIN run_registry r USING(run_id) WHERE r.comparison_group='setup_sweep') x WHERE position=1;
CREATE OR REPLACE VIEW vw_best_setup_per_objective AS
SELECT x.* FROM (SELECT o.*, ROW_NUMBER() OVER(PARTITION BY optimization_run_id ORDER BY objective_value) AS position
FROM fact_optimization_result o WHERE feasible=1) x WHERE position=1;
CREATE OR REPLACE VIEW vw_sector_comparison AS
SELECT r.circuit_id,r.setup_id,r.weather_id,s.sector_id,s.sector_time_s,s.run_id FROM fact_simulation_sector s JOIN run_registry r USING(run_id);
CREATE OR REPLACE VIEW vw_drs_comparison AS
SELECT a.pair_id,a.circuit_id,a.setup_id,b.lap_time_s-a1.lap_time_s AS drs_time_gain_s,a1.top_speed_mps-b.top_speed_mps AS drs_top_speed_gain_mps
FROM run_registry a JOIN fact_simulation_lap a1 ON a.run_id=a1.run_id
JOIN run_registry r ON r.pair_id=a.pair_id AND r.drs_available=0
JOIN fact_simulation_lap b ON b.run_id=r.run_id WHERE a.drs_available=1 AND a.comparison_group='drs_pair';
CREATE OR REPLACE VIEW vw_aero_efficiency AS
SELECT aero_map_id,setup_id,speed_mps,drs,downforce_n,drag_n,downforce_n/NULLIF(drag_n,0) AS aero_efficiency,cl_front/NULLIF(cl_front+cl_rear,0) AS front_aero_fraction FROM fact_aero_map;
CREATE OR REPLACE VIEW vw_pareto_front AS SELECT * FROM fact_optimization_result WHERE feasible=1 AND pareto=1;
CREATE OR REPLACE VIEW vw_weather_adjusted_lap AS
SELECT r.circuit_id,r.weather_id,r.tyre_id,r.setup_id,AVG(l.lap_time_s) AS average_lap_s
FROM run_registry r JOIN fact_simulation_lap l USING(run_id) WHERE r.comparison_group='setup_sweep' GROUP BY r.circuit_id,r.weather_id,r.tyre_id,r.setup_id;
CREATE OR REPLACE VIEW vw_model_validation AS SELECT * FROM fact_model_validation;
CREATE OR REPLACE VIEW vw_data_quality AS
SELECT 'vehicle_state' AS entity,COUNT(*) AS row_count,SUM(fuel_kg<0 OR speed_mps<0 OR dt_s<=0) AS invalid_count FROM fact_vehicle_state;
