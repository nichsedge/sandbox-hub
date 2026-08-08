"""
Sharia Banking Data Warehouse - Astronomer Cosmos Airflow DAG
Orchestrates dbt models on DuckDB organized by Sharia banking domain tags.
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

# Dynamic relative path definitions
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
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="sharia_banking_dw_pipeline",
    default_args=default_args,
    description="Full Sharia Banking Data Warehouse pipeline using dbt-duckdb & Astronomer Cosmos",
    schedule="@monthly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["sharia_banking", "dbt", "cosmos", "duckdb", "indonesia"],
) as dag:


    start_pipeline = EmptyOperator(task_id="start_pipeline")
    end_pipeline = EmptyOperator(task_id="end_pipeline")

    # 1. Staging TaskGroup (dbt tag: staging)
    staging_group = DbtTaskGroup(
        group_id="staging_layer",
        project_config=project_config,
        profile_config=profile_config,
        render_config=RenderConfig(
            select=["tag:staging"],
        ),
    )

    # 2. Retail Marts TaskGroup (dbt tag: marts_retail)
    retail_group = DbtTaskGroup(
        group_id="retail_marts",
        project_config=project_config,
        profile_config=profile_config,
        render_config=RenderConfig(
            select=["tag:marts_retail"],
        ),
    )

    # 3. Financing Marts TaskGroup (dbt tag: marts_financing)
    financing_group = DbtTaskGroup(
        group_id="financing_marts",
        project_config=project_config,
        profile_config=profile_config,
        render_config=RenderConfig(
            select=["tag:marts_financing"],
        ),
    )

    # 4. Nisbah & Profit Sharing Marts TaskGroup (dbt tag: marts_nisbah)
    nisbah_group = DbtTaskGroup(
        group_id="nisbah_profit_sharing_marts",
        project_config=project_config,
        profile_config=profile_config,
        render_config=RenderConfig(
            select=["tag:marts_nisbah"],
        ),
    )

    # 5. OJK Regulatory & Sharia Governance TaskGroup (dbt tag: marts_reg)
    regulatory_group = DbtTaskGroup(
        group_id="regulatory_governance_marts",
        project_config=project_config,
        profile_config=profile_config,
        render_config=RenderConfig(
            select=["tag:marts_reg"],
        ),
    )



    # DAG Dependency Flow
    start_pipeline >> staging_group
    staging_group >> retail_group
    staging_group >> financing_group
    retail_group >> nisbah_group
    financing_group >> nisbah_group
    nisbah_group >> regulatory_group
    regulatory_group >> end_pipeline
