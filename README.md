# Maritime AIS Data Pipeline

## Overview

This project is a data engineering pipeline that collects AIS vessel position data from a public API.
The data is processed with Python, loaded into PostgreSQL, transformed using dbt, and orchestrated with Apache Airflow.
The pipeline is designed to handle repeated AIS observations safely and produces daily vessel-level analytical metrics.

## Architecture
```text
OpenWaters AIS API
        │
        ▼
Python Ingestion
(src/ingest_vessels.py)
        │
        ▼
PostgreSQL Raw Layer
(raw.vessel_positions_raw)
        │
        ▼
dbt Staging Layer
(staging.stg_vessel_positions)
        │
        ▼
dbt Mart Layer
(marts.vessel_daily_metrics)
        │
        ▼
dbt Data Quality Tests
```

## Tech Stack
- **Python** — API extraction, transformation, and database loading
- **PostgreSQL** — raw data storage
- **dbt** — data transformation, modeling, and testing
- **Apache Airflow** — pipeline orchestration
- **Docker / Docker Compose** — containerized development environment
- **Git** — version control

## Pipeline
The Airflow DAG executes three sequential tasks:

1. **Ingest vessels**
   - Extracts AIS vessel observations from the OpenWaters API.
   - Converts the API response into a pandas DataFrame.
   - Removes duplicate `(mmsi, seen)` observations within the current batch.
   - Loads the batch into a temporary PostgreSQL table.
   - Inserts new observations into the raw table using `ON CONFLICT DO NOTHING`.

2. **Run dbt**
   - Transforms raw AIS observations into staging models.
   - Builds daily vessel-level analytical metrics.

3. **Test dbt models**
   - Runs data quality tests after the transformations complete.

The `(mmsi, seen)` combination identifies a vessel observation. This allows the pipeline to be rerun safely without inserting the same AIS observation multiple times.

## Data Model
The pipeline uses three logical data layers:

### Raw

`raw.vessel_positions_raw`

Stores AIS observations received from the source API, including:

- MMSI
- vessel name
- speed over ground (SOG)
- course over ground (COG)
- latitude and longitude
- observation timestamp
- ingestion timestamp

### Staging

`staging.stg_vessel_positions`

Cleans and prepares raw vessel observations for analytics, including coordinate rounding and creation of an observation date.

### Mart

`marts.vessel_daily_metrics`

Aggregates observations to one row per vessel per day and provides:

- number of observations
- average speed
- maximum speed
- first observation timestamp
- last observation timestamp

## Data Quality
Data quality is enforced at both the PostgreSQL and dbt layers.

- PostgreSQL enforces uniqueness on `(mmsi, seen)` to prevent duplicate vessel observations.
- The ingestion process uses `ON CONFLICT DO NOTHING` to make repeated API loads idempotent.
- dbt tests verify that critical fields such as MMSI, observation timestamp, latitude, and longitude are not null.
- The daily metrics model is designed with a grain of one row per vessel per observation date.

## Running the Project
The project runs in a Docker-based local environment.

1. Configure the required database environment variables.
2. Start the Docker services with Docker Compose.
3. Open the Airflow UI.
4. Trigger the `maritime_pipeline` DAG.

The DAG executes:

`ingest_vessels → dbt_run → dbt_test'