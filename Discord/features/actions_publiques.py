import datetime
import discord
from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from bdd_connect import db, Joueurs, Actions, BaseActions, BaseActionsRoles, CandidHaro
from features import gestion_actions, taches
from blocs import bdd_tools
import tools

class ActionsPubliques(commands.Cog):
    """ActionsPubliques - Gestion des actions publiques comme haros, candidatures à la mairie, etc..."""


    @commands.command()
    @tools.private
    async def haro(self, ctx, target=None):
        """Lance un haro contre [target]"""
        auteur = ctx.author
        cible = await tools.boucle_query_joueur(ctx, target, 'Contre qui souhaite-tu déverser ta haine ?')

        if cible.statut == "mort":
            await ctx.send("Nan mais oh, tu crois qu'il a pas assez souffert en mourrant lui ?")
            return

        elif cible.statut == "immortel":
            await ctx.send(f"Comment oses-tu t'en prendre à ceux qui te sont supérieurs ? {tools.role(ctx, 'MJ').mention}, regardez un peu ce qu'il se passe là...")
            return

        await tools.send_blocs(ctx, "Et quel est la raison de cette haine, d'ailleurs ?")
        motif = await ctx.bot.wait_for('message', check = lambda m: m.channel == ctx.channel and m.author != ctx.bot.user)

        if not CandidHaro.query.filter_by(player_id = cible.discord_id, type = "haro").all():
            haroted = CandidHaro(id = None, player_id = cible.discord_id, type = "haro")
            db.session.add(haroted)

        if not CandidHaro.query.filter_by(player_id = ctx.author.id, type = "haro").all():
            haroteur = CandidHaro(id=None, player_id = ctx.author.id, type="haro")
            db.session.add(haroteur)

        db.session.commit()

        emb = discord.Embed(title = f"{tools.emoji(ctx, 'ha')}{tools.emoji(ctx, 'ro')} contre {cible.nom} !",
                            description = f"**« {motif.content} »**\n \n" + f"{ctx.author.display_name} en a gros     :rage: :rage:", color=0xff0000 )
        m = await ctx.send("C'est tout bon ?", embed=emb)

        if await tools.yes_no(ctx.bot, m):
            await tools.channel(ctx, "haros").send(f"{ctx.guild.get_member(cible.discord_id).mention}", embed=emb)
            await ctx.send("Allez c'est parti !")


    @commands.command()
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

    @commands.command(enabled=False)
    @tools.private
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
    @tools.private
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

    ##Fonctions de gestion de la base CandidHaro (wipe les haros ou les votes)
    @commands.command()
    @commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_role("MJ"))
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
    @commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_role("MJ"))
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
