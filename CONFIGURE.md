# lg-rez manual configuration instructions

**Important notice**: we alternatively provide an assistant tool to help you
 configure your bot. See the *Configure* section of [`README.md`](README.md)
 for full details.



## Reminder

This program needs to be connected to several independent services, needing
several sensitive tokens searched among environments variables. We support
and encourage the use of
[`python-dotenv`](https://pypi.org/project/python-dotenv) to read them from
a `.env` file located at your program root, but you can export them as usual
environment variables if you prefer.

All necessary variables are listed in [`model.env`](model.env). Download it
at the root of your program, set the values of the variables according to the
following instructions and rename the file as `.env` (or export them).



## Instructions

### Step 1: Database connection

This program needs to be connected to a database.

Since it uses SQLAlchemy, every dialect it supports (see
[list](https://docs.sqlalchemy.org/en/13/dialects)) can theoretically be used,
but the package has been developed and tested with PostgreSQL only: for other
dialects, you may need to install complementary drivers packages (such as
PyMySQL).

You will need an empty database, local or on a specified host. The database
schema will be created by the bot the first time it runs. Your database URI
(`dialect[+driver]://user:password@host/base`) is the **`LGREZ_DISCORD_TOKEN`
variable**.


### Step 2-4: Discord application, server and scheduled tasks webhook

#### First use

* If not already done, create a new Bot application on
  [the Discord Developer Portal](https://discord.com/developers/applications)
* Name it as you wish (you will be able to rename the bot in your
  server after) and click "Add bot" under the "Bot" section.
* Here, turn on the two options under "Privilegied Gateway Intents".
  You may want to uncheck "Public bot" too to have finest control.
* Then, clic "Copy" under the "Token" session and paste it as the
  **`LGREZ_DISCORD_TOKEN` variable**. This token gives anyone
  full access to your bot, so don't leak it!

#### For each season

* Create a new Discord server. We provide the following Server model,
  initializing recommanded channels, roles and permissions organization:
  https://discord.new/RPGXChXXcKQZ. \
  Unfortunately, a Discord model doesn't contain the following:
    * Icon: create your own!
    * Emojis: the bot itself needs a few custom emojis to work correctly.
      We provide them in
      [the Templates folder](https://drive.google.com/drive/folders/1kjHzUSp-QfgI77Yg0GCxdM6YcFkHPYVw)
      (described below). Download them, go in your server settings / Emoji /
      Upload emoji and select them all; they well be named correctly.
* Write the server ID (can be found in the "Widget" tab of your server
  settings) as **`LGREZ_SERVER_ID` variable**;
* Add the bot to your server:
    * Go to the Discord Developer Portal, select your bot application;
    * Go to the OAuth2 tab, select the "bot" scope and clic "Copy". Bot
      permissions are not important in our settings;
    * Open the copied URL in your browser, select your newly created server
      and clic "Authorize".
* Go back to Discord and give the "Bot" role to the bot account. That will
  grant him every needed permissions.
* This bot supports task postponing. This feature requires a "webhook" (a
  protocol to post messages externally to a channel), called at scheduled time
  to trigger bot reaction. Create a new webhook (Server settings / Integrations /
  Webhooks) posting on the `#logs` channel and copy its URL into
  **`LGREZ_WEBHOOK_URL` variable**.

(For your first tests, note that the bot ignore every messages posted by
member without any role! Assign yourself the "MJ" role to get every
rights with the bot)


### Steps 5-7: Google Sheets creation, GCP connection and dashboard setup

This bot works with Google Sheets worksheets to gather players orders and
resolve play situations. We provide a readonly Google Drive folder with every
needed files:
https://drive.google.com/drive/folders/1kjHzUSp-QfgI77Yg0GCxdM6YcFkHPYVw

#### First use

* Duplicate all files into your own folder (right clic > Create a copy) and
  open them. Save their IDs (the URL part between `/d/` and `/edit`) as
  **`LGREZ_TDB_SHEET_ID`, `LGREZ_ROLES_SHEET_ID` and `LGREZ_DATA_SHEET_ID`
  variables**.;
* In the "Tableau de bord" sheet, edit the AN1 and BG1 cells to put the URLs
  of the "Données brutes" and "Rôles et actions" sheets, respectively.
  Once done, `#REF!` should appear in AH3 and BH4 cells (among other).
  A tooltip should appear when clicking on them, asking you to grant
  access to those files: do it.

* The bot needs a "special" Google account to access those files. Create a new
  projet on
  [Google Cloud Platform](https://console.cloud.google.com/home/dashboard)
  (you may need extra steps if you use GCP for the first time). Follow the
  basic setup guide, then open the "IAM & Admin" pane, go to "Service Accounts"
  and create a new service account. Name it as you wish, then open it and
  create a new key ("Keys"/"Add key"). Open the JSON file, paste its contents
  into the **`LGREZ_GCP_CREDENTIALS` variable** (remove pretty-printing
  newlines and escape double quotes) and delete it;
* Share the three sheets (or the whole folder) with the service account mail
  adress (account@project.iam.gserviceaccount.com) with Editor rights.
* *NOTE: if your GCP project is newly created, you may first encourter an
  error containing a link to visit to enable Google Sheets API for your
  project.*

#### For each season

* Create a new "Tableau de bord" file. The faster way is to duplicate it again
  from our template folder and put the URLs, but you may prefer duplicate one
  of your previous seasons and remove players and sheets: in this case,
  remember to remove cached properties of players (A-I columns);
* Now, open the scripts editor ("Tools/Scripts editor"), select
  the "Triggers" tab on the left (alarm clock).
  This tab will allow us to automatically backup and clear the dashboard
  each day: clic "Add a trigger" and configure it like (left, up to down):
  Backupfeuille / Head / Time trigger / Daily / Between 1am and 2am
  (important, because the data sheet clears itself between 3pm and 4pm).

  You may want to do that later, as it will create a new worksheet each
  day (except weekends) while enabled.


### Next steps

The installation should now be complete! See [`README.md`](README.md) for the
minimal code needed to run the bot.

The bot execution is quiet, except at startup and if an exception occurs,
so we advise you to log the output stream somewhere!
We also advise you to use an external script to ensure the bot has not
crashed (pretty unlikely, but it might always happen; see also
[`output_liveness` customization option](https://lg-rez.readthedocs.io/fr/2.0.0/config.html#lgrez.config.output_liveness)).

You can no try to interact with the bot!
(For your first tests, note that the bot ignore every messages posted by a
member without any role! Assign yourself the "MJ" role to get full rights
with the bot.)

Do not hesitate to reach us for any issue or suggestion, we're always happy
to get news. See bottom of README for contacts.

Enjoy!
