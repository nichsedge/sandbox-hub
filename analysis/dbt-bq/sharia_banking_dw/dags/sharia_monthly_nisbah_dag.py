"""
Sharia Banking DW - Monthly Nisbah & Profit Sharing DAG
Schedule: @monthly
Demonstrates:
1. Schedule separation (select=["tag:schedule_monthly"])
2. TestBehavior.AFTER_ALL to separate model materialization from cross-model testing
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
    ExecutionConfig,
)
from cosmos.constants import TestBehavior

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
    dag_id="sharia_monthly_nisbah_pipeline",
    default_args=default_args,
    description="Monthly Mudharabah profit-sharing payout & cross-model audit verification",
    schedule="@monthly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["sharia_banking", "monthly", "nisbah", "dbt", "cosmos"],
) as dag:

    start_monthly = EmptyOperator(task_id="start_monthly")
    end_monthly = EmptyOperator(task_id="end_monthly")

    # Monthly models with AFTER_ALL test behavior so cross-model tests
    # run AFTER all models in the group complete materialization.
    monthly_models_group = DbtTaskGroup(
        group_id="monthly_dbt_models_and_tests",
        project_config=project_config,
        profile_config=profile_config,
        render_config=RenderConfig(
            select=["tag:schedule_monthly"],
            test_behavior=TestBehavior.AFTER_ALL, # Separates run from test execution phase
        ),
    )

    start_monthly >> monthly_models_group >> end_monthly
