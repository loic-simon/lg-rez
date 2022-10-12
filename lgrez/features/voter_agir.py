"""lg-rez / features / Tâches planifiées

Planification, liste, annulation, exécution de tâches planifiées

"""

import datetime

import discord
from discord import app_commands

from lgrez import config, commons
from lgrez.blocs import env, gsheets, tools
from lgrez.bdd import (
    Joueur,
    Action,
    Role,
    Camp,
    Utilisation,
    Ciblage,
    BaseCiblage,
    CandidHaro,
    CandidHaroType,
    UtilEtat,
    CibleType,
    Vote,
)
from lgrez.blocs.journey import DiscordJourney, journey_command
from lgrez.features import gestion_actions


async def export_vote(vote: Vote | None, utilisation: Utilisation) -> None:
    """Enregistre un vote/les actions résolues dans le GSheet ad hoc.

    Écrit dans le GSheet ``LGREZ_DATA_SHEET_ID``. Peut être écrasé
    pour une autre implémentation.

    Args:
        vote: le vote concerné, ou ``None`` pour une action.
        utilisation: l'utilisation qui vient d'être effectuée.
            Doit être remplie (:attr:`.bdd.Utilisation.is_filled`).

    Raises:
        RuntimeError: si la variable d'environnement ``LGREZ_DATA_SHEET_ID``
            n'est pas définie.

    Note:
        Fonction asynchrone depuis la version 2.2.2.
    """
    if vote and not isinstance(vote, Vote):
        vote = Vote[vote]  # str -> Vote

    joueur = utilisation.action.joueur
    match vote:
        case Vote.cond:
            sheet_name = config.db_votecond_sheet
            data = [joueur.nom, utilisation.cible.nom]
        case Vote.maire:
            sheet_name = config.db_votemaire_sheet
            data = [joueur.nom, utilisation.cible.nom]
        case Vote.loups:
            sheet_name = config.db_voteloups_sheet
            data = [joueur.nom, joueur.camp.slug, utilisation.cible.nom]
        case _:
            sheet_name = config.db_actions_sheet
            recap = "\n+\n".join(
                f"{action.base.slug}({last_util.decision})"
                for action in joueur.actions_actives
                if (
                    (last_util := action.derniere_utilisation)
                    and last_util.is_filled  # action effectuée
                    and last_util.ts_decision.date() == datetime.date.today()
                )
            )
            data = [joueur.nom, joueur.role.slug, joueur.camp.slug, recap]

    LGREZ_DATA_SHEET_ID = env.load("LGREZ_DATA_SHEET_ID")
    workbook = await gsheets.connect(LGREZ_DATA_SHEET_ID)
    sheet = await workbook.worksheet(sheet_name)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await sheet.append_row([timestamp, *data], value_input_option="USER_ENTERED")


async def check_last_utilisation(
    action: Action, base_ciblage: BaseCiblage, cible: Joueur | Role | Camp | bool | str
) -> None:
    """Demande une cible à l'utilisateur.

    Args:
        ctx: le contexte de commande.
        action: action pour laquelle on cherche une cible.
        base_ciblage: ciblage à demander.
        first: proposition initiale du joueur (passée comme argument d'une commande).

    Returns:
        La cible sélectionnée, selon le type de ciblage.

    Réalise les interactions adéquates en fonction du type du base_ciblage,
    vérifie le changement de cible le cas échéant.
    """
    if not base_ciblage.doit_changer:
        return

    derniere_util = action.utilisations.filter(~Utilisation.is_open).order_by(Utilisation.ts_close.desc()).first()
    if derniere_util and derniere_util.etat == UtilEtat.validee:
        # Dernière utilisation validée : comparaison avec ciblages
        # de même prio que le ciblage en cours de demande
        cibles = [cib.valeur for cib in derniere_util.ciblages if cib.base.prio == base_ciblage.prio]

        if cible in cibles:  # interdit !
            raise commons.UserInputError(
                "cible",
                f":stop_sign: {cible} déjà ciblé(e) lors de la précédente utilisation, merci de changer :stop_sign:\n"
                "*(`@MJ` si contestation)*",
            )


DESCRIPTION = """Commandes de vote et d'action de rôle"""


