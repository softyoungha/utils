from typing import Union, Dict, List
from io import BytesIO
import pandas as pd
import json
import logging

from minio import Minio
from utils.config import Default
from utils.const import FileFormat, ParquetEngine, DType
from utils.tool import df_to_fileobj


class MinioClient:
    def __init__(self,
                 endpoint: str,
                 access_key: str,
                 secret_key: str,
                 secure: bool = False,
                 bucket_name: str = None):
        self.endpoint = endpoint
        self.client = Minio(endpoint=endpoint,
                            access_key=access_key,
                            secret_key=secret_key,
                            secure=secure)
        self.bucket_name = bucket_name

    @property
    def client(self) -> Minio:
        return self._client

    @client.setter
    def client(self, client: Minio):
        self._client = client

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @endpoint.setter
    def endpoint(self, endpoint: str):
        self._endpoint = endpoint

    @property
    def bucket_name(self) -> str:
        return self._bucket_name

    @bucket_name.setter
    def bucket_name(self, bucket_name: str):
        self._bucket_name = bucket_name

    def read_obj(self,
                 file_path: str,
                 file_format: str = FileFormat.PARQUET,
                 verbose: int = None,
                 **kwargs) -> pd.DataFrame:
        """
        read file in minio

        :param file_path: 파일 경로
        :param file_format: 파일형식(기본: PARQUET)
        :param verbose: 0보다 크면 path list 출력
        :param kwargs: pandas read_csv/read_parqeut 기본 params
        :return: [pd.DataFrame]
        """

        file_paths = [obj.object_name
                      for obj in self.list_objs(prefix=file_path, recursive=True)
                      if obj.object_name.split('/')[-1] != '_SUCCESS']

        if len(file_paths) == 0:
            raise FileNotFoundError(f"There is no such prefix '{file_path}' in minio storage")

        elif len(file_paths) == 1:
            if file_paths[0] == file_path:
                if Default.LogLevel <= logging.INFO:
                    print(f"# Use '{file_path}' as direct file path")

            else:
                if Default.LogLevel < logging.INFO:
                    print(f"# Use '{file_path}' as directory path")

        else:
            if Default.LogLevel < logging.INFO:
                print(f"# Use '{file_path}' as directory path")

        if verbose is None:
            if Default.LogLevel < logging.INFO:
                verbose = 1
            else:
                verbose = 0

        if verbose > 0:
            print('use:')
            for _file_path in file_paths:
                print(f'\t{_file_path}')

        dfs = []

        for _file_path in file_paths:
            buffer = BytesIO()

            response = self.client.get_object(bucket_name=self.bucket_name,
                                              object_name=_file_path)

            buffer.write(response.data)

            if file_format == FileFormat.CSV:
                buffer.seek(0)
                df = pd.read_csv(buffer, **kwargs)

            elif file_format == FileFormat.PARQUET:
                df = pd.read_parquet(buffer, engine=ParquetEngine.pyarrow, **kwargs)

            dfs.append(df)

            del df, buffer

        df = pd.concat(dfs, axis=0, ignore_index=True)

        del dfs

        return df

    def read_json_obj(self,
                      file_path: str,
                      **json_kwargs) -> dict:
        """
        read json in minio

        :param file_path: 파일 경로
        :param json_kwargs: json.load kwargs
        :return: [dict]
        """
        buffer = BytesIO()

        response = self.client.get_object(bucket_name=self.bucket_name,
                                          object_name=file_path)
        buffer.write(response.data)
        buffer.seek(0)

        return json.load(buffer, **json_kwargs)

    def download_obj(self,
                     object_name: str,
                     file_path: str):
        """
        download file in minio

        :param object_name: download 대상
        :param file_path: 다운로드할 파일 경로
        :return: [bool]
        """

        try:
            self.client.fget_object(object_name=object_name,
                                    file_path=file_path,
                                    bucket_name=self.bucket_name)
            return True

        except Exception as e:
            raise e

    def copy_obj(self,
                 source: str,
                 object_name: str,
                 src_bucket_name: str = None,
                 skip_if_not_exists: bool = True):
        """
        copy file(1개)

        :param source: source file path
        :param object_name: destination file path
        :param src_bucket_name: source file의 버킷명(기본: MARS_DEFAULT_BUCKET)
        :return: [str] copy 완료된 파일 path
        """
        from minio.commonconfig import CopySource

        if skip_if_not_exists:
            paths = [obj.object_name for obj in self.list_objs(prefix=source)]

            if len(paths) == 0:
                return source, 'Not exists. Skip!'
            else:
                if paths[0] != source:
                    return source, 'Not exists. Skip!'

        if src_bucket_name is None:
            src_bucket_name = self.bucket_name

        try:
            result = self.client.copy_object(bucket_name=self.bucket_name,
                                             object_name=object_name,
                                             source=CopySource(bucket_name=src_bucket_name,
                                                               object_name=source))

            return result.object_name, 'Success'

        except Exception as e:
            raise e

    def upload_df(self,
                  df: pd.DataFrame,
                  object_name: str,
                  **pd_kwargs):
        """
        upload dataframe

        :param df: 업로드할 dataframe
        :param object_name: 업로드될 file path
        :return: [str] upload 완료된 파일 path
        """
        buffer = df_to_fileobj(df,
                               buffer_type=DType.BYTE,
                               **pd_kwargs)
        return self.upload_file_obj(data=buffer,
                                    object_name=object_name)

    def upload_file_obj(self,
                        data,
                        object_name: str):
        """
        upload object(file buffer)

        :param data: 업로드할 data
        :param object_name: 업로드될 file path
        :return: [str] upload 완료된 파일 path
        """
        try:
            result = self.client.put_object(bucket_name=self.bucket_name,
                                            object_name=object_name,
                                            data=data,
                                            length=data.getbuffer().nbytes)
            return result.object_name

        except Exception as e:
            raise e

    def upload_file(self,
                    file_path: str,
                    object_name: str,
                    file_format: str = FileFormat.CSV):
        """
        upload object(file buffer)

        :param file_path: 업로드할 로컬 FILE PATH
        :param object_name: 업로드될 file path
        :param file_format: 파일 포맷(기본: CSV)
        :return: [str] upload 완료된 파일 path
        """
        if file_format == FileFormat.CSV:
            content_type = 'application/csv'

        elif file_format == FileFormat.JSON:
            content_type = 'application/json'

        else:
            content_type = 'application/octet-stream'

        try:
            result = self.client.fput_object(bucket_name=self.bucket_name,
                                             object_name=object_name,
                                             file_path=file_path,
                                             content_type=content_type)
            return result.object_name

        except Exception as e:
            raise e

    def get_stat_obj(self,
                     object_name: str):
        """
        minio 내의 파일 상태 확인

        :param object_name: file path
        :return: file status
        """
        try:
            result = self.client.stat_object(bucket_name=self.bucket_name,
                                             object_name=object_name)
            return result

        except Exception as e:
            raise e

    def rm_obj(self,
               object_name: str):
        """
        minio 내 파일 삭제

        :param object_name: file path
        :param bucket_name: 버킷명(기본: MARS_DEFAULT_BUCKET)
        :return: [bool]
        """
        try:
            self.client.remove_object(bucket_name=self.bucket_name,
                                      object_name=object_name)

            return True
        except Exception as e:
            raise e

    def rm_objs(self,
                object_names: list):
        """
        minio 내 여러 파일 삭제

        :param object_names: [list of str] file paths
        :return: [list of error]
        """

        from minio.deleteobjects import DeleteObject

        if len(object_names) > 0:
            errors = self.client.remove_objects(bucket_name=self.bucket_name,
                                                delete_object_list=[
                                                    DeleteObject(object_name)
                                                    for object_name in object_names
                                                ])

            for error in errors:
                print("error occured when deleting object", error)

            return errors

        else:
            return None

    def list_objs(self,
                  prefix: str = None,
                  recursive=False,
                  start_after: str = None):
        """
        해당 prefix의 minio file들 조회

        :param prefix: file 접두사
        :param recursive: 해당 prefix를 가진 파일들 순환 조회
        :param start_after: prefix 앞에 붙을 str(검색 조건)
        :return: [list of objects]
        """
        try:
            return self.client.list_objects(bucket_name=self.bucket_name,
                                            prefix=prefix,
                                            recursive=recursive,
                                            start_after=start_after)
        except Exception as e:
            raise e


