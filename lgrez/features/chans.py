"""lg-rez / features / Commandes de gestion des salons

Création, ajout, suppression de membres

"""

import asyncio
import functools
import datetime
from typing import Callable, Literal

import discord
from discord import app_commands

from lgrez import config
from lgrez.blocs import tools
from lgrez.blocs.journey import DiscordJourney, journey_command, journey_context_menu
from lgrez.bdd import Joueur, Boudoir, Bouderie
from lgrez.features.sync import transtype


def in_boudoir(callback: Callable) -> Callable:
    """Décorateur : commande utilisable dans un boudoir uniquement.

    Lors d'une invocation de la commande décorée hors d'un boudoir
    (enregistré dans :class:`.bdd.Boudoir`), affiche un message d'erreur.

    Ce décorateur n'est utilisable que sur une commande définie dans un Cog.
    """

    @functools.wraps(callback)
    async def new_callback(interaction: discord.Interaction, **kwargs):
        try:
            Boudoir.from_channel(interaction.channel)
        except ValueError:
            await interaction.response.send_message("Cette commande est invalide en dehors d'un boudoir.")
        else:
            return await callback(interaction, **kwargs)

    return new_callback


def gerant_only(callback: Callable) -> Callable:
    """Décorateur : commande utilisable par le gérant d'un boudoir uniquement.

    Lors d'une invocation de la commande décorée par un membre qui n'est
    pas gérant du boudoir, affiche un message d'erreur.

    Ce décorateur doit toujours être utilisé en combinaison avec
    :func:`in_boudoir` et positionné après lui.

    Ce décorateur n'est utilisable que sur une commande définie dans un Cog.
    """

    @functools.wraps(callback)
    async def new_callback(interaction: discord.Interaction, **kwargs):
        boudoir = Boudoir.from_channel(interaction.channel)
        gerant = Joueur.from_member(interaction.user)
        if boudoir.gerant != gerant:
            await interaction.response.send_message("Seul le gérant du boudoir peut utiliser cette commande.")
        else:
            return await callback(interaction, **kwargs)

    return new_callback


async def add_joueur_to_boudoir(boudoir: Boudoir, joueur: Joueur, gerant: bool = False) -> bool:
    """Ajoute un joueur sur un boudoir.

    Crée la :class:`.Bouderie` correspondante et modifie les permissions du salon.

    Args:
        boudoir: Le boudoir où ajouter un joueur.
        joueur: Le joueur à ajouter.
        gerant: Si le joueur doit être ajouté avec les permissions de gérant.

    Returns:
        ``True`` si le joueur a été ajouté, ``False`` si il y était déjà / le boudoir est fermé.
    """
    if joueur in boudoir.joueurs:
        # Joueur déjà dans le boudoir
        return False
    if not boudoir.joueurs and not gerant:
        # Boudoir fermé (plus de joueurs) et pas ajout comme gérant
        return False

    now = datetime.datetime.now()
    Bouderie(boudoir=boudoir, joueur=joueur, gerant=gerant, ts_added=now, ts_promu=now if gerant else None).add()
    await boudoir.chan.set_permissions(joueur.member, read_messages=True)

    # Sortie du cimetière le cas échéant
    if tools.in_multicateg(boudoir.chan.category, config.old_boudoirs_category_name):
        await boudoir.chan.send(tools.ital("[Ce boudoir contient au moins deux joueurs vivants, " "désarchivage...]"))
        categ = await tools.multicateg(config.boudoirs_category_name)
        await boudoir.chan.edit(name=boudoir.nom, category=categ)
    return True


async def remove_joueur_from_boudoir(boudoir: Boudoir, joueur: Joueur) -> None:
    """Retire un joueur d'un boudoir.

    Supprime la :class:`.Bouderie` correspondante et modifie les permissions du salon.

    Args:
        boudoir: Le boudoir d'où enlever un joueur.
        joueur: Le joueur à enlever.
    """
    Bouderie.query.filter_by(boudoir=boudoir, joueur=joueur).one().delete()
    await boudoir.chan.set_permissions(joueur.member, overwrite=None)
    # Déplacement dans le cimetière si nécessaire
    vivants = [jr for jr in boudoir.joueurs if jr.est_vivant]
    if len(vivants) < 2:
        if tools.in_multicateg(boudoir.chan.category, config.old_boudoirs_category_name):
            # Boudoir déjà au cimetière
            return
        await boudoir.chan.send(tools.ital("[Ce boudoir contient moins de deux joueurs vivants, " "archivage...]"))
        categ = await tools.multicateg(config.old_boudoirs_category_name)
        await boudoir.chan.edit(
            name=f"\N{CROSS MARK} {boudoir.nom}",
            category=categ,
        )


