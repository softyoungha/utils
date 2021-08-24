"""
프로젝트 내 상수 목록(Key/Value)
"""


"""
########################################################################################################################
                                                        About IO
########################################################################################################################
"""


class IOEngine:
    pandas = 'pandas'
    dask = 'dask'


class ParquetEngine:
    fastparquet = 'fastparquet'
    pyarrow = 'pyarrow'


class FileSystem:
    S3 = 's3'
    MINIO = 'minio'
    FILE = 'file'
    HDFS = 'hdfs'


class FileFormat:
    CSV = 'csv'
    PARQUET = 'parquet'
    JSON = 'json'


class Encoding:
    UTF8 = 'utf8'
    UTF_8 = 'utf-8'
    CP949 = 'CP949'


class Delimiter:
    COMMA = ','
    PIPE = '|'


class DType:
    BYTE = 'byte'
    STR = 'str'
    INT = 'int'
    FLOAT = 'float'
    LIST = 'list'
    TUPLE = 'tuple'
    DICT = 'dict'
    SET = 'set'
    INT32 = 'int32'
    INT64 = 'int64'
    FLOAT64 = 'float64'
    DATE = 'date'
    DATETIME = 'datetime'
    OBJECT = 'object'
    CALLABLE = 'callable'


"""
########################################################################################################################
                                                        About DB Connection
########################################################################################################################
"""


class DbDriver:
    POSTGRES = 'postgres'
    MYSQL = 'mysql'
    ORACLE = 'oracle'


class DbConn:
    HOST = 'host'
    PORT = 'port'
    USER = 'user'
    PASSWORD = 'password'
    PASSWORD_ENV = 'password_env'
    PASSWORD_FILE = 'password_file'
    DATABASE = 'database'
    DRIVER = 'driver'
    SCHEMA = 'schema'
    DNS_TNS = 'dns_tns'


class DbProfile:
    MART = 'mart'
    BACKEND = 'backend'
    ORIGIN = 'origin'


class DbSchema:
    PUBLIC = 'public'


class RedisConn:
    HOST = 'host'
    PORT = 'port'
    DB = 'db'
    PASSWORD = 'password'
    PASSWORD_ENV = 'password_env'


class AwsConn:
    ENDPOINT = 'endpoint'
    ACCESS_KEY = 'access_key'
    ACCESS_KEY_ENV = 'access_key_env'
    ACCESS_KEY_FILE = 'access_key_file'
    SECRET_KEY = 'secret_key'
    SECRET_KEY_ENV = 'secret_key_env'
    SECRET_KEY_FILE = 'secret_key_file'
    BUCKET_NAME = 'bucket_name'


class ApiConn:
    ENDPOINT = 'endpoint'
    DEFAULT_HEADERS = 'default_headers'
    DEFAULT_COOKIES = 'default_cookies'