async def do_vote(journey: DiscordJourney, vote: Vote, votant: Joueur, cible: Joueur, ephemeral: bool = False):
    match vote:
        case Vote.cond:
            vote_name = "le condamné du jour"
            pour_contre = "conte"
        case Vote.maire:
            vote_name = "le nouveau maire"
            pour_contre = "pour"
        case Vote.loups:
            vote_name = "la victime du soir"
            pour_contre = "contre"

    try:
        vaction = votant.action_vote(vote)
    except RuntimeError:
        await journey.send(":x: Minute papillon, le jeu n'est pas encore lancé !", ephemeral=ephemeral)
        return

    # Vérification vote en cours
    if not votant.votant_village:
        await journey.send(":x: Tu n'as pas le droit de participer à ce vote.", ephemeral=ephemeral)
        return
    if not vaction.is_open:
        await journey.send(f":x: Pas de vote pour {vote_name} en cours !", ephemeral=ephemeral)
        return

    util = vaction.derniere_utilisation

    # Test si la cible est sous le coup d'un haro / candidate
    if vote == Vote.cond and not CandidHaro.query.filter_by(joueur=cible, type=CandidHaroType.haro).first():
        await journey.send(
            f"{cible.nom} n'a pas (encore) subi ou posté de haro ! "
            "Si c'est toujours le cas à la fin du vote, ton vote sera compté comme blanc... \n"
            "Veux-tu continuer ?",
            ephemeral=ephemeral,
        )
    elif vote == Vote.maire and not CandidHaro.query.filter_by(joueur=cible, type=CandidHaroType.candidature).first():
        await journey.send(
            f"{cible.nom} ne s'est pas (encore) présenté(e) ! "
            "Si c'est toujours le cas à la fin de l'élection, ton vote sera compté comme blanc... \n"
            "Veux-tu continuer ?",
            ephemeral=ephemeral,
        )

    if not vaction.is_open:
        # On revérifie, si ça a fermé entre temps !!
        await journey.send(f":x: Le vote pour {vote_name} a fermé entre temps, pas de chance !", ephemeral=ephemeral)
        return

    # Modification en base
    if util.ciblages:  # ancien ciblage
        Ciblage.delete(*util.ciblages)
    Ciblage(utilisation=util, joueur=cible).add()
    util.ts_decision = datetime.datetime.now()
    util.etat = UtilEtat.remplie
    util.update()

    # Écriture dans sheet Données brutes
    await export_vote(vote, util)

    await journey.send(
        f"Vote {pour_contre} {tools.bold(cible.nom)} bien pris en compte.\n"
        + tools.ital("Tu peux modifier ton vote autant que nécessaire avant sa fermeture."),
        ephemeral=ephemeral,
    )
    if journey.channel != votant.private_chan:
        await votant.private_chan.send(f"Vote {pour_contre} {tools.bold(cible.nom)} bien pris en compte.")


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def vote(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.HaroteTransformer]):
    """Vote pour le condamné du jour.

    Args:
        joueur: Le joueur contre qui tu veux diriger ton vote.

    Cette commande n'est utilisable que lorsqu'un vote pour le condamné est en cours,
    pour les joueurs ayant le droit de voter.

    Le bot t'enverra un message à l'ouverture de chaque vote.

    La commande peut être utilisée autant que voulu pour changer de cible tant que le vote est en cours.
    """
    moi = Joueur.from_member(journey.member)
    await do_vote(journey, Vote.cond, votant=moi, cible=joueur)


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def votemaire(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.CandidatTransformer]):
    """Vote pour le nouveau maire.

    Args:
        joueur: Le joueur pour lequel tu souhaites voter.

    Cette commande n'est utilisable que lorsqu'une élection pour le maire est en cours,
    pour les joueurs ayant le droit de voter.

    Le bot t'enverra un message à l'ouverture de chaque vote.

    La commande peut être utilisée autant que voulu pour changer de cible tant que le vote est en cours.
    """
    moi = Joueur.from_member(journey.member)
    await do_vote(journey, Vote.maire, votant=moi, cible=joueur)


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def voteloups(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.VivantTransformer]):
    """Vote pour la victime de l'attaque des loups (si tu es un loup, évidemment...)

    Args:
        joueur: Le joueur que tu souhaites éliminer.

    Cette commande n'est utilisable que lorsqu'une vote pour la victime du soir est en cours,
    pour les joueurs concernés.

    Le bot t'enverra un message à l'ouverture de chaque vote.

    La commande peut être utilisée autant que voulu pour changer de cible tant que le vote est en cours.
    """
    moi = Joueur.from_member(journey.member)
    await do_vote(journey, Vote.loups, votant=moi, cible=joueur)


class ActionTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> Action:
        return Action.query.get(int(value))

    async def autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        async with DiscordJourney(interaction) as journey:
            try:
                joueur = Joueur.from_member(journey.member)
            except ValueError:
                return []
            return [
                app_commands.Choice(name=action.base.slug, value=str(action.id))
                for action in joueur.actions_actives
                if action.is_open
            ][:25]


class CibleTransformer(app_commands.Transformer):
    N_CIBLE = 0

    async def transform(self, interaction: discord.Interaction, value: str) -> Joueur | Role | Camp | bool | str | None:
        if value == "__NO_CIBLE":
            return None
        if value == "__PHRASE":
            raise commons.UserInputError(
                f"cible_{self.N_CIBLE}" if self.N_CIBLE else "cible",
                "L'en-tête d'explication des choix n'est pas un choix valide !",
            )

        action_id = interaction.namespace.action
        action: Action = Action.query.get(int(action_id))
        base_ciblage = action.base.base_ciblages[self.N_CIBLE]

        match base_ciblage.type:
            case CibleType.joueur:
                return await tools.JoueurTransformer().transform(interaction, value)
            case CibleType.vivant:
                return await tools.VivantTransformer().transform(interaction, value)
            case CibleType.mort:
                return await tools.MortTransformer().transform(interaction, value)
            case CibleType.role:
                return await tools.RoleTransformer().transform(interaction, value)
            case CibleType.camp:
                return await tools.CampTransformer().transform(interaction, value)
            case CibleType.booleen:
                return value == "yes"
            case CibleType.texte:
                return value

    async def autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        action_id = interaction.namespace.action
        if not action_id:
            return [app_commands.Choice(name="⚠️ Remplir d'abord le paramètre 'action' ⚠️", value="error")]

        action: Action = Action.query.get(int(action_id))
        try:
            base_ciblage = action.base.base_ciblages[self.N_CIBLE]
        except IndexError:
            # Pas autant de ciblages pour cette action
            return [app_commands.Choice(name="(Paramètre non utilisé par cette action)", value="__NO_CIBLE")]

        match base_ciblage.type:
            case CibleType.joueur:
                choices = await tools.JoueurTransformer().autocomplete(interaction, current)
            case CibleType.vivant:
                choices = await tools.VivantTransformer().autocomplete(interaction, current)
            case CibleType.mort:
                choices = await tools.MortTransformer().autocomplete(interaction, current)
            case CibleType.role:
                choices = await tools.RoleTransformer().autocomplete(interaction, current)
            case CibleType.camp:
                choices = await tools.CampTransformer().autocomplete(interaction, current)
            case CibleType.booleen:
                choices = [app_commands.Choice(name="Oui", value="yes"), app_commands.Choice(name="Non", value="no")]
            case CibleType.texte:
                choices = [app_commands.Choice(name="[Texte libre]", value=current)]

        return [app_commands.Choice(name=f"🔽  {base_ciblage.phrase} 🔽"[:100], value="__PHRASE"), *choices]


class Cible2Transformer(CibleTransformer):
    N_CIBLE = 1


class Cible3Transformer(CibleTransformer):
    N_CIBLE = 2


