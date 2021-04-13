"""lg-rez / features / Actions publiques

Gestion des haros, candidatures à la mairie, résultats des votes

"""

import discord
from discord.ext import commands

from lgrez import config
from lgrez.blocs import tools
from lgrez.bdd import Joueur, CandidHaro, Statut, CandidHaroType, Vote


class ActionsPubliques(commands.Cog):
    """Commandes d'actions vous engageant publiquement"""

    @commands.command()
    @tools.vivants_only
    @tools.private
    async def haro(self, ctx, *, cible=None):
        """Lance publiquement un haro contre un autre joueur.

        Args:
            cible: nom du joueur à accuser

        Cette commande n'est utilisable que lorsqu'un vote pour le
        condamné est en cours.
        """
        auteur = ctx.author
        joueur = Joueur.from_member(auteur)
        try:
            vaction = joueur.action_vote(Vote.cond)
        except RuntimeError:
            await ctx.send("Minute papillon, le jeu n'est pas encore lancé !")
            return

        if not vaction.is_open:
            await ctx.send("Pas de vote pour le condamné du jour en cours !")
            return

        cible = await tools.boucle_query_joueur(
            ctx, cible,
            "Contre qui souhaites-tu déverser ta haine ?"
        )

        if cible.statut == Statut.mort:
            await ctx.send("Nan mais oh, tu crois qu'il a pas assez "
                           "souffert en mourant lui ?")
            return

        elif cible.statut == Statut.immortel:
            await ctx.send("Comment oses-tu t'en prendre à ceux qui te sont "
                           f"supérieurs ? {config.Role.mj.mention}, regardez "
                           "un peu ce qu'il se passe là...")
            return

        await tools.send_blocs(
            ctx,
            "Et quelle est la raison de cette haine, d'ailleurs ?"
        )
        motif = await tools.wait_for_message_here(ctx)

        emb = discord.Embed(
            title=(f"**{config.Emoji.ha}{config.Emoji.ro} "
                   f"contre {cible.nom} !**"),
            description=f"**« {motif.content} »\n**",
            color=0xff0000
        )
        emb.set_author(name=f"{joueur.nom} en a gros 😡😡")
        emb.set_thumbnail(url=config.Emoji.bucher.url)
        emb.set_footer(
            text=f"Utilise !vote {cible.nom} pour voter contre cette personne."
        )

        mess = await ctx.send("C'est tout bon ?", embed=emb)
        if await tools.yes_no(mess):
            if not CandidHaro.query.filter_by(joueur=cible,
                                              type=CandidHaroType.haro).all():
                # Inscription haroté
                config.session.add(CandidHaro(joueur=cible,
                                              type=CandidHaroType.haro))

            if not CandidHaro.query.filter_by(joueur=joueur,
                                              type=CandidHaroType.haro).all():
                # Inscription haroteur
                config.session.add(CandidHaro(joueur=joueur,
                                              type=CandidHaroType.haro))

            config.session.commit()

            await config.Channel.haros.send(
                f"(Psst, {cible.member.mention} :3)",
                embed=emb
            )
            await config.Channel.debats.send(
                f"{config.Emoji.ha}{config.Emoji.ro} de {auteur.mention} "
                f"sur {cible.member.mention} ! Vous en pensez quoi vous ? "
                f"(détails sur {config.Channel.haros.mention})"
            )
            await ctx.send(
                f"Allez, c'est parti ! ({config.Channel.haros.mention})"
            )

        else:
            await ctx.send("Mission aborted.")


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def candid(self, ctx):
        """Candidate à l'élection du nouveau maire.

        Cette commande n'est utilisable que lorsqu'un vote pour le
        nouveau maire est en cours.
        """
        auteur = ctx.author
        joueur = Joueur.from_member(auteur)
        try:
            vaction = joueur.action_vote(Vote.maire)
        except RuntimeError:
            await ctx.send("Minute papillon, le jeu n'est pas encore lancé !")
            return

        if not vaction.is_open:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return

        if CandidHaro.query.filter_by(joueur=joueur,
                                      type=CandidHaroType.candidature).all():
            await ctx.send(
                "Hola collègue, tout doux, tu t'es déjà présenté(e) !"
            )
            return

        await tools.send_blocs(ctx, "Quel est ton programme politique ?")
        motif = await tools.wait_for_message_here(ctx)

        emb = discord.Embed(
            title=(f"**{config.Emoji.maire} {joueur.nom} "
                   "candidate à la Mairie !**"),
            description=("Voici son programme politique :\n"
                         + tools.bold(motif.content)),
            color=0xf1c40f
        )
        emb.set_author(name=f"{joueur.nom} vous a compris !")
        emb.set_thumbnail(url=config.Emoji.maire.url)
        emb.set_footer(
            text=(f"Utilise !votemaire {auteur.display_name} "
                  "pour voter pour cette personne.")
        )

        mess = await ctx.send("C'est tout bon ?", embed=emb)
        if await tools.yes_no(mess):
            ch = CandidHaro(joueur=joueur, type=CandidHaroType.candidature)
            config.session.add(ch)
            config.session.commit()

            await config.Channel.haros.send(
                "Here comes a new challenger !",
                embed=emb
            )
            await config.Channel.debats.send(
                f"{auteur.mention} se présente à la Mairie ! "
                "Vous en pensez quoi vous ?\n"
                f"(détails sur {config.Channel.haros.mention})"
            )
            await ctx.send(
                f"Allez, c'est parti ! ({config.Channel.haros.mention})"
            )

        else:
            await ctx.send("Mission aborted.")


    @commands.command()
    @tools.mjs_only
    async def wipe(self, ctx, quoi):
        """Efface les haros / candidatures du jour (COMMANDE MJ)

        Args:
            quoi (str): peut être

                - ``haros`` : Supprimer les haros
                - ``candids`` : Supprimer les candicatures

        (commande non testée unitairement)
        """
        if quoi == "haros":
            cht = CandidHaroType.haro
        elif quoi == "candids":
            cht = CandidHaroType.candidature
        else:
            await ctx.send("Mauvais argument")

        items = CandidHaro.query.filter_by(type=cht).all()

        if not items:
            await ctx.send("Rien à faire")
            await tools.log(f"!wipe {quoi} : rien à faire")
        else:
            CandidHaro.delete(*items)
            await ctx.send("Fait.")
            await tools.log(f"!wipe {quoi} : fait")
