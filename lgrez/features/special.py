"""lg-rez / features / Commandes spéciales

Commandes spéciales (méta-commandes, imitant ou impactant le
déroulement des autres ou le fonctionnement du bot)

"""

import asyncio
import os
import sys
import traceback
from typing import Literal

# Unused imports because useful for !do / !shell globals
import discord
from discord import app_commands

from lgrez import __version__, config, features, blocs, bdd, commands, commons
from lgrez.blocs import gsheets, tools, realshell
from lgrez.bdd import *  # toutes les tables dans globals()
from lgrez.blocs.journey import DiscordJourney, journey_command


DESCRIPTION = """Commandes spéciales (méta-commandes et expérimentations)"""


@app_commands.command()
@tools.mjs_only
@journey_command
async def panik(journey: DiscordJourney):
    """Tue instantanément le bot, sans confirmation (COMMANDE MJ)

    PAAAAANIK
    """
    sys.exit()


@app_commands.command()
@tools.mjs_only
@journey_command
async def do(journey: DiscordJourney, *, code: str):
    """Exécute du code Python et affiche le résultat (COMMANDE MJ)

    Args:
        code: Instruction Python évaluable (dispo : `journey`, `config`, `blocs`, `features`, `bdd`, `<table>`...)

    Si ``code`` est une coroutine, elle sera awaited (ne pas inclure ``await`` dans ``code``).

    Aussi connue sous le nom de « faille de sécurité », cette commande permet de faire environ
    tout ce qu'on veut sur le bot (y compris le crasher, importer des modules, exécuter des fichiers .py...
    même si c'est un peu compliqué) voire d'impacter le serveur sur lequel le bot tourne si on est motivé.

    À utiliser avec parcimonie donc, et QUE pour du développement/debug !
    """
    await journey.interaction.response.defer(thinking=True)

    class Answer:
        rep = None

    _a = Answer()

    locs = globals()
    locs["journey"] = journey
    locs["_a"] = _a
    try:
        exec(f"_a.rep = {code}", locs)
        if asyncio.iscoroutine(_a.rep):
            _a.rep = await _a.rep
    except Exception:
        _a.rep = traceback.format_exc()
    await journey.send(f">>> {code}\n{_a.rep}", code=True, langage="py")


@app_commands.command()
@tools.mjs_only
@journey_command
async def shell(journey: DiscordJourney):
    """Lance un terminal Python directement dans Discord (COMMANDE MJ)

    Envoyer ``help`` dans le pseudo-terminal pour plus d'informations sur son fonctionnement.

    Évidemment, les avertissements dans ``!do`` s'appliquent ici : ne pas faire n'imp avec cette commande !!
    (même si ça peut être très utile, genre pour ajouter des gens en masse à un channel)
    """
    locs = globals()
    locs["journey"] = journey
    shell = realshell.RealShell(journey, locs)
    try:
        await shell.interact()
    except realshell.RealShellExit:
        raise commons.CommandAbortedError()


@app_commands.command()
@tools.mjs_only
@journey_command
async def co(journey: DiscordJourney, member: discord.Member):
    """Lance la procédure d'inscription pour un membre (COMMANDE MJ)

    Fat comme si on se connectait au serveur pour la première fois.

    Args:
        member: Le membre à inscrire (si son inscription a foiré).

    Cette commande est principalement destinée aux tests de développement,
    mais peut être utile si un joueur chibre son inscription
    (à utiliser dans son channel, ou ``#bienvenue`` si même le début a chibré).
    """
    await journey.send(f"Lancement du processus d'inscription pour {member.mention}", ephemeral=True)
    await features.inscription.main(member)


@app_commands.command()
@tools.mjs_only
@journey_command
async def doas(journey: DiscordJourney, *, joueur: app_commands.Transform[Joueur, tools.JoueurTransformer]):
    """Exécute la prochaine commande en tant qu'un joueur (COMMANDE MJ)

    Args:
        joueur: Joueur inscrit en tant que qui exécuter la prochaine commande.

    Example:
        ``!doas Vincent Croquette !vote Annie Colin``
    """
    interaction, runner = await journey.catch_next_command(f"Exécuter la commande à exécuter en tant que {joueur.nom}")
    async with DiscordJourney(interaction, ephemeral=True) as _journey:
        _journey.member = joueur.member
        await runner(_journey)


