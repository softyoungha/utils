"""
모든 패키지 공통 tool
"""

from typing import List, Dict, Union, Any, Callable
import os
import numpy as np
import pandas as pd
import dask.dataframe as dd
import json
from io import StringIO, BytesIO
from datetime import datetime, timezone, timedelta, date

from .const import *


def path_join(*args, sep: str = '/') -> str:
    """
    os.path.join 사용시 s3, minio 에서도 사용

    :param args: path components
    :param sep: separator
    :return: joined path
    """

    args = list(map(str, args))
    joined_path = os.path.join(*args)

    if sep:
        return joined_path.replace(os.path.sep, sep)
    else:
        return joined_path


# About Json
def load_json(file_path: str) -> dict:
    with open(file_path) as f:
        _dict = json.load(f)
    return _dict


def save_json(_dict: dict, file_path: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(_dict, f, ensure_ascii=False, indent='\t')


def print_json(_dict) -> str:
    json_str = json.dumps(_dict, indent='\t')
    return json_str


def json_to_fileobj(data: dict,
                    buffer_type: str = 'str',
                    ensure_ascii: bool = False,
                    indent: str = '\t') -> Union[StringIO, BytesIO]:
    """
    json -> StringIO or BytesIO

    :param data: dictionary 형태의 data
    :param buffer_type: 'str' -> StringIO / 'byte' -> BytesIO
    :param ensure_ascii: ascii code 변환 여부
    :param indent: 변환된 json에 indentation 추가
    :return: StringIO or BytesIO
    """
    if buffer_type == 'str':
        buffer = StringIO()

    elif buffer_type == 'byte':
        buffer = BytesIO()

    else:
        raise ValueError('buffer type miss matched')

    json.dump(data, buffer, ensure_ascii=ensure_ascii, indent=indent)
    buffer.seek(0)

    return buffer


# About Yaml
def load_yaml(file_path: str) -> dict:
    import yaml

    with open(file_path) as f:
        _dict = yaml.load(f, Loader=yaml.FullLoader)

    return _dict


def save_yaml(_dict: dict, file_path: str):
    import yaml

    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(_dict, f)


# About pickle
def load_joblib(path: str):
    import joblib

    return joblib.load(path)


def save_joblib(clf, path: str):
    import joblib

    joblib.dump(clf, path)


# About text
def read_text(path: str, multilines: bool = False) -> Union[str, list]:
    with open(path, 'r') as f:
        if multilines:
            text = f.readlines()

        else:
            text = f.read()

    return text


# About Numpy array
def as_arr(obj: Union[pd.DataFrame, pd.Series, np.ndarray, List]) -> np.ndarray:
    """
    obj -> numpy array
    """
    if isinstance(obj, pd.DataFrame) or isinstance(obj, pd.Series):
        values = obj.values

        del obj

        return values

    elif isinstance(obj, np.ndarray):
        return obj

    elif isinstance(obj, list):
        return np.asarray(obj)

    else:
        raise TypeError('Input cannot be numpy array.')


# About DataFrame
def obj_to_df(obj: Union[pd.DataFrame, dd.DataFrame],
              scheduler: str = 'threads') -> pd.DataFrame:
    """
    dataframe -> pandas dataframe

    :param obj: Any object
    :param scheduler: dask dataframe의 경우 사용할 scheduler
    :return: pandas dataframe
    """
    if isinstance(obj, pd.DataFrame):
        df = obj

    elif isinstance(obj, dd.DataFrame):
        df = obj.compute(scheduler=scheduler)

    else:
        raise TypeError('Is it DataFrame?')

    return df


def obj_to_ddf(obj: Union[pd.DataFrame, dd.DataFrame], npartitions: int = None) -> dd.DataFrame:
    """
    dataframe -> dask dataframe

    :param obj: Any object
    :param npartitions: dask dataframe 변환시 나눌 partition
    :return: dask dataframe
    """
    from .config import Default

    if npartitions is None:
        npartitions = Default.DaskNPartition

    if isinstance(obj, pd.DataFrame):
        ddf = dd.from_pandas(obj, npartitions=npartitions)

    elif isinstance(obj, dd.DataFrame):
        ddf = obj

    else:
        raise TypeError('Is it DataFrame?')

    return ddf


def read_file(path: str,
              usecols: int = None,
              index_col: int = None,
              nrows: int = None,
              compute: bool = True,
              io_engine: str = IOEngine.pandas,
              scheduler: str = 'threads',
              file_format: str = None,
              **kwargs) -> Union[pd.DataFrame, dd.DataFrame]:
    """
    파일 read
    """
    from .config import Default

    if '*' not in path:
        if not os.path.exists(path):
            raise FileNotFoundError(f'Check path: {path}')

    if file_format is None:
        file_format = Default.FileFormat

    if not io_engine:
        io_engine = Default.IOEngine

    if io_engine == IOEngine.pandas:

        if file_format == FileFormat.CSV:
            df = pd.read_csv(path,
                             usecols=usecols,
                             index_col=index_col,
                             sep=Default.Delimiter,
                             nrows=nrows,
                             quoting=0,
                             engine='python',
                             **kwargs)

        elif file_format == FileFormat.PARQUET:
            df = pd.read_parquet(path, engine=Default.ParquetEngine)

            if nrows is not None:
                df = df.iloc[:nrows, :]

            if usecols is not None:
                if not isinstance(usecols, list):
                    raise TypeError("'usecols' must be list")

                if isinstance(usecols[0], int):
                    df = df.iloc[:, usecols]
                elif isinstance(usecols[0], str):
                    df = df.loc[:, usecols]

            if index_col is not None:
                if isinstance(index_col, list):
                    _index_col = df.columns[index_col].tolist()
                else:
                    _index_col = df.columns[index_col]

                df.set_index(_index_col, inplace=True)

        else:
            raise TypeError('Invalid file format')

        return df

    elif io_engine == IOEngine.dask:
        import dask.dataframe as dd

        if file_format == FileFormat.CSV:
            ddf = dd.read_csv(path, **kwargs)
        elif file_format == FileFormat.PARQUET:
            ddf = dd.read_parquet(path, engine=Default.ParquetEngine, **kwargs)
        else:
            raise TypeError('Invalid file format')

        if compute:
            df = ddf.compute(scheduler=scheduler)

            if nrows is not None:
                df = df.iloc[:nrows, :]

            if usecols is not None:
                if not isinstance(usecols, list):
                    raise TypeError("'usecols' must be list")

                if isinstance(usecols[0], int):
                    df = df.iloc[:, usecols]
                elif isinstance(usecols[0], str):
                    df = df.loc[:, usecols]

            if index_col is not None:
                if isinstance(index_col, list):
                    _index_col = df.columns[index_col].tolist()
                else:
                    _index_col = df.columns[index_col]

                df.set_index(_index_col, inplace=True)

            return df

        else:
            return ddf


def to_file(obj: Any,
            target: Union[StringIO, str],
            index: bool = True,
            io_engine: str = None,
            npartitions: int = None,
            scheduler: str = 'threads',
            partition_cols=None,
            file_format: str = None,
            overwrite: bool = True,
            **kwargs) -> Union[str, StringIO]:
    """
    파일 write
    """
    import logging

    from .const import IOEngine, FileFormat
    from .config import Default

    if isinstance(target, StringIO):
        pass

    elif isinstance(target, str):
        if os.path.exists(target):
            if overwrite:
                if Default.LogLevel <= logging.WARNING:
                    print('WARN: The path already exists. it will be overwritten')
            else:
                raise FileExistsError(f'Check path: {target}')

    if file_format is None:
        file_format = Default.FileFormat

    if not io_engine:
        io_engine = Default.IOEngine

    if io_engine == IOEngine.pandas:
        df = obj_to_df(obj)

        if file_format == FileFormat.CSV:
            df.to_csv(target,
                      index=index,
                      **kwargs)
        elif file_format == FileFormat.PARQUET:
            df.to_parquet(target,
                          index=index,
                          engine=Default.ParquetEngine,
                          partition_cols=partition_cols,
                          compression='snappy',
                          allow_truncated_timestamps=True,
                          **kwargs)
        else:
            raise TypeError('Invalid file format')

    elif io_engine == IOEngine.dask:
        import dask
        ddf = obj_to_ddf(obj)

        if npartitions is not None:
            ddf = ddf.repartition(npartitions)

        if file_format == FileFormat.CSV:
            ddf = ddf.to_csv(target, index=index, sep=Default.Delimiter, compute=False, **kwargs)

        elif file_format == FileFormat.PARQUET:
            ddf = ddf.to_parquet(target,
                                 engine=Default.ParquetEngine,
                                 partition_cols=partition_cols,
                                 compression='snappy',
                                 compute=False,
                                 allow_truncated_timestamps=True,
                                 **kwargs)

        dask.compute(ddf, scheduler=scheduler)

    return target


def df_to_fileobj(df,
                  buffer_type=DType.BYTE,
                  sep=',',
                  index=False,
                  quoting=0,
                  file_format=FileFormat.CSV,
                  io_wrapper=False,
                  **pd_kwargs):
    from io import StringIO, BytesIO, TextIOWrapper

    pandas_kwargs = pd_kwargs

    if file_format == FileFormat.CSV:
        pandas_kwargs['sep'] = sep
        pandas_kwargs['quoting'] = quoting

    if buffer_type == DType.STR:
        buffer = StringIO()

    elif buffer_type == DType.BYTE:
        buffer = BytesIO()

    else:
        raise ValueError('buffer type miss matched')

    if io_wrapper:
        w = TextIOWrapper(buffer, write_through=True)
        to_file(df, w,
                index=index,
                io_engine=IOEngine.pandas,
                file_format=file_format,
                **pandas_kwargs)
        buffer.seek(0)
        return buffer, w

    else:
        to_file(df, buffer,
                index=index,
                io_engine=IOEngine.pandas,
                file_format=file_format,
                **pandas_kwargs)
        buffer.seek(0)
        return buffer


# logging
def get_logger(name: str,
               log_path: str = None,
               log_level: int = None,
               use_stream_handler: bool = False):
    """
    Logger get or create
    """
    import logging

    from .config import Default

    if log_level is None:
        log_level = Default.LogLevel

    if name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name=name)
        logger.setLevel(log_level)

        return logger

    logger = logging.getLogger(name=name)
    logger.setLevel(log_level)

    formatter = logging.Formatter('[%(levelname)s| %(name)s| %(filename)s, %(lineno)s] %(asctime)s: %(message)s')

    if use_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    if log_path is not None:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False

    return logger


