# Assistant d'installation
import sys
import os
import traceback
import warnings
import time
import asyncio
import json

from dotenv import load_dotenv
import sqlalchemy
import discord
import discord_webhook
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def export(varname):
    """Returns "export varname={formated value}\\n" """
    var = str(globals()[varname])
    formated_var = var.strip("'\"").replace("\"", "\\\"").replace(r"\n", r"\\n")
    return f"export {varname}=\"{formated_var}\"\n"

def report_error(exc):
    print(f"Hmm, something went wrong ({type(exc).__name__}): {exc}")
    pft = input(f"Print the full traceback? (y/n) ")
    if pft.strip().lower() in ["y", "o", "yes"]:
        print(traceback.format_exc())

    print("Check that given values are correct and that every steps mentionned above have been done, then press Enter to retry.")
    input()


print("LG-Rez Installation Assistant - v1.0.1\n")

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

    load_dotenv(".env")

    if (LGREZ_DATABASE_URI := os.getenv("LGREZ_DATABASE_URI")):
        step = 1
        print("    step 1 ok")

    if (LGREZ_DISCORD_TOKEN := os.getenv("LGREZ_DISCORD_TOKEN")):
        step = 2
        print("    step 2 ok")
    if (LGREZ_SERVER_ID := os.getenv("LGREZ_SERVER_ID")):
        step = 3
        print("    step 3 ok")
    if (LGREZ_WEBHOOK_URL := os.getenv("LGREZ_WEBHOOK_URL")):
        step = 4
        print("    step 4 ok")

    if (LGREZ_GCP_CREDENTIALS := os.getenv("LGREZ_GCP_CREDENTIALS")):
        step = 5
        print("    step 5 ok")
    if ((LGREZ_TDB_SHEET_ID := os.getenv("LGREZ_TDB_SHEET_ID"))
        and (LGREZ_ROLES_SHEET_ID := os.getenv("LGREZ_ROLES_SHEET_ID"))
        and (LGREZ_DATA_SHEET_ID := os.getenv("LGREZ_DATA_SHEET_ID"))):

        step = 6
        print("    step 6 ok")

    if (LGREZ_CONFIG_STATUS := os.getenv("LGREZ_CONFIG_STATUS")):
        step = 7
        print("    step 7 ok")


    if step == 7:
        print("Installation already complete in this folder. To create a fresh installation, delete the .env file; otherwise, directly edit values in it.")
        exit(0)

    print(f"Found ongoing installation on step {step}/7. Press Enter to continue installation.")
    input()

else:
    print("Nothing found.")



# Base de .env
if step == 0:
    print("""
-----------------------------------------------------

Welcome to the LG-Rez Installation Assistant! Il will guide you through the whole process of making a functionnal installation for your bot.

You can pause the installation anytime by killing this assistant, it will resume at the current step.
Press Enter to begin.""")
    input()

    content = """# .env: file containing text variables, considered by Python as environment
# variables thanks to dotenv.loadenv() and then accessible through os.getenv
# Here should be put:
#   - everything sensitive (acces tokens to different APIs, ...) ;
#   - every parameter that may change from a season to another (server ID, ...).

# EVERY VARIABLES WILL BE READ AS STRINGS, even if written without quote marks.
# Itegers/... stored here will need to be transformed after os.getenv call.\n\n
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

    ok = False
    while not ok:
        LGREZ_DATABASE_URI = input("Database URI (dialect[+driver]://user:password@host/base): ")

        print("Testing connection...")
        try:
            engine = sqlalchemy.create_engine(LGREZ_DATABASE_URI)
            engine.connect()
        except Exception as e:
            report_error(e)
        else:
            print("Connected!")
            ok = True
            time.sleep(1)

    with open(".env", "a") as fich:
        fich.write(f"# -- Database\n\n" + export("LGREZ_DATABASE_URI"))
    step = 1


if step < 2:
    print("""\n\n------ STEP 2 : Discord application ------

