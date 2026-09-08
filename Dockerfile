FROM apache/airflow:3.2.2

RUN pip install dbt-postgres boto3 "botocore[crt]"