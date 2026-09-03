CREATE TABLE vessel_positions_raw (
mmsi BIGINT,
name TEXT,
sog	NUMERIC,
cog	NUMERIC,
lat	NUMERIC,
lon	NUMERIC,
seen TIMESTAMPTZ);
