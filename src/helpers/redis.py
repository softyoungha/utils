import redis
from utils.config import REDIS_CONFIG, Default


class Redis(redis.StrictRedis):
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password=None,
                 socket_timeout=None,
                 socket_connect_timeout=None,
                 connection_pool=None,
                 max_connections=None,
                 decode_responses=True):
        super().__init__(host=host,
                         port=port,
                         db=db,
                         password=password,
                         socket_timeout=socket_timeout,
                         socket_connect_timeout=socket_connect_timeout,
                         connection_pool=connection_pool,
                         max_connections=max_connections,
                         decode_responses=decode_responses)


def rc(profile_name: str) -> Redis:
    if profile_name is None:
        profile_name = Default.RedisProfile

    redis_config = REDIS_CONFIG.get(profile_name)

    if redis_config is None:
        raise KeyError(f"해당 profile_name을 찾을 수 없습니다: {profile_name}")

    return Redis(**REDIS_CONFIG.get(profile_name))
