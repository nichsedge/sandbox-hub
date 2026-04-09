import datetime
import logging

from airflow.models import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCheckOperator,
)

logger = logging.getLogger(__name__)

DAG_ID = "scrape_weekly"


def macro_year_week(data_interval_end):
    yearweek = int(data_interval_end.strftime("%Y%U"))
    logger.info("current_date: " + str(data_interval_end))
    logger.info("yearweek: " + str(yearweek))
    return yearweek


with DAG(
    DAG_ID,
    schedule="0 0 * * 1",
    start_date=datetime.datetime(2023, 1, 1),
    catchup=False,
    tags=[],
    user_defined_macros={"yearweek": macro_year_week},
) as dag:
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    check_count = BigQueryCheckOperator(
        gcp_conn_id="ichsanul_dev",
        task_id="check_count",
        sql="""
            SELECT COUNT(*) FROM `de_zoomcamp.enterkomputer_raw` 
            WHERE DATE(inserted_at) between date('{{ data_interval_start }}') and date('{{ data_interval_end }}')
            """,
        use_legacy_sql=False,
    )

    start >> check_count >> end
