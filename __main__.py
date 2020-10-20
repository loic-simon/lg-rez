# Assistant d'installation
import sys
from lgrez.blocs import env


print("LG-Rez Installation Assistant - v0.0.1\n")

# Déjà en cours ?
print("Looking for existing installation in this folder...")

try:
    with open(".env", "r"):
        exists = True
except FileNotFoundError:
    exists = False

step = 0
if exists:
    print("Found! Checking progress...")

    try:
        env.load("SQLALCHEMY_DATABASE_URI")
        step = 1
        print("    step 1 ok")

        env.load("DISCORD_TOKEN")
        step = 2
        print("    step 2 ok")
        env.load("DISCORD_GUILD_ID")
        step = 3
        print("    step 3 ok")
        env.load("WEBHOOK_TP_URL")
        step = 4
        print("    step 4 ok")

        env.load("TDB_SHEET_ID") and env.load("ROLES_SHEET_ID") and env.load("DONNEES_SHEET_ID")
        step = 5
        print("    step 5 ok")
        env.load("GSHEET_CREDENTIALS")
        step = 6
        print("    step 6 ok")

        env.load("INSTALLATION")
        step = 7
        print("    step 7 ok")

    except AssertionError:
        pass

    if step == 7:
        print("Installation already complete in this folder. To create a fresh installation, delete the .env file; otherwise, directly edit values in it.")
        sys.exit(0)

    print(f"Found ongoing installation on step {step}/7. Press Enter to continue installation.")
    input()

else:
    print("Nothing found.")


print("""
Welcome to the LG-Rez Installation Assistant! Il will guide you through the whole process of making a functionnal installation for your bot.

You can pause the installation anytime by killing this assistant, it will resume at the current step.
Press Enter to begin.""")
input()


# Base de .env
if step == 0:
    content = """
# .env : fichier reprenant divers paramètres textuels pour le bot, qui seront considérées par Python comme des variables d'environnement grâce à l'appel à dotenv.loadenv() et seront donc accessibles via os.getenv("VALUE").
# Mettre ici :
#   - tout ce qui est confidentiel (tokens d'accès aux différentes API) ;
#   - ce qui est susceptible de changer d'une saison à l'autre et/ou est utilisé à plusieurs endroits (IDs de guilds/docs/webhooks...).

# TOUTES LES VARIABLES SONT DES CHAÎNES DE CARACTÈRES : ne PAS mettre des guillemets (ils seront intégrés à la chaîne), et penser à transformer les entiers/... stockés ici après l'appel à os.getenv.
"""
    with open(".env", "w") as fich:
        fich.write(content)


if step < 1:
    print("""\n------ STEP 1 : database connection ------

This program needs to be connected to a database.

Since it uses SQLAlchemy, every language it supports can theoretically be used, but the package has been developed and tested with PostgreSQL exclusively (otherwise, you may need to install complementary packages such as PyMySQL).

You will need an empty database, local or on a specified host.
The database schema will be created by the bot the first time it runs.
""")

    SQLALCHEMY_DATABASE_URI = input("Database URI (protocol://user:password@host/base): ")

    # CONNECTION TEST

    with open(".env", "a") as fich:
        fich.write(f"# Base de données\n\nSQLALCHEMY_DATABASE_URI = {SQLALCHEMY_DATABASE_URI}\n\n")
    step = 1


if step < 2:
    print("""\n\n------ STEP 2 : Discord application ------

If not already done, create a new Bot application on the Discord Developer Portal: https://discord.com/developers/applications
Generate a new "client secret" on your app main page. This token gives anyone full access to your bot, so don't leak it!
""")

    DISCORD_TOKEN = input("Discord client secret: ")

    # CONNECTION TEST

    with open(".env", "a") as fich:
        fich.write(f"# Discord\n\nDISCORD_TOKEN = {DISCORD_TOKEN}\n")
    step = 2


if step < 3:
    print("""\n\n------ STEP 3 : Discord server ------

For each season, we recommand you to create a new Discord server. We provide the following model, with recommanded channels and permissions: https://discord.new/RPGXChXXcKQZ
""")

    DISCORD_GUILD_ID = input("Server ID (Server settings / Widget): ")

    # CONNECTION TEST

    with open(".env", "a") as fich:
        fich.write(f"DISCORD_GUILD_ID = {DISCORD_GUILD_ID}\n")
    step = 3

    print("""Add the bot to your server:
- Go to the Discord Developer Portal, select your bot application;
- Go to the OAuth2 tab, select the "bot" scope and clic "Copy". Bot permissions are not important in our settings;
- Open the copied URL in your browser and select your newly created server.
- Go back to Discord and give the "Bot" role to the bot account. That will grant him every needed permissions.

The bot should appear offline: you'll be able to run it at the end of this installation.
When this is done, hit Enter to continue.""")
    input()



