USE motorsport_aero;
SELECT run_id,sample_index,COUNT(*) copies FROM fact_vehicle_state GROUP BY run_id,sample_index HAVING COUNT(*)>1;
SELECT run_id FROM fact_vehicle_state WHERE drs=1 AND (drs_zone=0 OR acceleration_mps2<-.05);
SELECT run_id FROM fact_vehicle_state WHERE ABS(front_downforce_n+rear_downforce_n-downforce_n)>1e-7;
SELECT l.run_id,l.lap_time_s,SUM(s.sector_time_s) sector_sum FROM fact_simulation_lap l JOIN fact_simulation_sector s USING(run_id) GROUP BY l.run_id,l.lap_time_s HAVING ABS(l.lap_time_s-SUM(s.sector_time_s))>1e-6;
SELECT * FROM vw_data_quality;