@app_commands.command(name="action")
@tools.vivants_only
@tools.private()
@journey_command
async def action_(
    journey: DiscordJourney,
    *,
    action: app_commands.Transform[Action, ActionTransformer],
    cible: app_commands.Transform[Joueur | Role | Camp | bool | str | None, CibleTransformer] | None = None,
    cible_2: app_commands.Transform[Joueur | Role | Camp | bool | str | None, Cible2Transformer] | None = None,
    cible_3: app_commands.Transform[Joueur | Role | Camp | bool | str | None, Cible3Transformer] | None = None,
):
    """Utilise l'action de ton rôle / une des actions associées.

    Args:
        action: L'action pour laquelle agir (si il n'y a pas de suggestions, c'est que tu ne peux pas agir !)
        cible: La première cible de l'action, cf. la première suggestion (ne pas cliquer dessus !)
        cible_2: La deuxième cible de l'action, cf. la première suggestion (ne pas cliquer dessus !)
        cible_3: La troisième cible de l'action, cf. la première suggestion (ne pas cliquer dessus !)

    Cette commande n'est utilisable que si tu as au moins une action ouverte.
    Action = pouvoir associé à ton rôle, mais aussi pouvoirs ponctuels (Lame Vorpale, Chat d'argent...)
    Le bot t'enverra un message à l'ouverture de chaque action.

    La commande peut être utilisée autant que voulu pour changer d'action tant que la fenêtre d'action est en cours,
    SAUF pour certaines actions (dites "instantanées") ayant une conséquence immédiate (Barbier, Licorne...).
    Le bot mettra dans ce cas un message d'avertissement.
    """
    joueur = Joueur.from_member(journey.member)

    # Vérification rôle actif
    if not joueur.role_actif:
        await journey.send(":x: Tu ne peux pas utiliser tes pouvoirs pour le moment !")
        return

    # Détermine la/les actions en cours pour le joueur
    actions = [ac for ac in joueur.actions_actives if ac.is_open]
    if not actions:
        await journey.send(":x: Aucune action en cours pour toi.")
        return

    util = action.derniere_utilisation

    if not cible:
        if util.ciblages:
            await journey.ok_cancel(f"Action actuelle : {tools.bold(action.decision)}\n\nAnnuler l'action ?")
            # Annulation de l'action
            Ciblage.delete(*util.ciblages)
            util.ts_decision = datetime.datetime.now()
            util.etat = UtilEtat.ignoree
            util.update()
            await journey.send("Utilisation de l'action annulée.")
        else:
            await journey.send('Action non utilisée pour le moment. Remplir le paramètre "cible" pour agir !')
        return

    # Vérification nombre de cibles
    cibles = {}
    base_ciblages = action.base.base_ciblages
    await check_last_utilisation(action, base_ciblages[0], cible)
    cibles[base_ciblages[0]] = cible

    if len(base_ciblages) > 1:
        if not cible_2:
            raise commons.UserInputError("cible_2", "Cette action a besoin d'un second paramètre !")
        await check_last_utilisation(action, base_ciblages[1], cible_2)
        cibles[base_ciblages[1]] = cible_2

    if len(base_ciblages) > 2:
        if not cible_3:
            raise commons.UserInputError("cible_3", "Cette action a besoin d'un troisième paramètre !")
        await check_last_utilisation(action, base_ciblages[2], cible_3)
        cibles[base_ciblages[2]] = cible_3

    if not action.is_open:
        # On revérifie, si ça a fermé entre temps !!
        await journey.send("L'action a fermé entre temps, pas de chance !")
        return

    # Avertissement si action a conséquence instantanée (barbier...)
    if action.base.instant:
        await journey.ok_cancel(
            "Attention : cette action a une conséquence instantanée ! "
            "Si tu valides, tu ne pourras pas revenir en arrière.\n"
            "Ça part ?"
        )

    # Modification en base
    if util.ciblages:  # ancien ciblages
        Ciblage.delete(*util.ciblages)
    for bc, cible in cibles.items():
        cib = Ciblage(utilisation=util, base=bc)
        cib.valeur = cible  # affecte le bon attribut selon le bc.type

    util.ts_decision = datetime.datetime.now()
    util.etat = UtilEtat.remplie
    util.update()

    # Écriture dans sheet Données brutes
    await export_vote(None, util)
    await journey.send("Salut")

    # Conséquences si action instantanée
    if action.base.instant:
        await gestion_actions.close_action(action)
        await journey.send(tools.ital(f"[Allô {config.Role.mj.mention}, conséquence instantanée ici !]"))

    else:
        await journey.send(
            f"Action « {tools.bold(action.decision)} » bien prise en compte pour {tools.code(action.base.slug)}.\n"
            + tools.ital("Tu peux modifier ta décision autant que nécessaire avant la fin du créneau.")
        )
