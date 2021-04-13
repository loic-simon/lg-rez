"""lg-rez / features / Commandes de gestion des salons

Création, ajout, suppression de membres

"""

import asyncio
import functools
import datetime

from discord.ext import commands

from lgrez import config
from lgrez.blocs import tools, one_command
from lgrez.bdd import Joueur, Boudoir, Bouderie
from lgrez.features.sync import transtype



def in_boudoir(callback):
    """Décorateur : commande utilisable dans un boudoir uniquement.

    Lors d'une invocation de la commande décorée hors d'un boudoir
    (enregistré dans :class:`.bdd.Boudoir`), affiche un message d'erreur.

    Ce décorateur n'est utilisable que sur une commande définie dans un
    Cog.
    """
    @functools.wraps(callback)
    async def new_callback(self, ctx, *args, **kwargs):
        try:
            Boudoir.from_channel(ctx.channel)
        except ValueError:
            await ctx.reply("Cette commande est invalide en dehors "
                            "d'un boudoir.")
        else:
            # if ctx.authors
            return await callback(self, ctx, *args, **kwargs)

    return new_callback


async def _invite(joueur, boudoir, invite_msg):
    """Invitation d'un joueur dans un boudoir (lancer comme tâche à part)"""
    pc = joueur.private_chan
    bc = boudoir.chan
    mess = await pc.send(f"{boudoir.gerant.nom} t'as invité à rejoindre son "
                         f"boudoir : « {boudoir.nom} » !\nAcceptes-tu ?")

    if await tools.yes_no(mess):
        await boudoir.add_joueur(joueur)
        info = f"{joueur.nom} a rejoint le boudoir !"
        confirm = f"Tu as bien rejoint {bc.mention} !"
    else:
        info = f"{joueur.nom} a refusé l'invitation à rejoindre ce boudoir."
        confirm = "Invitation refusée."

    try:
        await invite_msg.reply(info)
    except discord.HTTPException:
        await bc.send(info)

    await mess.reply(confirm)