def mc(profile_name: str = None) -> MinioClient:
    from utils.tool import get_bucket_config

    if profile_name is None:
        profile_name = Default.BucketProfile

    endpoint, bucket_name, access_key, secret_key = get_bucket_config(profile_name=profile_name)

    return MinioClient(endpoint=endpoint,
                       access_key=access_key,
                       secret_key=secret_key,
                       bucket_name=bucket_name)


def read_obj(file_path: str,
             file_format: str = FileFormat.PARQUET,
             verbose: int = 1,
             **kwargs) -> pd.DataFrame:
    """
    read file in minio

    :param file_path: 파일 경로
    :param file_format: 파일형식(기본: PARQUET)
    :param kwargs: pandas read_csv/read_parqeut 기본 params
    :return: [pd.DataFrame]
    """
    return mc().read_obj(file_path=file_path,
                         file_format=file_format,
                         verbose=verbose,
                         **kwargs)


def read_json_obj(file_path: str,
                  **json_kwargs):
    """
    read json in minio

    :param file_path: 파일 경로
    :param json_kwargs: json.load kwargs
    :return: [dict]
    """
    return mc().read_json_obj(file_path=file_path,
                              **json_kwargs)


def download_obj(object_name: str,
                 file_path: str):
    """
    download file in minio

    :param object_name: download 대상
    :param file_path: 다운로드할 파일 경로
    :param bucket_name: 버킷명(기본: MARS_DEFAULT_BUCKET)
    :return: [bool]
    """
    return mc().download_obj(object_name=object_name,
                             file_path=file_path)