# About Time & Date & DateTime
def korean_now(dtype: str = DType.STR, datetime_format: str = '%Y-%m-%d') -> Union[Callable, datetime, str]:
    """
    한국 시간 출력
    """
    now = lambda: datetime.now(timezone.utc) + timedelta(hours=9)

    if dtype == DType.CALLABLE:
        return now

    elif dtype == DType.DATETIME:
        return now()

    elif dtype == DType.STR:
        return now().strftime(datetime_format)

    else:
        raise ValueError('Check dtype')


def print_now(year=True,
              month=True,
              day=True,
              hour=True,
              minute=False,
              second=False,
              day_sep='-',
              time_sep=':') -> str:
    """
    현재 시간 출력
    """
    timestamp_format = ''

    if year:
        timestamp_format += '%Y'

        if month:
            timestamp_format += f'{day_sep}%m'

            if day:
                timestamp_format += f'{day_sep}%d'

    if hour:
        timestamp_format += '_%H'

        if minute:
            timestamp_format += f'{time_sep}%M'

            if second:
                timestamp_format += f'{time_sep}%S'

    return datetime.now().strftime(timestamp_format)


def change_date_format(date_str: str, as_is: str = '%Y%m%d', to_be: str = '%Y-%m-%d') -> str:
    """
    날짜 형식의 string 변환
    """
    return datetime.strptime(date_str, as_is).strftime(to_be)


