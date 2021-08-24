# -*- encoding: utf8 -*
"""


"""
import logging
from typing import List, Any, Union, Dict
from io import StringIO, BytesIO
import pandas as pd
import json

from sqlalchemy import Table
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.engine.base import Engine
from contextlib import contextmanager

from utils.config import Default
from utils.const import *
from utils.tool import get_secret


class DbObj:
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.base: DeclarativeMeta = declarative_base()
        self.tables = self.base.metadata.tables
        self.engine = None

    @property
    def profile_name(self):
        return self._profile_name

    @profile_name.setter
    def profile_name(self, profile_name):
        self._profile_name = profile_name

    @property
    def base(self) -> DeclarativeMeta:
        return self._base

    @base.setter
    def base(self, base: DeclarativeMeta):
        self._base = base

    @property
    def db_config(self) -> dict:
        from utils.config import DB_CONFIG
        
        # get config by profile name
        db_config = DB_CONFIG(self.profile_name)

        if db_config is None:
            raise KeyError(f"해당 profile_name을 찾을 수 없습니다: {self.profile_name}")

        # get password
        password = get_secret(db_config.get(DbConn.PASSWORD),
                              db_config.get(DbConn.PASSWORD_ENV),
                              db_config.get(DbConn.PASSWORD_FILE))

        # db_config에 password 추가
        db_config.update({DbConn.PASSWORD: password})
        
        return db_config

    @property
    def database(self) -> str:
        return self.db_config['database']

    @property
    def schema(self) -> str:
        return self.db_config.get('schema') or self.database

    @property
    def engine(self) -> Engine:
        return self._engine

    @engine.setter
    def engine(self, engine: Engine):
        self._engine = engine

    @property
    def is_engine_exist(self):
        return self.engine is not None

    def create_engine(self) -> Engine:
        if not self.is_engine_exist:
            return create_sqlalchemy_engine(db_obj=self)


def register_json_to_psycopg2():
    from psycopg2.extras import Json
    from psycopg2.extensions import register_adapter

    register_adapter(dict, Json)


def create_sqlalchemy_engine(db_obj: DbObj = None, db_config: dict = None):
    from sqlalchemy import create_engine

    if db_obj is not None:
        db_config = db_obj.db_config

    else:
        if db_config is None:
            raise ValueError('set inputs')

    driver = db_config[DbConn.DRIVER]
    user = db_config[DbConn.USER]
    password = db_config[DbConn.PASSWORD]

    host = db_config.get(DbConn.HOST)
    port = db_config.get(DbConn.PORT)
    database = db_config.get(DbConn.DATABASE)
    schema = db_config.get(DbConn.SCHEMA)

    engine_config = {}

    encoding = 'utf-8'

    if driver in (DbDriver.MYSQL,):
        import pymysql

        pymysql.install_as_MySQLdb()

        connect_str = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'

    elif driver in (DbDriver.POSTGRES,):
        connect_str = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{schema}' \
                      f'?database={database}'
        engine_config['client_encoding'] = 'utf8'
        engine_config['json_serializer'] = lambda x: json.dumps(x, ensure_ascii=False)
        engine_config['connect_args'] = {'options': '-c lock_timeout=3000'}

    elif driver in (DbDriver.ORACLE,):
        import cx_Oracle

        dns_tns = db_config.get(DbConn.DNS_TNS)
        connect_str = f'oracle+cx_oracle://{user}:{password}@{dns_tns}'
        engine_config['max_identifier_length'] = 128

    else:
        raise ModuleNotFoundError('driver is wrong')

    if Default.LogLevel < logging.INFO:
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        echo = True

    else:
        echo = False

    engine = create_engine(connect_str,
                           echo=echo,
                           encoding=encoding,
                           pool_size=16,
                           max_overflow=5,
                           pool_recycle=3600,
                           pool_pre_ping=True,
                           **engine_config)

    if db_obj:
        db_obj.engine = engine

    return engine


def create_session(engine: Engine,
                   autoflush: bool = True,
                   autocommit: bool = False,
                   expire_on_commit: bool = True) -> Session:
    return sessionmaker(bind=engine,
                        autocommit=autocommit,
                        autoflush=autoflush,
                        expire_on_commit=expire_on_commit)()


