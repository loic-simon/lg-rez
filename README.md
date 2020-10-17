# lg-rez

*(Français)* lg-rez est un programme Python (pas vraiment un module, un jour peut-être) pour organiser des parties endiablées de Loup-Garou à la PCéenne.

*(English)* lg-rez is a Python program (not really a library, maybe someday) for organizing boisterous Werewolf RP games ESPCI-style.

## Installation

### Python

Don't use the package manager [pip](https://pypi.org/project/pip/) to install lg-rez. Really, don't. It won't work.

~~```pip install lg-rez```~~

You can not really install this at the moment. If you really want, though, use a 3.6+ Python interpreter and install all packages required when running `bot.py`.

This program needs to be connected to a database and several other environments variables. All necessary variables are listed in the `model.env` file ; change their value and rename the file as `.env`. You will need a Google Cloud Platform adress with Google Sheets editor rights and access to every docs.


### Discord server and bot

General:
* If not already done, create a new Bot application on [the Discord Developer Portal](https://discord.com/developers/applications)
* Put your application "client secret" in the `.env` file (`DISCORD_TOKEN` variable)

For each server:
* Create a new Discord server. We provide the following model, with recommanded channels and permissions: https://discord.new/RPGXChXXcKQZ
* Put the server ID (can be found in the "Widget" tab of your server parameters) in the `.env` file (`DISCORD_GUILD_ID` variable)
* Add the bot to your server:
    * Go to the Discord Developer Portal, select your bot application;
    * Go to the OAuth2 tab, select the "bot" scope and clic "Copy". Bot permissions are not important in our settings;
    * Open the copied URL in your browser and select your newly created server.
* Go back to Discord and give the "Bot" role to the bot account. That will grant him every needed permissions.
* Create tho new webhooks (Parameters / Integrations / Webhooks) posting on the `#logs` channel, one for the planified tasks calls and one for the dashboard synchronisation calls. Copy their URLs onto the `.env` file (`WEBHOOK_TP_URL` and `WEBHOOK_SYNC_URL` variables, respectively).

(For your first tests, note that the bot ignore every messages posted by member without any role!)


## Contributing

Pull requests are not welcome. Contact the authors for any question about this (half-private) project.

## License
This work is shared under [the MIT license](https://choosealicense.com/licenses/mit/).

© 2020 Loïc Simon, Tom Lacoma et al. – Club BD-Jeux × GRIs – ESPCI Paris - PSL

Reach us on Discord: [LaCarpe#1674](https://discordapp.com/users/264482202966818825), [TaupeOrAfk#3218](https://discordapp.com/users/176763552202358785) or by mail: [loic.simon@espci.org](mailto:loic.simon@espci.org)
