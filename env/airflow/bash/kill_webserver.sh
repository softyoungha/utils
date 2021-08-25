#!/bin/bash
source ~/.bashrc

if [[ -f $AIRFLOW_HOME/airflow-webserver.pid ]]; then
  echo "kill airflow-webserver: $(cat "$AIRFLOW_HOME/airflow-webserver.pid")"
  cat "$AIRFLOW_HOME/airflow-webserver.pid" | xargs kill -9

else
  echo "'$AIRFLOW_HOME/airflow-webserver.pid' does not exist"

fi

if [[ -f $AIRFLOW_HOME/airflow-webserver-monitor.pid ]]; then
  echo "kill airflow-webserver-monitor: $(cat "$AIRFLOW_HOME/airflow-webserver-monitor.pid")"
  cat "$AIRFLOW_HOME/airflow-webserver-monitor.pid" | xargs kill -9

else
  echo "'$AIRFLOW_HOME/airflow-webserver-monitor.pid' does not exist"

fi

GUVICORN_PIDS=$(pgrep -f "airflow-webserver")

if [[ ${GUVICORN_PIDS} != '' ]]; then
  echo "kill remained webserver process: ${GUVICORN_PIDS}"
  kill -9 ${GUVICORN_PIDS}
fi