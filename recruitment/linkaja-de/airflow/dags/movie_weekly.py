import datetime
import json
from google.cloud import bigquery

from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.operators.empty import EmptyOperator

from google.oauth2 import service_account

DAG_ID = "movie_weekly"

credentials = service_account.Credentials.from_service_account_file(
    "/home/al/projects/creds/ichsanul-dev-cc6f799c9121.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)


def csv2pg(
    conn_id="pg_local",
    target_table="public.movies",
    csv_path="/home/al/projects/detest_linkaja/.temp/IMDB-Movie-Data.csv",
):
    sql = f"COPY {target_table} FROM stdin WITH CSV HEADER"

    pg_hook = PostgresHook(postgres_conn_id=conn_id)
    pg_hook.copy_expert(sql, csv_path)


def pg2json(
    conn_id="pg_local",
    source_table="public.movies_top_animation",
    target_path="/home/al/projects/detest_linkaja/.temp/output.json",
):
    sql = f"SELECT JSON_AGG(ROW_TO_JSON(st)) FROM (SELECT * FROM {source_table} ) st"

    pg_hook = PostgresHook(postgres_conn_id=conn_id)
    rows = pg_hook.get_records(sql)[0][0]
    json_data = json.dumps(rows, indent=4)

    with open(target_path, "w") as json_file:
        json_file.write(json_data)


def json2bq(
    target_table="ichsanul-dev.dev.movies_top_animation",
    json_path="//home/al/projects/detest_linkaja/.temp/output.json",
):
    # Connect to BigQuery
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)

    # Load JSON data to BigQuery
    table = bigquery.Table(table_ref=target_table)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # optional
    )

    with open(json_path, "r") as f:
        # Load the JSON data
        json_data = json.load(f)

    load_job = client.load_table_from_json(json_data, table, job_config=job_config)

    # Wait for the job to complete
    load_job.result()  # Waits for table load to finish

    print(f"Data loaded successfully to BigQuery table: {table.full_table_id}")


with DAG(
    DAG_ID,
    schedule="0 1 * * 0,6",
    start_date=datetime.datetime(2023, 1, 1),
    catchup=False,
    tags=[],
) as dag:
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    # pg
    delete_pg_task = SQLExecuteQueryOperator(
        task_id="delete_pg_task", conn_id="pg_local", sql="DELETE FROM public.movies;"
    )
    csv2pg_task = PythonOperator(task_id="csv2pg_task", python_callable=csv2pg)

    # to bq
    pg2json_task = PythonOperator(task_id="pg2json_task", python_callable=pg2json)
    json2bq_task = PythonOperator(task_id="json2bq_task", python_callable=json2bq)

    start >> delete_pg_task >> csv2pg_task >> pg2json_task >> json2bq_task >> end
