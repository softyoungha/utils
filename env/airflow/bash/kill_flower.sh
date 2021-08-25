#!/bin/bash
source ~/.bashrc

if [[ -f $AIRFLOW_HOME/airflow-flower.pid ]]; then
  echo "kill airflow-flower: $(cat "$AIRFLOW_HOME/airflow-flower.pid")"
  cat "$AIRFLOW_HOME/airflow-flower.pid" | xargs kill -9

else
  echo "'$AIRFLOW_HOME/airflow-flower.pid' does not exist"

fi
