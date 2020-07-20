# lg-rez

:fr: lg-rez est un programme Python (pas vraiment un module, un jour peut-être) pour organiser des parties endiablées de Loup-Garou à la PCéenne.

:uk: lg-rez is a Python program (not really a library, maybe someday) for organizing boisterous Werewolf RP games ESPCI-style.

## Installation

Don't use the package manager [pip](https://pypi.org/project/pip/) to install lg-rez. Really, don't. It won't work.

~~```pip install foobar```~~

You can not really install this at the moment. If you really want, though, use a 3.6+ Python interpreter and install all packages required when running `bot.py`.

If you want the online part to be functional, run it on a uWGSI server. We use, for example, the French host [alwaysdata](https://www.alwaysdata.com/fr/) with a Flask application on a free plan.

Online or not, this program needs to be connected to a database and several other environments variables. All necessary variables are listed in the `model.env` file ; change their value and rename the file as `.env`. You will need a Google Cloud Platform adress with Google Sheets editor rights and... wait, why am I writing this? It's totally useless



## Contributing
Pull requests are not welcome. Contact the authors for any question about this (half-private) project.

## License
[MIT](https://choosealicense.com/licenses/mit/)
© 2020 Loïc Simon, Tom Lacoma et al. – Club BD-Jeux × GRIs – ESPCI Paris - PSL

Reach us on Discord: [LaCarpe#1674](https://discordapp.com/users/264482202966818825), [TaupeOrAfk#3218](https://discordapp.com/users/176763552202358785) or by mail: [loic.simon@espci.org](mailto:loic.simon@espci.org)
