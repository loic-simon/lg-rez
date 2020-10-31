"""lg-rez / Commandes et autres fonctionnalités

Chaque module de ``lgrez.features`` implémente une fonctionnalité spécifique des LGBots. La majorité implémentent un *Cog* (:class:`discord.ext.commands.Cog`) contenant une ou plusieurs commandes Discord, mais peuvent aussi définir des fonctions pour un usage public.

.. note ::

    Les Cogs et leurs commandes peuvent être vus en envoyant ``!help`` à un LGBot fonctionnel (en possédant les rôles `MJ` et `Joueur en vie`)

"""

__all__ = ["actions_publiques", "annexe", "gestion_actions", "IA", "informations", "inscription", "open_close", "remplissage_bdd", "sync", "taches", "voter_agir"]
