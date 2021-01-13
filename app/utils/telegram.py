import json
import os
import requests

from sentry_sdk import capture_message


TELEGRAM_BOT_API_URL = f'https://api.telegram.org/bot{os.environ["TELEGRAM_BOT_TOKEN"]}'


def send_high_priority_notification(message):
    response = requests.post(
        url=f'{TELEGRAM_BOT_API_URL}/sendMessage',
        data=json.dumps({'chat_id': os.environ['TELEGRAM_GROUP_ID'], 'text': message}),
        headers={'Content-Type': 'application/json'}
    )
    if not response.status_code == 200:
        capture_message(f'Telegram: {response.status_code} {response.reason} - {response.text}')
