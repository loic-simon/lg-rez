"""lg-rez / features / Actions publiques

Gestion des haros, candidatures à la mairie, résultats des votes

"""

import discord
from discord.ext import commands

from lgrez.blocs import bdd, tools
from lgrez.blocs.bdd import Joueur, CandidHaro, CandidHaroType


class ActionsPubliques(commands.Cog):
    """ActionsPubliques - Commandes pour gérer les actions vous engageant publiquement"""

    @commands.command()
    @tools.vivants_only
    @tools.private
    async def haro(self, ctx, *, cible=None):
        """Lance publiquement un haro contre un autre joueur

        Args:
            cible: nom du joueur à accuser

        Cette commande n'est utilisable que lorsqu'un vote pour le condamné est en cours.
        """
        auteur = ctx.author
        joueur = Joueur.from_member(auteur)

        if joueur.vote_condamne_ is None:
            await ctx.send("Pas de vote pour le condamné de jour en cours !")
            return

        cible = await tools.boucle_query_joueur(ctx, cible, 'Contre qui souhaites-tu déverser ta haine ?')

        if cible.statut == "mort":
            await ctx.send("Nan mais oh, tu crois qu'il a pas assez souffert en mourant lui ?")
            return

        elif cible.statut == "immortel":
            await ctx.send(f"Comment oses-tu t'en prendre à ceux qui te sont supérieurs ? {tools.role(ctx, 'MJ').mention}, regardez un peu ce qu'il se passe là...")
            return

        await tools.send_blocs(ctx, "Et quelle est la raison de cette haine, d'ailleurs ?")
        motif = await tools.wait_for_message_here(ctx)

        emb = discord.Embed(title = f"**{tools.emoji(ctx, 'ha')}{tools.emoji(ctx, 'ro')} contre {cible.nom} !**",
                            description = f"**« {motif.content} »\n**",
                            color=0xff0000)
        emb.set_author(name=f"{ctx.author.display_name} en a gros 😡😡")
        emb.set_thumbnail(url=tools.emoji(ctx, "bucher").url)
        emb.set_footer(text=f"Utilise !vote {cible.nom} pour voter contre lui.")

        mess = await ctx.send("C'est tout bon ?", embed=emb)
        if await tools.yes_no(ctx.bot, mess):
            if not CandidHaro.query.filter_by(joueur=cible, type=CandidHaroType.haro).all():     # Inscription haroté
                config.session.add(CandidHaro(joueur=cible, type=CandidHaroType.haro))

            if not CandidHaro.query.filter_by(joueur=joueur, type=CandidHaroType.haro).all():     # Inscription haroteur
                config.session.add(CandidHaro(joueur=joueur, type=CandidHaroType.haro))

            config.session.commit()

            await tools.channel(ctx, "haros").send(f"(Psst, {cible.member.mention} :3)", embed=emb)
            await tools.channel(ctx, "débats").send(f"{tools.emoji(ctx, 'ha')}{tools.emoji(ctx, 'ro')} de {auteur.mention} sur {cible.member.mention} ! Vous en pensez quoi vous ? (détails sur {tools.channel(ctx, 'haros').mention})")
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
        auteur = ctx.author
        joueur = Joueur.from_member(auteur)

        if joueur.vote_maire_ is None:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return

        if CandidHaro.query.filter_by(joueur=joueur, type=CandidHaroType.candidature).all():
            await ctx.send("Hola collègue, tout doux, tu t'es déjà présenté !")
            return

        await tools.send_blocs(ctx, "Quel est ton programme politique ?")
        motif = await tools.wait_for_message_here(ctx)

        emb = discord.Embed(title = f"**{tools.emoji(ctx, 'maire')} {auteur.display_name} candidate à la Mairie !** {tools.emoji(ctx, 'mc', must_be_found=False) or ''}",
                            description = "Voici ce qu'il a à vous dire :\n" + tools.bold(motif.content),
                            color=0xf1c40f)
        emb.set_author(name=f"{auteur.display_name} vous a compris !")
        emb.set_thumbnail(url=tools.emoji(ctx, "maire").url)
        emb.set_footer(text=f"Utilise !votemaire {auteur.display_name} pour voter pour lui.")

        mess = await ctx.send("C'est tout bon ?", embed=emb)
        if await tools.yes_no(ctx.bot, mess):
            ch = CandidHaro(joueur=joueur, type=CandidHaroType.candidature)
            config.session.add(ch)
            config.session.commit()

            await tools.channel(ctx, "haros").send("Here comes a new challenger !", embed=emb)
            await tools.channel(ctx, "débats").send(f"{auteur.mention} se présente à la Mairie ! Vous en pensez quoi vous ?\n (détails sur {tools.channel(ctx, 'haros').mention})")
            await ctx.send(f"Allez, c'est parti ! ({tools.channel(ctx, 'haros').mention})")


    ##Fonctions de gestion de la base CandidHaro (wipe les haros ou les votes)
    @commands.command()
    @tools.mjs_only
    async def wipe(self, ctx, quoi):
        """Efface les haros / candidatures du jour (COMMANDE MJ)

        Args:
            quoi (str): peut être

                - ``haros`` : Supprimer les haros
                - ``candids`` : Supprimer les candicatures
        """
        if quoi == "haros":
            items = CandidHaro.query.filter_by(type=CandidHaroType.haro).all()
        elif quoi == "candids":
            items = CandidHaro.query.filter_by(type=CandidHaroType.candidature).all()
        else:
            await ctx.send("Mauvais argument")

        if not items:
            await ctx.send("Rien à faire")
            await tools.log(ctx, f"!wipe {quoi} : rien à faire")
        else:
            for item in items:
                config.session.delete(item)
            config.session.commit()
            await ctx.send("Fait.")
            await tools.log(ctx, f"!wipe {quoi} : fait")
