"""
# Spark Context Loader

-

# 주의

- contextLoader의 read/write 사용시 s3 bucket_name이 맨 앞에 와야 함

"""
import os
from contextlib import contextmanager
from typing import List, Dict, Tuple
import atexit

from pyspark.sql import SparkSession
from pyspark import SparkConf, SparkContext

from utils.config import Default
from utils.const import *
from utils.tool import get_bucket_config

from .db import DbObj


# Yarn Manager 내에서 Spark Queue 세팅 가능
class SparkQueue:
    DEFAULT = 'default'


# aws s3 / minio bucket configuration -> spark hadoop config format
def s3_config_as_spark_form(profile_name: str) -> List[Tuple]:
    endpoint, bucket_name, access_key, secret_key = get_bucket_config(profile_name=profile_name)

    return [
        ('fs.s3a.access.key', access_key),
        ('fs.s3a.secret.key', secret_key),
        ('fs.s3a.endpoint', endpoint),
        ('fs.s3a.path.style.access', 'true'),
        ('fs.s3a.connection.ssl.enabled', 'false'),
        ('s3.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem'),
    ]


class SparkContextLoader:
    current_session = None

    def __init__(self,
                 app_name: str = 'pysparkApp',
                 job_group_id: str = None,
                 description: str = '',
                 master: str = 'local[10]',
                 deploy_mode: str = None,
                 spark_port: int = None,
                 driver_cores: int = 2,
                 driver_memory: str = '4g',
                 executor_cores: int = 2,
                 executor_memory: str = '4g',
                 num_executor: int = 0,
                 min_executor: int = 6,
                 max_executor: int = None,
                 queue: str = None,
                 spark_config: List[Dict] = None,
                 s3_profile_name: str = None,
                 hadoop_config: List[Dict] = None,
                 dynamic_allocation: bool = True):

        conf = SparkConf() \
            .setMaster(master) \
            .setAppName(app_name)

        # yarn mode
        if master == 'yarn':
            if not deploy_mode:
                deploy_mode = 'client'
            os.environ['PYSPARK_SUBMIT_ARGS'] = f'--master yarn --deploy-mode {deploy_mode} pyspark-shell'
            os.environ['HADOOP_CONF_DIR'] = '/app/bin/hadoop/etc/hadoop'
            os.environ['YARN_CONF_DIR'] = '/app/bin/hadoop/etc/hadoop'

        # else
        else:
            os.environ['PYSPARK_SUBMIT_ARGS'] = f'--master {master} pyspark-shell'

        conf_list = list()
        conf_list.append(('spark.driver.maxResultSize', '2g'))
        conf_list.append(('spark.driver.cores', driver_cores))
        conf_list.append(('spark.driver.memory', driver_memory))
        conf_list.append(('spark.executor.cores', executor_cores))
        conf_list.append(('spark.executor.memory', executor_memory))

        if num_executor > 0:
            conf_list.append(('spark.executor.instances', num_executor))

        if deploy_mode:
            conf_list.append(('spark.submit.deployMode', deploy_mode))

        if spark_port:
            conf_list.append(('spark.ui.port', str(spark_port)))

        conf_list.append(('spark.sql.broadcastTimeout', '3600'))
        conf_list.append(('spark.sql.parquet.writeLegacyFormat', 'true'))

        if dynamic_allocation:
            conf_list.append(('spark.shuffle.service.enabled', 'true'))
            conf_list.append(('spark.dynamicAllocation.enabled', 'true'))
            conf_list.append(('spark.dynamicAllocation.minExecutors', min_executor))

            if max_executor:
                conf_list.append(('spark.dynamicAllocation.maxExecutors', max_executor))

            # if num_executor > 0:
            #     conf_list.append(('spark.dynamicAllocation.maxExecutors', num_executor))

        else:
            conf_list.append(('spark.dynamicAllocation.enabled', 'false'))

        if queue:
            conf_list.append(('spark.yarn.queue', queue))

        conf_list.append(('spark.cleaner.referenceTracking.cleanCheckpoints', 'true'))

        conf = conf.setAll(conf_list)

        # spark config 추가
        if spark_config is not None:
            if isinstance(spark_config, dict):
                spark_config = list(spark_config.items())

            conf = conf.setAll(spark_config)

        self.spark = SparkSession.builder.config(conf=conf).getOrCreate()
        self.sc = self.spark.sparkContext

        # job group id 추가
        if job_group_id is None:
            self.job_group_id = app_name
        else:
            self.job_group_id = job_group_id

        self.sc.setJobGroup(groupId=self.job_group_id,
                            description=description,
                            interruptOnCancel=True)

        # checkpoint directory 추가
        self.sc.setCheckpointDir('/tmp/checkpoints')

        # get hadoop_config
        if hadoop_config is not None:
            if isinstance(hadoop_config, dict):
                hadoop_config = list(hadoop_config.items())

        # get s3 bucket profile
        if s3_profile_name is not None:
            hadoop_config += s3_config_as_spark_form(s3_profile_name)

        # set hadoop config
        for key, value in hadoop_config:
            self.sc._jsc.hadoopConfiguration().set(key, value)

        # python 하나에 한개의 spark context
        SparkContextLoader.current_session = self

        print(f'Start Spark Session: {self}')

        self.cached_dfs = []

    @property
    def sc(self) -> SparkContext:
        return self._sc

    @sc.setter
    def sc(self, sc: SparkContext):
        self._sc = sc

    @property
    def spark(self) -> SparkSession:
        return self._spark

    @spark.setter
    def spark(self, spark: SparkSession):
        self._spark = spark

    def stop_context(self):
        print(f'Stop Spark Session: {self}')
        self.sc.cancelJobGroup(self.job_group_id)
        self.clear_cache()
        self.sc.stop()
        SparkContextLoader.current_session = None

    def cache(self, df):
        cached_df = df.cache()
        self.cached_dfs.append(cached_df)
        return cached_df

    def as_view(self,
                df,
                table_name: str,
                cache: bool = False,
                checkpoint: bool = False):

        if checkpoint:
            df.checkpoint()

        elif cache:
            df = df.cache()

            self.cached_dfs.append(df)

        df.createOrReplaceTempView(table_name)

        return df

    def drop_temp_view(self, *table_names: str):
        for table_name in table_names:
            self.spark.catalog.uncacheTable(table_name)
            self.spark.catalog.dropGlobalTempView(table_name)
            self.spark.catalog.dropTempView(table_name)

    def clear_cache(self):
        for cached_df in self.cached_dfs:
            cached_df.unpersist()
            self.cached_dfs.remove(cached_df)

        for (i, rdd) in self.sc._jsc.getPersistentRDDs().items():
            rdd.unpersist()
            print(f"Unpersisted {i} rdd")

        self.spark.catalog.clearCache()

    def __del__(self):
        self.stop_context()

    def read(self,
             path: str,
             encoding: str = Encoding.UTF8,
             file_format: str = Default.FileFormat,
             sep: str = Default.Delimiter,
             file_system: str = FileSystem.MINIO):

        if file_system == FileSystem.MINIO:
            prefix = 's3a://'

        elif file_system == FileSystem.FILE:
            prefix = 'file://'

        elif file_system == FileSystem.HDFS:
            prefix = 'hdfs://'

        else:
            prefix = ''

        if isinstance(path, str):
            if file_system == FileSystem.FILE:
                path = os.path.abspath(path)

            local_path = f'{prefix}{path}'

        elif isinstance(path, list):
            if file_system == FileSystem.FILE:
                local_path = [f'{prefix}{os.path.abspath(_path)}' for _path in path]
            else:
                local_path = [f'{prefix}{_path}' for _path in path]

        else:
            raise ValueError('check path param')

        if file_format == FileFormat.CSV:
            if isinstance(path, str):
                return self.spark.read.csv(local_path, header=True, encoding=encoding, sep=sep)
            elif isinstance(path, list):
                return self.spark.read.csv(*local_path, header=True, encoding=encoding, sep=sep)

        elif file_format == FileFormat.PARQUET:
            if isinstance(path, str):
                return self.spark.read.parquet(local_path, encoding=encoding)
            elif isinstance(path, list):
                return self.spark.read.parquet(*local_path, encoding=encoding)

    @staticmethod
    def write(df,
              path: str,
              coalesce: int = None,
              overwrite: bool = True,
              header: bool = True,
              encoding: str = Encoding.UTF8,
              file_format: str = Default.FileFormat,
              file_system: str = FileSystem.MINIO):

        if file_system == FileSystem.MINIO:
            prefix = 's3a://'
            local_path = f'{prefix}{path}'

        elif file_system == FileSystem.FILE:
            prefix = 'file://'
            local_path = f'{prefix}{os.path.abspath(path)}'

        elif file_system == FileSystem.HDFS:
            prefix = 'hdfs://'
            local_path = f'{prefix}{path}'

        else:
            prefix = ''
            local_path = f'{prefix}{path}'

        if coalesce is not None:
            df = df.coalesce(coalesce)

        df = df.write

        if overwrite:
            df = df.mode('overwrite')

        if header:
            df = df.option('header', 'true')

        if encoding.lower() in [Encoding.UTF8, Encoding.UTF_8]:
            df = df.option('encoding', 'utf-8')

        if file_format == FileFormat.CSV:
            df.csv(local_path)

        elif file_format == FileFormat.PARQUET:
            df.parquet(local_path)

    def load_from_db(self,
                     table_name: str,
                     schema: str = None,
                     table_alias: str = None,
                     db_obj: DbObj = None,
                     db_config: dict = None,
                     use_schema: bool = True):
        """
        !!!사용시 주의!!!!
        테이블
        작은 테이블이면 상관 없지만 큰 테이블일 경우 메모리 에러 발생 가능

        :param table_name: [str] table명
        :param schema: [str] schema명
        :param table_alias: [str] createOrReplaceTempView(table_alias)
        :param db_obj: [DbObj] db_connector 내의 Db object
        :param db_config: [dict] db_config
        :param use_schema: [bool] schema 사용 여부
        :return Spark dataframe
        """
        assert db_obj is not None or db_config is not None

        if db_obj is not None:
            db_config = db_obj.db_config

        driver = db_config[DbConn.DRIVER]
        host = db_config[DbConn.HOST]
        port = db_config[DbConn.PORT]
        database = db_config[DbConn.DATABASE]
        user = db_config[DbConn.USER]
        password = db_config[DbConn.PASSWORD]

        if driver == DbDriver.POSTGRES:

            if use_schema:
                assert schema is not None or schema != ''

                # 미리 저장된 schema 로드
                if schema is None:
                    schema = db_config[DbConn.SCHEMA]

                table_name = f'{schema}.{table_name}'

            df = self.spark.read.format('jdbc') \
                .option('url', f'jdbc:postgresql://{host}:{port}/{database}') \
                .option('user', user) \
                .option('password', password) \
                .option('driver', 'org.postgresql.Driver') \
                .option('stringtype', 'unspecified') \
                .option('dbtable', table_name) \
                .load()

        elif driver == DbDriver.MYSQL:
            df = self.spark.read.format('jdbc') \
                .option('url', f'jdbc:mysql://{host}:{port}/{database}') \
                .option('user', user) \
                .option('password', password) \
                .option('driver', 'com.mysql.jdbc.Driver') \
                .option('dbtable', table_name) \
                .load()

        elif driver == DbDriver.ORACLE:

            if use_schema:
                assert schema is not None or schema != ''

                # 미리 저장된 schema 로드
                if schema is None:
                    schema = db_config[DbConn.SCHEMA]

                table_name = f'{schema}.{table_name}'

            df = self.spark.read.format('jdbc') \
                .option('url', f'jdbc:oracle:thin:@{host}:{port}:{database}') \
                .option('user', user) \
                .option('password', password) \
                .option('driver', 'oracle.jdbc.driver.OracleDriver') \
                .option('dbtable', table_name) \
                .load()

        else:
            raise TypeError

        if table_alias:
            df.createOrReplaceTempView(table_alias)

        return df

    def save_to_db(self,
                   df,
                   table_name: str,
                   schema: str = None,
                   db_obj: DbObj = None,
                   db_config: dict = None,
                   mode: str = 'append',
                   truncate: bool = False):
        """
        mode='append': 행 추가
        mode='overwrite': truncate and insert
        mode='ignore': create table if not exists 와 동일

        :param df: [Spark DataFrame] 테이블로 전달할 spark dataframe
        :param table_name: [str] table명
        :param db_obj: [DbObj] db_connector 내의 Db object
        :param db_config: [dict] db_config
        :param mode: [str] append/overwrite/ignore/errorifexists
        """

        assert db_obj is not None or db_config is not None

        if db_obj is not None:
            db_config = db_obj.db_config

        driver = db_config[DbConn.DRIVER]
        host = db_config[DbConn.HOST]
        port = db_config[DbConn.PORT]
        database = db_config[DbConn.DATABASE]
        user = db_config[DbConn.USER]
        password = db_config[DbConn.PASSWORD]

        if driver == DbDriver.POSTGRES:
            if schema is None:
                schema = db_config[DbConn.SCHEMA]

            table_name = f'{schema}.{table_name}'

            properties = {
                'user': user,
                'password': password,
                'stringtype': 'unspecified',
                'truncate': 'true' if truncate else 'false'
            }

            url = f'jdbc:postgresql://{host}:{port}/{database}'

            print(f'url: {url} - table_name: {table_name} - mode: {mode}')
            df.write \
                .jdbc(url=url,
                      table=table_name,
                      mode=mode,
                      properties=properties)

        elif driver == DbDriver.MYSQL:
            properties = {
                'user': user,
                'password': password,
                'truncate': 'true' if truncate else 'false'
            }

            url = f'jdbc:mysql://{host}:{port}/{database}'

            # .option('driver', 'com.mysql.jdbc.Driver')
            print(f'url: {url} - table_name: {table_name} - mode: {mode}')
            df.write \
                .jdbc(url=url,
                      table=table_name,
                      mode=mode,
                      properties=properties)

        elif driver == DbDriver.ORACLE:
            if schema is None:
                schema = db_config[DbConn.SCHEMA]

            table_name = f'{schema}.{table_name}'

            properties = {
                'user': user,
                'password': password,
                'truncate': 'true' if truncate else 'false'
            }

            url = f'jdbc:oracle:thin:@{host}:{port}:{database}'

            print(f'url: {url} - table_name: {table_name} - mode: {mode}')
            df.write \
                .jdbc(url=url,
                      table=table_name,
                      mode=mode,
                      properties=properties)

        else:
            raise TypeError

        print(f'# successfully written {table_name}: {mode}')


