{{ config(materialized='table') }}

SELECT
    mmsi,
    MAX(name) AS vessel_name,
	observation_date,
	COUNT(*) AS observations,
	ROUND(AVG(sog),2) AS avg_speed,
	MAX(sog) AS max_speed,
	MIN(seen) AS first_data,
	MAX(seen) AS last_data

FROM {{ ref("stg_vessel_positions") }}
GROUP BY mmsi, observation_date

