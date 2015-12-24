import os

SLACK_TOKEN = os.getenv('TARRASCH_SLACK_TOKEN')
MESSAGE_PREFIX = os.getenv('TARRASCH_MESSAGE_PREFIX', 'chess')

REDIS_HOST = os.getenv('TARRASCH_REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('TARRASCH_REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('TARRASCH_REDIS_DB', 0))