class LocalSCLoader(SparkContextLoader):
    def __init__(self,
                 app_name: str,
                 spark_port: int = 8100):
        super().__init__(app_name=app_name,
                         spark_port=spark_port,
                         master='local[8]',
                         driver_cores=2,
                         driver_memory='4g',
                         executor_cores=2,
                         executor_memory='4g',
                         dynamic_allocation=True)


class YarnSCLoader(SparkContextLoader):
    def __init__(self,
                 app_name: str,
                 num_executor: int = 0):
        super().__init__(app_name=app_name,
                         master='yarn',
                         deploy_mode='client',
                         executor_cores=2,
                         executor_memory='4g',
                         num_executor=num_executor,
                         queue=SparkQueue.DEFAULT,
                         dynamic_allocation=True)


class BigYarnSCLoader(SparkContextLoader):
    """
    - core: 2 / memory: 3g / num_executor 8 ~ 9
    - core: 4 / memory: 6g / num_executor 4
    """

    def __init__(self,
                 app_name: str):
        super().__init__(app_name=app_name,
                         master='yarn',
                         deploy_mode='client',
                         executor_cores=2,
                         executor_memory='3584m',
                         min_executor=4,
                         max_executor=8,
                         queue=SparkQueue.DEFAULT,
                         dynamic_allocation=True)


@contextmanager
def local_spark_session(app_name: str, spark_port: int) -> LocalSCLoader:
    session = LocalSCLoader(app_name=app_name,
                            spark_port=spark_port)

    try:
        yield session

    except Exception as e:
        raise e

    finally:
        del session


@contextmanager
def small_yarn_session(app_name: str) -> YarnSCLoader:
    session = YarnSCLoader(app_name=app_name)

    try:
        yield session

    except Exception as e:
        raise e

    finally:
        del session


@contextmanager
def big_yarn_session(app_name: str) -> BigYarnSCLoader:
    session = BigYarnSCLoader(app_name=app_name)

    try:
        yield session

    except Exception as e:
        raise e

    finally:
        del session


def release_spark():
    if SparkContextLoader.current_session is not None:
        SparkContextLoader.current_session.stop_context()


atexit.register(release_spark)