async def _create_boudoir(gerant: Joueur, nom: str) -> Boudoir:
    """Crée un boudoir avec le gérant et le nom requis"""
    now = datetime.datetime.now()
    categ = await tools.multicateg(config.boudoirs_category_name)
    chan = await config.guild.create_text_channel(
        nom,
        topic=f"Boudoir crée le {now:%d/%m à %H:%M}. " f"Gérant(e) : {gerant.nom}",
        category=categ,
    )

    boudoir = Boudoir(chan_id=chan.id, nom=nom, ts_created=now)
    boudoir.add()
    await add_joueur_to_boudoir(boudoir, gerant, gerant=True)
    await tools.log(f"Boudoir {chan.mention} créé par {gerant.nom}.")

    return boudoir


async def _invite(joueur: Joueur, boudoir: Boudoir, invite_msg: discord.Message) -> None:
    """Invitation d'un joueur dans un boudoir (lancer comme tâche à part)"""

    async def ack_invitation_response(info):
        try:
            await invite_msg.reply(info)
        except discord.HTTPException:  # Message d'invitation supprimé
            await boudoir.chan.send(info)

    class _InviteView(discord.ui.View):
        @discord.ui.button(style=discord.ButtonStyle.success, emoji="✅")
        async def ok(self, vote_interaction: discord.Interaction, button: discord.ui.Button):
            async with DiscordJourney(vote_interaction) as journey:
                if await add_joueur_to_boudoir(boudoir, joueur):
                    await ack_invitation_response(f"{joueur.nom} a rejoint le boudoir !")
                    await journey.final_message(f"Tu as bien rejoint {boudoir.chan.mention} !")
                else:
                    await journey.final_message("Impossible de rejoindre le boudoir :(")

        @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="❌")
        async def c_non(self, contre_haro_interaction: discord.Interaction, button: discord.ui.Button):
            async with DiscordJourney(contre_haro_interaction) as journey:
                await ack_invitation_response(f"{joueur.nom} a refusé l'invitation à rejoindre ce boudoir.")
                await journey.final_message("Invitation refusée.")

    await joueur.private_chan.send(
        f"{joueur.member.mention} {boudoir.gerant.nom} t'as invité(e) à "
        f"rejoindre son boudoir : « {boudoir.nom} » !\nAcceptes-tu ?",
        view=_InviteView(),
    )


DESCRIPTION = """Gestion des salons"""

boudoir = app_commands.Group(name="boudoir", description="Gestion des boudoirs")
"""Gestion des boudoirs

Les options relatives à un boudoir précis ne peuvent être
exécutées que dans ce boudoir ; certaines sont réservées au
gérant dudit boudoir.
"""


@boudoir.command()
@tools.joueurs_only
@tools.private()
@journey_command
async def list(journey: DiscordJourney):
    """Liste les boudoirs dans lesquels tu es"""
    joueur = Joueur.from_member(journey.member)
    bouderies = joueur.bouderies

    if not bouderies:
        await journey.final_message("Tu n'es dans aucun boudoir pour le moment.\n`/boudoir create` pour en créer un.")
        return

    rep = "Tu es dans les boudoirs suivants :"
    for bouderie in bouderies:
        rep += f"\n - {bouderie.boudoir.chan.mention}"
        if bouderie.gerant:
            rep += " (gérant)"

    rep += "\n\nUtilise `/boudoir leave` dans un boudoir pour le quitter."

    await journey.final_message(rep)


@boudoir.command()
@tools.vivants_only
@tools.private()
@journey_command
async def create(journey: DiscordJourney, *, nom: app_commands.Range[str, 1, 32]):
    """Crée un nouveau boudoir dont tu es gérant

    Args:
        nom: Nom du boudoir à créer. Doit faire moins de 32 caractères.
    """
    member = journey.member
    joueur = Joueur.from_member(member)

    boudoir = await _create_boudoir(joueur, nom)
    await boudoir.chan.send(
        f"{member.mention}, voici ton boudoir ! "
        "Tu peux maintenant y inviter des gens avec la commande `/boudoir invite`."
    )

    await journey.final_message(f"Ton boudoir a bien été créé : {boudoir.chan.mention}")


@boudoir.command()
@tools.joueurs_only
@in_boudoir
@gerant_only
@journey_command
async def invite(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.VivantTransformer]):
    """Invite un joueur à rejoindre ce boudoir

    Args:
        joueur: Le joueur à inviter
    """
    boudoir = Boudoir.from_channel(journey.channel)
    if joueur in boudoir.joueurs:
        await journey.final_message(f":x: {joueur.nom} est déjà dans ce boudoir !")
        return

    mess = await journey.final_message(f"Invitation envoyée à {joueur.nom}.")
    asyncio.create_task(_invite(joueur, boudoir, mess))
    # On envoie l'invitation en arrière-plan (libération du chan).


