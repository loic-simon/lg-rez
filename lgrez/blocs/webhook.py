"""lg-rez / blocs / Envoi de webhooks

(Implémentation de https://pypi.org/project/discord-webhook)

"""

from discord_webhook import DiscordWebhook


_last_time = None       # Temps (time.time) du derner envoi de webhook


def send(message, url):
    """Envoie un webhook Discord.

    Args:
        message (str): message à envoyer (limité à 2000 caractères).
        url (str): adresse du webhook
            (``"https://discordapp.com/api/webhooks/.../..."``)

    Returns:
        :class:`requests.Response` | ``False``

    Note:
        Seuls les webhooks textuels sont pris en charge.
    """
    webhook = DiscordWebhook(url=url, content=message)

    response = webhook.execute()

    return response
