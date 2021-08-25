#!/bin/bash
source ~/.bashrc

# pid 파일 존재 체크
if [[ -f $AIRFLOW_HOME/airflow-webserver.pid ]]; then

  # pid running 체크
  if [[ $(ps -ef | awk '{ print $2 }' | grep $(cat "$AIRFLOW_HOME"/airflow-webserver.pid)) != "" ]];then
    echo "Still running: webserver PID $(cat "$AIRFLOW_HOME"/airflow-webserver.pid)"
    exit 100
  fi

  # pid running 체크(-monitor)
  if [[ $(ps -ef | awk '{ print $2 }' | grep $(cat "$AIRFLOW_HOME"/airflow-webserver-monitor.pid)) != "" ]];then
    echo "Still running: monitor PID $(cat "$AIRFLOW_HOME"/airflow-webserver-monitor.pid)"
    exit 100
  fi

  echo "'$AIRFLOW_HOME/airflow-webserver.pid' will be overwrite, '.err', '.out', '.log' will be deleted"
  rm -f $AIRFLOW_HOME/{airflow-webserver.pid,airflow-webserver.err,airflow-webserver.out,airflow-webserver.log,airflow-webserver-monitor.pid}

fi

# run
airflow webserver -D > $AIRFLOW_HOME/logs/webserver.log &

# pid 파일 생성 wait
while true;do
  sleep 1

  if [[ -f $AIRFLOW_HOME/airflow-webserver.pid ]]; then
    echo "Webserver PID: $(cat $AIRFLOW_HOME/airflow-webserver.pid)"

    if [[ -f $AIRFLOW_HOME/airflow-webserver-monitor.pid ]]; then
      echo "Webserver monitor PID: $(cat $AIRFLOW_HOME/airflow-webserver-monitor.pid)"
      break;
    fi

  fi
done