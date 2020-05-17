import os
from dotenv import load_dotenv

from discord_webhook import DiscordWebhook

load_dotenv()
URL = os.getenv("WEBHOOK_LOGS_URL")

def send(message :str, url=URL):
    webhook = DiscordWebhook(url=url, content=message)
    response = webhook.execute()
    return response
