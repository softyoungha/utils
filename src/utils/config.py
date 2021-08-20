"""
프로젝트 내 config 세팅
"""
import os
import logging
from .const import *
from .tool import load_yaml, get_env, path_join


# Default Setting
class Default:

    # 기본 io engine
    IOEngine = IOEngine.pandas

    # parquet 사용시 기본 engine
    ParquetEngine = ParquetEngine.pyarrow

    # pandas read/write 시 데이터 형식
    FileFormat = FileFormat.PARQUET

    # 기본 저장 공간
    FileSystem = FileSystem.FILE

    # 기본 인코딩
    Encoding = Encoding.UTF8

    # csv 저장시 delimiter
    Delimiter = Delimiter.COMMA

    # log level
    LogLevel = logging.INFO

    DaskNPartition = 32


# 프로젝트 내에서 사용하는 모든 환경변수의 prefix
ENV_PREFIX = 'YH__'

_get_env = lambda name, default: get_env(name, default=default, prefix=ENV_PREFIX)


# 주요 폴더 경로
class Paths:

    HOME = _get_env('HOME_PATH', default='/home/ec2-user')
    SOURCE = _get_env('SOURCE_PATH', default='/home/ec2-user/src')
    DATA = _get_env('DATA_PATH', default='/data')
    LOG = _get_env('LOG_PATH', default='/log')
    CONFIG = _get_env('CONFIG_PATH', default=f'{SOURCE}/configs')

# parse
ENV = get_env('ENV', default='DEV', prefix=ENV_PREFIX)

# get configs
if ENV == 'DEV':
    DB_CONFIG = load_yaml(path_join(Paths.CONFIG, 'db.yml'))
    REDIS_CONFIG = load_yaml(path_join(Paths.CONFIG, 'redis.yml'))
    S3_CONFIG = load_yaml(path_join(Paths.CONFIG, 's3.yml'))

elif ENV == 'PRD':
    DB_CONFIG = load_yaml(path_join(Paths.CONFIG, 'db.prod.yml'))
    REDIS_CONFIG = load_yaml(path_join(Paths.CONFIG, 'redis.prod.yml'))
    S3_CONFIG = load_yaml(path_join(Paths.CONFIG, 's3.prod.yml'))

else:
    assert ENV in ('DEV', 'PRD'), "set MARS__ENV(windows) / export MARS__ENV(linux)"