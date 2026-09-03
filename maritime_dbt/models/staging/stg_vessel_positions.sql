SELECT
    mmsi,
    name,
    sog,
    cog,
    ROUND(lat, 4) AS lat,
    ROUND(lon, 4) AS lon,
    seen,
    CAST(seen AS DATE) AS observation_date
FROM {{ source('maritime', 'vessel_positions_raw') }}