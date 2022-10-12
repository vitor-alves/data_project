CREATE DATABASE IF NOT EXISTS app_db;

CREATE TABLE IF NOT EXISTS app_db.stg_trips (
    region varchar(200),
    origin_coord varchar(200),
    destination_coord varchar(200),
    datetime varchar(200),
    datasource varchar(200)
);

CREATE TABLE IF NOT EXISTS app_db.trips (
    trip_id bigint not null auto_increment,
    region varchar(50),
    origin_coord point,
    destination_coord point,
    datetime datetime,
    primary key(trip_id)
);
