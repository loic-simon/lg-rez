import sys
import os
from dotenv import load_dotenv

# À l'import
if len(sys.argv) > 1 and sys.argv[1].startswith(".env"):
    path = sys.argv[1]
else:
    path = ".env"

print(os.getcwd())
path = f"{path}"

load_dotenv(path, verbose=True)
print(f"Environment variables loaded from {path}")

def load(VAR_NAME):
    """Récupère la variable <VAR_NAME> depuis le .env demandé à l'appel de bot.py (.env par défaut)"""
    VAR = os.getenv(VAR_NAME)
    assert VAR, f"load_env : {VAR_NAME} introuvable"
    return VAR
