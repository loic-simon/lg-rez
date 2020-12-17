"""lg-rez / features / Communication

Envoi de messages, d'embeds...

"""

import os
import datetime
import traceback
from collections import Counter

import discord
from discord.ext import commands
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from lgrez.blocs import tools, env, gsheets
from lgrez.blocs.bdd import session, Joueurs, Actions, CandidHaro
from lgrez.features import gestion_actions


class Communication(commands.Cog):
    """Communication - Envoi de messages, d'embeds..."""

    current_embed = None

    @commands.command()
    @tools.mjs_only
    async def embed(self, ctx, key=None, *, val=None):
        """Prépare un embed (message riche) et l'envoie (COMMANDE MJ)

        Args:
            key: sous-commande (voir ci-dessous). Si omis, prévisualise le brouillon d'embed actuellement en préparation ;
            val: valeur associée. Pour les sous-commandes de construction d'élement, supprime ledit élément si omis.

        - Sous-commandes générales :
            - ``!embed create <titre>`` :          Créer un nouveau brouillon d'embed (un seul brouillon en parallèle, pour tous les utilisateurs)
            - ``!embed delete`` :                  Supprimer le brouillon d'embed
            - ``!embed preview``  :                Voir l'embed sans les rappels de commande
            - ``!embed post [#channel]`` :         Envoyer l'embed sur ``#channel`` (chan courant si omis)

        - Sous-commandes de construction d'éléments :
            - Éléments généraux :
                - ``!embed title [titre]``
                - ``!embed description [texte]``
                - ``!embed url [url*]``
                - ``!embed color [#ffffff]``      (barre de gauche, code hexadécimal)

            - Auteur :
                - ``!embed author [nom]``
                - ``!embed author_url [url*]``
                - ``!embed author_icon [url**]``

            - Talon :
                - ``!embed footer [texte]``
                - ``!embed footer_icon [url**]``

            - Images :
                - ``!embed image [url**]``        (grande image)
                - ``!embed thumb [url**]``        (en haut à droite)

            - Champs : syntaxe spéciale
                - ``!embed field <i> <skey> [val]``
                    - ``i`` :            Numéro du champ (commençant à ``0``). Si premier champ non existant, le crée.
                    - ``skey`` :
                        - ``name`` :       Nom du champ
                        - ``value`` :      Valeur du champ
                        - ``delete`` :     Supprime le champ

                Les champs sont (pour l'instant) forcément de type inline (côte à côte).

        \* Les URL doivent commencer par http(s):// pour être reconnues comme telles.

        ** Ces URL doivent correspondre à une image.
        """

        if val is None:
            val = discord.Embed.Empty

        emb = self.current_embed                # Récupération de l'embed (stocké dans le cog)

        direct = [                              # Attributs modifiables directement : emb.attr = value
            "title",
            "description",
            "url",
        ]
        method = {                              # Attributs à modifier en appelant une méthode : emb.set_<attr>(value)
            "footer": ("footer", "text"),                           # method[key] = (<attr>, <value>)
            "footer_icon": ("footer", "icon_url"),
            "image": ("image", "url"),
            "thumb": ("thumbnail", "url"),
            "author_url": ("author", "url"),
            "author_icon": ("author", "icon_url"),
        }

        if not emb:                             # Pas d'embed en cours
            if key == "create" and val:
                emb = discord.Embed(title=val)
            else:
                await ctx.send(f"Pas d'embed en préparation. {tools.code('!embed create <titre>')} pour en créer un.")
                return

        elif key in direct:                     # Attributs modifiables directement
            setattr(emb, key, val)

        elif key in method:                     # Attributs à modifier en appelant une méthode
            prop, attr = method[key]
            getattr(emb, f"set_{prop}")(**{attr: val})          # emb.set_<prop>(<attr>=val)

        elif key == "author":                   # Cas particulier
            emb.set_author(name=val) if val else emb.remove_author()

        elif key == "color":                    # Autre cas particulier : conversion couleur en int
            try:
                emb.color = eval(val.replace("#", "0x")) if val else discord.Embed.Empty
            except Exception:
                await ctx.send("Couleur invalide")
                return

        elif key == "field":                    # Cas encore plus particulier
            i_max = len(emb.fields)                 # N fields ==> i_max = N+1
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
                    emb.add_field(name=val, value=f"!embed field {i} value <valeur>")
                elif skey == "value":
                    emb.add_field(name=f"!embed field {i} name <nom>", value=val)
                # emb.add_field(*, name, value, inline=True)

            else:
                if skey == "name":
                    emb.set_field_at(i, name=val, value=emb.fields[i].name)
                elif skey == "value":
                    emb.set_field_at(i, name=emb.fields[i].name, value=val)
                else:
                    emb.remove_field(i)
                # emb.set_field_at(i, *, name, value, inline=True)

        elif key == "delete":
            self.current_embed = None
            await ctx.send(f"Supprimé. {tools.code('!embed create <titre>')} pour en créer un.")
            return

        elif key == "create":
            await ctx.send(f"Déjà un embed en cours de création. Utiliser {tools.code('!embed delete')} pour le supprimer.")

        elif key == "preview":
            await ctx.send("Prévisuatisation :", embed=emb)
            await ctx.send(f"Utiliser {tools.code('!embed post #channel')} pour publier l'embed.")
            return

        elif key == "post":
            if not val:     # channel non précisé
                await ctx.send(embed=emb)
            elif chan := tools.channel(ctx, val, must_be_found=False):
                await chan.send(embed=emb)
                await ctx.send("Et pouf !")
            else:
                await ctx.send(f"Channel inconnu. Réessaye en le mentionnant ({tools.code('#channel')})")
            return

        elif key is not None:
            await ctx.send(f"Option {key} incorrecte : utiliser {tools.code('!help embed')} pour en savoir plus.")
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
        h_emb.add_field(name=f"!embed field {i_max} name <nom>", value=f"!embed field {i_max} value <nom>")

        await ctx.send("Embed en préparation :", embed=h_emb)
        await ctx.send(f"Utiliser {tools.code('!embed preview')} pour prévisualiser l'embed.\n"
                       f"Autres options : {tools.code('!embed color <#xxxxxx> / url <url> / image <url> / thumb <url> / author_url <url> / footer_icon <url>')}")

        self.current_embed = emb



    @commands.command(aliases=["tell"])
    @tools.mjs_only
    async def send(self, ctx, cible, *, message):
        """Envoie un message à tous ou certains joueurs (COMMANDE MJ)

        Args:
            cible: destinataires
            message: message, éventuellement formaté

        ``cible`` peut être :
            - ``all`` :                 Tous les joueurs inscrits, vivants et morts
            - ``vivants`` :             Les joueurs en vie
            - ``morts`` :               Les joueurs morts
            - ``<crit>=<filtre>`` :     Les joueurs répondant au critère ``Joueurs.<crit> == <filtre>``. ``crit`` peut être ``"nom"``, ``"chambre"``, ``"statut"``, ``"role"``, ``"camp"``... L'ensemble doit être entouré de guillements si ``filtre`` contient un espace.
            - *le nom d'un joueur*      (raccourci pour ``nom=X``, doit être entouré de guillements si nom + prénom)

        ``message`` peut contenir un ou plusieurs bouts de code Python à évaluer, entourés d'accolades.

        L'évaluation est faite séparément pour chaque joueur, ce qui permet de personnaliser le message grâce aux variables particulières dépendant du joueur :
            - ``joueur`` :          objet BDD du joueur recevant le message  ==> ``joueur.nom``, ``joueur.role``...
            - ``member`` :          objet discord.Member associé             ==> ``member.mention``
            - ``chan`` :            objet :class:`discord.TextChannel` du chan privé du joueur

        Attention :
            - ``ctx`` :             objet :class:`discord.ext.commands.Context` de ``!send``  ==> ``ctx.author`` = lanceur de la commande !!!

        Les différentes tables de données sont accessibles sous leur nom (``Joueurs``, ``Roles``...)

        Il est impossible d'appeller des coroutines (await) dans le code à évaluer.

        Examples:
            - ``!send all Bonsoir à tous c'est Fanta``
            - ``!send vivants Attention {member.mention}, derrière toi c'est affreux !``
            - ``!send "role=Servante Dévouée" Ça va vous ? Vous êtes bien {joueur.role} ?``
        """
        if cible == "all":
            joueurs = Joueurs.query.all()
        elif cible == "vivants":
            joueurs = Joueurs.query.filter_by(statut="vivant").all()
        elif cible == "morts":
            joueurs = Joueurs.query.filter_by(statut="mort").all()
        elif "=" in cible:
            crit, filtre = cible.split("=", maxsplit=1)
            if hasattr(Joueurs, crit):
                joueurs = Joueurs.query.filter(getattr(Joueurs, crit) == filtre).all()
            else:
                await ctx.send(f"Critère \"{crit}\" incorrect. !help {ctx.invoked_with} pour plus d'infos.")
                return
        else:
            joueurs = [await tools.boucle_query_joueur(ctx, cible, "À qui ?")]

        if not joueurs:
            await ctx.send(f"Aucun joueur trouvé.")
            return

        await ctx.send(f"{len(joueurs)} trouvé(s), envoi...")
        for joueur in joueurs:
            member = ctx.guild.get_member(joueur.discord_id)
            chan = ctx.guild.get_channel(joueur.chan_id_)

            assert member, f"!send : Member associé à {joueur} introuvable"
            assert chan, f"!sed : Chan privé de {joueur} introuvable"

            evaluated_message = tools.eval_accols(message, locals_=locals())
            await chan.send(evaluated_message)

        await ctx.send(f"Fini.")



    @commands.command()
    @tools.mjs_only
    async def post(self, ctx, chan, *, message):
        """Envoie un message dans un salon (COMMANDE MJ)

        Args:
            chan: nom du salon ou sa mention
            message: message à envoyer (peut être aussi long que nécessaire, contenir des sauts de lignes...)
        """
        chan = tools.channel(ctx, chan)
        await chan.send(message)
        await ctx.send(f"Fait.")



    @commands.command()
    @tools.mjs_only
    async def plot(self, ctx, type):
        """Trace le résultat du vote et l'envoie sur #annonces (COMMANDE MJ)

        Args:
            type: peut être

                - ``cond``   pour le vote pour le condamné
                - ``maire``  pour l'élection à la Mairie

        Trace les votes sous forme d'histogramme à partir du Tableau de bord, en fait un embed en présisant les résultats détaillés et l'envoie sur le chan ``#annonces``.

        Si ``type == "cond"``, déclenche aussi les actions liées au mot des MJs.
        """
        class Cible():
            def __init__(self, nom, votes=0):
                self.nom = nom
                self.label = self.nom.replace(" ", "\n", 1)

                self.votes = votes

                self.votants = []

                self.joueur = Joueurs.query.filter_by(nom=nom).one()
                if not self.joueur:
                    raise ValueError(f"Joueur \"{nom}\" non trouvé en base")

                self.eligible = bool(CandidHaro.query.filter_by(type=haro_candidature, player_id=self.joueur.discord_id).all())

            def __repr__(self):
                return f"{self.nom} ({self.votes})"

            def __eq__(self, other):
                return isinstance(other, Cible) and self.nom == other.nom

            def set_votants(self, raw_votants):
                votants = [rv or "zzz" for rv in raw_votants]
                votants.sort()
                self.votants = ["Corbeau" if nom == "zzz" else nom for nom in votants]         # On trie par ordre alphabétique en mettant les corbeaux (= pas de votant) à la fin

            def couleur(self, choisi):
                if self == choisi:
                    return hex(couleur).replace("0x", "#")
                if self.eligible:
                    return "#64b9e9"
                else:
                    return "gray"


        try:
            if type == "cond":
                colonne_cible = "CondamnéRéel"
                colonne_votant = "VotantCond"
                haro_candidature = "haro"
                typo = "bûcher du jour"
                mort_election = "Mort"
                pour_contre = "contre"
                emoji = "bucher"
                couleur = 0x730000
                couleur_txt = "#730000"

            elif type == "maire":
                colonne_cible = "MaireRéel"
                colonne_votant = "VotantMaire"
                haro_candidature = "candidature"
                typo = "nouveau maire"
                mort_election = "Élection"
                pour_contre = "pour"
                emoji = "maire"
                couleur = 0xd4af37
                couleur_txt = "#d4af37"

            else:
                await ctx.send("Merci de spécifier les résultats à tracer parmi 'maire' et 'cond'")
                return


            await ctx.send("Récupération des votes...")
            async with ctx.typing():
            # Sorcellerie sur la feuille gsheets pour trouver la colonne "CondamnéRéel"

                workbook = gsheets.connect(env.load("LGREZ_TDB_SHEET_ID"))    # Tableau de bord
                sheet = workbook.worksheet("Journée en cours")
                values = sheet.get_all_values()         # Liste de liste des valeurs des cellules
                NL = len(values)

                head = values[2]            # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
                ind_col_cible = head.index(colonne_cible)
                ind_col_votants = head.index(colonne_votant)

                cibles_brutes = [val for i in range(3, NL) if (val := values[i][ind_col_cible])]
                nb_votes = len(cibles_brutes)

                cibles = [Cible(nom, votes) for (nom, votes) in Counter(cibles_brutes).most_common()]       # Liste des cibles (vérifie l'éligibilité...) triées du plus au moins votées
                for cible in cibles:        # Récupération votants
                    cible.set_votants([values[i][ind_col_votants] for i in range(3, NL) if values[i][ind_col_cible] == cible.nom])


            choisi = None
            eligibles = [c for c in cibles if c.eligible]

            if eligibles:
                maxvotes = eligibles[0].votes
                egalites = [c for c in eligibles if c.votes == maxvotes]

                if len(egalites) > 1:       # Égalité
                    mess = await ctx.send("Égalité entre\n" + "\n".join(f"{tools.emoji_chiffre(i+1)} {c.nom}" for i, c in enumerate(egalites)) + "\nQui meurt / est élu ? (regarder vote du maire, 0️⃣ pour personne / si le vainqueur est garde-loupé, inéligible ou autre)")
                    choice = await tools.choice(ctx.bot, mess, len(egalites), start=0)
                    if choice:      # pas 0
                        choisi = eligibles[choice-1]

                else:
                    mess = await ctx.send(f"Joueur éligible le plus voté : {tools.bold(eligibles[0].nom)}\nÇa meurt / est élu ? (pas garde-loupé, inéligible ou autre)")
                    if await tools.yes_no(ctx.bot, mess):
                        choisi = eligibles[0]


            # Paramètres plot
            discord_gray = '#2F3136'
            plt.figure(facecolor=discord_gray)
            plt.rcParams.update({'font.size': 16})
            ax = plt.axes(facecolor='#8F9194') #coloration de TOUT le graphe
            ax.tick_params(axis='both', colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color(discord_gray)
            ax.spines['right'].set_color(discord_gray)
            ax.spines['top'].set_color(discord_gray)
            ax.set_facecolor(discord_gray)
            ax.set_axisbelow(True)
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))

            # Plot
            ax.bar(x=range(len(cibles)),
                   height=[c.votes for c in cibles],
                   tick_label=[c.label for c in cibles],
                   color=[c.couleur(choisi) for c in cibles],
            )
            plt.grid(axis="y")

            if not os.path.isdir("figures"):
                os.mkdir("figures")

            image_path = f"figures/hist_{datetime.datetime.now().strftime('%Y-%m-%d')}_{type}.png"
            plt.savefig(image_path, bbox_inches="tight")


            ### --------------- Partie Discord ---------------

            # Détermination rôle et camp
            emoji_camp = None
            if choisi:
                if type == "cond":
                    role = tools.nom_role(choisi.joueur.role, prefixe=True)
                    mess = await ctx.send(f"Rôle à afficher pour {choisi.nom} = {role} ? (Pas double peau ou autre)")
                    if await tools.yes_no(ctx.bot, mess):
                        emoji_camp = tools.emoji_camp(ctx, choisi.joueur.camp)
                    else:
                        await ctx.send("Rôle à afficher :")
                        role = (await tools.wait_for_message_here(ctx)).content
                        mess = await ctx.send("Camp :")
                        emoji_camp = await tools.wait_for_react_clic(ctx.bot, mess, [tools.emoji_camp(ctx, camp) for camp in ["village", "loups", "nécro", "solitaire", "autre"]])

                    nometrole = f"{tools.bold(choisi.nom)}, {role}"
                else:
                    nometrole = f"{tools.bold(choisi.nom)}"

            # Création embed
            embed = discord.Embed(
                title=f"{mort_election} de {nometrole if choisi else 'personne, bande de tocards'}",
                description=f"{nb_votes} votes au total",
                color=couleur
            )
            embed.set_author(name=f"Résultats du vote pour le {typo}", icon_url=tools.emoji(ctx, emoji).url)

            if emoji_camp:
                embed.set_thumbnail(url=emoji_camp.url)

            rd = "\n".join(("A" if cible.votes == 1 else "Ont") + f" voté {pour_contre} {cible.nom} : " + ", ".join(cible.votants) for cible in cibles)
            embed.set_footer(text=rd)

            file = discord.File(image_path, filename="image.png")
            embed.set_image(url="attachment://image.png")

            # Envoi
            mess = await ctx.send("Ça part ?\n", file=file, embed=embed)
            if await tools.yes_no(ctx.bot, mess):
                # Envoi du graphe
                file = discord.File(image_path, filename="image.png")       # Un objet File ne peut servir qu'une fois, il faut le recréer
                # embed.set_image(url="attachment://image.png")

                await tools.channel(ctx, "annonces").send("@everyone Résultat du vote ! :fire:", file=file, embed=embed)
                await ctx.send(f"Et c'est parti dans {tools.channel(ctx, 'annonces').mention} !")

                if type == "cond":
                    # Actions au mot des MJs
                    for action in Actions.query.filter_by(trigger_debut="mot_mjs").all():
                        await gestion_actions.open_action(ctx, action)

                    await ctx.send("(actions liées au mot MJ activées)")

        except Exception:
            await tools.send_code_blocs(ctx, traceback.format_exc())

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
        joueur = await tools.boucle_query_joueur(ctx, victime, "Qui est la victime ?")

        role = tools.nom_role(joueur.role, prefixe=True)
        mess = await ctx.send(f"Rôle à afficher pour {joueur.nom} = {role} ? (Pas double peau ou autre)")
        if await tools.yes_no(ctx.bot, mess):
            emoji_camp = tools.emoji_camp(ctx, joueur.camp)
        else:
            await ctx.send("Rôle à afficher :")
            role = (await tools.wait_for_message_here(ctx)).content
            mess = await ctx.send("Camp :")
            emoji_camp = await tools.wait_for_react_clic(ctx.bot, mess, [tools.emoji_camp(ctx, camp) for camp in ["village", "loups", "nécro", "solitaire", "autre"]])

        if joueur.statut == "MV":
            mess = await ctx.send("Annoncer la mort-vivance ?")
            if await tools.yes_no(ctx.bot, mess):
                role += " Mort-Vivant"
                emoji_camp = tools.emoji_camp(ctx, "nécro")

        await ctx.send("Contexte ?")
        desc = (await tools.wait_for_message_here(ctx)).content

        # Création embed
        embed = discord.Embed(
            title=f"Mort de {tools.bold(joueur.nom)}, {role}",
            description=desc,
            color=0x730000
        )
        embed.set_author(name=f"Oh mon dieu, quelqu'un est mort !")
        if emoji_camp:
            embed.set_thumbnail(url=emoji_camp.url)

        mess = await ctx.send("Ça part ?\n" + tools.ital(f"(si Non, l'embed est personnalisable via {tools.code('!embed')} puis envoyable à la main)"), embed=embed)
        if await tools.yes_no(ctx.bot, mess):
            # Envoi du graphe
            await tools.channel(ctx, "annonces").send("@everyone Il s'est passé quelque chose ! :scream:", embed=embed)
            await ctx.send(f"Et c'est parti dans {tools.channel(ctx, 'annonces').mention} !")

        else:
            await ctx.send("Mission aborted.")
            self.current_embed = embed