@boudoir.command()
@tools.joueurs_only
@in_boudoir
@gerant_only
@journey_command
async def expulse(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.VivantTransformer]):
    """Expulse un membre de ce boudoir

    Args:
        joueur: Le joueur à expulser
    """
    boudoir = Boudoir.from_channel(journey.channel)
    if joueur not in boudoir.joueurs:
        await journey.final_message(f":x: {joueur.nom} n'est pas membre du boudoir !")
        return

    await remove_joueur_from_boudoir(boudoir, joueur)
    await joueur.private_chan.send(f"Tu as été expulsé(e) du boudoir " f"« {boudoir.nom} ».")
    await journey.final_message(f"{joueur.nom} a bien été expulsé de ce boudoir.")


@boudoir.command()
@tools.joueurs_only
@in_boudoir
@journey_command
async def leave(journey: DiscordJourney):
    """Quitte ce boudoir"""
    joueur = Joueur.from_member(journey.member)
    boudoir = Boudoir.from_channel(journey.channel)

    if boudoir.gerant == joueur:
        await journey.final_message(
            "Tu ne peux pas quitter un boudoir que tu gères. "
            "Utilise `/boudoir transfer` pour passer les droits "
            "de gestion ou `/boudoir delete` pour le supprimer."
        )
        return

    await journey.ok_cancel("Veux-tu vraiment quitter ce boudoir ? Tu ne pourras pas y retourner sans invitation.")

    await remove_joueur_from_boudoir(boudoir, joueur)
    await journey.final_message(tools.ital(f"{joueur.nom} a quitté ce boudoir."))


@boudoir.command()
@tools.joueurs_only
@in_boudoir
@gerant_only
@journey_command
async def transfer(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.VivantTransformer]):
    """Transfère les droits de gestion de ce boudoir

    Args:
        joueur: Le joueur à qui transférer le boudoir
    """
    boudoir = Boudoir.from_channel(journey.channel)
    if joueur not in boudoir.joueurs:
        await journey.final_message(f"{joueur.nom} n'est pas membre de ce boudoir !")
        return

    if not await journey.yes_no(
        "Veux-tu vraiment transférer les droits de ce boudoir ? Tu ne pourras pas les récupérer par toi-même."
    ):
        await journey.final_message("Mission aborted.")
        return

    boudoir.gerant = joueur
    boudoir.update()
    await boudoir.chan.edit(topic=f"Boudoir crée le {boudoir.ts_created:%d/%m à %H:%M}. " f"Gérant(e) : {joueur.nom}")

    await journey.final_message(f"Boudoir transféré à {joueur.nom}.")


@boudoir.command()
@tools.joueurs_only
@in_boudoir
@gerant_only
@journey_command
async def delete(journey: DiscordJourney):
    """Supprime ce boudoir"""
    boudoir = Boudoir.from_channel(journey.channel)
    await journey.ok_cancel("Veux-tu vraiment supprimer ce boudoir ? Cette action est irréversible.")

    await journey.final_message("Suppression...")
    for joueur in boudoir.joueurs:
        await remove_joueur_from_boudoir(boudoir, joueur)
        await joueur.private_chan.send(f"Le boudoir « {boudoir.nom } » a été supprimé.")

    await boudoir.chan.edit(name=f"\N{CROSS MARK} {boudoir.nom}")
    await journey.final_message(
        tools.ital("[Tous les joueurs ont été exclus de ce boudoir ; le channel reste présent pour archive.]")
    )


@boudoir.command()
@tools.joueurs_only
@in_boudoir
@gerant_only
@journey_command
async def rename(journey: DiscordJourney, *, nom: app_commands.Range[str, 1, 32]):
    """Renomme ce boudoir

    Args:
        nom: Le nouveau nom du boudoir. Doit faire moins de 32 caractères.
    """
    boudoir = Boudoir.from_channel(journey.channel)

    boudoir.nom = nom
    boudoir.update()
    await boudoir.chan.edit(name=nom)
    await journey.final_message("Boudoir renommé avec succès.")


@boudoir.command()
@tools.joueurs_only
@in_boudoir
@gerant_only
@journey_command
async def ping(journey: DiscordJourney, *, message: str = ""):
    """Mentionne tous les joueurs vivants dans le boudoir.

    Args:
        message: Message à faire passer
    """
    await journey.final_message(f"{config.Role.joueur_en_vie.mention} {message}")


