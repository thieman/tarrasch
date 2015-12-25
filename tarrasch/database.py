from redis import StrictRedis
from redis.utils import from_url

from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, REDIS_URL

if REDIS_URL:
    singleton = from_url(REDIS_URL, db=REDIS_DB)
else:
    singleton = StrictRedis(host=REDIS_HOST, port=REDIS_PORT,
                            db=REDIS_DB, password=REDIS_PASSWORD)
