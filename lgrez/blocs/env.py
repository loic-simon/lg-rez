"""lg-rez / blocs / Lecture des variables d'environnement

"""

import sys
import os

from dotenv import load_dotenv


# À l'import
if len(sys.argv) > 1 and sys.argv[1].startswith(".env"):
    path = sys.argv[1]
else:
    path = ".env"

load_dotenv(path)


def load(VAR_NAME):
    """Lit une variable depuis les variables d'environnement / le ``.env`` demandé à l'appel de bot.py (``.env`` par défaut)

    Équivaut globalement à :func:`os.getenv` suivi d'une assertion vérifiant que la variable existe.

    Args:
        VAR_NAME (:class:`str`): nom de la variable à charger (``LGREZ_...``)

    Returns:
        :class:`str`
    """
    VAR = os.getenv(VAR_NAME)
    assert VAR, f"Variable d'environnement {VAR_NAME} manquante"
    return VAR
