# Maritime AIS Data Pipeline

## Overview

This project is a data engineering pipeline that collects Dover Strait AIS vessel data from a public API.
The data is processed with Python, raw API responses are archived in Amazon S3,
structured observations are loaded into PostgreSQL on Amazon RDS, transformed
using dbt, and orchestrated with Apache Airflow.

## Architecture
```text
OpenWaters AIS API — Dover Strait
            │
            ▼
      Python Ingestion
            │
       ┌────┴────┐
       ▼         ▼
   AWS S3     AWS RDS
 Raw JSON    PostgreSQL
                 │
                 ▼
            dbt Staging
                 │
                 ▼
              dbt Mart
                 │
                 ▼
             dbt Tests

Orchestration: Apache Airflow / Docker
```

## Tech Stack
- **Python** — API extraction, transformation, and database loading
- **PostgreSQL** — relational database engine
- **dbt** — data transformation, modeling, and testing
- **Apache Airflow** — pipeline orchestration
- **Docker / Docker Compose** — containerized development environment
- **Amazon S3** — archival storage for original AIS API responses
- **Amazon RDS for PostgreSQL** — managed cloud database hosting
- **Git** — version control

## Pipeline
The Airflow DAG executes three sequential tasks:

1. **Ingest vessels**
   - Extracts AIS vessel observations from the OpenWaters API.
   - Converts the API response into a pandas DataFrame.
   - Archives the original API response in Amazon S3.
   - Validates required fields and geographic coordinates.
   - Logs received, invalid, duplicate, inserted, and skipped observations.
   - Inserts new observations into the raw table using `ON CONFLICT DO NOTHING`
   - The DAG runs hourly, retries failed tasks once after a five-minute delay,
and prevents overlapping DAG runs.
   

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
- Observations missing MMSI or timestamp are removed before loading.
- Latitude and longitude are validated against valid geographic ranges.
- Duplicate observations within each API batch are removed before loading.
- PostgreSQL enforces uniqueness on `(mmsi, seen)` to prevent duplicate vessel observations.
- The ingestion process uses `ON CONFLICT DO NOTHING` to make repeated API loads idempotent.
- dbt tests verify that critical fields such as MMSI, observation timestamp, latitude, and longitude are not null.
- The daily metrics model is designed with a grain of one row per vessel per observation date.

## Running the Project
Apache Airflow runs locally in Docker, while persistent pipeline data
is stored in AWS S3 and Amazon RDS for PostgreSQL.

1. Configure the required AWS and RDS environment variables.
2. Authenticate to AWS for S3 access.
3. Start the local Airflow services with Docker Compose.
4. Airflow runs the pipeline hourly, or the DAG can be triggered manually.

The DAG executes:

`ingest_vessels → dbt_run → dbt_test`