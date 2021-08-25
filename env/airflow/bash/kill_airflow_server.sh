#!/bin/bash
source ~/.bashrc

# kill all
$AIRFLOW_HOME/bash/kill_webserver.sh
$AIRFLOW_HOME/bash/kill_scheduler.sh
$AIRFLOW_HOME/bash/kill_flower.sh