def as_date(standard_date: Union[str, datetime, date], as_datetime=True) -> Union[datetime, date]:
    """
    string, datetime, date -> date or datetime
    """

    if isinstance(standard_date, str):
        try:
            return datetime.strptime(standard_date, '%Y-%m-%d').date()
        except ValueError as e:

            try:
                standard_date = datetime.strptime(standard_date, '%Y%m%d')
                print("# Warning: standard_date might be the form of %Y%m%d. '%Y-%m-%d' is recommended")
                if as_datetime:
                    return standard_date
                else:
                    return standard_date.date()
            except Exception:
                pass

            raise e

        except Exception as e:
            raise e

    elif isinstance(standard_date, datetime):
        if as_datetime:
            return standard_date
        else:
            return standard_date.date()

    elif isinstance(standard_date, date):
        if as_datetime:
            return datetime(standard_date.year, standard_date.month, standard_date.day)
        else:
            return standard_date

    else:
        raise TypeError("standard_date must be one of 'str' or 'datetime.datetime'")


def is_date(text: Any, fmt='%Y-%m-%d') -> bool:
    """
    date 형식인지 체크
    """
    try:
        datetime.strptime(text, fmt)
        return True

    except ValueError as e:
        return False

    except Exception as e:
        return False


# About Environment variable
def get_env(var: str, default: str = None, prefix: str = None):
    """
    환경변수 parsing
    """
    return os.getenv(prefix + var) or default


