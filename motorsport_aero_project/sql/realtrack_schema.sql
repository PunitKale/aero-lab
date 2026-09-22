CREATE DATABASE IF NOT EXISTS aero_lab_real CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aero_lab_real;
CREATE TABLE IF NOT EXISTS circuits (
 circuit_id INT PRIMARY KEY, name VARCHAR(120) NOT NULL, slug VARCHAR(80) NOT NULL UNIQUE,
 length_m DOUBLE NOT NULL CHECK(length_m>0), origin_lon DOUBLE NOT NULL, origin_lat DOUBLE NOT NULL,
 projection VARCHAR(200) NOT NULL, source_url VARCHAR(255) NOT NULL, source_license VARCHAR(40) NOT NULL,
 snapshot_sha256 CHAR(64) NOT NULL, geometry_version VARCHAR(80) NOT NULL,
 data_source VARCHAR(200) NOT NULL, is_synthetic BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS sectors (
 sector_id INT PRIMARY KEY, circuit_id INT NOT NULL, sector_number SMALLINT NOT NULL,
 name VARCHAR(80) NOT NULL, start_distance_m DOUBLE NOT NULL, end_distance_m DOUBLE NOT NULL,
 is_synthetic BOOLEAN NOT NULL, data_source VARCHAR(200) NOT NULL,
 UNIQUE KEY uq_sector_number(circuit_id,sector_number), UNIQUE KEY uq_sector_circuit(sector_id,circuit_id),
 FOREIGN KEY(circuit_id) REFERENCES circuits(circuit_id), CHECK(end_distance_m>start_distance_m)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS track_points (
 track_point_id BIGINT PRIMARY KEY, circuit_id INT NOT NULL, point_index INT NOT NULL,
 distance_m DOUBLE NOT NULL, step_m DOUBLE NOT NULL, x_m DOUBLE NOT NULL, y_m DOUBLE NOT NULL,
 heading_rad DOUBLE NOT NULL, curvature_1pm DOUBLE NOT NULL, classification VARCHAR(24) NOT NULL,
 sector_id INT NOT NULL, is_synthetic BOOLEAN NOT NULL, is_derived BOOLEAN NOT NULL, data_source VARCHAR(200) NOT NULL,
 UNIQUE KEY uq_track_sample(circuit_id,point_index), UNIQUE KEY uq_point_circuit(track_point_id,circuit_id),
 KEY ix_track_distance(circuit_id,distance_m),
 FOREIGN KEY(circuit_id) REFERENCES circuits(circuit_id), FOREIGN KEY(sector_id,circuit_id) REFERENCES sectors(sector_id,circuit_id),
 CHECK(distance_m>=0), CHECK(step_m>0)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS aero_setups (
 setup_id INT PRIMARY KEY, name VARCHAR(100) NOT NULL, front_wing_deg DOUBLE NOT NULL, rear_wing_deg DOUBLE NOT NULL,
 front_height_m DOUBLE NOT NULL, rear_height_m DOUBLE NOT NULL, cl_down DOUBLE NOT NULL, cd DOUBLE NOT NULL,
 vehicle_parameters JSON NOT NULL, data_source VARCHAR(200) NOT NULL, is_synthetic BOOLEAN NOT NULL,
 CHECK(front_height_m>0), CHECK(rear_height_m>0), CHECK(cl_down>0), CHECK(cd>0)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS simulation_runs (
 run_id INT PRIMARY KEY, circuit_id INT NOT NULL, setup_id INT NOT NULL, comparison_role VARCHAR(24) NOT NULL,
 model_version VARCHAR(40) NOT NULL, dataset_id CHAR(64) NOT NULL, lap_time_s DOUBLE NOT NULL,
 max_speed_mps DOUBLE NOT NULL, tyre_wear_change DOUBLE NOT NULL, solver_iterations INT NOT NULL,
 data_source VARCHAR(200) NOT NULL, is_synthetic BOOLEAN NOT NULL,
 UNIQUE KEY uq_run_circuit(run_id,circuit_id), UNIQUE KEY uq_run_dataset(circuit_id,setup_id,dataset_id),
 KEY ix_run_comparison(circuit_id,comparison_role),
 FOREIGN KEY(circuit_id) REFERENCES circuits(circuit_id), FOREIGN KEY(setup_id) REFERENCES aero_setups(setup_id),
 CHECK(lap_time_s>0), CHECK(tyre_wear_change>=0)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS telemetry_points (
 run_id INT NOT NULL, track_point_id BIGINT NOT NULL, circuit_id INT NOT NULL, sample_index INT NOT NULL,
 time_s DOUBLE NOT NULL, dt_s DOUBLE NOT NULL, speed_mps DOUBLE NOT NULL, exit_speed_mps DOUBLE NOT NULL,
 acceleration_mps2 DOUBLE NOT NULL, downforce_n DOUBLE NOT NULL, front_downforce_n DOUBLE NOT NULL,
 rear_downforce_n DOUBLE NOT NULL, drag_n DOUBLE NOT NULL, tyre_wear DOUBLE NOT NULL, tyre_wear_end DOUBLE NOT NULL,
 is_synthetic BOOLEAN NOT NULL, data_source VARCHAR(200) NOT NULL,
 PRIMARY KEY(run_id,track_point_id), UNIQUE KEY uq_run_sample(run_id,sample_index), KEY ix_time(run_id,time_s),
 FOREIGN KEY(run_id,circuit_id) REFERENCES simulation_runs(run_id,circuit_id),
 FOREIGN KEY(track_point_id,circuit_id) REFERENCES track_points(track_point_id,circuit_id),
 CHECK(dt_s>0), CHECK(speed_mps>=0), CHECK(exit_speed_mps>=0), CHECK(downforce_n>=0), CHECK(drag_n>=0),
 CHECK(tyre_wear>=0 AND tyre_wear_end>=tyre_wear AND tyre_wear_end<=1)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW dim_circuit AS SELECT * FROM circuits;
CREATE OR REPLACE VIEW dim_setup AS SELECT * FROM aero_setups;
CREATE OR REPLACE VIEW dim_sector AS SELECT * FROM sectors;
CREATE OR REPLACE VIEW dim_run AS SELECT run_id,comparison_role,model_version,dataset_id FROM simulation_runs;
CREATE OR REPLACE VIEW fact_lap AS SELECT * FROM simulation_runs;
CREATE OR REPLACE VIEW fact_telemetry AS
 SELECT t.*,p.point_index,p.distance_m,p.step_m,p.x_m,p.y_m,p.heading_rad,p.curvature_1pm,p.classification,p.sector_id,p.is_derived,
 r.setup_id,3.6*t.speed_mps AS speed_kmh
 FROM telemetry_points t JOIN track_points p ON p.track_point_id=t.track_point_id JOIN simulation_runs r ON r.run_id=t.run_id;
CREATE OR REPLACE VIEW fact_sector AS
 SELECT r.run_id,r.circuit_id,r.setup_id,p.sector_id,SUM(t.dt_s) AS sector_time_s,
 SUM(p.step_m) AS sector_distance_m,SUM(p.step_m)/SUM(t.dt_s)*3.6 AS average_speed_kmh
 FROM telemetry_points t JOIN track_points p ON p.track_point_id=t.track_point_id JOIN simulation_runs r ON r.run_id=t.run_id
 GROUP BY r.run_id,r.circuit_id,r.setup_id,p.sector_id;
