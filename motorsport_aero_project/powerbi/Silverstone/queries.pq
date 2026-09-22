// Query name: dim_circuit
let
    Source = MySQL.Database(MySQLServer, MySQLDatabase, [ReturnSingleDatabase=true]),
    Rows = Source{[Schema=MySQLDatabase, Item="dim_circuit"]}[Data],
    Typed = Table.TransformColumnTypes(Rows, {{"circuit_id", Int64.Type}, {"name", type text}, {"slug", type text}, {"length_m", type number}, {"origin_lon", type number}, {"origin_lat", type number}, {"projection", type text}, {"source_url", type text}, {"source_license", type text}, {"snapshot_sha256", type text}, {"data_source", type text}, {"is_synthetic", type logical}, {"geometry_version", type text}}, "en-US")
in
    Typed

// Query name: dim_setup
let
    Source = MySQL.Database(MySQLServer, MySQLDatabase, [ReturnSingleDatabase=true]),
    Rows = Source{[Schema=MySQLDatabase, Item="dim_setup"]}[Data],
    Typed = Table.TransformColumnTypes(Rows, {{"setup_id", Int64.Type}, {"name", type text}, {"front_wing_deg", type number}, {"rear_wing_deg", type number}, {"front_height_m", type number}, {"rear_height_m", type number}, {"cl_down", type number}, {"cd", type number}, {"vehicle_parameters", type text}, {"data_source", type text}, {"is_synthetic", type logical}}, "en-US")
in
    Typed

// Query name: dim_sector
let
    Source = MySQL.Database(MySQLServer, MySQLDatabase, [ReturnSingleDatabase=true]),
    Rows = Source{[Schema=MySQLDatabase, Item="dim_sector"]}[Data],
    Typed = Table.TransformColumnTypes(Rows, {{"sector_id", Int64.Type}, {"circuit_id", Int64.Type}, {"sector_number", Int64.Type}, {"name", type text}, {"start_distance_m", type number}, {"end_distance_m", type number}, {"is_synthetic", type logical}, {"data_source", type text}}, "en-US")
in
    Typed

// Query name: dim_run
let
    Source = MySQL.Database(MySQLServer, MySQLDatabase, [ReturnSingleDatabase=true]),
    Rows = Source{[Schema=MySQLDatabase, Item="dim_run"]}[Data],
    Typed = Table.TransformColumnTypes(Rows, {{"run_id", Int64.Type}, {"comparison_role", type text}, {"model_version", type text}, {"dataset_id", type text}}, "en-US")
in
    Typed

// Query name: fact_lap
let
    Source = MySQL.Database(MySQLServer, MySQLDatabase, [ReturnSingleDatabase=true]),
    Rows = Source{[Schema=MySQLDatabase, Item="fact_lap"]}[Data],
    Typed = Table.TransformColumnTypes(Rows, {{"run_id", Int64.Type}, {"circuit_id", Int64.Type}, {"setup_id", Int64.Type}, {"comparison_role", type text}, {"model_version", type text}, {"dataset_id", type text}, {"lap_time_s", type number}, {"max_speed_mps", type number}, {"tyre_wear_change", type number}, {"solver_iterations", Int64.Type}, {"data_source", type text}, {"is_synthetic", type logical}}, "en-US")
in
    Typed

// Query name: fact_sector
let
    Source = MySQL.Database(MySQLServer, MySQLDatabase, [ReturnSingleDatabase=true]),
    Rows = Source{[Schema=MySQLDatabase, Item="fact_sector"]}[Data],
    Typed = Table.TransformColumnTypes(Rows, {{"run_id", Int64.Type}, {"circuit_id", Int64.Type}, {"setup_id", Int64.Type}, {"sector_id", Int64.Type}, {"sector_time_s", type number}, {"sector_distance_m", type number}, {"average_speed_kmh", type number}}, "en-US")
in
    Typed

// Query name: fact_telemetry
let
    Source = MySQL.Database(MySQLServer, MySQLDatabase, [ReturnSingleDatabase=true]),
    Rows = Source{[Schema=MySQLDatabase, Item="fact_telemetry"]}[Data],
    Typed = Table.TransformColumnTypes(Rows, {{"run_id", Int64.Type}, {"track_point_id", Int64.Type}, {"circuit_id", Int64.Type}, {"sample_index", Int64.Type}, {"time_s", type number}, {"dt_s", type number}, {"speed_mps", type number}, {"exit_speed_mps", type number}, {"acceleration_mps2", type number}, {"downforce_n", type number}, {"front_downforce_n", type number}, {"rear_downforce_n", type number}, {"drag_n", type number}, {"tyre_wear", type number}, {"tyre_wear_end", type number}, {"is_synthetic", type logical}, {"data_source", type text}, {"point_index", Int64.Type}, {"distance_m", type number}, {"step_m", type number}, {"x_m", type number}, {"y_m", type number}, {"heading_rad", type number}, {"curvature_1pm", type number}, {"classification", type text}, {"sector_id", Int64.Type}, {"is_derived", type logical}, {"setup_id", Int64.Type}, {"speed_kmh", type number}}, "en-US")
in
    Typed