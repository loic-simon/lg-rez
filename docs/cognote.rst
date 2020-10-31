.. note::
    Cette classe est un **Cog**, *i.e.* un rassemblements de commandes.

    L'ensemble des commandes qu'elle contient, créées par le décorateur :py:func:`@discord.ext.commands.command <discord.ext.commands.command>`, sont des objets
    :py:class:`discord.ext.commands.Command` accessibles comme ``cog.cmd_name``.

    Pour plus de lisiblité, seules les fonctions appellées lors de l'invoquation des commandes (:py:attr:`Command.callback <discord.ext.commands.Command.callback>`) sont décrites ci-après, mais toutes les méthodes de :py:class:`~discord.ext.commands.Command` sont évidemment accessibles.

    Ces *callbacks* ont tous comme signature (sans compter ``self`` si définies dans un Cog) :

    .. code-block:: py

        async def command(ctx, [ arg1, [..., argN,] ] [{*args | *, rest}]) -> None

    avec
        - ``ctx`` (:class:`discord.ext.commands.Context`) le **contexte d'invocation** de la commande, construit automatiquement par ``discord.py`` à l'appel de :py:meth:`Bot.process_commands <discord.ext.commands.Bot.process_commands>` ou :py:meth:`Bot.get_context <discord.ext.commands.Bot.get_context>`, puis
        - ``arg1, ..., argN`` (:class:`str`) zéro, un ou plusieurs arguments(s) positionnels parsés à partir du texte entré par l'utilisateur (mots séparés par des espaces) ;
        - ``args`` (:class:`list`\[:class:`str`\]) un nombre arbitraire d'arguments, OU
        - ``rest`` (:class:`str`) le texte restant après le traitement des arguments positionnels.

    Une exception dérivant de :class:`discord.ext.commands.UserInputError` est levée en cas d'utilisation incorrecte (puis traitée par :meth:`.LGBot.on_command_error`).
