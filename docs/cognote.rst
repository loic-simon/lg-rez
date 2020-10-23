.. |cog| replace::
    .. note::
        Cette classe est un **Cog**, *i.e.* un rassemblements de commandes.

        L'ensemble des commandes qu'elle contient, créées par le décorateur :py:function:`discord.ext.commands.command`, sont des objets :py:class:`discord.ext.commands.Command` accessibles comme ``cog.cmd_name``.

        Pour plus de lisiblité, seules les fonctions appellées lors de l'invoquation des commandes (:py:attr:`Command.callback <discord.ext.commands.Command.callback>`) sont décrites ci-après, mais toutes les méthodes de :py:class:`~discord.ext.commands.Command` sont évidemment accessibles.

        Ces *callbacks* prennent comme premier argument ``ctx`` (:py:class:`discord.ext.commands.Context`), le **contexte d'invocation** de la commande. Cet argument est construit automatiquement par ``discord.py`` à l'appel de :py:meth:`Bot.process_commands <discord.ext.commands.Bot.process_commands>` ou :py:meth:`Bot.get_context <discord.ext.commands.Bot.get_context>`, puis passé au callback suivi des arguments entrés par l'utilisateur.
