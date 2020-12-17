"""Loup-Garou de la Rez (lg-rez)

Discord bot for organizing boisterous Werewolf RP games ESPCI-style.

See github.com/loic-simon/lg-rez for informations.
"""

__title__ = "lg-rez"
__author__ = "Loïc Simon, Tom Lacoma"
__license__ = "MIT"
__copyright__ = "Copyright 2020 Loïc Simon & Tom Lacoma – Club BD-Jeux × GRIs – ESPCI Paris - PSL"
__version__ = "1.2.0"

from lgrez import bot
LGBot = bot.LGBot                        # Accès direct à lgrez.LGBot

__all__ = ["LGBot"]
