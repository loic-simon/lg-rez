# lg-rez manual configuration instructions

**Important notice**: we alternatively provide an assistant tool to help you configure your bot. See the *Configure* section of [`README.md`] for full details.


## Reminder

This program needs to be connected to several independent services, needing several sensitive tokens searched among environments variables. We usually use [`python-dotenv`](https://pypi.org/project/python-dotenv/) to read them from a `.env` file at your program root, but you can export them as usual environment variables if you prefer.

All necessary variables are listed in the [`model.env`](model.env) file. Change their value according to the following instructions and rename the file as `.env`, or export them directly.


## Instructions


### Step 1: Database connection

This program needs to be connected to a database.

Since it uses SQLAlchemy, every language it supports can theoretically be used, but the package has been developed and tested with PostgreSQL (otherwise, you may need to install complementary packages such as PyMySQL).

You will need an empty database, local or on a specified host. The database schema will be created by the bot the first time it runs. Put your database URI (`protocol://user:password@host/base`) in the `.env` file (`LGREZ_DISCORD_TOKEN` variable).


### Step 2-4: Discord application, server and scheduled tasks webhook

#### First use
* If not already done, create a new Bot application on [the Discord Developer Portal](https://discord.com/developers/applications)
* Generate a new "client secret" on your app main page. This token gives anyone full access to your bot, so don't leak it! Put it in the `.env` file (`LGREZ_DISCORD_TOKEN` variable).

#### For each season

* Create a new Discord server. We provide the following model, with recommanded channels and permissions: https://discord.new/RPGXChXXcKQZ. Unfortunately, a Discord model doesn't contain the following:
    * Icon: create your own!
    * Emojis: the bot itself needs a few custom emojis to work correctly. We provide them in [the Templates folder](https://drive.google.com/drive/folders/1kjHzUSp-QfgI77Yg0GCxdM6YcFkHPYVw) (described below). Download them, go in your server settings / Emoji / Upload emoji and select them all; they well be named correctly.
* Put the server ID (can be found in the "Widget" tab of your server settings) in the `.env` file (`LGREZ_SERVER_ID` variable)
* Add the bot to your server:
    * Go to the Discord Developer Portal, select your bot application;
    * Go to the OAuth2 tab, select the "bot" scope and clic "Copy". Bot permissions are not important in our settings;
    * Open the copied URL in your browser and select your newly created server.
* Go back to Discord and give the "Bot" role to the bot account. That will grant him every needed permissions.
* This bot supports task postponing. This feature requires a "webhook" (a protocol to post messages externally to a channel), called at scheduled time to trigger bot reaction. Create a new webhook (Parameters / Integrations / Webhooks) posting on the `#logs` channel and copy its URL into the `.env` file (`LGREZ_WEBHOOK_URL` variable).

(For your first tests, note that the bot ignore every messages posted by member without any role! Assign yourself the "MJ" role to get every rights with the bot)


### Steps 5-7: Google Sheets creation, GCP connection and dashboard setup

This bot works with Google Sheets worksheets to gather players orders and resolve play situations. We provide a readonly Google Drive folder with every needed files: [Templates](https://drive.google.com/drive/folders/1kjHzUSp-QfgI77Yg0GCxdM6YcFkHPYVw)

#### First use

* Duplicate all files into your own folder (right clic > Create a copy) and open them. Copy their IDs (the URL part between `/d/` and `/edit`) into the `.env` file (`LGREZ_TDB_SHEET_ID`, `LGREZ_ROLES_SHEET_ID` and `LGREZ_DATA_SHEET_ID` variables);
* In the "Tableau de bord" sheet, edit the AN1 and BG1 cells to put the URLs of the "Données brutes" and "Rôles et actions" sheets, respectively. You should be prompted to grant access to those files, do it;

* The bot needs a "special" Google account to access those files. Create a new projet on [Google Cloud Platform](https://console.cloud.google.com/home/dashboard) (you may need extra steps if you use GCP for the first time). Follow the basic setup guide, then open the "IAM & Admin" pane, go to "Service Accounts" and create a new service account. Name it as you wish, then open it and create a new key ("Keys"/"Add key"). Open the JSON file, paste its contents into the `.env` file (`LGREZ_GCP_CREDENTIALS` variable) and delete it;
* Share the three sheets (or the whole folder) with the service account mail adress (account@project.iam.gserviceaccount.com) with Editor rights.

#### For each season

* Create a new "Tableau de bord" file. The faster way is to duplicate it again from our template folder and put the URLs, but you may prefer duplicate one of your previous seasons and remove players and sheets: in this case, remember to remove cached properties of players (A-I columns);
* Open the scripts of the new file ("Tools/Scripts editor"), and select "Edit/Triggers of this project". This page allows you to automatically backup and clear the "Tableau de bord" each day: when the season starts, clic "Add a trigger" and configure it: Backupfeuille / Head / Temporal trigger / Daily / Between 1am and 2am (important, because the data sheet clears data between 3pm and 4pm).
