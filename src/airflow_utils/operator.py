# -*- coding: utf-8 -*-
"""
Airflow Custom Operator
            modified by     youngha.park
            modified day    2020.04.13
-   Airflow built-in Operator가 마음에 들지 않아서 커스텀함
"""

import os
from typing import Callable, List, Dict

from sqlalchemy import func

from airflow.models import TaskInstance, DagModel, DagRun, DagBag
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.db import provide_session
from airflow.exceptions import AirflowException


# Python operator
class CustomPythonOperator(PythonOperator):
    def __init__(self,
                 *,
                 python_callable: Callable,
                 task_id: str = None,
                 task_prefix: str = None,
                 op_args: List = None,
                 op_kwargs: Dict = None,
                 queue: str = None,
                 **kwargs):
        """
        :param python_callable: [Callable] 실행할 함수
        :param task_id: [str] 없을 경우 python_callable 함수명
        :param task_prefix: [str] task_id 접두사
        :param op_args: [List] 함수 parameter(args)
        :param op_kwargs: [Dict] 함수 parameter(keyword args)
        """
        from .setting import Queue

        if task_id is None:
            task_id = python_callable.__name__

        if task_prefix is not None:
            task_id = f'{task_prefix}{task_id}'

        if queue is None:
            queue = Queue.DEFAULT

        super().__init__(task_id=task_id,
                         python_callable=python_callable,
                         op_args=op_args,
                         op_kwargs=op_kwargs,
                         queue=queue,
                         **kwargs)


# MARS 전용 Spark Operator
class PySparkOperator(PythonOperator):
    ui_color = '#b2c1d1'
    ui_fgcolor = '#000'

    def __init__(self,
                 *,
                 python_callable: Callable,
                 task_id: str = None,
                 task_prefix: str = None,
                 op_args: List = None,
                 op_kwargs: Dict = None,
                 **kwargs):
        """
        :param python_callable: [Callable] 실행할 함수
        :param task_id: [str] 없을 경우 python_callable 함수명
        :param task_prefix: [str] task_id 접두사
        :param op_args: [List] 함수 parameter(args)
        :param op_kwargs: [Dict] 함수 parameter(keyword args)
        """
        from .setting import Queue

        if task_id is None:
            task_id = python_callable.__name__

        if task_prefix is not None:
            task_id = f'{task_prefix}{task_id}'

        super().__init__(task_id=task_id,
                         python_callable=python_callable,
                         op_args=op_args,
                         op_kwargs=op_kwargs,
                         queue=Queue.SPARK,
                         **kwargs)


class TaskTrigger(TriggerDagRunOperator):
    ui_color = '#efebff'


class TaskSensor(ExternalTaskSensor):
    """
    original ExternalTaskSensor는 정확한 execution_date 를 지정하도록 되어있어서
    trigger -> sensor 순으로 실행되므로 sensor의 execution_date 이후에 success된 trigger 노드 자동 서치해주는
    커스텀 ExternalTaskSensor 생성
    """
    ui_color = '#d7d3e5'

    @provide_session
    def poke(self, context, session=None):
        if self.execution_delta:
            dttm = context['execution_date'] - self.execution_delta
        elif self.execution_date_fn:
            dttm = self.execution_date_fn(context['execution_date'])
            # dttm = self._handle_execution_date_fn(context=context)
        else:
            dttm = context['execution_date']

        dttm_filter = dttm if isinstance(dttm, list) else [dttm]
        serialized_dttm_filter = ','.join(
            [datetime.isoformat() for datetime in dttm_filter])

        self.log.info(
            'Poking for %s.%s on %s ... ',
            self.external_dag_id, self.external_task_id, serialized_dttm_filter
        )

        DM = DagModel
        TI = TaskInstance
        DR = DagRun
        if self.check_existence:
            dag_to_wait = session.query(DM).filter(
                DM.dag_id == self.external_dag_id
            ).first()

            if not dag_to_wait:
                raise AirflowException('The external DAG '
                                       '{} does not exist.'.format(self.external_dag_id))
            else:
                if not os.path.exists(dag_to_wait.fileloc):
                    raise AirflowException('The external DAG '
                                           '{} was deleted.'.format(self.external_dag_id))

            if self.external_task_id:
                refreshed_dag_info = DagBag(dag_to_wait.fileloc).get_dag(self.external_dag_id)
                if not refreshed_dag_info.has_task(self.external_task_id):
                    raise AirflowException('The external task'
                                           '{} in DAG {} does not exist.'.format(self.external_task_id,
                                                                                 self.external_dag_id))

        if self.external_task_id:
            # .count() is inefficient
            count = session.query(func.count()).filter(
                TI.dag_id == self.external_dag_id,
                TI.task_id == self.external_task_id,
                TI.state.in_(self.allowed_states),
                TI.execution_date >= dttm,
            ).scalar()
        else:
            # .count() is inefficient
            count = session.query(func.count()).filter(
                DR.dag_id == self.external_dag_id,
                DR.state.in_(self.allowed_states),
                DR.execution_date >= dttm,
            ).scalar()

        session.commit()
        return count == len(dttm_filter)



