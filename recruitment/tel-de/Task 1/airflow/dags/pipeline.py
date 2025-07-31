from datetime import datetime, timedelta
import airflow
from airflow import DAG
from custom import PostgreToMySqlOperator
from airflow.operators.mysql_operator import MySqlOperator

dag = DAG(
    dag_id="dag_daily",
    start_date=datetime.today() - timedelta(days=1),
    schedule_interval="@daily",
    concurrency=100,
)

create_table = MySqlOperator(
    mysql_conn_id="mysql", task_id="create_table", sql="sql/create.sql", dag=dag
)

t1 = PostgreToMySqlOperator(
    task_id="dim_customer",
    sql="sql/dwh/dim_customer.sql",
    target_table="dimCustomer",
    identifier="id",
    dag=dag,
)

t2 = PostgreToMySqlOperator(
    task_id="dim_date",
    sql="sql/dwh/dim_date.sql",
    target_table="dimDate",
    identifier="id",
    dag=dag,
)

t3 = PostgreToMySqlOperator(
    task_id="dim_movie",
    sql="sql/dwh/dim_movie.sql",
    target_table="dimMovie",
    identifier="id",
    dag=dag,
)

t4 = PostgreToMySqlOperator(
    task_id="dim_store",
    sql="sql/dwh/dim_store.sql",
    target_table="dimStore",
    identifier="id",
    dag=dag,
)

t5 = PostgreToMySqlOperator(
    task_id="fact_sales",
    sql="sql/dwh/fact_sales.sql",
    target_table="factSales",
    identifier="id",
    dag=dag,
)

create_table >> [t1, t2, t3, t4, t5]
