CREATE DATABASE IF NOT EXISTS motorsport_aero CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE motorsport_aero;

CREATE TABLE IF NOT EXISTS `dim_car` (
  `car_id` BIGINT NOT NULL,
  `car_name` VARCHAR(500),
  `dry_mass_kg` BIGINT,
  `wheelbase_m` DOUBLE,
  `track_m` DOUBLE,
  `cg_height_m` DOUBLE,
  `front_weight_fraction` DOUBLE,
  `area_m2` DOUBLE,
  `power_w` BIGINT,
  `efficiency` DOUBLE,
  `rolling_coefficient` DOUBLE,
  `brake_limit_n` BIGINT,
  `brake_bias` DOUBLE,
  `wheel_radius_m` DOUBLE,
  `final_drive` DOUBLE,
  `max_rpm` BIGINT,
  `torque_nm` BIGINT,
  `axle_heave_stiffness_n_m` BIGINT,
  `roll_front_fraction` DOUBLE,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`car_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_circuit` (
  `circuit_id` BIGINT NOT NULL,
  `circuit_name` VARCHAR(500),
  `length_m` BIGINT,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`circuit_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_date` (
  `date_id` BIGINT NOT NULL,
  `date_iso` VARCHAR(500),
  `year` BIGINT,
  `month` BIGINT,
  `day` BIGINT,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`date_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_driver` (
  `driver_id` BIGINT NOT NULL,
  `driver_name` VARCHAR(500),
  `consistency_sigma_s` BIGINT,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`driver_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_sector` (
  `sector_id` BIGINT NOT NULL,
  `circuit_id` BIGINT NOT NULL,
  `sector_name` VARCHAR(500),
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`sector_id`),
  CONSTRAINT `fk_dim_sector_circuit_id` FOREIGN KEY (`circuit_id`) REFERENCES `dim_circuit` (`circuit_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_session` (
  `session_id` BIGINT NOT NULL,
  `session_name` VARCHAR(500),
  `date_id` BIGINT NOT NULL,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`session_id`),
  CONSTRAINT `fk_dim_session_date_id` FOREIGN KEY (`date_id`) REFERENCES `dim_date` (`date_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_setup` (
  `setup_id` BIGINT NOT NULL,
  `setup_name` VARCHAR(500),
  `front_wing_deg` DOUBLE,
  `rear_wing_deg` DOUBLE,
  `front_height_m` DOUBLE,
  `rear_height_m` DOUBLE,
  `package` VARCHAR(500),
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`setup_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_track_segment` (
  `segment_id` BIGINT NOT NULL,
  `circuit_id` BIGINT NOT NULL,
  `sector_id` BIGINT NOT NULL,
  `segment_order` BIGINT,
  `kind` VARCHAR(500),
  `length_m` BIGINT,
  `radius_m` BIGINT,
  `banking_rad` DOUBLE,
  `grade_rad` BIGINT,
  `surface_grip` BIGINT,
  `width_m` BIGINT,
  `drs_zone` BIGINT,
  `drs_start_fraction` DOUBLE,
  `drs_end_fraction` DOUBLE,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`segment_id`),
  CONSTRAINT `fk_dim_track_segment_circuit_id` FOREIGN KEY (`circuit_id`) REFERENCES `dim_circuit` (`circuit_id`),
  CONSTRAINT `fk_dim_track_segment_sector_id` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_tyre` (
  `tyre_id` BIGINT NOT NULL,
  `name` VARCHAR(500),
  `mu` DOUBLE,
  `wear_per_m` DOUBLE,
  `optimal_temp_c` BIGINT,
  `load_exponent` DOUBLE,
  `reference_load_n` BIGINT,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`tyre_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_weather` (
  `weather_id` BIGINT NOT NULL,
  `name` VARCHAR(500),
  `pressure_pa` BIGINT,
  `temperature_k` DOUBLE,
  `grip` DOUBLE,
  `headwind_mps` BIGINT,
  `crosswind_mps` BIGINT,
  `aero_multiplier` BIGINT,
  `density_multiplier` BIGINT,
  `height_offset_m` BIGINT,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`weather_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_aero_map` (
  `aero_map_id` BIGINT NOT NULL,
  `setup_id` BIGINT NOT NULL,
  `speed_mps` BIGINT,
  `front_height_m` DOUBLE,
  `rear_height_m` DOUBLE,
  `yaw_deg` BIGINT,
  `drs` BIGINT,
  `cl_front` DOUBLE,
  `cl_rear` DOUBLE,
  `cd` DOUBLE,
  `downforce_n` DOUBLE,
  `drag_n` DOUBLE,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`aero_map_id`),
  CONSTRAINT `fk_fact_aero_map_setup_id` FOREIGN KEY (`setup_id`) REFERENCES `dim_setup` (`setup_id`),
  CHECK (`speed_mps` >= 0),
  CHECK (`downforce_n` >= 0),
  CHECK (`drag_n` >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_optimization_run` (
  `optimization_run_id` BIGINT NOT NULL,
  `circuit_id` BIGINT NOT NULL,
  `objective` VARCHAR(500),
  `seed` BIGINT,
  `evaluation_count` BIGINT,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`optimization_run_id`),
  CONSTRAINT `fk_fact_optimization_run_circuit_id` FOREIGN KEY (`circuit_id`) REFERENCES `dim_circuit` (`circuit_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `run_registry` (
  `run_id` BIGINT NOT NULL,
  `circuit_id` BIGINT NOT NULL,
  `setup_id` BIGINT NOT NULL,
  `weather_id` BIGINT NOT NULL,
  `tyre_id` BIGINT NOT NULL,
  `session_id` BIGINT NOT NULL,
  `car_id` BIGINT NOT NULL,
  `driver_id` BIGINT NOT NULL,
  `date_id` BIGINT NOT NULL,
  `comparison_group` VARCHAR(500),
  `drs_available` BIGINT,
  `pair_id` BIGINT NOT NULL,
  `lap_number` BIGINT,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`run_id`),
  CONSTRAINT `fk_run_registry_circuit_id` FOREIGN KEY (`circuit_id`) REFERENCES `dim_circuit` (`circuit_id`),
  CONSTRAINT `fk_run_registry_setup_id` FOREIGN KEY (`setup_id`) REFERENCES `dim_setup` (`setup_id`),
  CONSTRAINT `fk_run_registry_weather_id` FOREIGN KEY (`weather_id`) REFERENCES `dim_weather` (`weather_id`),
  CONSTRAINT `fk_run_registry_tyre_id` FOREIGN KEY (`tyre_id`) REFERENCES `dim_tyre` (`tyre_id`),
  CONSTRAINT `fk_run_registry_session_id` FOREIGN KEY (`session_id`) REFERENCES `dim_session` (`session_id`),
  CONSTRAINT `fk_run_registry_car_id` FOREIGN KEY (`car_id`) REFERENCES `dim_car` (`car_id`),
  CONSTRAINT `fk_run_registry_driver_id` FOREIGN KEY (`driver_id`) REFERENCES `dim_driver` (`driver_id`),
  CONSTRAINT `fk_run_registry_date_id` FOREIGN KEY (`date_id`) REFERENCES `dim_date` (`date_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `dim_corner` (
  `corner_id` BIGINT NOT NULL,
  `sector_id` BIGINT NOT NULL,
  `radius_m` BIGINT,
  `banking_rad` DOUBLE,
  `width_m` BIGINT,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`corner_id`),
  CONSTRAINT `fk_dim_corner_sector_id` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_drs_event` (
  `drs_event_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `start_time_s` DOUBLE,
  `end_time_s` DOUBLE,
  `start_distance_m` BIGINT,
  `end_distance_m` BIGINT,
  `entry_speed_mps` DOUBLE,
  `exit_speed_mps` DOUBLE,
  PRIMARY KEY (`drs_event_id`),
  CONSTRAINT `fk_fact_drs_event_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_lap` (
  `lap_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `lap_time_s` VARCHAR(500),
  PRIMARY KEY (`lap_id`),
  CONSTRAINT `fk_fact_lap_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`),
  CHECK (`lap_time_s` >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_model_validation` (
  `validation_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `test_name` VARCHAR(500),
  `passed` BOOLEAN,
  `validation_scope` VARCHAR(500),
  PRIMARY KEY (`validation_id`),
  CONSTRAINT `fk_fact_model_validation_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_optimization_result` (
  `optimization_result_id` BIGINT NOT NULL,
  `optimization_run_id` BIGINT NOT NULL,
  `front_wing_deg` DOUBLE,
  `rear_wing_deg` DOUBLE,
  `front_height_m` DOUBLE,
  `rear_height_m` DOUBLE,
  `package` VARCHAR(500),
  `method` VARCHAR(500),
  `objective` VARCHAR(500),
  `lap_time_s` DOUBLE,
  `top_speed_mps` DOUBLE,
  `fuel_used_kg` DOUBLE,
  `tyre_wear_end` DOUBLE,
  `tyre_wear_delta` DOUBLE,
  `distance_m` BIGINT,
  `high_speed_corner_mps` DOUBLE,
  `braking_distance_m` DOUBLE,
  `mean_downforce_n` DOUBLE,
  `mean_drag_n` DOUBLE,
  `max_tyre_load_n` DOUBLE,
  `solver_iterations` BIGINT,
  `shift_loss_s` DOUBLE,
  `feasible` BOOLEAN,
  `constraint_reasons` VARCHAR(500),
  `objective_value` DOUBLE,
  `pareto` BOOLEAN,
  PRIMARY KEY (`optimization_result_id`),
  CONSTRAINT `fk_fact_optimization_result_optimization_run_id` FOREIGN KEY (`optimization_run_id`) REFERENCES `fact_optimization_run` (`optimization_run_id`),
  CHECK (`lap_time_s` >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_sector` (
  `sector_fact_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `sector_id` BIGINT NOT NULL,
  `sector_time_s` VARCHAR(500),
  PRIMARY KEY (`sector_fact_id`),
  CONSTRAINT `fk_fact_sector_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`),
  CONSTRAINT `fk_fact_sector_sector_id` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`),
  CHECK (`sector_time_s` >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_simulation_lap` (
  `simulation_lap_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `lap_time_s` DOUBLE,
  `top_speed_mps` DOUBLE,
  `fuel_used_kg` DOUBLE,
  `tyre_wear_end` DOUBLE,
  `tyre_wear_delta` DOUBLE,
  `distance_m` BIGINT,
  `high_speed_corner_mps` DOUBLE,
  `braking_distance_m` BIGINT,
  `mean_downforce_n` DOUBLE,
  `mean_drag_n` DOUBLE,
  `max_tyre_load_n` DOUBLE,
  `solver_iterations` BIGINT,
  `shift_loss_s` DOUBLE,
  `data_source_type` VARCHAR(500),
  `synthetic_flag` BOOLEAN,
  `model_version` VARCHAR(500),
  `data_version` VARCHAR(500),
  `generation_timestamp` VARCHAR(500),
  `random_seed` BIGINT,
  `validation_status` VARCHAR(500),
  PRIMARY KEY (`simulation_lap_id`),
  CONSTRAINT `fk_fact_simulation_lap_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`),
  CHECK (`lap_time_s` >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_simulation_sector` (
  `simulation_sector_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `sector_id` BIGINT NOT NULL,
  `sector_time_s` DOUBLE,
  PRIMARY KEY (`simulation_sector_id`),
  CONSTRAINT `fk_fact_simulation_sector_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`),
  CONSTRAINT `fk_fact_simulation_sector_sector_id` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`),
  CHECK (`sector_time_s` >= 0),
  UNIQUE KEY `uq_run_sector` (`run_id`,`sector_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_simulation_segment` (
  `simulation_segment_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `segment_id` BIGINT NOT NULL,
  `sector_id` BIGINT NOT NULL,
  `segment_time_s` DOUBLE,
  `top_speed_mps` DOUBLE,
  `length_m` BIGINT,
  PRIMARY KEY (`simulation_segment_id`),
  CONSTRAINT `fk_fact_simulation_segment_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`),
  CONSTRAINT `fk_fact_simulation_segment_segment_id` FOREIGN KEY (`segment_id`) REFERENCES `dim_track_segment` (`segment_id`),
  CONSTRAINT `fk_fact_simulation_segment_sector_id` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`),
  CHECK (`segment_time_s` >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_simulation_warning` (
  `warning_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `warning_code` VARCHAR(500),
  `severity` VARCHAR(500),
  PRIMARY KEY (`warning_id`),
  CONSTRAINT `fk_fact_simulation_warning_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_telemetry` (
  `telemetry_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `sample_index` VARCHAR(500),
  `speed_mps` VARCHAR(500),
  PRIMARY KEY (`telemetry_id`),
  CONSTRAINT `fk_fact_telemetry_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`),
  CHECK (`speed_mps` >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_tyre_state` (
  `tyre_state_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `tyre_id` BIGINT NOT NULL,
  `sample_index` BIGINT,
  `distance_m` BIGINT,
  `tyre_wear` DOUBLE,
  `tyre_temperature_c` DOUBLE,
  `tyre_mu` DOUBLE,
  `fuel_kg` DOUBLE,
  PRIMARY KEY (`tyre_state_id`),
  CONSTRAINT `fk_fact_tyre_state_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`),
  CONSTRAINT `fk_fact_tyre_state_tyre_id` FOREIGN KEY (`tyre_id`) REFERENCES `dim_tyre` (`tyre_id`),
  CHECK (`fuel_kg` >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `fact_vehicle_state` (
  `vehicle_state_id` BIGINT NOT NULL,
  `run_id` BIGINT NOT NULL,
  `sample_index` BIGINT,
  `distance_m` BIGINT,
  `step_m` BIGINT,
  `time_s` DOUBLE,
  `dt_s` DOUBLE,
  `shift_loss_s` DOUBLE,
  `speed_mps` DOUBLE,
  `exit_speed_mps` DOUBLE,
  `acceleration_mps2` DOUBLE,
  `lateral_acceleration_mps2` DOUBLE,
  `gear` BIGINT,
  `drs` BIGINT,
  `drs_zone` BIGINT,
  `fuel_kg` DOUBLE,
  `mass_kg` DOUBLE,
  `tyre_wear` DOUBLE,
  `tyre_temperature_c` DOUBLE,
  `engine_force_n` DOUBLE,
  `available_engine_force_n` DOUBLE,
  `brake_force_n` DOUBLE,
  `rolling_force_n` DOUBLE,
  `front_tyre_load_n` DOUBLE,
  `rear_tyre_load_n` DOUBLE,
  `max_wheel_load_n` DOUBLE,
  `tyre_mu` DOUBLE,
  `segment_id` BIGINT NOT NULL,
  `sector_id` BIGINT NOT NULL,
  `radius_m` BIGINT,
  `front_downforce_n` DOUBLE,
  `rear_downforce_n` DOUBLE,
  `downforce_n` DOUBLE,
  `drag_n` DOUBLE,
  `drag_longitudinal_n` DOUBLE,
  `front_height_m` DOUBLE,
  `rear_height_m` DOUBLE,
  `yaw_deg` BIGINT,
  `roll_deg` DOUBLE,
  `cl_down` DOUBLE,
  `cd` DOUBLE,
  `front_aero_fraction` DOUBLE,
  PRIMARY KEY (`vehicle_state_id`),
  CONSTRAINT `fk_fact_vehicle_state_run_id` FOREIGN KEY (`run_id`) REFERENCES `run_registry` (`run_id`),
  CHECK (`speed_mps` >= 0),
  CHECK (`fuel_kg` >= 0),
  CONSTRAINT `fk_fact_vehicle_state_segment_id` FOREIGN KEY (`segment_id`) REFERENCES `dim_track_segment` (`segment_id`),
  CONSTRAINT `fk_fact_vehicle_state_sector_id` FOREIGN KEY (`sector_id`) REFERENCES `dim_sector` (`sector_id`),
  CHECK (`downforce_n` >= 0),
  CHECK (`drag_n` >= 0),
  UNIQUE KEY `uq_state_sample` (`run_id`,`sample_index`)
) ENGINE=InnoDB;