@contextmanager
def scoped_session(engine: Engine, expire_on_commit: bool = True) -> Session:
    session = sessionmaker(bind=engine,
                           expire_on_commit=expire_on_commit)()

    try:
        if Default.LogLevel < logging.INFO:
            print(f'{engine}: CREATED')

        yield session

        if Default.LogLevel < logging.INFO:
            print(f'{engine}: COMMIT')

        session.commit()

    except:
        if Default.LogLevel < logging.INFO:
            print(f'{engine}: ROLLBACK')

        session.rollback()
        raise

    finally:
        if Default.LogLevel < logging.INFO:
            print(f'{engine}: CLOSED')

        session.close()


def create_all_tables(db_obj: DbObj):
    from sqlalchemy_utils import database_exists, create_database

    if not db_obj.is_engine_exist:
        engine = create_sqlalchemy_engine(db_obj=db_obj)
    else:
        engine = db_obj.engine

    if str(engine.url).startswith('postgresql'):
        engine_url = str(engine.url).replace('postgresql', 'postgres')

    else:
        engine_url = str(engine.url)

    print(engine.url)
    if not database_exists(engine_url):
        create_database(engine_url)
        print(f'# CREATE DATABASE: {repr(engine_url)}')

    create_table(db_obj=db_obj, table_names=None)


def create_table(db_obj: DbObj, table_names: List[str] = None):
    if table_names is None:
        table_objs = [table_obj for table_obj in db_obj.tables.values()]
        table_names = [table_name for table_name in db_obj.tables.keys()]
    else:
        table_objs = [table_obj
                      for table_name, table_obj in db_obj.tables.items()
                      if (table_name.split('.')[1] if '.' in table_name else table_name) in table_names]

    db_obj.base.metadata.create_all(bind=db_obj.engine,
                                    tables=table_objs,
                                    checkfirst=True)
    print(f'# CREATE ALL: ')
    for table in table_names:
        print(f'\t\t\t{table}')


def drop_all_tables(db_obj: DbObj):
    from sqlalchemy_utils import database_exists

    if not db_obj.is_engine_exist:
        engine = create_sqlalchemy_engine(db_obj=db_obj)
    else:
        engine = db_obj.engine

    if str(engine.url).startswith('postgresql'):
        engine_url = str(engine.url).replace('postgresql', 'postgres')

    else:
        engine_url = str(engine.url)

    if not database_exists(engine_url):
        print(f"# There is no '{engine_url}'")

    drop_table(db_obj=db_obj, table_names=None)


def drop_table(db_obj: DbObj, table_names: List[str] = None):
    if table_names is None:
        table_objs = [table_obj for table_obj in db_obj.tables.values()]
        table_names = [table_name for table_name in db_obj.tables.keys()]
    else:
        table_objs = [table_obj
                      for table_name, table_obj in db_obj.tables.items()
                      if (table_name.split('.')[1] if '.' in table_name else table_name) in table_names]

    db_obj.base.metadata.drop_all(bind=db_obj.engine,
                                  tables=table_objs,
                                  checkfirst=True)
    print(f'# CREATE ALL: ')
    for table in table_names:
        print(f'\t\t\t{table}')


def truncate_all_tables(db_obj: DbObj):
    if not db_obj.is_engine_exist:
        engine = create_sqlalchemy_engine(db_obj=db_obj)
    else:
        engine = db_obj.engine

    table_list = [table_name for table_name in db_obj.tables.keys()
                  if (table_name.split('.')[1] if '.' in table_name else table_name)[:2] not in ('v_', 'V_')]

    with scoped_session(engine=engine) as session:
        for table in table_list:
            session.execute(f'TRUNCATE TABLE {table}')
            print(f'# TRUNCATE: {table}')


def truncate_table(db_obj: DbObj, table_name: str):
    with scoped_session(engine=db_obj.engine) as session:
        session.execute(f'TRUNCATE TABLE {table_name}')
        print(f'# TRUNCATE: {table_name}')


def rows_as_dict(rows, table_obj):
    from sqlalchemy import Integer, Numeric

    columns = table_obj.__table__.columns

    parsed_rows = []

    for row in rows:
        _dict = row.__dict__.copy()

        if _dict.get('_sa_instance_state'):
            _dict.pop('_sa_instance_state')

        for column in columns:
            colname = column.name
            coltype = column.type
            value = _dict[colname]

            if value is None:
                continue

            elif isinstance(coltype, Integer):
                _dict[colname] = int(value)

            elif isinstance(coltype, Numeric):
                _dict[colname] = float(value)

            else:
                continue

        parsed_rows.append(_dict)

    return parsed_rows


