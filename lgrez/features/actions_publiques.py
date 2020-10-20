import datetime
import traceback
from collections import Counter

import discord
from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from lgrez.blocs import env, gsheets, bdd_tools, bdd, tools
from lgrez.blocs.bdd import Joueurs, Actions, BaseActions, BaseActionsRoles, CandidHaro
from lgrez.features import gestion_actions, taches


class ActionsPubliques(commands.Cog):
    """ActionsPubliques - Commandes pour gérer les actions vous engageant publiquement"""

    @commands.command()
    @tools.vivants_only
    @tools.private
    async def haro(self, ctx, cible=None):
        """Lance publiquement un haro contre un autre joueur

        [cible]     joueur à accuser

        Cette commande n'est utilisable que lorsqu'un vote pour le condamné est en cours.
        """
        auteur = ctx.author

        joueur = Joueurs.query.get(auteur.id)
        assert joueur, f"Joueur {auteur.display_name} introuvable"

        if joueur._vote_condamne is None:
            await ctx.send("Pas de vote pour le condamné de jour en cours !")
            return

        cible = await tools.boucle_query_joueur(ctx, cible, 'Contre qui souhaite-tu déverser ta haine ?')

        if cible.statut == "mort":
            await ctx.send("Nan mais oh, tu crois qu'il a pas assez souffert en mourant lui ?")
            return

        elif cible.statut == "immortel":
            await ctx.send(f"Comment oses-tu t'en prendre à ceux qui te sont supérieurs ? {tools.role(ctx, 'MJ').mention}, regardez un peu ce qu'il se passe là...")
            return

        await tools.send_blocs(ctx, "Et quel est la raison de cette haine, d'ailleurs ?")
        motif = await tools.wait_for_message_here(ctx)
        # ATTENTION : Ne JAMAIS utiliser bot.wait_for, toujours tools.wait_for_message (il détecte les stop)

        if not CandidHaro.query.filter_by(player_id=cible.discord_id, type="haro").all():       # Inscription haroté
            haroted = CandidHaro(player_id=cible.discord_id, type="haro")
            bdd.session.add(haroted)

        if not CandidHaro.query.filter_by(player_id=ctx.author.id, type="haro").all():          # Inscription haroteur
            haroteur = CandidHaro(player_id=ctx.author.id, type="haro")
            bdd.session.add(haroteur)

        bdd.session.commit()

        emb = discord.Embed(title = f"**{tools.emoji(ctx, 'ha')}{tools.emoji(ctx, 'ro')} contre {cible.nom} !**",
                            description = f"**« {motif.content} »\n**",
                            color=0xff0000)
        emb.set_author(name=f"{ctx.author.display_name} en a gros 😡😡")
        emb.set_thumbnail(url=tools.emoji(ctx, "bucher").url)
        emb.set_footer(text=f"Utilise !vote {cible.nom} pour voter contre lui.")

        mess = await ctx.send("C'est tout bon ?", embed=emb)
        if await tools.yes_no(ctx.bot, mess):
            cible_member = ctx.guild.get_member(cible.discord_id)
            assert cible_member, f"!haro : Member {cible} introuvable"

            await tools.channel(ctx, "haros").send( f"(Psst, {cible_member.mention} :3)", embed=emb)
            await tools.channel(ctx, "débats").send( f"{tools.emoji(ctx, 'ha')}{tools.emoji(ctx, 'ro')} de {auteur.display_name} sur {cible.nom} ! Vous en pensez quoi vous ? (détails sur {tools.channel(ctx, 'haros').mention})")
            await ctx.send(f"Allez, c'est parti ! ({tools.channel(ctx, 'haros').mention})")

        else:
            await ctx.send("Mission aborted.")


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def candid(self, ctx):
        """Candidate à l'élection du nouveau maire

        Cette commande n'est utilisable que lorsqu'un vote pour le nouveau maire est en cours.
        """
        joueur = Joueurs.query.get(ctx.author.id)
        assert joueur, f"Joueur {auteur.display_name} introuvable"

        if joueur._vote_maire is None:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return

        if CandidHaro.query.filter_by(player_id=ctx.author.id, type = "candidature").all():
            await ctx.send("Hola collègue, tout doux, tu t'es déjà présenté !")
            return

        auteur = ctx.author

        await tools.send_blocs(ctx, "Quel est ton programme politique ?")
        motif = await tools.wait_for_message_here(ctx)

        candidat = CandidHaro(id=None, player_id=ctx.author.id, type="candidature")
        bdd.session.add(candidat)
        bdd.session.commit()

        emb = discord.Embed(title = f"**{tools.emoji(ctx, 'maire')} {auteur.display_name} candidate à la Mairie !** {tools.emoji(ctx, 'mc', must_be_found=False) or ''}",
                            description = "Voici ce qu'il a à vous dire :\n" + tools.bold(motif.content),
                            color=0xf1c40f)
        emb.set_author(name=f"{auteur.display_name} vous a compris !")
        emb.set_thumbnail(url=tools.emoji(ctx, "maire").url)
        emb.set_footer(text=f"Utilise !votemaire {auteur.display_name} pour voter pour lui.")

        mess = await ctx.send("C'est tout bon ?", embed=emb)
        if await tools.yes_no(ctx.bot, mess):
            await tools.channel(ctx, "haros").send("Here comes a new challenger !", embed=emb)
            await ctx.send(f"Allez, c'est parti ! ({tools.channel(ctx, 'haros').mention})")


    ##Fonctions de gestion de la base CandidHaro (wipe les haros ou les votes)
    @commands.command()
    @tools.mjs_only
    async def wipe(self, ctx, quoi):
        """Efface les haros / candidatures du jour (COMMANDE MJ)

        <quoi> peut être
            haros       Supprimer les haros
            candids     Supprimer les candicatures
        """
        if quoi == "haros":
            items = CandidHaro.query.filter_by(type="haro").all()
        elif quoi == "candids":
            items = CandidHaro.query.filter_by(type="candidature").all()
        else:
            await ctx.send()

        if not items:
            await ctx.send("Rien à faire")
            await tools.log(ctx, f"!wipe {qui} : rien à faire")
        else:
            for item in items:
                bdd.session.delete(item)
            bdd.session.commit()
            await ctx.send("Fait.")
            await tools.log(ctx, f"!wipe {qui} : fait")



    @commands.command()
    @tools.mjs_only
    async def plot(self, ctx, type):
        """Trace le résultat du vote et l'envoie sur #annonces (COMMANDE MJ)

        <type> peut être
            cond    Pour le vote poour le condamné
            maire   Pour l'élection à la Mairie

        Trace les votes sous forme d'histogramme à partir du Tableau de bord, en fait un embed en présisant les résultats détaillés et l'envoie sur le chan #annonces.
        Si <type> == "cond", déclenche aussi les actions liées au mot des MJs.
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

            def nometrole(self):
                return f"{tools.bold(self.nom)}, {tools.nom_role(self.joueur.role, prefixe=True)}"


        try:
            if type == "cond":
                colonne_cible = "CondamnéRéel"
                colonne_votant = "VotantCond"
                haro_candidature = "haro"
                typo = "condamné du jour"
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

            # assert type in ["maire", "cond"], "Merci de spécifier l'histogramme à tracer parmi 'maire' et 'cond'"
            # NON !!!  Enfin ça marche, mais assert n'est censé être utilisée QUE dans des cas où c'est normalement impossible que ce ne soit pas le cas, pas pour vérifier une entrée utilisateur

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

            image_path=f"figures/hist_{datetime.datetime.now().strftime('%Y-%m-%d')}_{type}.png"
            plt.savefig(image_path, bbox_inches="tight")

            # Création embed
            embed = discord.Embed(
                title=f"{mort_election} de {choisi.nometrole() if choisi else 'personne, bande de tocards'}",
                description=f"{nb_votes} votes au total",
                color=couleur
            )
            embed.set_author(name=f"Résultats du vote pour le {typo}", icon_url=tools.emoji(ctx, emoji).url)

            rd = "\n".join(("A" if cible.votes == 1 else "Ont") + f" voté {pour_contre} {cible.nom} : " + ", ".join(cible.votants) for cible in cibles)
            embed.set_footer(text=rd)

            file = discord.File(image_path, filename="image.png")
            embed.set_image(url="attachment://image.png")

        except Exception:
            await tools.send_code_blocs(ctx, traceback.format_exc())

        # Envoi
        mess = await ctx.send("Ça part ?", file=file, embed=embed)
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

        else:
            await ctx.send("Mission aborted.")


    @commands.command(enabled=False)
    async def listharo(self, ctx):
        """Liste les gens qui ont subi un haro aujourd'hui"""
        mess = "Les gens que tu pourras (peut être) voir sur le bûcher aujourd'hui sont:\n"
        haroted = CandidHaro.query.filter_by(type="haro").all()
        if not haroted:
            await ctx.send("Le village est encore calme, personne n'a encore accusé personne...")
        else:
            for joueur in haroted:
                mess += f"- {Joueurs.query.filter_by(discord_id = joueur.player_id).first().nom} \n"
        await tools.send_code_blocs(ctx, mess)

    @commands.command(enabled=False)
    async def listcandid(self, ctx):
        """Liste les candidats à la mairie aujourd'hui"""
        mess = "Les candidats à la mairie pour aujourd'hui sont les suivants :\n"
        candids = CandidHaro.query.filter_by(type="candidature").all()
        if not candids:
            await ctx.send("Pas de chance, personne ne s'est présenté...")
            return
        else:
            for joueur in candids:
                mess += f"- {Joueurs.query.filter_by(discord_id = joueur.player_id).first().nom} \n"
        await tools.send_code_blocs(ctx, mess)
