from airflow.contrib.operators.dataflow_operator import DataFlowPythonOperator


t1 = DataFlowPythonOperator(
    "data_ingestion.py",
    job_name="t1",
    py_options=None,
    dataflow_default_options=None,
    options=None,
    gcp_conn_id="google_cloud_default",
    delegate_to=None,
    poll_sleep=10,
)
