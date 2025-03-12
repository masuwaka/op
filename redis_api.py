from time import sleep

from redis import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError

REDIS_PORT = 56379
REDIS_PASSWORD = "project"
REDIS_RECONNECTION_INTERVAL = 1
REDIS_MAX_RETRIES_BEFORE_RESET = 600


class RedisAPI:
    def __init__(self, host="127.0.0.1"):
        self.host = host
        self._create_redis_instance()

    def _create_redis_instance(self):
        pool = ConnectionPool(
            host=self.host,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responces=True,
            socket_timeout=5,
            retry_on_timeout=True,
            max_connections=10,
            socket_keepalive=True,
        )
        self.r = Redis(connection_pool=pool)

    def execute(self, command, *args, **kwargs):
        retryCount = 0

        while True:
            try:
                return getattr(self.r, command)(*args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                print(f"Connecting to redis-server failed: {e}. Retry after 1sec.")
                sleep(REDIS_RECONNECTION_INTERVAL)
                retryCount += 1

                if retryCount >= REDIS_MAX_RETRIES_BEFORE_RESET:
                    print("Connection to redis-server has been suspended long time: Re-create connection pool.")
                    self._create_redis_instance()
                    retryCount = 0