@boudoir.command()
@tools.mjs_only
@journey_command
async def find(
    journey: DiscordJourney,
    joueur1: app_commands.Transform[Joueur, tools.VivantTransformer],
    joueur2: app_commands.Transform[Joueur, tools.VivantTransformer] | None = None,
    joueur3: app_commands.Transform[Joueur, tools.VivantTransformer] | None = None,
):
    """✨ Trouve le(s) boudoir(s) réunissant certains joueurs (COMMANDE MJ)

    Args:
        joueur1: Premier joueur
        joueur1: Deuxième joueur (optionnel)
        joueur1: Troisième joueur (optionnel)
    """
    joueurs = [joueur1]
    if joueur2:
        joueurs.append(joueur2)
    if joueur3:
        joueurs.append(joueur3)
    boudoirs = [boudoir for boudoir in Boudoir.query.all() if all(joueur in boudoir.joueurs for joueur in joueurs)]

    if not boudoirs:
        await journey.final_message(f":x: Pas de boudoir(s) réunissant {joueurs}.")
    else:
        liste = "\n".join(f"- {boudoir.chan.mention} ({len(boudoir.joueurs)} joueurs)" for boudoir in boudoirs)
        await journey.final_message(f"{len(boudoirs)} boudoirs :\n{liste}")


async def _mp(journey: DiscordJourney, *, joueur: Joueur):
    member = journey.member
    moi = Joueur.from_member(member)

    if moi == joueur:
        await journey.final_message(f"Ton boudoir a bien été créé : {moi.private_chan.mention}\n(tocard)")
        return

    # Recherche si boudoir existant
    boudoir = next((boudoir for boudoir in moi.boudoirs if set(boudoir.joueurs) == {moi, joueur}), None)
    if boudoir:
        await journey.final_message(f":x: Ce boudoir existe déjà : {boudoir.chan.mention}")
        return

    boudoir = await _create_boudoir(moi, f"{moi.nom} × {joueur.nom}")
    await boudoir.chan.send(f"{member.mention}, voici ton boudoir !")

    await journey.final_message(f":sunglasses: Ton boudoir a bien été créé : {boudoir.chan.mention}")

    mess = await boudoir.chan.send(f"Invitation envoyée à {joueur.nom}.")
    asyncio.create_task(_invite(joueur, boudoir, mess))
    # On envoie l'invitation en arrière-plan (libération du chan).


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def mp(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.VivantTransformer]):
    """✨ Raccourci pour créer un boudoir et y ajouter un joueur.

    Si un boudoir existe déjà avec uniquement ce joueur et toi, n'en crée pas un nouveau.

    Args:
        joueur: La personne avec qui créer un boudoir.
    """
    await _mp(journey, joueur=joueur)


@app_commands.context_menu(name="Créer un boudoir avec ce joueur")
@tools.vivants_only
@journey_context_menu
async def mp_menu(journey: DiscordJourney, member: discord.Member):
    if member.top_role >= config.Role.mj:
        await journey.final_message(":x: Tu ne peux pas créer de boudoir avec un MJ, sacrebleu !", ephemeral=True)
        return

    if member == config.bot.user:
        await journey.final_message(":x: Tu ne peux pas créer de boudoir avec le bot, enfin !!!", ephemeral=True)
        return

    try:
        joueur = Joueur.from_member(member)
    except ValueError:
        await journey.final_message(":x: Hmm, ce joueur n'a pas l'air inscrit, réessaye plus tard !", ephemeral=True)
        return

    await _mp(journey, joueur=joueur)


@app_commands.command()
@tools.mjs_only
@journey_command
async def addhere(
    journey: DiscordJourney,
    crit: Literal["chambre", "statut", "camp", "role", "votant_village", "votant_loups", "role_actif"],
    filtre: str,
):
    """Ajoute les membres au chan courant (COMMANDE MJ)

    Args:
        crit: Critère sur lequel filtrer les joueurs à ajouter
        filtre: Valeur de `crit` à récupérer

    Si ``*joueurs`` est un seul élément, il peut être de la forme
    ``<crit>=<filtre>`` tel que décrit dans l'aide de ``!send``.
    """
    ts_debut = journey.created_at - datetime.timedelta(microseconds=1)

    col = Joueur.attrs[crit]
    arg = transtype(filtre.strip(), col)
    joueurs = Joueur.query.filter_by(**{crit: arg}).all()

    for joueur in joueurs:
        await journey.channel.set_permissions(joueur.member, read_messages=True)
        await journey.channel.send(f"{joueur.nom} ajouté")

    await journey.ok_cancel("Fini, purge les messages ?")
    await journey.channel.purge(after=ts_debut)


@app_commands.command()
@tools.mjs_only
@journey_command
async def purge(journey: DiscordJourney, limit: int | None = None):
    """Supprime tous les messages de ce chan (COMMANDE MJ)

    Args:
        limit: Nombre de messages à supprimer (défaut : tous)
    """
    if limit:
        mess = f"Supprimer les {limit} messages les plus récents de ce chan ?"
    else:
        mess = "Supprimer tous les messages de ce chan ?"

    await journey.ok_cancel(mess, ephemeral=True)
    await journey.channel.purge(limit=limit)
    await journey.final_message(content="Fait.", ephemeral=True)
