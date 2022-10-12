"""lg-rez / features / Tâches planifiées

Planification, liste, annulation, exécution de tâches planifiées

"""

import datetime

import discord
from discord import app_commands

from lgrez import commons
from lgrez.blocs import tools
from lgrez.bdd import Tache, Action
from lgrez.blocs.journey import DiscordJourney, journey_command
from lgrez.features import communication


DESCRIPTION = """Commandes de planification, exécution, annulation de tâches"""


class TimestampTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> datetime.datetime:
        now = datetime.datetime.now()

        for format in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y %Hh%M", "%d/%m/%Y %Hh"]:
            try:
                return datetime.datetime.strptime(value, format)
            except ValueError:
                continue

        for format in ["%d/%m %H:%M:%S", "%d/%m %H:%M", "%d/%m %Hh%M", "%d/%m %Hh"]:
            try:
                return datetime.datetime.strptime(value, format).replace(year=now.year)
            except ValueError:
                continue

        for format in ["%H:%M:%S", "%H:%M", "%Hh%M", "%Hh"]:
            try:
                return datetime.datetime.strptime(value, format).replace(year=now.year, month=now.month, day=now.day)
            except ValueError:
                continue

        raise commons.UserInputError("quand", "Format invalide (doit être [DD/MM[/YYYY]] HH:MM[:SS]")

    async def autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not current:
            return [
                app_commands.Choice(name="Demain 7h", value="7:01"),
                app_commands.Choice(name="Demain 9h", value="9:01"),
            ]
        return []


@app_commands.command()
@tools.mjs_only
@journey_command
async def taches(journey: DiscordJourney):
    """Liste les tâches actuellement planifiées (COMMANDE MJ)

    Affiche les commandes en attente d'exécution et le timestamp d'exécution associé.
    Lorsque la tâche est liée à une action, affiche le nom de l'action et du joueur concerné.
    """
    lst: list[Tache] = Tache.query.order_by(Tache.timestamp).all()
    rep = ""
    for tache in lst:
        rep += f"\n{str(tache.id).ljust(5)} {tache.timestamp:%d/%m/%Y %H:%M:%S}    {tache.description.ljust(25)} "
        if action := tache.action:
            rep += f"{action.base.slug.ljust(20)} {action.joueur.nom}"

    if rep:
        prefix = "Tâches en attente :"
        mess = (
            "ID    Timestamp              Commande                  Action               Joueur\n"
            f"{'-' * 105}{rep}\n\n"
            "Utilisez /cancel <ID> pour annuler une tâche."
        )
    else:
        prefix = "Aucune tâche en attente."
        mess = ""

    await journey.send(mess, code=True, prefix=prefix)


planif = app_commands.Group(name="planif", description="Planification de commandes")


async def _planif(journey: DiscordJourney, quand: datetime.datetime, command: app_commands.Command, **parameters):
    mess = ""
    if quand < datetime.datetime.now():
        quand = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=1), quand.time())
        mess = ":warning: Date dans le passé, décalée à demain\n"

    tache = await planif_command(quand, command, **parameters)

    await journey.send(
        mess
        + f":arrow_forward: Commande `{tache.description}` planifiée pour le {quand:%d/%m/%Y} à {quand:%H:%M:%S}.\n"
        f"`/cancel {tache.id}` pour annuler."
    )


async def planif_command(timestamp: datetime.datetime, command: app_commands.Command, **parameters) -> Tache:
    action = None
    # ID de l'action associée à la tâche le cas échéant
    if command.name == "action" and (id := parameters.get("id")):  # open / close / remind
        action = Action.query.get(int(id))

    tache = Tache(timestamp=timestamp, commande=command.qualified_name, parameters=parameters, action=action)
    tache.add()  # Planifie la tâche
    return tache


@planif.command()
@tools.mjs_only
@journey_command
async def post(
    journey: DiscordJourney,
    *,
    quand: app_commands.Transform[datetime.datetime, TimestampTransformer],
    chan: discord.TextChannel,
    message: str,
):
    """Planifie l'envoi d'un message dans un salon (raccourci pour /planif command, COMMANDE MJ)

    Args:
        quand: Quand planifier la commande (date optionnelle, défaut aujourd’hui, année / minutes / secondes aussi).
        chan: Salon ou poster le message.
        message: Message à envoyer (utiliser "\n" pour un saut de ligne).

    Si la date spécifiée est dans le passé, la commande est planifiée pour le lendemain.
    """
    await _planif(journey, quand, communication.post, chan=chan, message=message)


@planif.command()
@tools.mjs_only
@journey_command
async def command(journey: DiscordJourney, *, quand: app_commands.Transform[datetime.datetime, TimestampTransformer]):
    """Planifie l'exécution d'une commande quelconque (COMMANDE MJ)

    Args:
        quand: Quand planifier la commande (date optionnelle, défaut aujourd’hui, année / minutes / secondes aussi).

    Ne pas planifier de commandes avec confirmation / modale !

    Si la date spécifiée est dans le passé, la commande est planifiée pour le lendemain.
    """
    interaction, _runner = await journey.catch_next_command("Exécuter la commande à planifier")
    journey.interaction = interaction
    await _planif(journey, quand, interaction.command, **dict(iter(interaction.namespace)))


@app_commands.command()
@tools.mjs_only
@journey_command
async def cancel(journey: DiscordJourney, *, id: int):
    """Annule une tâche planifiée (COMMANDE MJ)

    Args:
        id: ID de la tâche à annuler (voir /taches).

    Utiliser ``!taches`` pour voir la liste des IDs.
    """
    if tache := Tache.query.get(int(id)):
        tache.delete()
        await journey.send(f"Tâche annulée :\n```/planif command {tache.timestamp:%d/%m/%Y %X}\n{tache.description}```")
    else:
        await journey.send(f":x: Tâche #{id} introuvable.")
