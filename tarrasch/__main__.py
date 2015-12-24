import json
import time
import logging

from slackclient import SlackClient

from .config import SLACK_TOKEN, MESSAGE_PREFIX
from .handler import handle_message

USER_CACHE = {}

def _ensure_cached_user_info(client, event):
    user_id = event.get('user')
    if user_id in USER_CACHE or not user_id:
        return
    USER_CACHE[user_id] = json.loads(client.api_call('users.info', user=user_id))['user']

def _route_event(client, event):
    _ensure_cached_user_info(client, event)
    if event.get('type') == 'message' and 'subtype' not in event:
        print event
        if event.get('text').startswith(MESSAGE_PREFIX):
            channel = event['channel']
            message = event['text'].lstrip(MESSAGE_PREFIX).strip()
            user_name = USER_CACHE[event['user']]['name']
            if message:
                handle_message(client, channel, user_name, message)

def main():
    client = SlackClient(SLACK_TOKEN)
    if client.rtm_connect():
        while True:
            events = client.rtm_read()
            if events:
                for event in events:
                    _route_event(client, event)
            else:
                time.sleep(0.5)
    else:
        raise IOError('Connection to Slack failed, check your token')

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e: # die on any other error
            logging.exception('Error bubbled up to main loop')