class GestionChans(commands.Cog):
    """Gestion des salons"""

    @commands.group(aliases=["boudoirs"])
    async def boudoir(self, ctx):
        """Gestion des boudoirs

        Les options relatives à un boudoir précis ne peuvent être
        exécutées que dans ce boudoir ; certaines sont réservées au
        gérant dudit boudoir.
        """
        if not ctx.invoked_subcommand:
            # Pas de sous-commande (correspondante)
            if ctx.subcommand_passed:
                # Tentative de subcommand
                raise commands.BadArgument(
                    f"Option '{ctx.subcommand_passed}' inconnue"
                )
            ctx.message.content = f"!help {ctx.invoked_with}"
            with one_command.bypass(ctx):
                await config.bot.process_commands(ctx.message)


    @boudoir.command(aliases=["liste"])
    @tools.joueurs_only
    @tools.private
    async def list(self, ctx):
        """Liste les boudoirs dans lesquels tu es"""
        joueur = Joueur.from_member(ctx.author)
        bouderies = joueur.bouderies

        if not bouderies:
            await ctx.reply(
                "Tu n'es dans aucun boudoir pour le moment.\n"
                f"{tools.code('!boudoir create')} pour en créer un."
            )
            return

        rep = "Tu es dans les boudoirs suivants :"
        for bouderie in bouderies:
            rep += f"\n - {bouderie.boudoir.chan.mention}"
            if bouderie.gerant:
                rep += " (gérant)"

        rep += "\n\nUtilise `!boudoir leave` dans un boudoir pour le quitter."

        await ctx.send(rep)


    @boudoir.command(aliases=["new", "creer", "créer"])
    @tools.joueurs_only
    @tools.private
    async def create(self, ctx, *, nom=None):
        """Crée un nouveau boudoir dont tu es gérant"""
        member = ctx.author
        joueur = Joueur.from_member(member)

        if not nom:
            await ctx.send("Comment veux-tu nommer ton boudoir ?\n"
                           + tools.ital("(`stop` pour annuler)"))
            mess = await tools.wait_for_message_here(ctx)
            nom = mess.content

        if len(nom) > 32:
            await ctx.send("Le nom des boudoirs est limité à 32 caractères.")
            return

        await ctx.send("Création du boudoir...")
        async with ctx.typing():
            now = datetime.datetime.now()
            categ = tools.channel(config.boudoirs_category_name)
            if len(categ.channels) >= 50:
                # Limitation Discord : 50 channels par catégorie
                ok = False
                N = 2
                while not ok:
                    nom_nouv_cat = f"{config.boudoirs_category_name} {N}"
                    categ_new = tools.channel(nom_nouv_cat,
                                              must_be_found=False)
                    if not categ_new:
                        categ = await categ.clone(name=nom_nouv_cat)
                        ok = True
                    elif len(categ_new.channels) < 50:
                        # Catégorie N pas pleine
                        categ = categ_new
                        ok = True
                    N += 1

            chan = await config.guild.create_text_channel(
                nom,
                topic=f"Boudoir crée le {now:%d/%m à %H:%M}. "
                      f"Gérant : {joueur.nom}",
                category=categ,
            )

            boudoir = Boudoir(chan_id=chan.id, nom=nom, ts_created=now)
            boudoir.add()
            await boudoir.add_joueur(joueur, gerant=True)

            await chan.send(
                f"{member.mention}, voici ton boudoir ! "
                "Tu peux maintenant y inviter des gens avec la commande "
                "`!boudoir invite`."
            )

        await ctx.send(f"Ton boudoir a bien été créé : {chan.mention} !")
        await tools.log(f"Boudoir {chan.mention} créé par {joueur.nom}.")


    @boudoir.command(aliases=["add"])
    @tools.joueurs_only
    @in_boudoir
    async def invite(self, ctx, *cibles):
        """Invite un ou plusieur joueur(s) à rejoindre ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        gerant = Joueur.from_member(ctx.author)
        if boudoir.gerant != gerant:
            await ctx.reply("Seul le gérant du boudoir peut y inviter "
                            "de nouvelles personnes.")
            return

        for cible in cibles:
            joueur = await tools.boucle_query_joueur(
                ctx, cible=cible, message="Qui souhaites-tu inviter ?"
            )
            if joueur in boudoir.joueurs:
                await ctx.send(f"{joueur.nom} est déjà dans ce boudoir !")
                return

            mess = await ctx.send(f"Invitation envoyée à {joueur.nom}.")
            asyncio.create_task(_invite(joueur, boudoir, mess))
            # On envoie l'invitation en arrière-plan (libération du chan).


    @boudoir.command(aliases=["remove"])
    @tools.joueurs_only
    @in_boudoir
    async def expulse(self, ctx, *cibles):
        """Expulse un ou plusieur membre(s) de ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        gerant = Joueur.from_member(ctx.author)
        if boudoir.gerant != gerant:
            await ctx.reply("Seul le gérant du boudoir peut en expulser "
                            "des membres.")
            return

        for cible in cibles:
            joueur = await tools.boucle_query_joueur(
                ctx, cible=cible, message="Qui souhaites-tu expulser ?"
            )
            if joueur not in boudoir.joueurs:
                await ctx.send(f"{joueur.nom} n'est pas membre du boudoir !")
                return

            await boudoir.remove_joueur(joueur)
            await joueur.private_chan.send(f"Tu as été expulsé(e) du boudoir "
                                           f"« {boudoir.nom} ».")
            await ctx.send(f"{joueur.nom} a bien été expulsé de ce boudoir.")


    @boudoir.command(aliases=["quit"])
    @tools.joueurs_only
    @in_boudoir
    async def leave(self, ctx):
        """Quitte ce boudoir"""
        joueur = Joueur.from_member(ctx.author)
        boudoir = Boudoir.from_channel(ctx.channel)

        if boudoir.gerant == joueur:
            await ctx.send(
                "Tu ne peux pas quitter un boudoir que tu gères. "
                "Utilise `!boudoir transfer` pour passer les droits "
                "de gestion ou `!boudoir delete` pour le supprimer."
            )
            return

        mess = await ctx.reply(
            "Veux-tu vraiment quitter ce boudoir ? Tu ne "
            "pourras pas y retourner sans invitation."
        )
        if not await tools.yes_no(mess):
            await ctx.send("Mission aborted.")
            return

        await boudoir.remove_joueur(joueur)
        await ctx.send(tools.ital(f"{joueur.nom} a quitté ce boudoir."))


    @boudoir.command(aliases=["transmit"])
    @tools.joueurs_only
    @in_boudoir
    async def transfer(self, ctx, cible=None):
        """Transfère les droits de gestion de ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        gerant = Joueur.from_member(ctx.author)
        if boudoir.gerant != gerant:
            await ctx.reply("Seul le gérant du boudoir peut en transférer "
                            "les droits de gestion.")
            return

        joueur = await tools.boucle_query_joueur(
            ctx, cible=cible, message=("À qui souhaites-tu confier "
                                       "la gestion de ce boudoir ?")
        )
        if joueur not in boudoir.joueurs:
            await ctx.send(f"{joueur.nom} n'est pas membre de ce boudoir !")
            return

        mess = await ctx.reply(
            "Veux-tu vraiment transférer les droits de ce boudoir ? "
            "Tu ne pourras pas les récupérer par toi-même."
        )
        if not await tools.yes_no(mess):
            await ctx.send("Mission aborted.")
            return

        bd_gerant = next(bd for bd in boudoir.bouderies if bd.joueur == gerant)
        bd_nouv = next(bd for bd in boudoir.bouderies if bd.joueur == joueur)

        bd_gerant.gerant = False
        bd_nouv.gerant = True
        bd_nouv.ts_promu = datetime.datetime.now()
        Bouderie.update()
        await boudoir.chan.edit(
            topic=f"Boudoir crée le {boudoir.ts_created:%d/%m à %H:%M}. "
                  f"Gérant : {joueur.nom}"
        )

        await ctx.send(f"Boudoir transféré à {joueur.nom}.")


    @boudoir.command()
    @tools.joueurs_only
    @in_boudoir
    async def delete(self, ctx):
        """Supprime ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        gerant = Joueur.from_member(ctx.author)
        if boudoir.gerant != gerant:
            await ctx.reply("Seul le gérant du boudoir peut le supprimer.")
            return

        mess = await ctx.reply("Veux-tu vraiment supprimer ce boudoir ? "
                               "Cette action est irréversible.")
        if not await tools.yes_no(mess):
            await ctx.send("Mission aborted.")
            return

        await ctx.send("Suppression...")
        for joueur in boudoir.joueurs:
            await boudoir.remove_joueur(joueur)
            await joueur.private_chan.send(
                f"Le boudoir « {boudoir.nom } » a été supprimé."
            )

        await boudoir.chan.edit(name=f"\N{CROSS MARK} {boudoir.nom}")
        await ctx.send(tools.ital(
            "[Tous les joueurs ont été exclus de ce boudoir ; "
            "le channel reste présent pour archive.]"
        ))


    @boudoir.command()
    @tools.joueurs_only
    @in_boudoir
    async def rename(self, ctx, nom=None):
        """Renomme ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        gerant = Joueur.from_member(ctx.author)
        if boudoir.gerant != gerant:
            await ctx.reply("Seul le gérant du boudoir peut le renommer.")
            return

        if not nom:
            await ctx.send("Comment veux-tu renommer ce boudoir ?\n"
                           + tools.ital("(`stop` pour annuler)"))
            mess = await tools.wait_for_message_here(ctx)
            nom = mess.content

        if len(nom) > 32:
            await ctx.send("Le nom des boudoirs est limité à 32 caractères.")
            return

        boudoir.nom = nom
        boudoir.update()
        await boudoir.chan.edit(name=nom)
        await ctx.send("Boudoir renommé avec succès.")


    @commands.command()
    @tools.mjs_only
    async def addhere(self, ctx, *joueurs):
        """Ajoute les membres au chan courant (COMMANDE MJ)

        Args:
            *joueurs: membres à ajouter, chacun entouré par des
                guillemets si nom + prénom

        Si ``*joueurs`` est un seul élément, il peut être de la forme
        ``<crit>=<filtre>`` tel que décrit dans l'aide de ``!send``.
        """
        ts_debut = ctx.message.created_at - datetime.timedelta(microseconds=1)

        if len(joueurs) == 1 and "=" in joueurs[0]:
            # Si critère : on remplace joueurs
            crit, _, filtre = joueurs[0].partition("=")
            crit = crit.strip()
            if crit in Joueur.attrs:
                col = Joueur.attrs[crit]
                arg = transtype(filtre.strip(), col)
                joueurs = Joueur.query.filter_by(**{crit: arg}).all()
            else:
                raise commands.UserInputError(f"critère '{crit}' incorrect")
        else:
            # Sinon, si noms / mentions
            joueurs = [await tools.boucle_query_joueur(ctx, cible)
                       for cible in joueurs]

        for joueur in joueurs:
            await ctx.channel.set_permissions(joueur.member,
                                              read_messages=True,
                                              send_messages=True)
            await ctx.send(f"{joueur.nom} ajouté")

        mess = await ctx.send("Fini, purge les messages ?")
        if await tools.yes_no(mess):
            await ctx.channel.purge(after=ts_debut)


    @commands.command()
    @tools.mjs_only
    async def purge(self, ctx, N=None):
        """Supprime tous les messages de ce chan (COMMANDE MJ)

        Args:
            N: nombre de messages à supprimer (défaut : tous)
        """
        if N:
            mess = await ctx.send(
                f"Supprimer les {N} messages les plus récents de ce chan ? "
                "(sans compter le `!purge` et ce message)"
            )
        else:
            mess = await ctx.send("Supprimer tous les messages de ce chan ?")

        if await tools.yes_no(mess):
            await ctx.channel.purge(limit=int(N) + 2 if N else None)
