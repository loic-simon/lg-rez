"""lg-rez / features / Commandes informatives

Commandes donnant aux joueurs des informations sur le jeu, leurs
actions, les joueurs en vie et morts...

"""

import discord
from discord import app_commands

from lgrez import config
from lgrez.blocs import tools, env
from lgrez.bdd import Joueur, Role, Camp, BaseAction, ActionTrigger, Vote
from lgrez.blocs.journey import DiscordJourney, journey_command
from lgrez.features import gestion_actions


def _roles_list(roles: list[Role]) -> str:
    return "\n".join(
        str(role.camp.discord_emoji_or_none or "") + tools.code(f"{role.nom.ljust(25)} {role.description_courte}")
        for role in roles
        if not role.nom.startswith("(")
    )


DESCRIPTION = """Commandes pour en savoir plus sur soi et les autres"""


@app_commands.command()
@journey_command
async def roles(journey: DiscordJourney, *, role: app_commands.Transform[Role, tools.RoleTransformer] | None = None):
    """Affiche la liste des rôles / des informations sur un rôle.

    Args:
        role: Le rôle pour lequel avoir les informations détaillées (liste tous les rôles par défaut).

    Voir aussi la commande `/camps`.
    """
    if role:
        await journey.send(embed=role.embed)
        return

    roles = Role.query.filter_by(actif=True).order_by(Role.nom).all()
    await journey.send(
        f"Rôles trouvés :\n{_roles_list(roles)}\n"
        + tools.ital(f"({tools.code('/role <role>')} pour plus d'informations sur un rôle.)"),
    )


@app_commands.command()
@journey_command
async def camps(journey: DiscordJourney, *, camp: app_commands.Transform[Camp, tools.CampTransformer] | None = None):
    """Affiche la liste des camps / les rôles d'un camp.

    Args:
        camp: Le camp pour lequel avoir les informations détaillées et la liste des rôles.

    Voir aussi la commande `/roles`.
    """
    if camp:
        await journey.send(embed=camp.embed)
        await journey.send(
            f"Rôles dans ce camp :\n{_roles_list(camp.roles)}\n"
            + tools.ital(f"({tools.code('/roles <role>')} pour plus d'informations sur un rôle.)"),
        )
        return

    camps = Camp.query.filter_by(public=True).order_by(Camp.nom).all()
    await journey.send(
        "Camps trouvés :\n"
        + "\n".join(f"{camp.discord_emoji_or_none or ''} {camp.nom}" for camp in camps if not camp.nom.startswith("("))
        + "\n"
        + tools.ital(f"({tools.code('/camps <camp>')} pour plus d'informations sur un camp.)"),
    )


@app_commands.command()
@tools.mjs_only
@journey_command
async def rolede(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.JoueurTransformer]):
    """Donne le rôle d'un joueur (COMMANDE MJ)

    Args:
        joueur: Le joueur dont on veut connaître le rôle.
    """
    await journey.send(f"Rôle de {joueur.nom} : {joueur.role.nom_complet}")