if step < 4:
    print("""\n\n------ STEP 4 : planified tasks webhook ------

This bot supports task postponing. This feature requires a "webhook" (a protocol to post messages externally to a channel), called at scheduled time to trigger bot reaction. Create a new webhook (Parameters / Integrations / Webhooks) posting on the '#logs' channel.
""")

    WEBHOOK_TP_URL = input("Webhook URL: ")

    # CONNECTION TEST

    with open(".env", "a") as fich:
        fich.write(f"WEBHOOK_TP_URL = {WEBHOOK_TP_URL}\n\n")
    step = 4



if step < 5:
    print("""\n\n------ STEP 5 : Sheets IDs ------

This bot works with Google Sheets worksheets to gather players orders and resolve play situations. We provide a readonly Google Drive folder with every needed files: https://drive.google.com/drive/folders/1kjHzUSp-QfgI77Yg0GCxdM6YcFkHPYVw

If not already done, duplicate all files into your own folder (right clic > Create a copy) and open them. The bot needs the filed IDs, ie the URL part between '/d/' and '/edit'.

(for a new season, we recommand you to create a new "Tableau de bord" file. The faster way is to duplicate it again from our template folder, but you may prefer duplicate one of your previous seasons and remove players and sheets: in this case, remember to remove cached properties of players (A-I columns).)
""")

    TDB_SHEET_ID = input("'Tableau de bord' ID: ")
    ROLES_SHEET_ID = input("'Roles et actions' ID: ")
    DONNEES_SHEET_ID = input("'Donnees brutes' ID: ")

    # CONNECTION TEST

    with open(".env", "a") as fich:
        fich.write(f"""# Google Sheets

# RAPPEL : le doc doit être partagé avec <account@project.iam.gserviceaccount.com> (en tant qu'Éditeur) pour que le bot puisse lire et modifier les valeurs. Normalement, c'est le cas de tous les fichiers du Drive LG Rez.

TDB_SHEET_ID = {TDB_SHEET_ID}
ROLES_SHEET_ID = {ROLES_SHEET_ID}
DONNEES_SHEET_ID = {DONNEES_SHEET_ID}
""")
    step = 5



if step < 6:
    print("""\n\n------ STEP 6 : GCP connection ------

The bot needs a "special" Google account to access those files.
If not already done, create a new projet on Google Cloud Platform : https://console.cloud.google.com/home/dashboard (you may need extra steps if you use GCP for the first time).

Follow the basic setup guide, then open the "IAM & Admin" pane, go to "Service Accounts" and create a new service account. Name it as you wish, then open it and create a new key ("Keys"/"Add key"). Open the JSON file, copy its contents and delete it.
""")

    GSHEETS_CREDENTIALS = input("JSON key (file contents): ")

    print("""
Now, share the three sheets (or the whole folder) with the service account mail adress (account@project.iam.gserviceaccount.com) with Editor rights.
Hit Enter when done.""")
    input()

    # CONNECTION TEST

    with open(".env", "a") as fich:
        fich.write(f"GSHEETS_CREDENTIALS = {GSHEETS_CREDENTIALS}\n\n")
    step = 6



# END

# "étape" liée à aucune variable d'environnement, donc écrite en durs

if step < 7:
    print("""\n------ STEP 7 : dashboard setup ------

In the "Tableau de bord" sheet, edit the AN1 and BG1 cells to put the URLs of the "Données brutes" and "Rôles et actions" sheets, respectively. You should be prompted to grant access to those files, do it.

Hit Enter when done.
""")
    input()
    print("""Now, open the scripts editor ("Tools/Scripts editor"), and select "Edit/Triggers of this project". This page allows you to automatically backup and clear the "Tableau de bord" each day: when the season starts, clic "Add a trigger" and configure it: Backupfeuille / Head / Temporal trigger / Daily / Between 1am and 2am (important, because the data sheet clears data between 3pm and 4pm).

Hit Enter when done.""")
    input()

    with open(".env", "a") as fich:
        fich.write("INSTALLATION = 1\n")        # Fin de l'installation
    step = 7



# Création de bot.py
code = """# Minimal working code to run LG-bot!

from lgrez import LGBot

bot = LGBot()
bot.run()
"""

with open("bot.py", "w") as fich:
    fich.write(code)



print("""\n------ THE END ------

Congrats, the installation is now complete! Variables have been written to the ".env" file: edit it directly for minor changes.
A file named "bot.py" has been created in the current folder: it contains the minimal code needed to run the bot. It will be running unless it crashes or is manually killed.

The bot execution is quiet, except at startup and if an exception occurs, so we advise you to log the output stream somewhere!
We also advise you to use an external script to ensure the bot has not crashed (pretty unlikely, but it might always happen).

You can no try to interact with the bot!
(For your first tests, note that the bot ignore every messages posted by member without any role! Assign yourself the "MJ" role to get every rights with the bot)

Do not hesitate to reach us for any issue or suggestion, we're always happy to get news. See bottom of README for contacts.

Enjoy!""")
