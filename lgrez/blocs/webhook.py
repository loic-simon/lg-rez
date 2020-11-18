"""lg-rez / blocs / Envoi de webhooks

(Implémentation de https://pypi.org/project/discord-webhook)

"""

import time

from discord_webhook import DiscordWebhook


_last_time = None       # Temps (time.time) du derner envoi de webhook

def send(message, url):
    """Envoie un webhook Discord

    Args:
        message (:class:`str`): message à envoyer
        url (:class:`str`): adresse du webhook (``"https://discordapp.com/api/webhooks/.../..."``)

    Returns:
        :class:`requests.Response` | ``False``

    Seuls les webhooks textuels sont pris en charge.

    Limitation interne de 2 secondes minimum entre deux webhooks (renvoie ``False`` si appelé trop tôt), pour se conformer à la rate limit Discord (30 messages / minute) et ne pas engoncer la loop
    """
    global _last_time

    if _last_time and (delta := time.time() - _last_time) < 2:      # Moins de deux secondes depuis le dernier envoi
        return False        # on interdit l'envoi du webhook

    webhook = DiscordWebhook(url=url, content=message)

    response = webhook.execute()
    _last_time = time.time()

    return response
