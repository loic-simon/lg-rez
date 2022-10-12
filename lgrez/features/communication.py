"""lg-rez / features / Communication

Envoi de messages, d'embeds...

"""
import datetime
import functools
import os
import re
from typing import Literal

import discord
from discord import app_commands
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from lgrez import commons, config
from lgrez.blocs import tools, gsheets
from lgrez.blocs.journey import DiscordJourney, journey_command, journey_context_menu
from lgrez.bdd import (
    Joueur,
    Action,
    Camp,
    BaseAction,
    Utilisation,
    Statut,
    ActionTrigger,
    CandidHaroType,
    UtilEtat,
    Vote,
)
from lgrez.features import gestion_actions
from lgrez.features.sync import transtype


def _joueur_repl(mtch: re.Match) -> str:
    """Remplace @... par la mention d'un joueur, si possible"""
    nearest = Joueur.find_nearest(mtch.group(1), col=Joueur.nom, sensi=0.8)
    if nearest:
        joueur = nearest[0][0]
        try:
            return joueur.member.mention
        except ValueError:
            pass
    return mtch.group(0)


def _role_repl(mtch: re.Match) -> str:
    """Remplace @role_slug par la mention du rôle, si possible"""
    try:
        role = getattr(config.Role, mtch.group(1).lower())
    except AttributeError:
        return mtch.group(0)
    else:
        return role.mention


def _emoji_repl(mtch: re.Match) -> str:
    """Remplace :(emoji): par la représentation de l'emoji, si possible"""
    emo = tools.emoji(mtch.group(1), must_be_found=False)
    if emo:
        return str(emo)
    return mtch.group()


async def _chose_role_and_camp(journey: DiscordJourney, joueur: Joueur) -> tuple[str, discord.Emoji | None]:
    role = joueur.role.nom_complet
    if await journey.yes_no(f"Rôle à afficher pour {joueur.nom} = {role} ? (Pas double peau ou autre)"):
        emoji_camp = joueur.camp.discord_emoji_or_none
    else:
        (role,) = await journey.modal(
            "Choix du rôle à afficher",
            discord.ui.TextInput(label=f"Rôle de {joueur.nom} = {role}"[:45]),
        )
        camp = await journey.select(
            f'Camp du rôle "{role}" :',
            {
                camp: discord.SelectOption(label=camp.nom, emoji=camp.discord_emoji)
                for camp in Camp.query.filter_by(public=True).all()
            },
        )
        emoji_camp = camp.discord_emoji
    return role, emoji_camp


DESCRIPTION = """Commandes d'envoi de messages, d'embeds, d'annonces..."""

current_embed = None


@app_commands.command()
@tools.mjs_only
@journey_command
async def send(journey: DiscordJourney, *, cibles: str, message: str):
    """Envoie un message à tous ou certains joueurs (COMMANDE MJ)

    Args:
        cibles: Destinataires (`all`, `vivants`, `morts`, `<crit>=<filtre>`, `<joueur`)
        message: Message, éventuellement formaté ({member.mention}, ...)

    ``cibles`` peut être :
        - ``all`` :             Tous les joueurs inscrits, vivants et morts
        - ``vivants`` :         Les joueurs en vie
        - ``morts`` :           Les joueurs morts
        - ``<crit>=<filtre>`` : Les joueurs répondant au critère ``Joueur.<crit> == <filtre>``.
            ``crit`` peut être ``"nom"``, ``"chambre"``, ``"statut"``, ``"role"``, ``"camp"``...
            L'ensemble doit être entouré de guillemets si ``filtre`` contient un espace.
            Les rôles/camps sont cherchés par slug.
        - *le nom d'un joueur*  (raccourci pour ``nom=X``, doit être entouré de guillemets si nom + prénom)

    ``message`` peut contenir un ou plusieurs bouts de code Python à évaluer, entourés d'accolades.

    L'évaluation est faite séparément pour chaque joueur, ce qui permet de personnaliser le message
    grâce aux variables particulières dépendant du joueur :

        - ``joueur`` :  objet BDD du joueur recevant le message ==> ``joueur.nom``, ``joueur.role``...
        - ``member`` :  objet :class:`discord.Member` associé ==> ``member.mention``
        - ``chan``   :  objet :class:`discord.TextChannel` du chan privé du joueur

    Les différentes tables de données sont accessibles sous leur nom (``Joueur``, ``Role``...)

    Il est impossible d'appeler des coroutines (await) dans le code à évaluer.

    Examples:
        - ``!send all Bonsoir à tous c'est Fanta``
        - ``!send vivants Attention {member.mention}, derrière toi c'est affreux !``
        - ``!send "role=servante" Ça va vous ? Vous êtes bien {joueur.role.nom} ?``
    """
    if cibles == "all":
        joueurs = Joueur.query.all()
    elif cibles == "vivants":
        joueurs = Joueur.query.filter(Joueur.est_vivant).all()
    elif cibles == "morts":
        joueurs = Joueur.query.filter(Joueur.est_mort).all()
    elif "=" in cibles:
        crit, _, filtre = cibles.partition("=")
        crit = crit.strip()
        if crit in Joueur.attrs:
            col = Joueur.attrs[crit]
            arg = transtype(filtre.strip(), col)
            joueurs = Joueur.query.filter_by(**{crit: arg}).all()
        else:
            raise commons.UserInputError(f"critère '{crit}' incorrect")
    else:
        raise commons.UserInputError("cibles", f"Destinataires invalides : {cibles}")

    descr = f"Cibles : {cibles}\nMessage : {message}\n"

    if not joueurs:
        await journey.send(f"{descr}:x: Aucun joueur trouvé.")
        return

    await journey.send(f"{descr}:arrow_forward: {len(joueurs)} trouvé(s), envoi...")
    for joueur in joueurs:
        member = joueur.member
        chan = joueur.private_chan

        evaluated_message = tools.eval_accols(message, locals_=locals())
        await chan.send(evaluated_message)

    await journey.channel.send("Fini.")


