"""lg-rez bot features

Each file in this module implements a specific feature of LGBot bots.
Most of them implement a discord.py cog (discord.ext.commands.Cog) containing
one or more Discord commands, but may also define functions for internal or
external use.

Note: you can see cogs names and the commands they contain by sending "!help"
to a functionnal LGBot after granting yourself "MJ" and "Joueur en vie" roles.
"""

__all__ = ["actions_publiques", "annexe", "gestion_actions", "IA", "informations", "inscription", "open_close", "remplissage_bdd", "sync", "taches", "voter_agir"]
