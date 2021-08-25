#!/bin/bash

# airflow home path
export AIRFLOW_HOME="/home/ec2-user/airflow"
export AIRFLOW__CORE__SQL_ALCHEMY_CONN="postgresql+psycopg2://user:password@host:port/airflow"
export AIRFLOW__CORE__FERNET_KEY='3nw_SZV6ngJk2V-a_rK1pU2U9nDbOwxsBmP_efpUPeg='
export AIRFLOW__CELERY__BROKER_URL="redis://:redis_password@redis_port/redis_db"
export AIRFLOW__CELERY__RESULT_BACKEND="db+postgresql://user:password@host:port/airflow"