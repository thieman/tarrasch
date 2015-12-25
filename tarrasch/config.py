import os

SLACK_TOKEN = os.getenv('TARRASCH_SLACK_TOKEN')
MESSAGE_PREFIX = os.getenv('TARRASCH_MESSAGE_PREFIX', 'chess')

REDIS_URL = os.getenv('TARRASCH_REDIS_URL')
# we'll also make it easier to use with Heroku out of the box
# the integration sets up a url at REDIS_URL by default
if not REDIS_URL:
    possible_heroku_setting = os.getenv('REDIS_URL')
    if possible_heroku_setting:
        REDIS_URL = possible_heroku_setting

REDIS_HOST = os.getenv('TARRASCH_REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('TARRASCH_REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('TARRASCH_REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('TARRASCH_REDIS_PASSWORD')

COOLDOWN_SECONDS = int(os.getenv('TARRASCH_COOLDOWN_SECONDS', 0))
