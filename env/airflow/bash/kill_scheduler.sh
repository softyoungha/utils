#!/bin/bash
source ~/.bashrc

if [[ -f $AIRFLOW_HOME/airflow-scheduler.pid ]]; then
  echo "kill airflow-scheduler: $(cat "$AIRFLOW_HOME/airflow-scheduler.pid")"
  cat "$AIRFLOW_HOME/airflow-scheduler.pid" | xargs kill -9

else
  echo "'$AIRFLOW_HOME/airflow-scheduler.pid' does not exist"

fi

SCHEDULER_PIDS=$(pgrep -f "airflow scheduler")

if [[ ${SCHEDULER_PIDS} != '' ]]; then
  echo "kill remained scheduler process: ${SCHEDULER_PIDS}"
  kill -9 ${SCHEDULER_PIDS}
fi