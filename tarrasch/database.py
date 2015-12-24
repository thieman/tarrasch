from redis import StrictRedis

from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

singleton = StrictRedis(host=REDIS_HOST, port=REDIS_PORT,
                        db=REDIS_DB, password=REDIS_PASSWORD)