@app_commands.command()
@tools.mjs_only
@journey_command
async def post(journey: DiscordJourney, *, chan: discord.TextChannel, message: str):
    """Envoie un message dans un salon (COMMANDE MJ)

    Args:
        chan: Salon ou poster le message.
        message: Message à envoyer (utiliser "\n" pour un saut de ligne).
    """
    message = message.replace(r"\n", "\n")
    await chan.send(message)
    await journey.send(f"Message posté sur {chan.mention} :\n" + tools.quote_bloc(message))


@app_commands.command()
@tools.mjs_only
@journey_command
async def plot(journey: DiscordJourney, *, quoi: Literal["cond", "maire"], depuis: str | None = None):
    """Trace le résultat du vote et l'envoie sur #annonces (COMMANDE MJ)

    Args:
        quoi: Vote pour le condamné ou pour l'élection à la Mairie ?
        depuis: Heure à partir de laquelle compter les votes (si plusieurs votes dans la journée, HHh / HHhMM).
            Compte tous les votes du jour par défaut.
            Si plus tard que l'heure actuelle, compte les votes de la veille.

    Trace les votes sous forme d'histogramme à partir du Tableau de bord, en fait un embed
    en précisant les résultats détaillés et l'envoie sur le chan ``#annonces``.

    Si ``quoi == "cond"``, déclenche aussi les actions liées au mot des MJs (:attr:`.bdd.ActionTrigger.mot_mjs`).
    """
    # Différences plot cond / maire
    if quoi == "cond":
        vote_enum = Vote.cond
        haro_candidature = CandidHaroType.haro
        typo = "bûcher du jour"
        mort_election = "Mort"
        pour_contre = "contre"
        emoji = config.Emoji.bucher
        couleur = 0x730000

    else:
        vote_enum = Vote.maire
        haro_candidature = CandidHaroType.candidature
        typo = "nouveau maire"
        mort_election = "Élection"
        pour_contre = "pour"
        emoji = config.Emoji.maire
        couleur = 0xD4AF37

    if depuis:
        tps = tools.heure_to_time(depuis)
    else:
        tps = datetime.time(0, 0)

    ts = datetime.datetime.combine(datetime.date.today(), tps)
    if ts > datetime.datetime.now():  # hier
        ts -= datetime.timedelta(days=1)

    log = f"!plot {quoi} (> {ts}) :"
    query = Utilisation.query.filter(
        Utilisation.etat == UtilEtat.validee,
        Utilisation.ts_decision > ts,
        Utilisation.action.has(active=True),
    )
    cibles = {}

    # Get votes
    utils = query.filter(Utilisation.action.has(vote=vote_enum)).all()
    votes = {util.action.joueur: util.cible for util in utils}
    votelog = " / ".join(f"{v.nom} -> {c.nom}" for v, c in votes.items())
    log += f"\n  - Votes : {votelog}"

    for votant, vote in votes.items():
        cibles.setdefault(vote, [])
        cibles[vote].append(votant.nom)

    # Get intriguants
    intba = BaseAction.query.get(config.modif_vote_baseaction)
    if intba:
        log += "\n  - Intrigant(s) : "
        for util in query.filter(Utilisation.action.has(base=intba)).all():

            votant = util.ciblage("cible").valeur
            vote = util.ciblage("vote").valeur
            log += f"{util.action.joueur.nom} : {votant.nom} -> {vote.nom} / "

            initial_vote = votes.get(votant)
            if initial_vote:
                cibles[initial_vote].remove(votant.nom)
                if not cibles[initial_vote]:  # plus de votes
                    del cibles[initial_vote]
            votes[votant] = vote
            cibles.setdefault(vote, [])
            cibles[vote].append(votant.nom)

    # Tri des votants
    for votants in cibles.values():
        votants.sort()  # ordre alphabétique

    # Get corbeaux, après tri -> à la fin
    corba = BaseAction.query.get(config.ajout_vote_baseaction)
    if corba:
        log += "\n  - Corbeau(x) : "
        for util in query.filter(Utilisation.action.has(base=corba)).all():
            log += f"{util.action.joueur.nom} -> {util.cible} / "
            cibles.setdefault(util.cible, [])
            cibles[util.cible].extend([util.action.joueur.role.nom] * config.n_ajouts_votes)

    # Classe utilitaire
    @functools.total_ordering
    class _Cible:
        """Représente un joueur ciblé, pour usage dans !plot"""

        def __init__(self, joueur, votants):
            self.joueur = joueur
            self.votants = votants

        def __repr__(self) -> str:
            return f"{self.joueur.nom} ({self.votes})"

        def __eq__(self, other):
            if not isinstance(other, type(self)):
                return NotImplemented
            return self.joueur.nom == other.joueur.nom and self.votes == other.votes

        def __lt__(self, other):
            if not isinstance(other, type(self)):
                return NotImplemented
            if self.votes == other.votes:
                return self.joueur.nom < other.joueur.nom
            return self.votes < other.votes

        @property
        def votes(self):
            return len(self.votants)

        @property
        def eligible(self):
            return any(ch.type == haro_candidature for ch in self.joueur.candidharos)

        def couleur(self, choisi) -> str:
            if self == choisi:
                return hex(couleur).replace("0x", "#")
            if self.eligible:
                return "#64b9e9"
            else:
                return "gray"

    # Récupération votes
    cibles = [_Cible(jr, vts) for (jr, vts) in cibles.items()]
    cibles.sort(reverse=True)  # par nb de votes, puis ordre alpha
    log += f"\n  - Cibles : {cibles}"

    # Détermination cible
    choisi = None
    eligibles = [cible for cible in cibles if cible.eligible]
    log += f"\n  - Éligibles : {eligibles}"

    if eligibles:
        maxvotes = eligibles[0].votes
        egalites = [cible for cible in eligibles if cible.votes == maxvotes]

        if len(egalites) > 1:  # Égalité
            choisi = await journey.select(
                "Égalité entre plusieurs joueurs :" + "\nQui meurt / est élu ? "
                "(regarder vote du maire, si joueur garde-loupé ou inéligible...)",
                {cible: cible.joueur.nom for cible in egalites} | {None: "Personne (pas de vote du maire)"},
            )

        elif await journey.yes_no(
            f"Joueur éligible le plus voté : {tools.bold(eligibles[0].joueur.nom)}\n"
            "Ça meurt / est élu ? (pas garde-loupé, inéligible ou autre)"
        ):
            choisi = eligibles[0]

    log += f"\n  - Choisi : {choisi or '[aucun]'}"
    await tools.log(log)

    # Paramètres plot
    discord_gray = "#2F3136"
    plt.figure(facecolor=discord_gray)
    plt.rcParams.update({"font.size": 16})
    ax = plt.axes(facecolor="#8F9194")  # coloration de TOUT le graphe
    ax.tick_params(axis="both", colors="white")
    ax.spines["bottom"].set_color("white")
    ax.spines["left"].set_color(discord_gray)
    ax.spines["right"].set_color(discord_gray)
    ax.spines["top"].set_color(discord_gray)
    ax.set_facecolor(discord_gray)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Plot
    ax.bar(
        x=range(len(cibles)),
        height=[cible.votes for cible in cibles],
        tick_label=[cible.joueur.nom.replace(" ", "\n", 1) for cible in cibles],
        color=[cible.couleur(choisi) for cible in cibles],
    )
    plt.grid(axis="y")

    if not os.path.isdir("figures"):
        os.mkdir("figures")

    now = datetime.datetime.now().strftime("%Y-%m-%d--%H")
    image_path = f"figures/hist_{now}_{quoi}.png"
    plt.savefig(image_path, bbox_inches="tight")

    # --------------- Partie Discord ---------------

    # Détermination rôle et camp
    emoji_camp = None
    if choisi:
        if quoi == "cond":
            role, emoji_camp = _chose_role_and_camp(journey, choisi.joueur)
            nom_et_role = f"{tools.bold(choisi.joueur.nom)}, {role}"
        else:
            # Maire : ne pas annoncer le rôle
            nom_et_role = f"{tools.bold(choisi.joueur.nom)}"
    else:
        nom_et_role = "personne, bande de tocards"

    # Création embed
    embed = discord.Embed(
        title=f"{mort_election} de {nom_et_role}", description=f"{len(votes)} votes au total", color=couleur
    )
    embed.set_author(name=f"Résultats du vote pour le {typo}", icon_url=emoji.url)

    if emoji_camp:
        embed.set_thumbnail(url=emoji_camp.url)

    embed.set_footer(
        text="\n".join(
            ("A" if cible.votes == 1 else "Ont")
            + f" voté {pour_contre} {cible.joueur.nom} : "
            + ", ".join(cible.votants)
            for cible in cibles
        )
    )

    file = discord.File(image_path, filename="image.png")
    embed.set_image(url="attachment://image.png")

    await journey.ok_cancel("Ça part ?", file=file, embed=embed)

    # Envoi du graphe
    file = discord.File(image_path, filename="image.png")
    # Un objet File ne peut servir qu'une fois, il faut le recréer

    await config.Channel.annonces.send("@everyone Résultat du vote ! :fire:", file=file, embed=embed)
    await journey.send(f"Et c'est parti dans {config.Channel.annonces.mention} !")

    if quoi == "cond":
        # Actions au mot des MJs
        for action in Action.query.filter(Action.base.has(trigger_debut=ActionTrigger.mot_mjs)).all():
            await gestion_actions.open_action(action)

        await journey.channel.send("(actions liées au mot MJ ouvertes)")


