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
    """Récupère la variable <VAR_NAME> depuis le .env demandé à l'appel de bot.py (.env par défaut)"""
    VAR = os.getenv(VAR_NAME)
    assert VAR, f"Variable d'environnement {VAR_NAME} manquante"
    return VAR
