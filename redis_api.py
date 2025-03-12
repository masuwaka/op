from time import sleep

from redis import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError

REDIS_PORT = 56379
REDIS_PASSWORD = "passwd"
RECONNECTION_INTERVAL = 1


class RedisAPI:
    def __init__(self, host):
        self.conn = ConnectionPool(host=host, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responces=True)
        self.r = None

    def reconnect_redis(self):
        self.r = Redis(connection_pool=self.conn)

    def execute_with_retry(self, command, *args, **kwargs):
        while True:
            try:
                return getattr(self.r, command)(*args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                print(f"Connecting to redis failed: {e}. Retry after 1sec.")
                sleep(RECONNECTION_INTERVAL)
                self.reconnect_redis()
