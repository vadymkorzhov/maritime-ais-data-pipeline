from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="maritime_pipeline",
    start_date=datetime(2026, 9, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
) as dag:

    ingest_vessels = BashOperator(
        task_id="ingest_vessels",
        bash_command="python /opt/airflow/src/ingest_vessels.py",
        env={
            "MARITIME_DB_HOST": "postgres",
            "MARITIME_DB_PORT": "5432",
        },
        append_env=True,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/maritime_dbt && dbt run --target docker"
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/maritime_dbt && dbt test --target docker"
    )

    ingest_vessels >> dbt_run >> dbt_test