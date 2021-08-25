from typing import Callable, List, Dict

from airflow.models import BaseOperator


def list_to_sequential_task(task_lst: List[BaseOperator] or List[List[BaseOperator]],
                            upstream_task: BaseOperator = None,
                            downstream_task: BaseOperator = None):
    """
    task list를 넣으면 sequential 하게 연결해주는 함수

    :param task_lst: [list of BaseOperator]
    :param upstream_task: [BaseOperator] 선행 task instance
    :param downstream_task: [BaseOperator] 후행 task instance
    """
    for i, task in enumerate(task_lst):
        assert isinstance(task, (list, BaseOperator))

        if isinstance(task, list):
            list_to_sequential_task(task_lst=task)

        if i == 0:
            if upstream_task is not None:
                if isinstance(task, list):
                    upstream_task >> task[0]
                else:
                    upstream_task >> task

        else:
            if isinstance(task, list):
                last_task[-1] >> task[0]
            else:
                last_task >> task

        last_task = task

    if downstream_task is not None:
        if isinstance(task, list):
            last_task[-1] >> downstream_task
        else:
            last_task >> downstream_task


def custom_make_aware(value, timezone=None):
    """
    Pendulum dtype(UTC 관련 패키지)를 datetime 형식으로 변경시켜줌
    airflow 내에서 사용하는 execution_date 가 기본적으로 pendulum.pendulum.Pendulum 클래스이므로
    datetime 으로 변환해주기 위해서 필요한 함수
    """
    from airflow.utils.timezone import make_aware
    from datetime import datetime

    # if isinstance(value, Pendulum):
    value = datetime.fromtimestamp(value.timestamp())

    return make_aware(value=value, timezone=timezone)


def dummy_python(raise_error=True, **context):
    import pprint

    pprint.pprint(context)
    if raise_error:
        raise Exception('skip!')

    return 'skip!'
