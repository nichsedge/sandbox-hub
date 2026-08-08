"""
Sharia Banking DW - Daily Pipeline DAG
Schedule: @daily
Selects models tagged with 'schedule_daily' (Staging & Retail Transaction Ledger)
"""

from pathlib import Path
from datetime import datetime, timedelta
from airflow import DAG

try:
    from airflow.providers.standard.operators.empty import EmptyOperator
except ImportError:
    from airflow.operators.empty import EmptyOperator

from cosmos import (
    DbtTaskGroup,
    ProjectConfig,
    ProfileConfig,
    RenderConfig,
)

DBT_PROJECT_PATH = (Path(__file__).parent.parent / "dbt_project").resolve()
DBT_PROFILES_PATH = DBT_PROJECT_PATH / "profiles.yml"

profile_config = ProfileConfig(
    profile_name="sharia_dw",
    target_name="dev",
    profiles_yml_filepath=DBT_PROFILES_PATH,
)

project_config = ProjectConfig(
    dbt_project_path=DBT_PROJECT_PATH,
)

default_args = {
    "owner": "sharia_data_team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="sharia_daily_pipeline",
    default_args=default_args,
    description="Daily ingestion & retail ledger materialization",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["sharia_banking", "daily", "dbt", "cosmos"],
) as dag:

    start_daily = EmptyOperator(task_id="start_daily")
    end_daily = EmptyOperator(task_id="end_daily")

    daily_models_group = DbtTaskGroup(
        group_id="daily_dbt_models",
        project_config=project_config,
        profile_config=profile_config,
        render_config=RenderConfig(
            select=["tag:schedule_daily"],
        ),
    )

    start_daily >> daily_models_group >> end_daily
