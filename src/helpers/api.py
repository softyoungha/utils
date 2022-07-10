import requests
from typing import Dict, List, Union
from json import dumps as json_dumps

from utils.config import ApiConn, API_CONFIG
from dataclasses import dataclass


@dataclass
class Api:
    profile_name: str

    def __post_init__(self):
        api_config = API_CONFIG.get(self.profile_name)

        if api_config is None:
            raise KeyError(f"해당 profile_name을 찾을 수 없습니다: {self.profile_name}")

        # get url_prefix
        endpoint = api_config.get(ApiConn.ENDPOINT)

        assert endpoint is not None, "api endpoint 가 없습니다"

        # set
        self.prefix = endpoint

        # get url_prefix
        self.headers = api_config.get(ApiConn.DEFAULT_HEADERS) or {}
        self.cookies = api_config.get(ApiConn.DEFAULT_COOKIES) or {}

        # init
        self.csrf_token = None
        self.session_id = None

        # create session
        self._session = requests.Session()

    @property
    def session(self) -> requests.Session:
        return self._session

    def get(self,
            url: str,
            params: dict = None,
            headers: dict = None,
            cookies: dict = None,
            as_json=True,
            raise_exception=False):

        # update headers and cookies
        headers, cookies = self.update_headers_and_cookies(headers=headers, cookies=cookies)

        # requests
        res = self.session.get(url=f'{self.prefix}/{url}',
                               params=params,
                               headers=headers,
                               cookies=cookies,
                               verify=False)
        print(f'# url: {res.url} - GET: {res.status_code}')

        return self.response(res=res, as_json=as_json, raise_exception=raise_exception)

    def post(self,
             url: str,
             data: Union[Dict, List] = None,
             json: Union[Dict, List] = None,
             headers: dict = None,
             as_json: bool = True,
             dumps: bool = False,
             cookies: dict = None,
             raise_exception=False):

        # update headers and cookies
        headers, cookies = self.update_headers_and_cookies(headers=headers, cookies=cookies)

        # parse data
        if dumps and (isinstance(data, list) or isinstance(data, dict)):
            data = json_dumps(data, ensure_ascii=False).encode('utf-8')
            headers['Content-type'] = 'application/json; charset=utf-8'

        # requests
        res = self.session.post(url=f'{self.prefix}/{url}',
                                data=data,
                                json=json,
                                headers=headers,
                                cookies=cookies,
                                verify=False)
        print(f'# url: {res.url} - POST: {res.status_code}')

        return self.response(res=res, as_json=as_json, raise_exception=raise_exception)

    def put(self,
            url: str,
            data: Union[Dict, List] = None,
            headers: dict = None,
            cookies: dict = None,
            dumps: bool = False,
            as_json=True,
            raise_exception=False):

        # update headers and cookies
        headers, cookies = self.update_headers_and_cookies(headers=headers, cookies=cookies)

        # parse data
        if dumps and (isinstance(data, list) or isinstance(data, dict)):
            data = json_dumps(data, ensure_ascii=False).encode('utf-8')
            headers['Content-type'] = 'application/json; charset=utf-8'

        # requests
        res = self.session.put(url=f'{self.prefix}/{url}',
                               data=data,
                               headers=headers,
                               cookies=cookies,
                               verify=False)

        print(f'# url: {res.url} - PUT: {res.status_code}')

        return self.response(res=res, as_json=as_json, raise_exception=raise_exception)

    def patch(self,
              url: str,
              data: Union[Dict, List] = None,
              headers: dict = None,
              cookies: dict = None,
              dumps: bool = False,
              as_json=True,
              raise_exception=False):
        # update headers and cookies
        headers, cookies = self.update_headers_and_cookies(headers=headers, cookies=cookies)

        # parse data
        if dumps and (isinstance(data, list) or isinstance(data, dict)):
            data = json_dumps(data, ensure_ascii=False).encode('utf-8')
            headers['Content-type'] = 'application/json; charset=utf-8'

        res = self.session.patch(url=f'{self.prefix}/{url}',
                                 data=data,
                                 headers=headers,
                                 cookies=cookies,
                                 verify=False)

        print(f'# url: {res.url} - PATCH: {res.status_code}')

        return self.response(res=res, as_json=as_json, raise_exception=raise_exception)

    def delete(self,
               url: str,
               as_json=True,
               headers: dict = None,
               cookies: dict = None,
               raise_exception=False):
        # update headers and cookies
        headers, cookies = self.update_headers_and_cookies(headers=headers, cookies=cookies)

        res = self.session.delete(url=f'{self.prefix}/{url}',
                                  headers=headers,
                                  cookies=cookies,
                                  verify=False)

        print(f'# url: {res.url} - DELETE: {res.status_code}')

        return self.response(res=res, as_json=as_json, raise_exception=raise_exception)

    def update_headers_and_cookies(self, headers: dict = None, cookies: dict = None, ):

        # parse headers
        _headers = self.headers.copy()

        if headers:
            _headers.update(headers)

        # parse cookies
        _cookies = self.cookies.copy()

        if cookies:
            _cookies.update(cookies)

        return _headers, _cookies

    @staticmethod
    def response(res, as_json=True, raise_exception=False):
        status_code = int(res.status_code)

        if status_code < 300:
            if as_json:
                return status_code, res.json()
            else:
                return status_code, res

        else:
            print(f'status_code: {status_code}')
            print(res.content.decode())
            if raise_exception:
                raise requests.HTTPError()
            else:
                return status_code, res


def api_client(profile_name: str):
    return Api(profile_name=profile_name)
