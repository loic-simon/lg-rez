"""lg-rez / blocs / Limitation à une commande

Système maison pour ne pas pouvoir utiliser plus d'une commande
à la fois

"""

import asyncio

from discord.ext import commands

from lgrez import config


#: list[~discord.ext.command.Command]: Commands exempted from
#: one_command limitation, registered by :func:`.do_not_limit`
exempted = []


class AlreadyInCommand(commands.CheckFailure):
    """Salon déjà occupé par une commande non finissable.

    Exception levée lorsqu'un membre veut lancer une commande dans un
    salon où une commande est déjà en cours d'exécution, et que cette
    commande n'a pas pu être arrêtée (ou pas assez rapidement) par
    un message ``"stop"``.

    Dérive de :exc:`discord.ext.commands.CheckFailure`.
    """
    pass


async def not_in_command(ctx):
    """Check : assure qu'une commande n'est pas en cours dans ce salon.

    Fonction à utiliser comme check global, pour toutes les commandes
    (enregistrer avec :meth:`~discord.ext.commands.Bot.add_check`)

    Args:
        ctx (discord.ext.commands.Context): contexte d'invocation
            de la commande.

    Returns:
        ``True``

    Raises:
        :exc:`AlreadyInCommand`.
    """
    if ctx.command in exempted:
        return True         # Commandes exemptées
    if ctx.channel.id not in config.bot.in_command:
        return True         # Channel libre

    # On envoie (discrètement) l'ordre d'arrêter la commande précédente
    await ctx.send(config.stop_keywords[0], delete_after=0)
    # On attend qu'il soit pris en compte
    await asyncio.sleep(1)

    if ctx.channel.id in config.bot.in_command:    # Si ça n'a pas suffit
        raise AlreadyInCommand()                    # on raise l'erreur

    return True


# @bot.before_invoke
async def add_to_in_command(ctx):
    """Ajoute le channel à la liste des channels dans une commande.

    Fonction à appeller avant chaque appel de fonction
    (enregistrer avec :meth:`~discord.ext.commands.Bot.before_invoke`)

    Elle est appellée seulement si les checks sont OK, donc pas si le
    salon est déjà dans :attr:`config.bot.in_command <.LGBot.in_command>`.

    Args:
        ctx (discord.ext.commands.Context): contexte d'invocation de
            la commande.
    """
    if ctx.command not in exempted and not ctx.message.webhook_id:
        config.bot.in_command.append(ctx.channel.id)


# @bot.after_invoke
async def remove_from_in_command(ctx):
    """Retire le channel de la liste des channels dans une commande.

    Fonction à appeller après chaque appel de fonction.
    (enregistrer avec :meth:`~discord.ext.commands.Bot.after_invoke`)

    Elle attend 0.1 secondes avant d'enlever le joueur afin d'éviter
    que le bot réagisse « nativement » (IA) à un message déjà traité
    par un :func:`.tools.wait_for_message` ayant mené à la fin de la
    commande.

    Args:
        ctx (discord.ext.commands.Context): contexte d'invocation de
            la commande.
    """
    await asyncio.sleep(0.1)        # On attend un peu
    if (ctx.channel.id in config.bot.in_command
        and ctx.command not in exempted):

        config.bot.in_command.remove(ctx.channel.id)


class _Bypasser():
    def __init__(self, ctx):
        self.ctx = ctx

    def __enter__(self):
        config.bot.in_command.remove(self.ctx.channel.id)
        return self

    def __exit__(self, exc_type, exc, tb):
        config.bot.in_command.append(self.ctx.channel.id)


def bypass(ctx):
    """Context manager: bypass one-command limitation.

    Args:
        ctx (discord.ext.commands.Context): running command context.

    Use in a command callback to launch a second one without problems::

        with one_command.bypass(ctx):
            await config.bot.process_commands(some_message)

    """
    return _Bypasser(ctx)


def do_not_limit(command):
    """Decorator for commands not concerned by one_command limitation.

    Register the command in :attr:`.one_command.exempted`.

    Args:
        command (discord.ext.commands.Command): the command to register.

    Returns:
        :class:`discord.ext.commands.Command`
    """
    if not isinstance(command, commands.Command):
        raise TypeError("one_command.not_limited is a decorator for Commands")

    exempted.append(command)
    return command