@app_commands.command()
@tools.mjs_only
@journey_command
async def annoncemort(
    journey: DiscordJourney,
    *,
    victime: app_commands.Transform[Joueur, tools.VivantTransformer],
    victime_2: app_commands.Transform[Joueur, tools.VivantTransformer] | None = None,
    victime_3: app_commands.Transform[Joueur, tools.VivantTransformer] | None = None,
    victime_4: app_commands.Transform[Joueur, tools.VivantTransformer] | None = None,
    victime_5: app_commands.Transform[Joueur, tools.VivantTransformer] | None = None,
):
    """Annonce un ou plusieurs mort(s) hors-vote (COMMANDE MJ)

    Args:
        victime: (Premier) mort à annoncer.
        victime_2: Deuxième mort à annoncer.
        victime_3: Troisième mort à annoncer.
        victime_4: Quatrième mort à annoncer.
        victime_5: Cinquième mort à annoncer (pour plus, faire en 2 fois, merde)

    Envoie un embed par mort dans ``#annonces``
    """
    joueurs = [joueur for joueur in (victime, victime_2, victime_3, victime_4, victime_5) if joueur]
    roles = []
    emojis = []
    for joueur in joueurs:
        role, emoji_camp = await _chose_role_and_camp(journey, joueur)

        if joueur.statut == Statut.MV:
            if await journey.yes_no("Annoncer la mort-vivance ?"):
                role += " Mort-Vivant"
            else:
                emoji_camp = joueur.role.camp.discord_emoji_or_none

        roles.append(role)
        emojis.append(emoji_camp)

    contextes = await journey.modal("Contextes", *[f"Pour {joueur.nom} :" for joueur in joueurs])
    authors = [
        "Oh mon dieu, quelqu'un est mort !",
        "Oh non, un deuxième !!",
        "Mais c'est une vraie hécatombe !?!?",
        "Cela s'arrêtera-t-il un jour ?",
        "Bon, ça va commencer à se voir...",
    ]

    # Création embeds
    embeds = []
    for joueur, role, emoji_camp, contexte, author in zip(joueurs, roles, emojis, contextes, authors):
        embed = discord.Embed(title=f"Mort de {tools.bold(joueur.nom)}, {role}", description=contexte, color=0x730000)
        embed.set_author(name=author)
        if emoji_camp:
            embed.set_thumbnail(url=emoji_camp.url)

        embeds.append(embed)

    await journey.ok_cancel("Ça part ?", embeds=embeds)
    await config.Channel.annonces.send("@everyone Il s'est passé quelque chose ! :scream:", embeds=embeds)
    await journey.send(f"Et c'est parti dans {config.Channel.annonces.mention} !")


