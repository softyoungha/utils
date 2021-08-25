#!/bin/bash
source ~/.bashrc

$AIRFLOW_HOME/bash/run_webserver.sh
$AIRFLOW_HOME/bash/run_scheduler.sh
$AIRFLOW_HOME/bash/run_flower.sh