If not already done, create a new Bot application on the Discord Developer Portal: https://discord.com/developers/applications
Generate a new "client secret" on your app main page. This token gives anyone full access to your bot, so don't leak it!
""")

    ok = False
    while not ok:
        LGREZ_DISCORD_TOKEN = input("Discord client secret: ")

        print("Testing connection...")
        try:
            client = discord.Client()
            loop = asyncio.new_event_loop()
            loop.run_until_complete(client.login(LGREZ_DISCORD_TOKEN))
        except Exception as e:
            report_error(e)
        else:
            print("Connected!")
            loop.run_until_complete(client.logout())
            ok = True
            time.sleep(1)


    with open(".env", "a") as fich:
        fich.write(f"\n\n# -- Discord\n\n" + export("LGREZ_DISCORD_TOKEN"))
    step = 2


if step < 3:
    print("""\n\n------ STEP 3 : Discord server ------

For each season, we recommand you to create a new Discord server. We provide the following model, with recommanded channels and permissions: https://discord.new/RPGXChXXcKQZ
""")

    ok = False
    while not ok:
        LGREZ_SERVER_ID = input("Server ID (Server settings / Widget): ")

        try:
            if not(LGREZ_SERVER_ID.isdigit() and len(LGREZ_SERVER_ID) == 18):
                raise ValueError("Server ID must be a 18-digits number")
        except Exception as e:
            report_error(e)
        else:
            ok = True
            time.sleep(1)

    with open(".env", "a") as fich:
        fich.write(export("LGREZ_SERVER_ID"))

    print("""
