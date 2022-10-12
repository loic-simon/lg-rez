"""lg-rez / features / Actions publiques

Gestion des haros, candidatures à la mairie, résultats des votes

"""

from typing import Literal

import discord
from discord import app_commands

from lgrez import config
from lgrez.blocs import tools
from lgrez.blocs.journey import DiscordJourney, journey_command, journey_context_menu
from lgrez.bdd import Joueur, CandidHaro, CandidHaroType, Vote
from lgrez.features.voter_agir import do_vote


DESCRIPTION = """Commandes d'actions vous engageant publiquement"""


async def _haro(journey: DiscordJourney, joueur: Joueur):
    moi = Joueur.from_member(journey.member)
    try:
        vaction = joueur.action_vote(Vote.cond)
    except RuntimeError:
        await journey.send(":x: Minute papillon, le jeu n'est pas encore lancé !")
        return

    if not vaction.is_open:
        await journey.send(":x: Pas de vote pour le condamné du jour en cours !")
        return

    (motif,) = await journey.modal(
        f"Haro contre {joueur.nom}",
        discord.ui.TextInput(label="Quelle est la raison de cette haine ?", style=discord.TextStyle.paragraph),
    )

    emb = discord.Embed(
        title=(f"**{config.Emoji.ha}{config.Emoji.ro} contre {joueur.nom} !**"),
        description=f"**« {motif} »\n**",
        color=0xFF0000,
    )
    emb.set_author(name=f"{moi.nom} en a gros 😡😡")
    emb.set_thumbnail(url=config.Emoji.bucher.url)

    await journey.ok_cancel("C'est tout bon ?", embed=emb)

    class _HaroView(discord.ui.View):
        @discord.ui.button(
            label=f"Voter contre {joueur.nom}"[:80], style=discord.ButtonStyle.primary, emoji=config.Emoji.bucher
        )
        async def vote(self, vote_interaction: discord.Interaction, button: discord.ui.Button):
            async with DiscordJourney(vote_interaction, ephemeral=True) as vote_journey:
                try:
                    votant = Joueur.from_member(vote_journey.member)
                except ValueError:
                    await vote_journey.send(":x: Tu n'as pas le droit de vote, toi")
                await do_vote(vote_journey, Vote.cond, votant=votant, cible=joueur)

        @discord.ui.button(label=f"Contre-haro", style=discord.ButtonStyle.danger, emoji=config.Emoji.ha)
        async def contre_haro(self, contre_haro_interaction: discord.Interaction, button: discord.ui.Button):
            async with DiscordJourney(contre_haro_interaction, ephemeral=True) as contre_info_journey:
                await _haro(contre_info_journey, joueur=moi)

    haro_message = await config.Channel.haros.send(f"(Psst, {joueur.member.mention} :3)", embed=emb, view=_HaroView())
    await config.Channel.debats.send(
        f"{config.Emoji.ha}{config.Emoji.ro} de {journey.member.mention} sur {joueur.member.mention} ! "
        f"Vous en pensez quoi vous ? (détails sur {config.Channel.haros.mention})"
    )

    haro = CandidHaro(joueur=joueur, type=CandidHaroType.haro, message_id=haro_message.id)
    contre_haro = CandidHaro(joueur=moi, type=CandidHaroType.haro)
    CandidHaro.add(haro, contre_haro)

    await journey.send(f"Allez, c'est parti ! ({config.Channel.haros.mention})")


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def haro(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.VivantTransformer]):
    """Lance publiquement un haro contre une autre personne.

    Args:
        joueur: Le joueur ou la joueuse à accuser de tous les maux.

    Cette commande n'est utilisable que lorsqu'un vote pour le condamné est en cours.
    """
    await _haro(journey, joueur=joueur)


