import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
assert SECRET_KEY, "config.py : SECRET_KEY introuvable"
assert SQLALCHEMY_DATABASE_URI, "config.py : SQLALCHEMY_DATABASE_URI introuvable"

SQLALCHEMY_TRACK_MODIFICATIONS = False
