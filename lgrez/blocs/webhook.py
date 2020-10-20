from discord_webhook import DiscordWebhook

def send(message: str, url):
    """Appelle le webhook Discord de l'url <url> avec le message <message>."""
    webhook = DiscordWebhook(url=url, content=message)
    response = webhook.execute()
    return response
