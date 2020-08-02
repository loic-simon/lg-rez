try:
    from Discord.blocs import env
except ModuleNotFoundError:
    from blocs import env

SECRET_KEY = env.load("SECRET_KEY")
SQLALCHEMY_DATABASE_URI = env.load("SQLALCHEMY_DATABASE_URI")

SQLALCHEMY_TRACK_MODIFICATIONS = False
