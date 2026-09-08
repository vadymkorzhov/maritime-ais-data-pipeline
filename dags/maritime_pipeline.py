from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator

default_args = {"retries": 1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="maritime_pipeline",
    start_date=datetime(2026, 9, 1),
    schedule="0 * * * * ",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
) as dag:

    ingest_vessels = BashOperator(
        task_id="ingest_vessels",
        bash_command="python /opt/airflow/src/ingest_vessels.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/maritime_dbt && dbt run --target rds"
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/maritime_dbt && dbt test --target rds"
    )

    ingest_vessels >> dbt_run >> dbt_test