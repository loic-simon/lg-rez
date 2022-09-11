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


async def _haro(journey: DiscordJourney, joueur: Joueur, ephemeral: bool = False):
    moi = Joueur.from_member(journey.member)
    try:
        vaction = joueur.action_vote(Vote.cond)
    except RuntimeError:
        await journey.final_message("Minute papillon, le jeu n'est pas encore lancé !", ephemeral=ephemeral)
        return

    if not vaction.is_open:
        await journey.final_message("Pas de vote pour le condamné du jour en cours !", ephemeral=ephemeral)
        return

    (motif,) = await journey.modal(
        f"Haro contre {joueur.nom}",
        discord.ui.TextInput(label="Quelle est la raison de cette haine ?", style=discord.TextStyle.paragraph),
    )

    emb = discord.Embed(
        title=(f"**{config.Emoji.ha}{config.Emoji.ro} " f"contre {joueur.nom} !**"),
        description=f"**« {motif} »\n**",
        color=0xFF0000,
    )
    emb.set_author(name=f"{moi.nom} en a gros 😡😡")
    emb.set_thumbnail(url=config.Emoji.bucher.url)
    # emb.set_footer(text=f"Envoie `/vote {joueur.nom}` pour voter contre cette personne.")

    await journey.ok_cancel("C'est tout bon ?", embed=emb, ephemeral=ephemeral)

    class _HaroView(discord.ui.View):
        @discord.ui.button(
            label=f"Voter contre {joueur.nom}"[:80], style=discord.ButtonStyle.primary, emoji=config.Emoji.bucher
        )
        async def vote(self, vote_interaction: discord.Interaction, button: discord.ui.Button):
            async with DiscordJourney(vote_interaction) as vote_journey:
                try:
                    votant = Joueur.from_member(vote_journey.member)
                except ValueError:
                    await vote_journey.final_message(":x: Tu n'as pas le droit de vote, toi", ephemeral=True)
                await do_vote(vote_journey, Vote.cond, votant=votant, cible=joueur)

        @discord.ui.button(label=f"Contre-haro", style=discord.ButtonStyle.danger, emoji=config.Emoji.ha)
        async def contre_haro(self, contre_haro_interaction: discord.Interaction, button: discord.ui.Button):
            async with DiscordJourney(contre_haro_interaction) as contre_info_journey:
                await _haro(contre_info_journey, joueur=moi, ephemeral=True)

    haro_message = await config.Channel.haros.send(f"(Psst, {joueur.member.mention} :3)", embed=emb, view=_HaroView())
    await config.Channel.debats.send(
        f"{config.Emoji.ha}{config.Emoji.ro} de {journey.member.mention} sur {joueur.member.mention} ! "
        f"Vous en pensez quoi vous ? (détails sur {config.Channel.haros.mention})"
    )

    haro = CandidHaro(joueur=joueur, type=CandidHaroType.haro, message_id=haro_message.id)
    contre_haro = CandidHaro(joueur=moi, type=CandidHaroType.haro)
    CandidHaro.add(haro, contre_haro)

    if not ephemeral:
        await journey.final_message(f"Allez, c'est parti ! ({config.Channel.haros.mention})")


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def haro(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.VivantTransformer]):
    """Lance publiquement un haro contre un autre joueur.

    Args:
        joueur: Le joueur à accuser

    Cette commande n'est utilisable que lorsqu'un vote pour le condamné est en cours.
    """
    await _haro(journey, joueur=joueur)


@app_commands.context_menu(name="Lancer un haro contre ce joueur")
@tools.vivants_only
@journey_context_menu
async def haro_menu(journey: DiscordJourney, member: discord.Member):
    if member.top_role >= config.Role.mj:
        await journey.final_message(":x: Attends deux secondes, tu pensais faire quoi là ?", ephemeral=True)
        return

    if member == config.bot.user:
        await journey.final_message(":x: Tu ne peux pas haro le bot, enfin !!!", ephemeral=True)
        return

    try:
        joueur = Joueur.from_member(member)
    except ValueError:
        await journey.final_message(":x: Hmm, ce joueur n'a pas l'air inscrit !", ephemeral=True)
        return

    await _haro(journey, joueur=joueur, ephemeral=True)


@app_commands.command()
@tools.vivants_only
@tools.private()
@journey_command
async def candid(journey: DiscordJourney):
    """Candidate à l'élection du nouveau maire.

    Cette commande n'est utilisable que lorsqu'un vote pour le
    nouveau maire est en cours.
    """
    joueur = Joueur.from_member(journey.member)
    try:
        vaction = joueur.action_vote(Vote.cond)
    except RuntimeError:
        await journey.final_message("Minute papillon, le jeu n'est pas encore lancé !")
        return

    if not vaction.is_open:
        await journey.final_message("Pas de vote pour le nouveau maire en cours !")
        return

    if CandidHaro.query.filter_by(joueur=joueur, type=CandidHaroType.candidature).first():
        await journey.final_message("Hola collègue, tout doux, tu t'es déjà présenté(e) !")
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
    emb.set_footer(text=(f"Envoie `/votemaire {joueur.nom}` pour voter pour cette personne."))

    await journey.ok_cancel("C'est tout bon ?", embed=emb)

    candid_message = await config.Channel.haros.send("Here comes a new challenger !", embed=emb)
    await config.Channel.debats.send(
        f"{journey.member.mention} se présente à la Mairie ! Vous en pensez quoi vous ?\n"
        f"(détails sur {config.Channel.haros.mention})"
    )
    await journey.final_message(f"Allez, c'est parti ! ({config.Channel.haros.mention})")

    ch = CandidHaro(joueur=joueur, type=CandidHaroType.candidature, message_id=candid_message.id)
    CandidHaro.add(ch)


@app_commands.command()
@tools.mjs_only
@journey_command
async def wipe(journey: DiscordJourney, quoi: Literal["haros", "candids"]):
    """Efface les haros / candidatures du jour (COMMANDE MJ)

    Args:
        quoi: Type d'objet à supprimer
    """
    if quoi == "haros":
        cht = CandidHaroType.haro
    elif quoi == "candids":
        cht = CandidHaroType.candidature
    else:
        await journey.final_message("Mauvais argument")
        return

    candid_haros: list[CandidHaro] = CandidHaro.query.filter_by(type=cht).all()

    if not candid_haros:
        await journey.final_message("Rien à faire")
        return

    for candid_haro in candid_haros:
        await candid_haro.disable_message_buttons()
    CandidHaro.delete(*candid_haros)

    await journey.final_message("Fait.")
    await tools.log(f"/wipe : {len(candid_haros)} {quoi} supprimés")
