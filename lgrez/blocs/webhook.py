"""lg-rez / blocs / Envoi de webhooks

(Implémentation de https://pypi.org/project/discord-webhook)

"""

import time

from discord_webhook import DiscordWebhook



def send(message, url):
    """Envoie un webhook Discord

    Args:
        message (:class:`str`): message à envoyer
        url (:class:`str`): adresse du webhook (``"https://discordapp.com/api/webhooks/.../..."``)

    Returns:
        :class:`requests.Response` | ``False``

    Seuls les webhooks textuels sont pris en charge.
    """
    webhook = DiscordWebhook(url=url, content=message)

    response = webhook.execute()

    return response