Unfortunately, a Discord model doesn't contain the following:
- Icon: create your own!
- Emojis: the bot itself needs a few custom emojis to work correctly. We provide them in [the Templates folder](https://drive.google.com/drive/folders/1kjHzUSp-QfgI77Yg0GCxdM6YcFkHPYVw) (described below). Download them, go in your server settings / Emoji / Upload emoji and select them all; they well be named correctly.
When done, press Enter to continue.""")
    input()

    print("""Now, you can add the bot to your server:
- Go to the Discord Developer Portal, select your bot application;
- Go to the OAuth2 tab, select the "bot" scope and clic "Copy". Bot permissions are not important in our settings;
- Open the copied URL in your browser and select your newly created server.
- Go back to Discord and give the "Bot" role to the bot account. That will grant him every needed permissions.

The bot should appear offline: you'll be able to run it at the end of this installation.
ONCE THE BOT IS SHOWN IN YOUR SERVER MEMBERS, press Enter to continue.""")
    input()

    step = 3



if step < 4:
    print("""\n\n------ STEP 4 : scheduled tasks webhook ------

This bot supports task postponing. This feature requires a "webhook" (a protocol to post messages externally to a channel), called at scheduled time to trigger bot reaction. Create a new webhook (Server settings / Integrations / Webhooks) posting on the '#logs' channel.
""")

    ok = False
    while not ok:
        LGREZ_WEBHOOK_URL = input("Webhook URL: ")

        print("Testing webhook...")
        try:
            webhook = discord_webhook.DiscordWebhook(
                url=LGREZ_WEBHOOK_URL,
                content="Test Webhook!"
            )
            response = webhook.execute()
            if not response:
                raise RuntimeError(f"Bad response: {response}")
        except Exception as e:
            report_error(e)
        else:
            print("OK!")
            ok = True
            time.sleep(1)


    with open(".env", "a") as fich:
        fich.write(export("LGREZ_WEBHOOK_URL"))
    step = 4



if step < 5:
    print("""\n\n------ STEP 5 : GCP connection ------

The bot needs a "special" Google account to access Google Sheets files.
If not already done, create a new projet on Google Cloud Platform : https://console.cloud.google.com/home/dashboard (you may need extra steps if you use GCP for the first time).

Follow the basic setup guide, then open the "IAM & Admin" pane, go to "Service Accounts" and create a new service account. Name it as you wish, then open it and create a new key ("Keys"/"Add key"). Open the JSON file, copy its contents and delete it.
""")

    ok = False
    while not ok:
        LGREZ_GCP_CREDENTIALS = input("JSON key (file contents): ")

        print("Authentificating...")
        try:
            scope = ['https://spreadsheets.google.com/feeds']
            with warnings.catch_warnings(record=True) as warns:
                creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(LGREZ_GCP_CREDENTIALS), scope)
                client = gspread.Client(creds)
                if warns:
                    raise RuntimeError(wl[0].message)

        except Exception as e:
            report_error(e)
        else:
            print("OK!")
            ok = True
            time.sleep(1)


    with open(".env", "a") as fich:
        fich.write("\n\n# -- Google Sheets\n\n" + export("LGREZ_GCP_CREDENTIALS"))
    step = 5



if step < 6:
    print("""\n\n------ STEP 6 : Sheets IDs ------

This bot works with Google Sheets worksheets to gather players orders and resolve play situations. We provide a readonly Google Drive folder with every needed files: https://drive.google.com/drive/folders/1kjHzUSp-QfgI77Yg0GCxdM6YcFkHPYVw

If not already done, duplicate all files into your own folder (right clic > Create a copy) and open them. The bot needs the filed IDs, ie the URL part between '/d/' and '/edit'.

(for a new season, we recommand you to create a new "Tableau de bord" file. The faster way is to duplicate it again from our template folder, but you may prefer duplicate one of your previous seasons and remove players and sheets: in this case, remember to remove cached properties of players (A-I columns).)

IMPORTANT: to allow your bot to read and write the sheets, share the three (or the whole folder) with the service account mail adress created just before (account@project.iam.gserviceaccount.com), with Editor rights.
""")

    ok = False
    while not ok:
        LGREZ_TDB_SHEET_ID = input("'Tableau de bord' ID: ")
        LGREZ_ROLES_SHEET_ID = input("'Roles et actions' ID: ")
        LGREZ_DATA_SHEET_ID = input("'Donnees brutes' ID: ")

        print("Checking access...")
        try:
            scope = ['https://spreadsheets.google.com/feeds']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(LGREZ_GCP_CREDENTIALS), scope)
            client = gspread.authorize(creds)

            workbook = client.open_by_key(LGREZ_TDB_SHEET_ID)
            workbook.sheet1.add_rows(1)     # Test en écriture
            print("'Tableau de bord' OK...")

            workbook = client.open_by_key(LGREZ_ROLES_SHEET_ID)
            workbook.sheet1.add_rows(1)     # Test en écriture
            print("'Roles et actions' OK...")

            workbook = client.open_by_key(LGREZ_DATA_SHEET_ID)
            workbook.sheet1.add_rows(1)     # Test en écriture

        except Exception as e:
            report_error(e)
        else:
            print("'Donnees brutes' OK!")
            ok = True
            time.sleep(1)

    with open(".env", "a") as fich:
        fich.write("\n"
            + export("LGREZ_TDB_SHEET_ID")
            + export("LGREZ_ROLES_SHEET_ID")
            + export("LGREZ_DATA_SHEET_ID")
            + """
# Reminder: the sheets need to be shared with GCP_CREDENTIALS["client_email"]
# (as an Editor) to grant the bot read and write rights.\n\n"""
        )
    step = 6



if step < 7:
    print("""\n\n------ STEP 7 : dashboard setup ------

In the "Tableau de bord" sheet, edit the AN1 and BG1 cells to put the URLs of the "Données brutes" and "Rôles et actions" sheets, respectively. You should be prompted to grant access to those files, do it.

Press Enter when done.
""")
    input()
    print("""Now, open the scripts editor ("Tools/Scripts editor"), and select "Edit/Triggers of this project". This page allows you to automatically backup and clear the "Tableau de bord" each day: when the season starts, clic "Add a trigger" and configure it: Backupfeuille / Head / Temporal trigger / Daily / Between 1am and 2am (important, because the data sheet clears data between 3pm and 4pm).

Press Enter when done.""")
    input()

    LGREZ_CONFIG_STATUS = 1
    with open(".env", "a") as fich:
        fich.write("# -- Configuration status: set it to 1 when everything is functionnal\n\n"
            + export("LGREZ_CONFIG_STATUS"))        # Fin de l'installation
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
