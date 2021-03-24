"""lg-rez / Commandes et autres fonctionnalités

Chaque module de ``lgrez.features`` implémente une fonctionnalité
spécifique des LGBots. La majorité implémentent un *Cog*
(:class:`discord.ext.commands.Cog`) contenant une ou plusieurs
commandes Discord, mais peuvent aussi définir des fonctions pour
un usage public.

.. note ::

    Les Cogs et leurs commandes peuvent être vus en envoyant ``!help``
    à un LGBot fonctionnel (en possédant les rôles :attr:`.config.Role.mj`
    et :attr:`.config.Role.joueur_en_vie`)

"""

import os

dir = os.path.dirname(os.path.realpath(__file__))

__all__ = []
for file in os.listdir(dir):
    if not file.endswith(".py"):
        # Not a Python file
        continue

    name = file[:-3]
    if name.startswith("_"):
        # Private / magic module
        continue

    # Public submodule: add to __all__
    __all__.append(name)