@app_commands.context_menu(name="Lancer un haro contre ce joueur")
@tools.vivants_only
@journey_context_menu
async def haro_menu(journey: DiscordJourney, member: discord.Member):
    if member.top_role >= config.Role.mj:
        await journey.send(":x: Attends deux secondes, tu pensais faire quoi là ?")
        return

    if member == config.bot.user:
        await journey.send(":x: Tu ne peux pas haro le bot, enfin !!!")
        return

    try:
        joueur = Joueur.from_member(member)
    except ValueError:
        await journey.send(":x: Hmm, ce joueur n'a pas l'air inscrit !")
        return

    await _haro(journey, joueur=joueur, ephemeral=True)


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def candid(journey: DiscordJourney):
    """Déclare ta candidature à l'élection du nouveau maire.

    Cette commande n'est utilisable que lorsqu'un vote pour le nouveau maire est en cours.
    """
    joueur = Joueur.from_member(journey.member)
    try:
        vaction = joueur.action_vote(Vote.cond)
    except RuntimeError:
        await journey.send(":x: Minute papillon, le jeu n'est pas encore lancé !")
        return

    if not vaction.is_open:
        await journey.send(":x: Pas de vote pour le nouveau maire en cours !")
        return

    if CandidHaro.query.filter_by(joueur=joueur, type=CandidHaroType.candidature).first():
        await journey.send(":x: Hola collègue, tout doux, tu t'es déjà présenté(e) !")
        return

    (motif,) = await journey.modal(
        "Candidature à la Mairie",
        discord.ui.TextInput(label="Quel est ton programme politique ?", style=discord.TextStyle.paragraph),
    )

    emb = discord.Embed(
        title=(f"**{config.Emoji.maire} {joueur.nom} candidate à la Mairie !**"),
        description=("Voici son programme politique :\n" + tools.bold(motif)),
        color=0xF1C40F,
    )
    emb.set_author(name=f"{joueur.nom} vous a compris !")
    emb.set_thumbnail(url=config.Emoji.maire.url)

    await journey.ok_cancel("C'est tout bon ?", embed=emb)

    class _CandidView(discord.ui.View):
        @discord.ui.button(
            label=f"Voter pour {joueur.nom}"[:80], style=discord.ButtonStyle.success, emoji=config.Emoji.maire
        )
        async def vote(self, vote_interaction: discord.Interaction, button: discord.ui.Button):
            async with DiscordJourney(vote_interaction, ephemeral=True) as vote_journey:
                try:
                    votant = Joueur.from_member(vote_journey.member)
                except ValueError:
                    await vote_journey.send(":x: Oh, tu n'as pas le droit de vote, toi !")
                await do_vote(vote_journey, Vote.maire, votant=votant, cible=joueur)

    candid_message = await config.Channel.haros.send("Here comes a new challenger!", embed=emb, view=_CandidView())
    await config.Channel.debats.send(
        f"{journey.member.mention} se présente à la Mairie ! Vous en pensez quoi vous ?\n"
        f"(détails sur {config.Channel.haros.mention})"
    )
    await journey.send(f"Allez, c'est parti ! ({config.Channel.haros.mention})")

    ch = CandidHaro(joueur=joueur, type=CandidHaroType.candidature, message_id=candid_message.id)
    CandidHaro.add(ch)


@app_commands.command()
@tools.mjs_only
@journey_command
async def wipe(journey: DiscordJourney, quoi: Literal["haros", "candids"]):
    """Efface les haros / candidatures du jour (COMMANDE MJ)

    Args:
        quoi: Type d'objet à supprimer.
    """
    if quoi == "haros":
        cht = CandidHaroType.haro
    elif quoi == "candids":
        cht = CandidHaroType.candidature
    else:
        await journey.send("Mauvais argument")
        return

    candid_haros: list[CandidHaro] = CandidHaro.query.filter_by(type=cht).all()

    if not candid_haros:
        await journey.send("Rien à faire.")
        return

    for candid_haro in candid_haros:
        await candid_haro.disable_message_buttons()
    CandidHaro.delete(*candid_haros)

    await journey.send("Fait.")
    await tools.log(f"/wipe : {len(candid_haros)} {quoi} supprimés")
