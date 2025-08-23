
```
docker-compose up airflow-init

docker-compose up -d

docker-compose stop
```

refresh

docker exec -it --user airflow airflow-scheduler bash -c "airflow dags list"

docker exec -it --user airflow airflow-scheduler bash -c "airflow dags list-import-errors"