@app_commands.command()
@tools.mjs_only
@journey_command
async def quiest(journey: DiscordJourney, *, role: app_commands.Transform[Role, tools.RoleTransformer]):
    """Liste les joueurs ayant un rôle donné (COMMANDE MJ)

    Args:
        role: Le rôle qu'on cherche.
    """
    joueurs = Joueur.query.filter_by(role=role).filter(Joueur.est_vivant).all()
    if joueurs:
        await journey.send(f"{role.nom_complet} : " + ", ".join(joueur.nom for joueur in joueurs))
    else:
        await journey.send(f"{role.nom_complet} : Personne.")


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def menu(journey: DiscordJourney):
    """Affiche des informations et boutons sur les votes / actions en cours.

    Le menu a une place beaucoup moins importante ici que sur Messenger, vu que tout est accessible par commandes.
    """
    joueur = Joueur.from_member(journey.member)

    rep = ""

    try:
        vaction = joueur.action_vote(Vote.cond)
    except RuntimeError:
        await journey.send("Minute papillon, le jeu n'est pas encore lancé !")
        return

    if vaction.is_open:
        rep += (
            f" - {config.Emoji.bucher}  Vote pour le bûcher en cours – vote actuel : {tools.code(vaction.decision)} "
            f":arrow_forward: Tape `/vote` pour voter\n"
        )

    vaction = joueur.action_vote(Vote.maire)
    if vaction.is_open:
        rep += (
            f" - {config.Emoji.maire}  Vote pour le maire en cours – vote actuel : {tools.code(vaction.decision)} "
            f":arrow_forward: Tape `/votemaire` pour voter\n"
        )

    vaction = joueur.action_vote(Vote.loups)
    if vaction.is_open:
        rep += (
            f" - {config.Emoji.lune}  Vote des loups en cours – vote actuel : {tools.code(vaction.decision)} "
            f":arrow_forward: Tape `/voteloups` pour voter\n"
        )

    if not rep:
        rep = "Aucun vote en cours.\n"

    actions = [ac for ac in joueur.actions_actives if ac.is_open]
    if actions:
        for action in actions:
            rep += (
                f" - {config.Emoji.action}  Action en cours : {tools.code(action.base.slug)} (id {action.id})"
                f" – décision : {tools.code(action.decision)} :arrow_forward: Tape `/action` pour agir\n"
            )
    else:
        rep += "Aucune action en cours.\n"

    await journey.send(f"––– MENU –––\n\n{rep}\n`/infos` pour voir ton rôle et tes actions, `@MJ` en cas de problème")


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def infos(journey: DiscordJourney):
    """Affiche tes informations de rôle / actions.

    Toutes les actions liées à ton rôle (et parfois d'autres) sont indiquées,
    même celles que tu ne peux pas utiliser pour l'instant (plus de charges, déclenchées automatiquement...)
    """
    joueur = Joueur.from_member(journey.member)
    rep = ""

    rep += f"Ton rôle actuel : {tools.bold(joueur.role.nom_complet)}\n"
    rep += tools.ital(f"({tools.code(f'/roles {joueur.role.nom}')} pour tout savoir sur ce rôle)")

    if joueur.actions_actives:
        rep += "\n\nActions :"
        rep += tools.code_bloc(
            "\n".join(
                f" - {action.base.slug.ljust(20)} "
                + (f"Cooldown : {action.cooldown}" if action.cooldown else action.base.temporalite).ljust(22)
                + (
                    f"   {action.charges} charge(s)"
                    + (" pour cette semaine" if "weekends" in action.base.refill else "")
                    if isinstance(action.charges, int)
                    else "Illimitée"
                )
                for action in joueur.actions_actives
            )
        )
        # Vraiment désolé pour cette immondice j'ai la flemme
    else:
        rep += "\n\nAucune action disponible."

    await journey.send(
        f"{rep}\n{tools.code('/menu')} pour voir les votes et "
        f"actions en cours, {tools.code('@MJ')} en cas de problème"
    )