def df_from_db(query: str,
               db_obj: DbObj,
               save: bool = False,
               save_path: str = None,
               index: bool = False,
               file_format: str = Default.FileFormat) -> pd.DataFrame:
    from utils.tool import to_file

    if not db_obj.is_engine_exist:
        engine = create_sqlalchemy_engine(db_obj=db_obj)
    else:
        engine = db_obj.engine

    try:
        df = pd.read_sql(query, con=engine)

    except:
        raise

    if save:
        if save_path is not None:
            to_file(df, save_path, encoding='utf8', index=index, file_format=file_format)

    return df


def df_to_db(df: pd.DataFrame,
             table: Union[str, DeclarativeMeta],
             db_obj: DbObj,
             if_exists: str = 'append',
             index: bool = False,
             index_label: bool = None):

    if not db_obj.is_engine_exist:
        engine = create_sqlalchemy_engine(db_obj=db_obj)
    else:
        engine = db_obj.engine

    if isinstance(table, str):
        table_name = table
        dtype = None

    elif isinstance(table, DeclarativeMeta):
        table_name = table.__table__.name
        dtype = {
            column.name: column.type
            for column in table.__table__.columns
        }

    else:
        raise TypeError("Invalid 'table' input")

    with engine.connect() as conn:
        df.to_sql(name=table_name,
                  con=engine,
                  dtype=dtype,
                  if_exists=if_exists,
                  index=index,
                  index_label=index_label,
                  method='multi')


