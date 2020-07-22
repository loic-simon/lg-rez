import os

import datetime
import discord
from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_
from dotenv import load_dotenv

from blocs import gsheets

from bdd_connect import db, Joueurs, Actions, BaseActions, BaseActionsRoles, CandidHaro
from features import gestion_actions, taches
from blocs import bdd_tools
import tools

import matplotlib.pyplot as plt

class ActionsPubliques(commands.Cog):
    """ActionsPubliques - Commandes pour gérer les actions vous engageant publiquement"""


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def haro(self, ctx, target=None):
        """Lance un haro contre [target]"""
        auteur = ctx.author

        joueur = Joueurs.query.get(auteur.id)
        assert joueur, f"Joueur {auteur.display_name} introuvable"

        if joueur._vote_condamne is None:
            await ctx.send("Pas de vote pour le condamné de jour en cours !")
            return

        cible = await tools.boucle_query_joueur(ctx, target, 'Contre qui souhaite-tu déverser ta haine ?')

        if cible.statut == "mort":
            await ctx.send("Nan mais oh, tu crois qu'il a pas assez souffert en mourant lui ?")
            return

        elif cible.statut == "immortel":
            await ctx.send(f"Comment oses-tu t'en prendre à ceux qui te sont supérieurs ? {tools.role(ctx, 'MJ').mention}, regardez un peu ce qu'il se passe là...")
            return

        await tools.send_blocs(ctx, "Et quel est la raison de cette haine, d'ailleurs ?")
        motif = await tools.wait_for_message(ctx.bot, check=lambda m: m.channel == ctx.channel and m.author != ctx.bot.user)
        # ATTENTION : Ne JAMAIS utiliser bot.wait_for, toujours tools.wait_for_message (il détecte les stop)
        # motif = await ctx.bot.wait_for('message', check = lambda m: m.channel == ctx.channel and m.author != ctx.bot.user)

        if not CandidHaro.query.filter_by(player_id=cible.discord_id, type="haro").all():
            haroted = CandidHaro(player_id=cible.discord_id, type="haro")
            db.session.add(haroted)

        if not CandidHaro.query.filter_by(player_id=ctx.author.id, type="haro").all():
            haroteur = CandidHaro(player_id=ctx.author.id, type="haro")
            db.session.add(haroteur)

        db.session.commit()

        emb = discord.Embed(title = f"**{tools.emoji(ctx, 'ha')}{tools.emoji(ctx, 'ro')} contre {cible.nom} !**",
                            description = f"**« {motif.content} »\n**",
                            color=0xff0000)
        emb.set_author(name = f"{ctx.author.display_name} en a gros 😡😡")
        emb.set_thumbnail(url = tools.emoji(ctx, "bucher").url)
        emb.set_footer(text = f"Utilise !vote {cible.nom} pour voter contre lui")
        m = await ctx.send("C'est tout bon ?", embed=emb)

        if await tools.yes_no(ctx.bot, m):
            cible_member = ctx.guild.get_member(cible.discord_id)
            assert cible_member, f"!haro : Member associé à {cible} non trouvé"
            await tools.channel(ctx, "haros").send( f"(Psst, {ctx.guild.get_member(cible.discord_id).mention} :3)", embed=emb)
            await tools.channel(ctx, "débats").send( f"{tools.emoji(ctx, 'ha')}{tools.emoji(ctx, 'ro')} de {auteur.display_name} sur {cible.nom} ! Vous en pensez quoi vous (et allez voir {tools.channel(ctx, 'haros').mention} hein)?")
            await ctx.send(f"Allez c'est parti ! ({tools.channel(ctx, 'haros').mention})")

        else:
            await ctx.send("Compris, mission aborted.")

    @commands.command()
    @tools.vivants_only
    @tools.private
    async def candid(self, ctx, target=None):
        """Permet de se présenter à une élection"""
        if CandidHaro.query.filter_by(player_id = ctx.author.id, type = "candidature").all():
            await ctx.send("Hola collègue, tout doux, tu t'es déjà présenté !")
            return

        auteur = ctx.author

        await tools.send_blocs(ctx, "Quel est ton programme politique ?")
        motif = await ctx.bot.wait_for('message', check = lambda m: m.channel == ctx.channel and m.author != ctx.bot.user)

        candidat = CandidHaro(id=None, player_id = ctx.author.id, type="candidature")
        db.session.add(candidat)
        db.session.commit()

        emb = discord.Embed(title = f" {tools.emoji(ctx, 'maire')} {auteur.display_name} vous a compris ! {tools.emoji(ctx, 'mc')}",
                            description = "Voici ce qu'il a à vous dire :\n" + tools.bold(motif.content))
        m = await ctx.send("C'est tout bon ?", embed=emb)

        if await tools.yes_no(ctx.bot, m):
            await tools.channel(ctx, "haros").send("Here comes a new challenger !", embed=emb)
            await ctx.send("Allez c'est parti !")


    ##Fonctions de gestion de la base CandidHaro (wipe les haros ou les votes)
    @commands.command()
    @tools.mjs_only
    async def wipe_haro(self, ctx):
        """Efface les HAROs du jour (COMMANDE MJ)"""

        haros = CandidHaro.query.filter_by(type = "haro").all()
        if not haros:
            await tools.log(ctx, "Pas de haros en cours, wipe terminé")
        else:
            for haro in haros:
                db.session.delete(haro)
            db.session.commit()
            await tools.log(ctx, "Tous les haros ont bien été effacés !")


    @commands.command()
    @tools.mjs_only
    async def wipe_candid(self, ctx):
        """Efface les candidatures à la mairie du jour (COMMANDE MJ)"""

        candids = CandidHaro.query.filter_by(type = "candidature").all()
        if not candids:
            await tools.log(ctx, "Aucun candidat actuellement, wipe terminé")
        else:
            for candid in candids:
                db.session.delete(candid)
            db.session.commit()
            await tools.log(ctx, "Toutes les candidatures ont bien été effacés !")



    @commands.command()
    @tools.mjs_only
    async def plot(self, ctx, type=None):
        """Trace le résultat du vote indiqué sous forme d'histogramme, en fait un embed et l'envoie sur le chan #annonces

        <type> - Choisir entre maire et cond pour l'élection municipale ou le condamné du jour"""

        d = {"maire":"MaireRéel", "cond":"CondamnéRéel"}

        assert type in ["maire", "cond"], "Merci de spécifier l'histogramme à tracer parmi 'maire' et 'cond'"

        #Sorcellerie sur la feuille gsheets pour trouver la colonne "CondamnéRéel"
        load_dotenv()
        SHEET_ID = os.getenv("TDB_SHEET_ID")
        assert SHEET_ID, "inscription.main : TDB_SHEET_ID introuvable"

        workbook = gsheets.connect(SHEET_ID)    # Tableau de bord
        sheet = workbook.worksheet("Journée en cours")
        values = sheet.get_all_values()         # Liste de liste des valeurs des cellules
        NL = len(values)

        head = values[2]            # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
        col_cond = head.index(d[type])
        conds = [values[i][col_cond] for i in range(3,NL) if values[i][col_cond]]

        await tools.log(ctx, conds)

        """
        cond_count = {} #dict {élem : nb ocurrences}
        for cond in conds:
            if not cond in cond_count:
                cond_count[cond]=1
            else:
                cond_count[cond]+=1
        """
        plt.clf()
        plt.figure()
        #plt.plot([k for k in cond_count], [v for v in cond_count.values()])
        plt.hist(conds, align="mid")
        plt.grid()
        plt.savefig(f"www/figures/hist_{type}.png")

        embed = discord.Embed(title="Title", description="Desc", color=0x00ff00) #creates embed
        file = discord.File(f"www/figures/hist_{type}.png", filename="image.png")
        embed.set_image(url="attachment://image.png")
        await ctx.send(file=file, embed=embed)


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
