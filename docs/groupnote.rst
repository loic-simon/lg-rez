.. note::
    Cette commande est un **Groupe** (:class:`discord.ext.commands.Group`),
    *i.e.* une commande composée de plusieurs sous-commandes (ou *options*).

    Les sous-commandes, créées par le décorateur
    :func:`@\<group\>.command <discord.ext.commands.Group.command>`
    (ou :func:`@\<group\>.group <discord.ext.commands.core.Group.group>`
    pour ajouter un niveau), sont également des objets
    :py:class:`~discord.ext.commands.Command` accessibles via
    :meth:`<group>.get_command <discord.ext.commands.Group.get_command>`
    et la note relative aux cogs (callback, signature...) s'applique.