@app_commands.command()
@tools.mjs_only
@journey_command
async def secret(journey: DiscordJourney):
    """Exécute la prochaine commande en mode "éphémère" (les messages ne s'affichent que pour le lanceur).

    Utile notamment pour faire des commandes dans un channel public, pour que la commande soit invisible.
    """
    interaction, runner = await journey.catch_next_command("Exécuter la commande à rendre silencieuse")
    async with DiscordJourney(interaction, ephemeral=True) as _journey:
        await runner(_journey)


@app_commands.command()
@journey_command
async def apropos(journey: DiscordJourney):
    """Informations et mentions légales du projet.

    N'hésitez-pas à nous contacter pour en savoir plus !
    """
    embed = discord.Embed(
        title=f"**LG-bot** - v{__version__}", description="LG-bot – Plateforme pour parties endiablées de Loup-Garou"
    )
    embed.set_author(name="À propos de ce bot :", icon_url=config.bot.user.avatar.url)
    embed.set_image(
        url=(
            "https://gist.githubusercontent.com/loic-simon/"
            "66c726053323017dba67f85d942495ef/raw/48f2607a61f3fc1b7285fd64873621035c6fbbdb/logo_espci.png"
        ),
    )
    embed.add_field(name="Auteurs", value="Loïc Simon\nTom Lacoma")
    embed.add_field(name="Licence", value="Projet open-source sous licence MIT\nhttps://opensource.org/licenses/MIT")
    embed.add_field(name="Pour en savoir plus :", value="https://github.com/loic-simon/lg-rez", inline=False)
    embed.add_field(name="Copyright :", value=":copyright: 2022 Club BD-Jeux × GRIs – ESPCI Paris - PSL", inline=False)
    embed.set_footer(text="Retrouvez-nous sur Discord : LaCarpe#1674, TaupeOrAfk#3218")

    await journey.send(embed=embed)