def generate_fernet_key(save: bool = False, save_path: str = None) -> bytes:
    """
    암호화에 사용할 키 생성

    :param save: 저장 여부
    :param save_path: save True 시 저장할 경로
    :return: key
    """
    from cryptography.fernet import Fernet

    key: bytes = Fernet.generate_key()

    if save:
        assert save_path is not None, "save_path is not None when save is True"

        with open(save_path, 'w') as f:
            f.write(key.decode())

    return key


def encrypt(plain_str: str, fernet_key: bytes = None, key_path: str = None) -> bytes:
    """
    암호화

    :param plain_str: 암호화할 string
    :param fernet_key: key
    :param key_path: fernet_key None일 경우 key_path에서 읽음
    :return: 암호화된 bytes
    """
    from cryptography.fernet import Fernet

    if fernet_key is None:
        assert key_path is not None, "fernet_key와 key_path 가 입력되지 않았습니다"

        fernet_key: str = read_text(key_path)

    # only bytes enable
    if isinstance(fernet_key, str):
        fernet_key: bytes = fernet_key.encode()

    # get fernet
    cipher = Fernet(fernet_key)

    # encrypt
    return cipher.encrypt(plain_str.encode())


def decrypt(encoded_str: bytes, fernet_key: bytes = None, key_path: str = None) -> str:
    """
    복호화

    :param encoded_str: 암호화된 bytes
    :param fernet_key: key
    :param key_path: fernet_key None일 경우 key_path에서 읽음
    :return: 복호화된 string
    """
    from cryptography.fernet import Fernet

    if fernet_key is None:
        assert key_path is not None, "fernet_key와 key_path 가 입력되지 않았습니다"

        fernet_key: str = read_text(key_path)

    if isinstance(fernet_key, str):
        fernet_key: bytes = fernet_key.encode()

    cipher = Fernet(fernet_key)

    return cipher.decrypt(encoded_str).decode()


# About List & Dictionary
def find_indices(list_: list,
                 condition: Callable,
                 idx: int = None,
                 raise_if_null: bool = True):
    """
    list 내에서 condition을 만족시키는 item의 index 출력
    idx가 None일 경우 전체 리스트,
    idx가 숫자일 경우 condition 만족시키는 item 들 중 idx번째 item 반환
    """
    indices = [i for i, e in enumerate(list_) if condition(e)]

    if idx is None:
        return indices
    else:
        if len(indices) == 0:
            if raise_if_null:
                raise
            else:
                return None
        else:
            return indices[idx]


def find_item(lst: list, condition: Callable):
    """
    condition을 만족하는 item들 중 첫번째 item 반환
    """
    idx = find_indices(list_=lst, condition=condition, idx=0, raise_if_null=False)

    if idx is None:
        return None
    else:
        return lst[idx]


def remove_duplicates(data: List[Dict], key: str) -> List[Dict]:
    """
    List of Dict 에서 key에 대해서 중복 제거
    """
    return list({v[key]: v for v in data}.values())


