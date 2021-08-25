#!/bin/bash
source ~/.bashrc

# pid 파일 존재 체크
if [[ -f $AIRFLOW_HOME/airflow-worker.pid ]]; then

  # pid running 체크
  if [[ $(ps -ef | awk '{ print $2 }' | grep $(cat "$AIRFLOW_HOME"/airflow-worker.pid)) != "" ]];then
    echo "Still running: worker PID $(cat "$AIRFLOW_HOME"/airflow-worker.pid)"
    exit 100
  fi

  echo "'$AIRFLOW_HOME/airflow-worker.pid' will be overwrite, '.err', '.out', '.log' will be deleted"
  rm -f $AIRFLOW_HOME/{airflow-worker.pid,airflow-worker.err,airflow-worker.out,airflow-worker.log}

fi

# run
echo -e "MONITOR: use default, monitor Queue"
airflow celery worker --queues "default,$(hostname)" -H monitor@%h -c 1 -D

# pid 파일 생성 wait
while true;do
  sleep 1

  if [[ -f $AIRFLOW_HOME/airflow-worker.pid ]]; then
    echo "Worker PID: $(cat $AIRFLOW_HOME/airflow-worker.pid)"
    break;

  fi
done