@app_commands.command()
@tools.mjs_only
@journey_command
async def actions(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.VivantTransformer]):
    """Affiche et modifie les actions d'un joueur (COMMANDE MJ)

    Args:
        joueur: Le joueur dont on veut voir ou modifier les actions.
    """
    actions = [ac for ac in joueur.actions if ac.base]

    rep = f"Rôle : {joueur.role.nom_complet or joueur.role}\n"

    rep += "Actions :"
    rep += tools.code_bloc(
        "id   active  baseaction               début     fin       cd   charges   refill\n"
        "--------------------------------------------------------------------------------------\n"
        + "\n".join(
            str(action.id).ljust(5)
            + str(action.active).ljust(8)
            + action.base.slug.ljust(25)
            + str(
                action.base.heure_debut
                if action.base.trigger_debut == ActionTrigger.temporel
                else action.base.trigger_debut.name
            ).ljust(10)
            + str(
                action.base.heure_fin
                if action.base.trigger_fin == ActionTrigger.temporel
                else action.base.trigger_fin.name
            ).ljust(10)
            + str(action.cooldown).ljust(5)
            + str(action.charges).ljust(10)
            + str(action.base.refill)
            for action in actions
        )
    )
    rep += "Modifier/ajouter/stop :"
    choix = await journey.select(
        rep,
        {action: f"Modifier {action.id} {action.base.slug}" for action in actions}
        | {"new": "Ajouter une action", "stop": "Stop"},
        placeholder="Action à réaliser",
    )

    if choix == "new":  # ajouter
        base_slug, cooldown, charges = await journey.modal(
            f"Nouvelle action pour {joueur.nom}",
            discord.ui.TextInput(label="Slug de la baseaction (cf Gsheet R&A)"),
            discord.ui.TextInput(label="Cooldown (nombre entier)", max_length=2, default="0"),
            discord.ui.TextInput(label="Charges (vide = illimité)", required=False),
        )
        if not (base := BaseAction.query.filter_by(slug=base_slug).one_or_none()):
            await journey.send(f"Action `{base_slug}` invalide, vérifier dans le Gsheet Rôles et actions")
            return
        cooldown = int(cooldown)
        charges = int(charges) if charges else None

        action = gestion_actions.add_action(joueur=joueur, base=base, cooldown=cooldown, charges=charges)
        await journey.send(f"Action ajoutée (id {action.id}).")
        return

    elif choix == "stop":
        await journey.send("Au revoir.")
        return

    # Modifier
    action = choix
    gsheet_id = env.load("LGREZ_ROLES_SHEET_ID")
    url = f"https://docs.google.com/spreadsheets/d/{gsheet_id}"
    while True:
        choix = await journey.buttons(
            "Pour modifier les attributs de la baseaction, modifier le Gsheet et utiliser `/fillroles` ; "
            f"pour ouvrir/fermer l'action, utiliser `/open_action {action.id}` / `/close_action {action.id}`.)",
            {
                "active": discord.ui.Button(label="Désactiver", style=discord.ButtonStyle.gray)
                if action.active
                else discord.ui.Button(label="Activer", style=discord.ButtonStyle.success),
                "edit": discord.ui.Button(label="Modifier cooldown / charges", style=discord.ButtonStyle.blurple),
                "gsheet": discord.ui.Button(label="Modifier sur le Gsheet", style=discord.ButtonStyle.link, url=url),
                "validate": discord.ui.Button(label="Valider et quitter", style=discord.ButtonStyle.success),
                "cancel": discord.ui.Button(label="Annuler les modifications", style=discord.ButtonStyle.danger),
            },
        )

        if choix == "active":
            action.active = not action.active

        elif choix == "edit":
            cooldown, charges = await journey.modal(
                "Modifier l'action",
                discord.ui.TextInput(label="Cooldown (nombre entier)", max_length=2, default=str(action.cooldown)),
                discord.ui.TextInput(label="Charges (vide = illimité)", required=False, default=str(action.charges)),
            )
            action.cooldown = int(cooldown)
            action.charges = int(charges) if charges else None

        elif choix == "validate":
            action.update()
            await journey.send("Modifications enregistrées.")
            return

        elif choix == "cancel":
            await journey.send("Modifications annulées.")
            return

        else:
            await journey.send(f"C'est possible ça ? {choix}")
            return


@app_commands.command()
@journey_command
async def vivants(journey: DiscordJourney):
    """Affiche la liste des joueurs vivants.

    Aussi dite : « liste des joueurs qui seront bientôt morts »
    """
    joueurs = Joueur.query.filter(Joueur.est_vivant).order_by(Joueur.nom).all()

    mess = " Joueur                     en chambre\n"
    mess += "––––––––––––––––––––––––––––––––––––––––––––––\n"
    if config.demande_chambre:
        for joueur in joueurs:
            mess += f" {joueur.nom.ljust(25)}  {joueur.chambre}\n"
    else:
        for joueur in joueurs:
            mess += f" {joueur.nom}\n"

    await journey.send(mess, code=True, prefix=f"Les {len(joueurs)} joueurs vivants sont :")


@app_commands.command()
@journey_command
async def morts(journey: DiscordJourney):
    """Affiche la liste des joueurs morts.

    Aussi dite : « liste des joueurs qui mangent leurs morts »
    """
    joueurs = Joueur.query.filter(Joueur.est_mort).order_by(Joueur.nom).all()

    if joueurs:
        mess = ""
        for joueur in joueurs:
            mess += f" {joueur.nom}\n"
    else:
        mess = "Toi (mais tu ne le sais pas encore)"

    await journey.send(mess, code=True, prefix=f"Les {len(joueurs) or ''} morts sont :")
