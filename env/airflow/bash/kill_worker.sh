#!/bin/bash
source ~/.bashrc

if [[ -f $AIRFLOW_HOME/airflow-worker.pid ]]; then

  if [[ $(ps -ef | awk '{ print $2 }' | grep $(cat "$AIRFLOW_HOME"/airflow-worker.pid)) != "" ]];then
    echo "kill airflow-worker: $(cat "$AIRFLOW_HOME/airflow-worker.pid")"
    pkill celeryd
    cat "$AIRFLOW_HOME/airflow-worker.pid" | xargs kill -9

  else
    echo "no PID of airflow-worker: $(cat "$AIRFLOW_HOME/airflow-worker.pid")"

  fi

else
  echo "'$AIRFLOW_HOME/airflow-worker.pid' does not exist"

fi

WORKER_PIDS=$(pgrep -f "celery worker")

if [[ ${WORKER_PIDS} != '' ]]; then
  echo "kill remained worker process: ${WORKER_PIDS}"
  kill -9 ${WORKER_PIDS}
fi

# serve_logs 삭제
SERVER_LOGS=$(pgrep -f "airflow serve_logs")

if [[ ${SERVER_LOGS} != '' ]]; then
  echo "kill server logs: ${SERVER_LOGS}"
  kill -9 ${SERVER_LOGS}
fi
