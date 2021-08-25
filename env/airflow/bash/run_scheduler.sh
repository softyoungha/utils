#!/bin/bash
source ~/.bashrc

# pid 파일 존재 체크
if [[ -f $AIRFLOW_HOME/airflow-scheduler.pid ]]; then

  # pid running 체크
  if [[ $(ps -ef | awk '{ print $2 }' | grep $(cat "$AIRFLOW_HOME"/airflow-scheduler.pid)) != "" ]];then
    echo "Still running: scheduler PID $(cat "$AIRFLOW_HOME"/airflow-scheduler.pid)"
    exit 100
  fi

  echo "'$AIRFLOW_HOME/airflow-scheduler.pid' will be overwrite, '.err', '.out', '.log' will be deleted"
  rm -f $AIRFLOW_HOME/{airflow-scheduler.pid,airflow-scheduler.err,airflow-scheduler.out,airflow-scheduler.log}

fi

# run
airflow scheduler -D > $AIRFLOW_HOME/logs/scheduler.log &

# pid 파일 생성 wait
while true;do
  sleep 1

  if [[ -f $AIRFLOW_HOME/airflow-scheduler.pid ]]; then
    echo "Scheduler PID: $(cat $AIRFLOW_HOME/airflow-scheduler.pid)"
    break;

  fi
done