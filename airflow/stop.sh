pgrep -af airflow
pkill -f airflow

rm airflow-scheduler* -f
rm airflow-webserver* -f