def file_to_postgres(file_obj: Union[StringIO, BytesIO],
                     table_name: str,
                     db_obj: DbObj = None,
                     db_config: dict = None,
                     null: str = None,
                     sep: str = None,
                     columns: list = None):
    """
    file obj(csv-like) -> 대량 db insert 시 사용
    row가 적을 경우 더 느릴 수 있음

    :param file_obj: [io.StringIO] 파일 오브젝트
    :param table_name: [str] 테이블명
    :param db_obj: [DbObj]
    :param db_config: [dict] db config(DbConn key 모두 포함)
    :param null: [str, default "None"] -> None String일 경우 null로 치환
    :param sep: [sep, default ","] separator
    :param columns: [list or tuple] insert할 column 리스트
    :return: None
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if db_obj:
        db_config = db_obj.db_config

    if db_config is None:
        raise AssertionError('db_config must be in')

    if null is None:
        null = 'None'

    if sep is None:
        sep = ','

    try:
        conn = psycopg2.connect(host=db_config[DbConn.HOST],
                                port=db_config[DbConn.PORT],
                                user=db_config[DbConn.USER],
                                password=db_config[DbConn.PASSWORD],
                                database=db_config[DbConn.DATABASE])

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.copy_from(file_obj,
                             table_name,
                             null=null,
                             sep=sep,
                             columns=columns)

        conn.commit()

    except Exception as e:
        print(f'unexpected error occurs: {type(e)}, {e}')
        raise e

    finally:
        if conn is not None:
            conn.close()


def df_to_postgres(df: pd.DataFrame,
                   table_name: str,
                   db_obj: DbObj = None,
                   db_config: dict = None,
                   index: bool = False,
                   columns: list = None,
                   chunk: int = None,
                   null: str = None,
                   **kwargs):
    """
    [POSTGRES only]
    데이터프레임을 StringIO file buffer로 만들어서 postgres 대량 insert

    - pandas.to_csv quoting=3 고정
    - sep='|' 고정
    - file_obj 로 변환 후 double quotes -> single quote 으로 변경

    :param df: [pd.DataFrame] 데이터프레임
    :param table_name: [str] 테이블명
    :param db_obj: [DbObj]
    :param db_config: [dict] db config(DbConn key 모두 포함)
    :param null: [str, default "None"] -> None String일 경우 null로 치환
    :param index: [bool, default False] dataframe index 를 포함할지 여부(True시 column으로 변환)
    :param columns: [list or tuple] insert할 column 리스트
    :param chunk: [int, default None] 사이즈가 클 경우 chunk만큼씩 잘라서 insert
    :param kwargs: pandas to_csv 참조
    :return:
    """
    from utils.const import DType
    from utils.tool import df_to_fileobj, print_now
    import time

    if chunk is None:
        file_obj = df_to_fileobj(df,
                                 buffer_type=DType.STR,
                                 index=index,
                                 quoting=3,
                                 sep='|',
                                 file_format=FileFormat.CSV,
                                 header=False,
                                 **kwargs)

        # text = file_obj.getvalue()
        # text = text.replace("\'{", "\{").replace('}\'', "\}").replace("\'", "\"")
        # file_obj.seek(0)
        # file_obj.write(text)
        # file_obj.seek(0)

        file_to_postgres(file_obj,
                         table_name=table_name,
                         db_obj=db_obj,
                         db_config=db_config,
                         null=null,
                         sep='|',
                         columns=columns)

        file_obj.close()

        return True

    else:
        length = df.shape[0]

        start = time.time()
        print(f'# DataFrame length: {length}', print_now(hour=True, minute=True, second=True))

        if chunk > length:
            print(f'## all, {length} < {chunk}')
            df_to_postgres(df,
                           table_name=table_name,
                           db_obj=db_obj,
                           db_config=db_config,
                           index=index,
                           columns=columns,
                           chunk=None,
                           **kwargs)

            return True

        print(f'## do chunk: {length // chunk}')

        for i in range(0, length, chunk):

            # 마지막 iteration
            if i // chunk == length // chunk:
                target_df = df.iloc[i:length]

            # chunk만큼 자르기
            else:
                target_df = df.iloc[i:i + chunk]

            success = df_to_postgres(target_df,
                                     table_name=table_name,
                                     db_obj=db_obj,
                                     db_config=db_config,
                                     index=index,
                                     columns=columns,
                                     chunk=None,
                                     **kwargs)

            print(f'### {i}th chunk')

            if not success:
                break

        end = time.time()
        print(print_now(hour=True, minute=True, second=True), f'# all done, elapsed time: {end - start}')

        return True


def df_to_insert_sql_mysql(df: pd.DataFrame,
                           table_name: str,
                           db_obj: DbObj = None,
                           execute: bool = False,
                           update_duplicates: bool = False,
                           update_columns: List[str] = None):
    """
    [MYSQL only]
    데이터프레임 -> insert sql
    execute True일 때 db_obj.engine으로 해당 db로 insert

    :param df: [pd.DataFrame] 대상 데이터프레임
    :param table_name: [str] 테이블명(스키마가 존재할 경우 '.'으로 연결)
    :param db_obj: [DbObj] default None, 대상 데이터베이스
    :param execute: [bool] 바로 실행
    :param update_duplicates: [bool] 중복 업데이트할 때
    :param update_columns: [List[str]] 중복 업데이트할 대상 칼럼
    :return: [str] 생성된 쿼리
    """
    if db_obj.db_config[DbConn.DRIVER] == DbDriver.MYSQL:

        # parse dtypes: str -> '{value}', json parsing
        def parse_dtype(value):
            if isinstance(value, dict) or isinstance(value, list):
                return json.dumps(value, ensure_ascii=False)
            else:
                return value

        # join: ('asdf', 123, 'foo', 3.44)
        values = df.to_dict('records')
        for row in values:
            for column in df.columns:
                row[column] = parse_dtype(row[column])

        columns_table_form = '`, `'.join(df.columns.tolist())
        columns_value_form = ', '.join([f':{column}' for column in df.columns])

        # insert query
        query = f"""
INSERT INTO {table_name}(`{columns_table_form}`)
VALUES  ({columns_value_form}) """

        if update_duplicates:
            assert update_columns is not None, 'update_columns를 특정해주세요'

            joined_update_columns = ',\n\t\t'.join([f"{column} = new.{column}" for column in update_columns])

            query += f"""
AS new
ON DUPLICATE KEY 
UPDATE  {joined_update_columns}"""

        print(query)

        if execute:
            assert db_obj is not None, 'db_obj를 입력하세요'

            with scoped_session(engine=db_obj.engine) as session:
                session.execute(query, values)

        return query, values

    else:
        raise TypeError('Mysql DB만 가능합니다.')
