"""lg-rez / features / Communication

Envoi de messages, d'embeds...

"""

import os
import datetime
from collections import Counter

import discord
from discord.ext import commands
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from lgrez import config
from lgrez.blocs import tools, env, gsheets
from lgrez.bdd import (Joueur, Action, Camp, CandidHaro,
                       Statut, ActionTrigger, CandidHaroType)
from lgrez.features import gestion_actions
from lgrez.features.sync import transtype


class Communication(commands.Cog):
    """Commandes d'envoi de messages, d'embeds, d'annonces..."""

    current_embed = None

    @commands.command()
    @tools.mjs_only
    async def embed(self, ctx, key=None, *, val=None):
        """Prépare un embed (message riche) et l'envoie (COMMANDE MJ)

        Warning:
            Commande en bêta, non couverte par les tests unitaires
            et souffrant de bugs connus (avec les fields notemment)

        Args:
            key: sous-commande (voir ci-dessous). Si omis, prévisualise
                le brouillon d'embed actuellement en préparation ;
            val: valeur associée. Pour les sous-commandes de
                construction d'élement, supprime ledit élément si omis.

        - Sous-commandes générales :
            - ``!embed create <titre>`` :  Créer un nouveau brouillon
              d'embed (un seul brouillon en parallèle, partout)
            - ``!embed delete`` :          Supprimer le brouillon d'embed
            - ``!embed preview``  :        Voir l'embed sans les aides
            - ``!embed post [#channel]`` : Envoyer l'embed sur ``#channel``
              (chan courant si omis)

        - Sous-commandes de construction d'éléments :
            - Éléments généraux :
                - ``!embed title [titre]``
                - ``!embed description [texte]``
                - ``!embed url [url*]``
                - ``!embed color [#ffffff]`` (barre de gauche,
                  code hexadécimal)

            - Auteur :
                - ``!embed author [nom]``
                - ``!embed author_url [url*]``
                - ``!embed author_icon [url**]``

            - Talon :
                - ``!embed footer [texte]``
                - ``!embed footer_icon [url**]``

            - Images :
                - ``!embed image [url**]`` (grande image)
                - ``!embed thumb [url**]`` (en haut à droite)

            - Champs : syntaxe spéciale
                - ``!embed field <i> <skey> [val]``
                    - ``i`` : Numéro du champ (commençant à ``0``).
                      Si premier champ non existant, le crée ;
                    - ``skey`` :
                        - ``name`` :    Nom du champ
                        - ``value`` :   Valeur du champ
                        - ``delete`` :  Supprime le champ

                Les champs sont (pour l'instant) forcément de type
                inline (côte à côte).

        \* Les URL doivent commencer par http(s):// pour être
        reconnues comme telles.

        \*\* Ces URL doivent correspondre à une image.
        """

        if val is None:
            val = discord.Embed.Empty

        # Récupération de l'embed (stocké dans le cog)
        emb = self.current_embed

        # Attributs modifiables directement : emb.attr = value
        direct = [
            "title",
            "description",
            "url",
        ]
        # Attributs à modifier en appelant une méthode : emb.set_<attr>(value)
        # avec method[key] = (<attr>, <value>)
        method = {
            "footer": ("footer", "text"),
            "footer_icon": ("footer", "icon_url"),
            "image": ("image", "url"),
            "thumb": ("thumbnail", "url"),
            "author_url": ("author", "url"),
            "author_icon": ("author", "icon_url"),
        }

        if not emb:             # Pas d'embed en cours
            if key == "create" and val:
                emb = discord.Embed(title=val)
            else:
                await ctx.send(
                    "Pas d'embed en préparation. "
                    + tools.code("!embed create <titre>")
                    + " pour en créer un.")
                return

        elif key in direct:         # Attributs modifiables directement
            setattr(emb, key, val)

        elif key in method:         # Attributs à modifier via une méthode
            prop, attr = method[key]
            getattr(emb, f"set_{prop}")(**{attr: val})

        elif key == "author":       # Cas particulier
            emb.set_author(name=val) if val else emb.remove_author()

        elif key == "color":        # Cas particulier : cast couleur en int
            try:
                if val:
                    emb.color = eval(val.replace("#", "0x"))
                else:
                    emb.color = discord.Embed.Empty
            except Exception:
                await ctx.send("Couleur invalide")
                return

        elif key == "field":        # Cas encore plus particulier
            i_max = len(emb.fields)     # N fields ==> i_max = N+1
            try:
                i, skey, val = val.split(" ", maxsplit=2)
                i = int(i)
                if i < 0 or i > i_max:
                    await ctx.send("Numéro de field invalide")
                    return
                if skey not in ["name", "value", "delete"]:
                    raise ValueError()
            except Exception:
                await ctx.send("Syntaxe invalide")
                return

            if i == i_max:
                if skey == "name":
                    emb.add_field(name=val,
                                  value=f"!embed field {i} value <valeur>")
                elif skey == "value":
                    emb.add_field(name=f"!embed field {i} name <nom>",
                                  value=val)
                # emb.add_field(*, name, value, inline=True)

            else:
                if skey == "name":
                    emb.set_field_at(i, name=val, value=emb.fields[i].value)
                elif skey == "value":
                    emb.set_field_at(i, name=emb.fields[i].name, value=val)
                else:
                    emb.remove_field(i)
                # emb.set_field_at(i, *, name, value, inline=True)

        elif key == "delete":
            self.current_embed = None
            await ctx.send(
                "Supprimé. " + tools.code("!embed create <titre>")
                + " pour en créer un."
            )
            return

        elif key == "create":
            await ctx.send(
                "Déjà un embed en cours de création. Utiliser "
                + tools.code("!embed delete") + "pour le supprimer."
            )

        elif key == "preview":
            await ctx.send("Prévisuatisation :", embed=emb)
            await ctx.send(
                "Utiliser " + tools.code("!embed post #channel")
                + "pour publier l'embed."
            )
            return

        elif key == "post":
            if not val:     # channel non précisé
                await ctx.send(embed=emb)
            elif (chan := tools.channel(val, must_be_found=False)):
                await chan.send(embed=emb)
                await ctx.send("Et pouf !")
            else:
                await ctx.send(
                    f"Channel inconnu. Réessaye en le mentionnant "
                    f"({tools.code('#channel')})"
                )
            return

        elif key is not None:
            await ctx.send(
                f"Option {key} incorrecte ; voir "
                + tools.code("!help embed") + "pour en savoir plus."
            )
            return

        h_emb = emb.copy()
        if not emb.title:
            h_emb.title = "!embed title <titre>"
        if not emb.description:
            h_emb.description = "!embed description <description>"
        if not emb.footer:
            h_emb.set_footer(text="!embed footer <footer>")
        if not emb.author:
            h_emb.set_author(name="!embed author <auteur>")

        i_max = len(emb.fields)                 # N fields ==> i_max = N+1
        h_emb.add_field(name=f"!embed field {i_max} name <nom>",
                        value=f"!embed field {i_max} value <nom>")

        await ctx.send("Embed en préparation :", embed=h_emb)
        await ctx.send(
            f"Utiliser {tools.code('!embed preview')} pour prévisualiser "
            f"l'embed.\n Autres options : "
            + tools.code("!embed color <#xxxxxx> / url <url> / image <url> / "
                         "thumb <url> / author_url <url> / footer_icon <url>")
        )

        self.current_embed = emb


    @commands.command(aliases=["tell"])
    @tools.mjs_only
    async def send(self, ctx, cible, *, message):
        """Envoie un message à tous ou certains joueurs (COMMANDE MJ)

        Args:
            cible: destinataires
            message: message, éventuellement formaté

        ``cible`` peut être :
            - ``all`` :             Tous les joueurs inscrits, vivants et morts
            - ``vivants`` :         Les joueurs en vie
            - ``morts`` :           Les joueurs morts
            - ``<crit>=<filtre>`` : Les joueurs répondant au critère
              ``Joueur.<crit> == <filtre>``. ``crit`` peut être ``"nom"``,
              ``"chambre"``, ``"statut"``, ``"role"``, ``"camp"``...
              L'ensemble doit être entouré de guillements si ``filtre``
              contient un espace. Les rôles/camps sont cherchés par slug.
            - *le nom d'un joueur*  (raccourci pour ``nom=X``, doit être
              entouré de guillements si nom + prénom)

        ``message`` peut contenir un ou plusieurs bouts de code Python
        à évaluer, entourés d'accolades.

        L'évaluation est faite séparément pour chaque joueur, ce qui
        permet de personnaliser le message grâce aux variables
        particulières dépendant du joueur :

            - ``joueur`` :  objet BDD du joueur recevant le message
              ==> ``joueur.nom``, ``joueur.role``...
            - ``member`` :  objet discord.Member associé
              ==> ``member.mention``
            - ``chan`` :    objet :class:`discord.TextChannel` du
              chan privé du joueur

        Attention :
            - ``ctx`` :     objet :class:`discord.ext.commands.Context`
              de ``!send``  ==> ``ctx.author`` = lanceur de la commande !!!

        Les différentes tables de données sont accessibles sous leur nom
        (``Joueur``, ``Role``...)

        Il est impossible d'appeller des coroutines (await) dans le code
        à évaluer.

        Examples:
            - ``!send all Bonsoir à tous c'est Fanta``
            - ``!send vivants Attention {member.mention},
              derrière toi c'est affreux !``
            - ``!send "role=servante" Ça va vous ?
              Vous êtes bien {joueur.role.nom} ?``
        """
        if cible == "all":
            joueurs = Joueur.query.all()
        elif cible == "vivants":
            joueurs = Joueur.query.filter(
                Joueur.statut.in_([Statut.vivant, Statut.MV])
            ).all()
        elif cible == "morts":
            joueurs = Joueur.query.filter_by(statut=Statut.mort).all()
        elif "=" in cible:
            crit, _, filtre = cible.partition("=")
            crit = crit.strip()
            if crit in Joueur.attrs:
                col = Joueur.attrs[crit]
                arg = transtype(filtre.strip(), col)
                joueurs = Joueur.query.filter_by(**{crit: arg}).all()
            else:
                raise commands.UserInputError(f"critère '{crit}' incorrect")
        else:
            joueurs = [await tools.boucle_query_joueur(ctx, cible, "À qui ?")]

        if not joueurs:
            await ctx.send("Aucun joueur trouvé.")
            return

        await ctx.send(f"{len(joueurs)} trouvé(s), envoi...")
        for joueur in joueurs:
            member = joueur.member
            chan = joueur.private_chan

            evaluated_message = tools.eval_accols(message, locals_=locals())
            await chan.send(evaluated_message)

        await ctx.send("Fini.")


    @commands.command()
    @tools.mjs_only
    async def post(self, ctx, chan, *, message):
        """Envoie un message dans un salon (COMMANDE MJ)

        Args:
            chan: nom du salon ou sa mention
            message: message à envoyer (peut être aussi long que
                nécessaire, contenir des sauts de lignes...)
        """
        chan = tools.channel(chan)
        await chan.send(message)
        await ctx.send("Fait.")


    @commands.command()
    @tools.mjs_only
    async def plot(self, ctx, type):
        """Trace le résultat du vote et l'envoie sur #annonces (COMMANDE MJ)

        Warning:
            Commande en bêta, non couverte par les tests unitaires

        Args:
            type: peut être

                - ``cond``   pour le vote pour le condamné
                - ``maire``  pour l'élection à la Mairie

        Trace les votes sous forme d'histogramme à partir du Tableau de
        bord, en fait un embed en présisant les résultats détaillés et
        l'envoie sur le chan ``#annonces``.

        Si ``type == "cond"``, déclenche aussi les actions liées au mot
        des MJs (:attr:`bdd.ActionTrigger.mot_mjs`).
        """
        # Différences plot cond / maire

        if type == "cond":
            ind_col_cible = gsheets.a_to_index(config.tdb_votecond_column)
            ind_col_votants = gsheets.a_to_index(config.tdb_votantcond_column)
            haro_candidature = CandidHaroType.haro
            typo = "bûcher du jour"
            mort_election = "Mort"
            pour_contre = "contre"
            emoji = "bucher"
            couleur = 0x730000

        elif type == "maire":
            ind_col_cible = gsheets.a_to_index(config.tdb_votemaire_column)
            ind_col_votants = gsheets.a_to_index(config.tdb_votantmaire_column)
            haro_candidature = CandidHaroType.candidature
            typo = "nouveau maire"
            mort_election = "Élection"
            pour_contre = "pour"
            emoji = "maire"
            couleur = 0xd4af37

        else:
            await ctx.send("`type` doit être `maire` ou `cond`")
            return

        # Classe utilitaire

        class _Cible():
            """Représente un joueur ciblé, pour usage dans !plot"""
            def __init__(self, nom, votes=0):
                self.nom = nom
                self.label = self.nom.replace(" ", "\n", 1)

                self.votes = votes
                self.votants = []

                self.joueur = Joueur.query.filter_by(nom=nom).one()
                if not self.joueur:
                    raise ValueError(f"Joueur \"{nom}\" non trouvé en base")

                self.eligible = bool(CandidHaro.query.filter_by(
                    joueur=self.joueur, type=haro_candidature).all())

            def __repr__(self):
                return f"{self.nom} ({self.votes})"

            def __eq__(self, other):
                return isinstance(other, type(self)) and self.nom == other.nom

            def set_votants(self, raw_votants):
                votants = [rv or "zzz" for rv in raw_votants]
                votants.sort()
                self.votants = ["Corbeau" if nom == "zzz" else nom
                                for nom in votants]
                # On trie par ordre alphabétique
                # en mettant les corbeaux (= pas de votant) à la fin

            def couleur(self, choisi):
                if self == choisi:
                    return hex(couleur).replace("0x", "#")
                if self.eligible:
                    return "#64b9e9"
                else:
                    return "gray"

        # Récupération votes

        await ctx.send("Récupération des votes...")
        async with ctx.typing():
            workbook = gsheets.connect(env.load("LGREZ_TDB_SHEET_ID"))
            sheet = workbook.worksheet(config.tdb_votes_sheet)
            values = sheet.get_all_values()
            # Liste de liste des valeurs des cellules

            cibles_brutes = []
            for lig in values[config.tdb_header_row:NL]:
                val = lig[ind_col_cible]
                if val:
                    cibles_brutes.append(val)

            nb_votes = len(cibles_brutes)

            cibles = [_Cible(nom, votes)
                      for (nom, votes) in Counter(cibles_brutes).most_common()]
            # Liste des cibles (vérifie l'éligibilité...)
            # triées du plus au moins votées
            for cible in cibles:        # Récupération votants
                votants = []
                for lig in values[config.tdb_header_row:NL]:
                    if lig[ind_col_cible] == cible.nom:
                        votants.append(lig[ind_col_votants])

        # Détermination cible

        choisi = None
        eligibles = [c for c in cibles if c.eligible]

        if eligibles:
            maxvotes = eligibles[0].votes
            egalites = [c for c in eligibles if c.votes == maxvotes]

            if len(egalites) > 1:       # Égalité
                mess = await ctx.send(
                    "Égalité entre\n"
                    + "\n".join(f"{tools.emoji_chiffre(i+1)} {c.nom}"
                                for i, c in enumerate(egalites))
                    + "\nQui meurt / est élu ? (regarder vote du maire, "
                    "0️⃣ pour personne / si le vainqueur est garde-loupé, "
                    "inéligible ou autre)"
                )
                choice = await tools.choice(mess, len(egalites), start=0)
                if choice:      # pas 0
                    choisi = eligibles[choice - 1]

            else:
                mess = await ctx.send(
                    "Joueur éligible le plus voté : "
                    + tools.bold(eligibles[0].nom)
                    + " \nÇa meurt / est élu ? (pas garde-loupé, "
                    "inéligible ou autre)"
                )
                if await tools.yes_no(mess):
                    choisi = eligibles[0]

        # Paramètres plot

        discord_gray = '#2F3136'
        plt.figure(facecolor=discord_gray)
        plt.rcParams.update({'font.size': 16})
        ax = plt.axes(facecolor='#8F9194')  # coloration de TOUT le graphe
        ax.tick_params(axis='both', colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color(discord_gray)
        ax.spines['right'].set_color(discord_gray)
        ax.spines['top'].set_color(discord_gray)
        ax.set_facecolor(discord_gray)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

        # Plot

        ax.bar(
            x=range(len(cibles)),
            height=[c.votes for c in cibles],
            tick_label=[c.label for c in cibles],
            color=[c.couleur(choisi) for c in cibles],
        )
        plt.grid(axis="y")

        if not os.path.isdir("figures"):
            os.mkdir("figures")

        now = datetime.datetime.now().strftime("%Y-%m-%d--%H")
        image_path = f"figures/hist_{now}_{type}.png"
        plt.savefig(image_path, bbox_inches="tight")

        # --------------- Partie Discord ---------------

        # Détermination rôle et camp
        emoji_camp = None
        if choisi:
            if type == "cond":
                role = choisi.joueur.role.nom_complet
                mess = await ctx.send(
                    f"Rôle à afficher pour {choisi.nom} = {role} ? "
                    "(Pas double peau ou autre)"
                )
                if await tools.yes_no(mess):
                    emoji_camp = choisi.joueur.camp.discord_emoji_or_none
                else:
                    await ctx.send("Rôle à afficher :")
                    role = (await tools.wait_for_message_here(ctx)).content
                    mess = await ctx.send("Camp :")
                    camps = Camp.query.filter_by(public=True).all()
                    emoji_camp = await tools.wait_for_react_clic(
                        mess,
                        [camp.emoji for camp in camps if camp.emoji]
                    )

                nometrole = f"{tools.bold(choisi.nom)}, {role}"
            else:
                # Maire : ne pas annoncer le rôle
                nometrole = f"{tools.bold(choisi.nom)}"
        else:
            nometrole = "personne, bande de tocards"

        # Création embed
        embed = discord.Embed(
            title=f"{mort_election} de {nometrole}",
            description=f"{nb_votes} votes au total",
            color=couleur
        )
        embed.set_author(name=f"Résultats du vote pour le {typo}",
                         icon_url=tools.emoji(emoji).url)

        if emoji_camp:
            embed.set_thumbnail(url=emoji_camp.url)

        embed.set_footer(text="\n".join(
            ("A" if cible.votes == 1 else "Ont")
            + f" voté {pour_contre} {cible.nom} : "
            + ", ".join(cible.votants)
            for cible in cibles
        ))

        file = discord.File(image_path, filename="image.png")
        embed.set_image(url="attachment://image.png")

        # Envoi
        mess = await ctx.send("Ça part ?\n", file=file, embed=embed)
        if await tools.yes_no(mess):
            # Envoi du graphe
            file = discord.File(image_path, filename="image.png")
            # Un objet File ne peut servir qu'une fois, il faut le recréer

            await config.Channel.annonces.send(
                "@everyone Résultat du vote ! :fire:",
                file=file,
                embed=embed,
            )
            await ctx.send(
                f"Et c'est parti dans {config.Channel.annonces.mention} !"
            )

            if type == "cond":
                # Actions au mot des MJs
                for action in Action.query.filter_by(
                        trigger_debut=ActionTrigger.mot_mjs).all():
                    await gestion_actions.open_action(action)

                await ctx.send("(actions liées au mot MJ ouvertes)")

        else:
            await ctx.send("Mission aborted.")
            self.current_embed = embed


    @commands.command()
    @tools.mjs_only
    async def annoncemort(self, ctx, *, victime=None):
        """Annonce un mort hors-vote (COMMANDE MJ)

        Args:
            victime: mort à annoncer

        Envoie un embed dans ``#annonces``
        """
        joueur = await tools.boucle_query_joueur(ctx, victime,
                                                 "Qui est la victime ?")

        role = joueur.role.nom_complet
        mess = await ctx.send(
            f"Rôle à afficher pour {joueur.nom} = {role} ? "
            "(Pas double peau ou autre)"
        )
        if await tools.yes_no(mess):
            emoji_camp = joueur.camp.discord_emoji_or_none
        else:
            await ctx.send("Rôle à afficher :")
            role = (await tools.wait_for_message_here(ctx)).content
            mess = await ctx.send("Camp :")
            camps = Camp.query.filter_by(public=True).all()
            emoji_camp = await tools.wait_for_react_clic(
                mess,
                [camp.emoji for camp in camps if camp.emoji]
            )

        if joueur.statut == Statut.MV:
            mess = await ctx.send("Annoncer la mort-vivance ?")
            if await tools.yes_no(mess):
                role += " Mort-Vivant"
            else:
                emoji_camp = joueur.role.camp.discord_emoji_or_none

        await ctx.send("Contexte ?")
        desc = (await tools.wait_for_message_here(ctx)).content

        # Création embed
        embed = discord.Embed(
            title=f"Mort de {tools.bold(joueur.nom)}, {role}",
            description=desc,
            color=0x730000
        )
        embed.set_author(name="Oh mon dieu, quelqu'un est mort !")
        if emoji_camp:
            embed.set_thumbnail(url=emoji_camp.url)

        mess = await ctx.send(
            "Ça part ?\n"
            + tools.ital("(si Non, l'embed est personnalisable via "
                         "`!embed` puis envoyable à la main)"),
            embed=embed
        )
        if await tools.yes_no(mess):
            # Envoi du graphe
            await config.Channel.annonces.send(
                "@everyone Il s'est passé quelque chose ! :scream:",
                embed=embed
            )
            await ctx.send(
                f"Et c'est parti dans {config.Channel.annonces.mention} !"
            )

        else:
            await ctx.send("Mission aborted.")
            self.current_embed = embed