@app_commands.command()
@tools.mjs_only
@journey_command
async def lore(journey: DiscordJourney, doc_id: str):
    """Récupère et poste un lore depuis un Google Docs (COMMANDE MJ)

    Convertit les formats et éléments suivants vers Discord :
        - Gras, italique, souligné, barré;
        - Petites majuscules (-> majuscules);
        - Polices à chasse fixe (Consolas / Courier New) (-> code);
        - Liens hypertextes;
        - Listes à puces;
        - Mentions de joueurs, sous la forme ``@Prénom Nom``;
        - Mentions de rôles, sous la forme ``@nom_du_role``;
        - Emojis, sous la forme ``:nom:``.

    Permet soit de poster directement dans #annonces, soit de
    récupérer la version formatée du texte (pour copier-coller).

    Args:
        doc_id: ID ou URL du document (doit être public ou dans le Drive LG Rez).
    """
    if len(doc_id) < 44:
        raise commons.UserInputError("doc_id", "Doit être l'ID ou l'URL d'un document Google Docs")
    elif len(doc_id) > 44:  # URL fournie (pas que l'ID)
        mtch = re.search(r"/d/([\w-]{44})(\W|$)", doc_id)
        if mtch:
            doc_id = mtch.group(1)
        else:
            raise commons.UserInputError("doc_id", "Doit être l'ID ou l'URL d'un document Google Docs")

    await journey.send("Récupération du document...")
    async with journey.channel.typing():
        content = gsheets.get_doc_content(doc_id)

    formatted_text = ""
    for (_text, style) in content:
        _text = _text.replace("\v", "\n").replace("\f", "\n")

        # Espaces/newlines au début/fin de _text ==> à part
        motif = re.fullmatch(r"(\s*)(.*?)(\s*)", _text)
        pref, text, suff = motif.group(1, 2, 3)

        if not text:  # espaces/newlines uniquement
            formatted_text += pref + suff
            continue

        # Remplacement des mentions
        for i in (3, 2, 1, 0):
            text = re.sub(rf"@([\w-]+( [\w-]+){{{i}}})", _joueur_repl, text)
        text = re.sub(r"@(\w+)", _role_repl, text)
        text = re.sub(r":(\w+):", _emoji_repl, text)

        if style.get("bold"):
            text = tools.bold(text)
        if style.get("italic"):
            text = tools.ital(text)
        if style.get("strikethrough"):
            text = tools.strike(text)
        if style.get("smallCaps"):
            text = text.upper()
        if wff := style.get("weightedFontFamily"):
            if wff["fontFamily"] in ["Consolas", "Courier New"]:
                text = tools.code(text)
        if link := style.get("link"):
            if url := link.get("url"):
                if "://" not in text:
                    text = text + f" (<{url}>)"
        elif style.get("underline"):  # ne pas souligner si lien
            text = tools.soul(text)

        formatted_text += pref + text + suff

    await tools.send_blocs(journey.channel, formatted_text)
    choice = await journey.buttons(
        f"————————————————————",
        {
            "publish": discord.ui.Button(label="Publier sur #annonces", emoji="📣"),
            "get_raw": discord.ui.Button(label="Récupérer la version formatée", emoji="📝"),
            "stop": discord.ui.Button(label="Stop", emoji="⏹"),
        },
    )

    if choice == "publish":
        await tools.send_blocs(config.Channel.annonces, formatted_text)
        await journey.send("Fait !")
    elif choice == "get_raw":
        await journey.send(formatted_text, code=True)
    else:
        await journey.send("Mission aborted.")


@app_commands.context_menu(name="Modifier ce message")
@tools.mjs_only
@journey_context_menu
async def modif(journey: DiscordJourney, message: discord.Message):
    """Modifie un message du bot (COMMANDE MJ)

    Il n'est pas possible (pour le moment ?) de modifier une image, pièce jointe ou embed.
    """
    if message.author == journey.member:
        await journey.send("Pour modifier ton propre message, utilise le petit crayon\n(blaireau)", ephemeral=True)
        return

    if message.author != config.bot.user:
        await journey.send(":x: Les messages des autres membres ne sont pas modifiables !", ephemeral=True)
        return

    (content,) = await journey.modal(
        "Modifier le message",
        discord.ui.TextInput(
            label="Contenu", style=discord.TextStyle.paragraph, default=message.content, min_length=1, max_length=2000
        ),
    )
    await message.edit(content=content)
