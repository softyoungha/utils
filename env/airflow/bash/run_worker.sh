#!/bin/bash
source ~/.bashrc

# choices: MASTER / None
export NODE="$1"
export CONCURRENCY="${2:-1}"

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
if [[ "${NODE}" == 'MASTER' ]]; then
  echo -e "MASTER: use default, master, mars, engine Queue"
  airflow celery worker --queues "default,master,mars,engine,$(hostname)" -H master@%h -c $CONCURRENCY -D

else
  echo -e "SLAVE: use default, slave, mars, engine Queue"
  airflow celery worker --queues "default,slave,mars,engine,$(hostname)" -H slave@%h -c $CONCURRENCY -D

fi

# pid 파일 생성 wait
while true;do
  sleep 1

  if [[ -f $AIRFLOW_HOME/airflow-worker.pid ]]; then
    echo "Worker PID: $(cat $AIRFLOW_HOME/airflow-worker.pid)"
    break;

  fi
done