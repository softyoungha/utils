#!/bin/bash
source ~/.bashrc

# pid 파일 존재 체크
if [[ -f $AIRFLOW_HOME/airflow-flower.pid ]]; then

  # pid running 체크
  if [[ $(ps -ef | awk '{ print $2 }' | grep $(cat "$AIRFLOW_HOME"/airflow-flower.pid)) != "" ]];then
    echo "Still running: flower PID $(cat "$AIRFLOW_HOME"/airflow-flower.pid)"
    exit 100
  fi

  echo "'$AIRFLOW_HOME/airflow-flower.pid' will be overwrite, '.err', '.out', '.log' will be deleted"
  rm -f $AIRFLOW_HOME/{airflow-flower.pid,airflow-flower.err,airflow-flower.out,airflow-flower.log}

fi

# run
airflow celery flower -D > $AIRFLOW_HOME/logs/flower.log &

# pid 파일 생성 wait
while true;do
  sleep 1

  if [[ -f $AIRFLOW_HOME/airflow-flower.pid ]]; then
    echo "Flower PID: $(cat $AIRFLOW_HOME/airflow-flower.pid)"
    break;
    
  fi
done