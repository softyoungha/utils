"""
Airflow 기본 세팅

- DEFAULT_ARGS: 모든 DAG들의 default_args
- NamedDagId: Trigger 하기 위해 Dag name list 입력
- NamedTaskId: Start/End/Fork/Join 의 자주 사용하는 Task Name
- Pool: Airflow Pool 종류
- Queue: Airflow Queue 종류
"""
from airflow.utils.timezone import make_aware
from datetime import timedelta, datetime


DEFAULT_ARGS = dict(
    owner='youngha',
    depends_on_past=False,
    start_date=make_aware(datetime(2021, 8, 25)),
    retries=0,
    retry_delay=timedelta(minutes=5),
)


class NamedDagId:
    # trigger
    DAILY_TRIGGER = 'trigger_daily'
    LRN_TRIGGER = 'trigger_lrn'
    TRG_TRIGGER = 'trigger_trg'

    # dags
    ETL = 'dag_etl'
    MART = 'dag_mart'
    LRN_PROCESSING = 'dag_lrn_processing'
    LRN_TRAINING = 'dag_lrn_training'
    TRG_PROCESSING = 'dag_trg_processing'
    TRG_PREDICTION = 'dag_trg_prediction'
    VECTOR_MODEL = 'dag_vector_model'

    # ETC
    BACKUP = 'backup_weekly'
    CLEAR = 'clear'


def get_priority(name: str):
    if name == NamedDagId.DAILY_TRIGGER:
        return 900
    elif name == NamedDagId.ETL:
        return 800
    elif name == NamedDagId.MART:
        return 700
    elif name == NamedDagId.LRN_TRIGGER:
        return 600
    elif name == NamedDagId.LRN_PROCESSING:
        return 500
    elif name in (NamedDagId.LRN_TRAINING, ):
        return 400
    elif name == NamedDagId.TRG_TRIGGER:
        return 300
    elif name == NamedDagId.TRG_PROCESSING:
        return 200
    elif name == NamedDagId.TRG_PREDICTION:
        return 100


def get_default_args(name: str):
    default_args = dict(**DEFAULT_ARGS,
                        priority_weight=get_priority(name=name))

    if name == NamedDagId.DAILY_TRIGGER:
        default_args.update(dict(pool=Pool.DEFAULT))
        return default_args
    elif name == NamedDagId.ETL:
        default_args.update(dict(pool=Pool.SPARK))
        return default_args
    elif name == NamedDagId.MART:
        default_args.update(dict(pool=Pool.SPARK))
        return default_args
    elif name == NamedDagId.LRN_TRIGGER:
        default_args.update(dict(pool=Pool.DEFAULT))
        return default_args
    elif name == NamedDagId.LRN_PROCESSING:
        default_args.update(dict(pool=Pool.SPARK))
        return default_args
    elif name in (NamedDagId.LRN_TRAINING, ):
        default_args.update(dict(pool=Pool.ENGINE,
                                 retries=1,
                                 retry_delay=timedelta(minutes=3),
                                 execution_timeout=timedelta(hours=3)))
        return default_args
    elif name == NamedDagId.TRG_TRIGGER:
        default_args.update(dict(pool=Pool.DEFAULT))
        return default_args
    elif name == NamedDagId.TRG_PROCESSING:
        default_args.update(dict(pool=Pool.SPARK))
        return default_args
    elif name == NamedDagId.TRG_PREDICTION:
        default_args.update(dict(pool=Pool.ENGINE,
                                 retries=1,
                                 retry_delay=timedelta(minutes=1),
                                 execution_timeout=timedelta(hours=1, minutes=0),
                                 # start_date=make_aware(datetime(2020, 6, 28))
                                 ))
        return default_args


class NamedTaskId:
    START = 'Start'
    FORK = 'Fork'
    JOIN = 'Join'
    END = 'End'


class Pool:
    DEFAULT = 'default_pool'
    ENGINE = 'engine'
    SPARK = 'spark'


class Queue:
    # group alias
    DEFAULT = 'default'
    SPARK = 'spark'
    SLAVE = 'slave'
    ENGINE = 'engine'