@app_commands.command()
@app_commands.check(lambda interaction: not config.is_setup)
@journey_command
async def setup(journey: DiscordJourney):
    """✨ Prépare un serveur nouvellement crée (COMMANDE MJ)

    À n'utiliser que dans un nouveau serveur, pour créer les rôles, catégories, salons et emojis nécessaires.
    """
    await journey.ok_cancel("Setup le serveur ?")

    original_channels = list(config.guild.channels)

    structure = config.server_structure

    # Création rôles
    await journey.send("Création des rôles...")
    roles = {}
    for slug, role in structure["roles"].items():
        roles[slug] = tools.role(role["name"], must_be_found=False)
        if roles[slug]:
            continue
        if isinstance(role["permissions"], list):
            perms = discord.Permissions(**{perm: True for perm in role["permissions"]})
        else:
            perms = getattr(discord.Permissions, role["permissions"])()
        roles[slug] = await config.guild.create_role(
            name=role["name"],
            color=int(role["color"], base=16),
            hoist=role["hoist"],
            mentionable=role["mentionable"],
            permissions=perms,
        )
    # Modification @everyone
    roles["@everyone"] = tools.role("@everyone")
    await roles["@everyone"].edit(
        permissions=discord.Permissions(**{perm: True for perm in structure["everyone_permissions"]})
    )
    await journey.send(f"{len(roles)} rôles créés.")

    # Assignation rôles
    for member in config.guild.members:
        await member.add_roles(roles["bot"] if member == config.bot.user else roles["mj"])

    # Création catégories et channels
    await journey.send("Création des salons...")
    categs = {}
    channels = {}
    for slug, categ in structure["categories"].items():
        categs[slug] = tools.channel(categ["name"], must_be_found=False)
        if not categs[slug]:
            categs[slug] = await config.guild.create_category(
                name=categ["name"],
                overwrites={
                    roles[role]: discord.PermissionOverwrite(**perms) for role, perms in categ["overwrites"].items()
                },
            )
        for position, (chan_slug, channel) in enumerate(categ["channels"].items()):
            channels[chan_slug] = tools.channel(channel["name"], must_be_found=False)
            if channels[chan_slug]:
                continue
            channels[chan_slug] = await categs[slug].create_text_channel(
                name=channel["name"],
                topic=channel["topic"],
                position=position,
                overwrites={
                    roles[role]: discord.PermissionOverwrite(**perms) for role, perms in channel["overwrites"].items()
                },
            )
        for position, (chan_slug, channel) in enumerate(categ["voice_channels"].items()):
            channels[chan_slug] = tools.channel(channel["name"], must_be_found=False)
            if channels[chan_slug]:
                continue
            channels[chan_slug] = await categs[slug].create_voice_channel(
                name=channel["name"],
                position=position,
                overwrites={roles[role]: discord.PermissionOverwrite(**perms) for role, perms in channel["overwrites"]},
            )
    await journey.send(f"{len(channels)} salons créés dans {len(categs)} catégories.")

    # Création emojis
    await journey.send("Import des emojis... (oui c'est très long)")

    async def _create_emoji(name: str, data: bytes):
        can_use = None
        if restrict := structure["emojis"]["restrict_roles"].get(name):
            can_use = [roles[role] for role in restrict]
        await config.guild.create_custom_emoji(
            name=name,
            image=data,
            roles=can_use,
        )

    n_emojis = 0
    if structure["emojis"]["drive"]:
        folder_id = structure["emojis"]["folder_path_or_id"]
        for file in gsheets.get_files_in_folder(folder_id):
            if file["extension"] != "png":
                continue
            name = file["name"].removesuffix(".png")
            if tools.emoji(name, must_be_found=False):
                continue
            data = gsheets.download_file(file["file_id"])
            await _create_emoji(name, data)
            n_emojis += 1
    else:
        root = structure["emojis"]["folder_path_or_id"]
        for file in os.scandir(root):
            name, extension = os.path.splitext(file.name)
            if extension != ".png":
                continue
            if tools.emoji(name, must_be_found=False):
                continue
            with open(file.path, "rb") as fh:
                data = fh.read()
            await _create_emoji(name, data)
            n_emojis += 1
    await journey.send(f"{n_emojis} emojis importés.")

    # Paramètres généraux du serveur
    await journey.send("Configuration du serveur...")
    if not structure["icon"]:
        icon_data = None
    elif structure["icon"]["drive"]:
        file_id = structure["icon"]["png_path_or_id"]
        icon_data = gsheets.download_file(file_id)
    else:
        with open(structure["icon"]["png_path_or_id"], "rb") as fh:
            icon_data = fh.read()

    await config.guild.edit(
        name=structure["name"],
        icon=icon_data,
        afk_channel=channels.get(structure["afk_channel"]),
        afk_timeout=int(structure["afk_timeout"]),
        verification_level=discord.VerificationLevel[structure["verification_level"]],
        default_notifications=discord.NotificationLevel[structure["default_notifications"]],
        explicit_content_filter=discord.ContentFilter[structure["explicit_content_filter"]],
        system_channel=channels[structure["system_channel"]],
        system_channel_flags=discord.SystemChannelFlags(**structure["system_channel_flags"]),
        preferred_locale=structure["preferred_locale"],
        reason="Guild set up!",
    )
    await journey.send(f"Fin de la configuration !")

    config.is_setup = True

    # Delete current chan (will also trigger on_ready)
    await journey.yes_no("Terminé ! Ce salon va être détruit (ce n'est pas une question).")
    for channel in original_channels:
        await channel.delete()


class CommandTransformer(app_commands.Transformer):
    def _get_commands(interaction: discord.Interaction) -> dict[str, app_commands.Command]:
        if interaction.namespace.mode == "enable":
            return config.bot.tree.disabled_commands
        else:
            return config.bot.tree.enabled_commands

    async def transform(self, interaction: discord.Interaction, value: str) -> app_commands.Command:
        return self._get_commands()[value]

    async def autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=name, value=name) for name in self._get_commands() if current in name][:25]


@app_commands.command()
@journey_command
async def command(
    journey: DiscordJourney,
    mode: Literal["enable", "disable"],
    command: app_commands.Transform[app_commands.Command, CommandTransformer],
):
    """✨ Active ou désactive une commande (COMMANDE MJ)

    Args:
        mode: Opération à réaliser.
        command: Commande à activer/désactiver (Y COMPRIS POUR LES MJS !).
    """
    if mode == "enable":
        if config.bot.tree.enable_command(command.qualified_name):
            await config.bot.tree.sync(guild=config.guild)
        await journey.send(f"Commande `/{command.qualified_name}` activée.")
    else:
        if config.bot.tree.disable_command(command.qualified_name):
            await config.bot.tree.sync(guild=config.guild)
        await journey.send(f"Commande `/{command.qualified_name}` désactivée.")