def deep_update(d, u):
    """
    dictionary deep update
    """
    from collections import abc

    for k, v in u.items():
        if isinstance(v, abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


# About Memory
def get_memory_usage(as_msg: bool = False) -> Union[str, dict]:
    """
    :keyword buffers: buffer cache, 파일시스템의 메타데이터 관련 블록을 저장하는 캐시
    :keyword cached: page cache, 파일 내용을 저장하는 캐시
    :keyword active: buffers + cached
    """
    import psutil
    mem = psutil.virtual_memory()
    divide = 1024 ** 3

    total = f'{mem.total / divide:.1f}G'
    available = f'{mem.available / divide:.1f}G'
    percent = f'{mem.percent:.1f}%'
    used = f'{mem.used / divide:.1f}G'
    free = f'{mem.free / divide:.1f}G'
    active = f'{mem.active / divide:.1f}G'
    inactive = f'{mem.inactive / divide:.1f}G'
    buffers = f'{mem.buffers / divide:.1f}G'
    cached = f'{mem.cached / divide:.1f}G'
    shared = f'{mem.shared / divide:.1f}G'
    slab = f'{mem.slab / divide:.1f}G'

    if as_msg:
        return f'Total: {total}, Available: {available}, percent: {percent}, used: {used}, free: {free}, buffers: {buffers}, cached: {cached}'

    else:
        return {
            'total': total,
            'available': available,
            'percent': percent,
            'used': used,
            'free': free,
            'active': active,
            'inactive': inactive,
            'buffers': buffers,
            'cached': cached,
            'shared': shared,
            'slab': slab,
        }


def pause(cut_off: Union[float, int] = 70,
          interval: int = 60,
          timeout: int = None) -> bool:
    """
    메모리 사용률이 cut_off 를 넘을 경우 interval 만큼 기다림
    timeout을 설정할 경우 해당 시간이 넘으면 에러 발생
    """
    import time
    import psutil
    counter = 0

    while True:

        # 새롭게 계산
        mem = psutil.virtual_memory()

        # interval(초)마다 체크
        time.sleep(interval)

        counter += 1

        # 현재 사용중인 메모리 퍼센트가 cut_off 이하일 경우 실행
        if mem.percent < cut_off:
            print(f'# {counter}: 현재 메모리 percent {mem.percent} < {cut_off}: 시작')
            return True

        else:
            print(f'# {counter}: 현재 메모리 percent {mem.percent} >= {cut_off}: {interval}s 이후 메모리 확인을 다시 합니다.')

        if timeout is not None:
            if counter > timeout:
                raise TimeoutError(f"timeout({timeout}s) 시간동안 메모리가 {cut_off}를 초과했습니다")


def memory_safe(cut_off: Union[float, int] = 70,
                interval: int = 60,
                timeout: int = None):
    """
    cut_off: memory 임계점(넘어가면 delay
    interval: memory check interval
    timeout: None이 아닐 경우 timeout 시간 이후 raise TimeoutError
    """
    def decorator(f):
        from functools import wraps

        @wraps(f)
        def wrapper(*args, **kwargs):
            if pause(cut_off=cut_off,
                     interval=interval,
                     timeout=timeout):
                return f(*args, **kwargs)

        return wrapper

    return decorator


def runtime(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        import timeit
        from datetime import timedelta

        start = timeit.default_timer()
        result = f(*args, **kwargs)
        end = timeit.default_timer()

        time_str = str(timedelta(seconds=end - start))

        print(f'{f.__name__} : {time_str}')

        return result

    return wrapper


# ETC
def geometric_mean(value_list, weight_list=None):
    from tensorflow.keras import backend as K
    value_list = list(value_list)

    if len(value_list) > 1:
        if weight_list is None:
            weight_list = [1. / len(value_list)] * len(value_list)

        else:
            assert len(value_list) == len(weight_list), "'value_list' and 'weight_list' must be the same length"
            assert int(np.sum(weight_list)) == 1, "The sum of 'weight_list' must be 1"

        return np.prod([(value + K.epsilon()) ** weight for value, weight in zip(value_list, weight_list)])

    elif len(value_list) == 1:
        return value_list[0]

    else:
        raise ValueError("The length of 'value_list' is equal to 0")


def get_jupyter_id():
    import os
    import ipykernel

    connection_file = os.path.basename(ipykernel.get_connection_file())
    kernel_id = connection_file.split('-', 1)[1].split('.')[0]

    return kernel_id


def sql2python(item):
    from decimal import Decimal

    if isinstance(item, Decimal):
        return float(item)
    else:
        return item