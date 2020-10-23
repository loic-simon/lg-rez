Référence de l'API
=====================

Bot
----------------

LGBot
~~~~~~~~~~

.. autoclass:: lgrez.LGBot
    :members:


Commandes spéciales
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lgrez.bot.Special
    :members:

    Cette classe est un **Cog**, *i.e.* un rassemblements de commandes.

    L'ensemble des commandes qu'elle contient, créées par le décorateur :py:func:`@discord.ext.commands.command`, sont des objets :py:class:`discord.ext.commmands.Command` accessibles comme ``cog.cmd_name``.

    Pour plus de lisiblité, seules les fonctions appellées lors de l'invoquation des commandes (:py:meth:~`discord.ext.commmands.Command.callback`) sont décrites ci-après, mais toutes les méthodes de :py:class:~`discord.ext.commmands.Command` sont évidemment accessibles.

    Ces *callbacks* prennent toutes comme premier argument ``ctx`` (:py:class:`discord.ext.commmands.Context`), le **contexte d'invocation** de la commande. Cet argument est construit automatiquement par ``discord.py`` à l'appel de :py:meth:~`discord.ext.commmands.Bot.invoke_commands` puis passé au callback suivi des arguments entrés par l'utilisateur (à la manière d'une utilisation en ligne de commande).

    .. automethod:: lgrez.bot.Special.do.callback
    .. automethod:: lgrez.bot.Special.shell.callback
    .. automethod:: lgrez.bot.Special.co.callback
    .. automethod:: lgrez.bot.Special.doas.callback
    .. automethod:: lgrez.bot.Special.secret.callback
    .. automethod:: lgrez.bot.Special.stop.callback
    .. automethod:: lgrez.bot.Special.help.callback


Fonctionnalités
-----------------

.. automodule:: lgrez.features

.. toctree::
   :maxdepth: 3

   features


Blocs
-----------------

.. automodule:: lgrez.blocs

.. toctree::
   :maxdepth: 3

   blocs