def copy_obj(source: str,
             object_name: str, ):
    """
    copy file(1개)

    :param source: source file path
    :param object_name: destination file path
    :param bucket_name: 버킷명(기본: MARS_DEFAULT_BUCKET)
    :param src_bucket_name: source file의 버킷명(기본: MARS_DEFAULT_BUCKET)
    :return: [str] copy 완료된 파일 path
    """
    return mc().copy_obj(source=source,
                         object_name=object_name)


def upload_df(df: pd.DataFrame,
              object_name: str,
              **pd_kwargs):
    """
    upload df(file buffer)

    :param data: 업로드할 data
    :param object_name: 업로드될 file path
    :return: [str] upload 완료된 파일 path
    """
    return mc().upload_df(df, object_name, **pd_kwargs)


def upload_file_obj(data,
                    object_name: str):
    """
    upload object(file buffer)

    :param data: 업로드할 data
    :param object_name: 업로드될 file path
    :return: [str] upload 완료된 파일 path
    """
    return mc().upload_file_obj(data=data,
                                object_name=object_name)


def upload_file(file_path: str,
                object_name: str,
                file_format: str = FileFormat.CSV):
    """
    upload object(file buffer)

    :param file_path: 업로드할 로컬 FILE PATH
    :param object_name: 업로드될 file path
    :param file_format: 파일 포맷(기본: CSV)
    :return: [str] upload 완료된 파일 path
    """
    return mc().upload_file(file_path=file_path,
                            object_name=object_name,
                            file_format=file_format)


def get_stat_obj(object_name: str):
    """
    minio 내의 파일 상태 확인

    :param object_name: file path
    :return: file status
    """
    return mc().get_stat_obj(object_name=object_name)


def rm_obj(object_name: str):
    """
    minio 내 파일 삭제

    :param object_name: file path
    :return: [bool]
    """
    return mc().rm_obj(object_name=object_name)


def rm_objs(object_names: list):
    """
    minio 내 여러 파일 삭제

    :param object_names: [list of str] file paths
    :return: [list of error]
    """
    return mc().rm_objs(object_names=object_names)


def list_objs(prefix: str = None,
              recursive=False,
              start_after: str = None):
    """
    해당 prefix의 minio file들 조회

    :param prefix: file 접두사
    :param recursive: 해당 prefix를 가진 파일들 순환 조회
    :param start_after: prefix 앞에 붙을 str(검색 조건)
    :return: [list of objects]
    """
    return mc().list_objs(prefix=prefix,
                          recursive=recursive,
                          start_after=start_after)


def upload_json(data: Union[Dict, List], object_name: str):
    import json
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(mode='w+', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent='\t')

        f.seek(0)

        upload_file(file_path=f.name,
                    object_name=object_name,
                    file_format=FileFormat.JSON)
    return object_name
