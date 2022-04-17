"""lg-rez / features / Commandes de gestion des salons

Création, ajout, suppression de membres

"""

import asyncio
import functools
import datetime

import discord
from discord.ext import commands

from lgrez import config
from lgrez.blocs import tools, one_command
from lgrez.bdd import Joueur, Boudoir, Bouderie
from lgrez.features.sync import transtype



def in_boudoir(callback):
    """Décorateur : commande utilisable dans un boudoir uniquement.

    Lors d'une invocation de la commande décorée hors d'un boudoir
    (enregistré dans :class:`.bdd.Boudoir`), affiche un message d'erreur.

    Ce décorateur n'est utilisable que sur une commande définie dans un Cog.
    """
    @functools.wraps(callback)
    async def new_callback(cog, ctx, *args, **kwargs):
        try:
            Boudoir.from_channel(ctx.channel)
        except ValueError:
            await ctx.reply("Cette commande est invalide en dehors "
                            "d'un boudoir.")
        else:
            return await callback(cog, ctx, *args, **kwargs)

    return new_callback


def gerant_only(callback):
    """Décorateur : commande utilisable par le gérant d'un boudoir uniquement.

    Lors d'une invocation de la commande décorée par un membre qui n'est
    pas gérant du boudoir, affiche un message d'erreur.

    Ce décorateur doit toujours être utilisé en combinaison avec
    :func:`in_boudoir` et positionné après lui.

    Ce décorateur n'est utilisable que sur une commande définie dans un Cog.
    """
    @functools.wraps(callback)
    async def new_callback(cog, ctx, *args, **kwargs):
        boudoir = Boudoir.from_channel(ctx.channel)
        gerant = Joueur.from_member(ctx.author)
        if boudoir.gerant != gerant:
            await ctx.reply("Seul le gérant du boudoir peut utiliser "
                            "cette commande.")
        else:
            return await callback(cog, ctx, *args, **kwargs)

    return new_callback


async def add_joueur_to_boudoir(boudoir, joueur, gerant=False):
    """Ajoute un joueur sur un boudoir.

    Crée la :class:`.Bouderie` correspondante et modifie les
    permissions du salon.

    Args:
        boudoir (.Boudoir): Le boudoir où ajouter un joueur.
        joueur (.Joueur): Le joueur à ajouter.
        gerant (bool): Si le joueur doit être ajouté avec les
            permissions de gérant.

    Returns:
        :class:`bool` - ``True`` si le joueur a été ajouté,
            ``False`` si il y était déjà / le boudoir est fermé.
    """
    if joueur in boudoir.joueurs:
        # Joueur déjà dans le boudoir
        return False
    if not boudoir.joueurs and not gerant:
        # Boudoir fermé (plus de joueurs) et pas ajout comme gérant
        return False

    now = datetime.datetime.now()
    Bouderie(boudoir=boudoir, joueur=joueur, gerant=gerant,
                ts_added=now, ts_promu=now if gerant else None).add()
    await boudoir.chan.set_permissions(joueur.member, read_messages=True)

    # Sortie du cimetière le cas échéant
    if tools.in_multicateg(boudoir.chan.category,
                            config.old_boudoirs_category_name):
        await boudoir.chan.send(tools.ital(
            "[Ce boudoir contient au moins deux joueurs vivants, "
            "désarchivage...]"
        ))
        categ = await tools.multicateg(config.boudoirs_category_name)
        await boudoir.chan.edit(name=boudoir.nom, category=categ)
    return True


async def remove_joueur_from_boudoir(boudoir, joueur):
    """Retire un joueur d'un boudoir.

    Supprime la :class:`.Bouderie` correspondante et modifie les
    permissions du salon.

    Args:
        boudoir (.Boudoir): Le boudoir d'où enlever un joueur.
        joueur (.Joueur): Le joueur à enlever.
    """
    Bouderie.query.filter_by(boudoir=boudoir, joueur=joueur).one().delete()
    await boudoir.chan.set_permissions(joueur.member, overwrite=None)
    # Déplacement dans le cimetière si nécessaire
    vivants = [jr for jr in boudoir.joueurs if jr.est_vivant]
    if len(vivants) < 2:
        if tools.in_multicateg(boudoir.chan.category,
                                config.old_boudoirs_category_name):
            # Boudoir déjà au cimetière
            return
        await boudoir.chan.send(tools.ital(
            "[Ce boudoir contient moins de deux joueurs vivants, "
            "archivage...]"
        ))
        categ = await tools.multicateg(config.old_boudoirs_category_name)
        await boudoir.chan.edit(
            name=f"\N{CROSS MARK} {boudoir.nom}",
            category=categ,
        )


async def _create_boudoir(joueur, nom):
    """Crée un boudoir avec le gérant et le nom requis"""
    now = datetime.datetime.now()
    categ = await tools.multicateg(config.boudoirs_category_name)
    chan = await config.guild.create_text_channel(
            nom,
            topic=f"Boudoir crée le {now:%d/%m à %H:%M}. "
                    f"Gérant(e) : {joueur.nom}",
            category=categ,
        )

    boudoir = Boudoir(chan_id=chan.id, nom=nom, ts_created=now)
    boudoir.add()
    await add_joueur_to_boudoir(boudoir, joueur, gerant=True)
    await tools.log(f"Boudoir {chan.mention} créé par {joueur.nom}.")

    return boudoir


async def _invite(joueur, boudoir, invite_msg):
    """Invitation d'un joueur dans un boudoir (lancer comme tâche à part)"""
    pc = joueur.private_chan
    bc = boudoir.chan
    mess = await pc.send(
        f"{joueur.member.mention} {boudoir.gerant.nom} t'as invité(e) à "
        f"rejoindre son boudoir : « {boudoir.nom} » !\nAcceptes-tu ?"
    )

    if await tools.yes_no(mess):
        ok = await add_joueur_to_boudoir(boudoir, joueur)
        if ok:
            info = f"{joueur.nom} a rejoint le boudoir !"
            confirm = f"Tu as bien rejoint {bc.mention} !"
        else:
            info = None
            confirm = f"Impossible de rejoindre le boudoir."
    else:
        info = f"{joueur.nom} a refusé l'invitation à rejoindre ce boudoir."
        confirm = "Invitation refusée."

    if info:
        try:
            await invite_msg.reply(info)
        except discord.HTTPException:       # Message d'inviation supprimé
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
    @tools.vivants_only
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
            boudoir = await _create_boudoir(joueur, nom)
            await boudoir.chan.send(
                f"{member.mention}, voici ton boudoir ! "
                "Tu peux maintenant y inviter des gens avec la commande "
                "`!boudoir invite`."
            )

        await ctx.send(f"Ton boudoir a bien été créé : {boudoir.chan.mention}")


    @boudoir.command(aliases=["add"])
    @tools.joueurs_only
    @in_boudoir
    @gerant_only
    async def invite(self, ctx, *, cible=None):
        """Invite un joueur à rejoindre ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        joueur = await tools.boucle_query_joueur(
            ctx, cible=cible, message="Qui souhaites-tu inviter ?"
        )
        if joueur in boudoir.joueurs:
            await ctx.send(f"{joueur.nom} est déjà dans ce boudoir !")
            return

        mess = await ctx.send(f"Invitation envoyée à {joueur.nom}.")
        asyncio.create_task(_invite(joueur, boudoir, mess))
        # On envoie l'invitation en arrière-plan (libération du chan).


    @boudoir.command(aliases=["remove", "kick"])
    @tools.joueurs_only
    @in_boudoir
    @gerant_only
    async def expulse(self, ctx, *, cible=None):
        """Expulse un membre de ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        joueur = await tools.boucle_query_joueur(
            ctx, cible=cible, message="Qui souhaites-tu expulser ?"
        )
        if joueur not in boudoir.joueurs:
            await ctx.send(f"{joueur.nom} n'est pas membre du boudoir !")
            return

        await remove_joueur_from_boudoir(boudoir, joueur)
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

        await remove_joueur_from_boudoir(boudoir, joueur)
        await ctx.send(tools.ital(f"{joueur.nom} a quitté ce boudoir."))


    @boudoir.command(aliases=["transmit"])
    @tools.joueurs_only
    @in_boudoir
    @gerant_only
    async def transfer(self, ctx, cible=None):
        """Transfère les droits de gestion de ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        gerant = Joueur.from_member(ctx.author)
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
                  f"Gérant(e) : {joueur.nom}"
        )

        await ctx.send(f"Boudoir transféré à {joueur.nom}.")


    @boudoir.command()
    @tools.joueurs_only
    @in_boudoir
    @gerant_only
    async def delete(self, ctx):
        """Supprime ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
        mess = await ctx.reply("Veux-tu vraiment supprimer ce boudoir ? "
                               "Cette action est irréversible.")
        if not await tools.yes_no(mess):
            await ctx.send("Mission aborted.")
            return

        await ctx.send("Suppression...")
        for joueur in boudoir.joueurs:
            await remove_joueur_from_boudoir(boudoir, joueur)
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
    @gerant_only
    async def rename(self, ctx, *, nom=None):
        """Renomme ce boudoir"""
        boudoir = Boudoir.from_channel(ctx.channel)
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


    @boudoir.command(aliases=["hého"])
    @tools.joueurs_only
    @in_boudoir
    @gerant_only
    async def ping(self, ctx, *, mess=""):
        """Mentionne tous les joueurs vivants dans le boudoir."""
        await ctx.channel.send(f"{config.Role.joueur_en_vie.mention} {mess}")


    @boudoir.command(aliases=["locate", "whereis"])
    @tools.mjs_only
    async def find(self, ctx, *cibles):
        """✨ Trouve le(s) boudoir(s) réunissant certains joueurs (COMMANDE MJ)

        Args:
            *cibles: noms ou mentions des joueurs qui nous intéressent.
        """
        joueurs = [await tools.boucle_query_joueur(ctx, cible=cible)
                   for cible in cibles]
        boudoirs = [boudoir for boudoir in Boudoir.query.all()
                    if all(joueur in boudoir.joueurs for joueur in joueurs)]

        if not boudoirs:
            await ctx.reply("Pas de boudoir(s) réunissant ces joueurs.")
        else:
            await tools.send_blocs(ctx, "\n".join(
                f"- {boudoir.chan.mention} ({len(boudoir.joueurs)} joueurs)"
                for boudoir in boudoirs
            ))


    @boudoir.command()
    async def help(self, ctx):
        """✨ Informations sur les sous-commandes disponibles

        Alias pour ``!help boudoir``.
        """
        ctx.message.content = "!help boudoir"
        with one_command.bypass(ctx):
            await config.bot.process_commands(ctx.message)


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def mp(self, ctx, *, cible=None):
        """✨ Raccourci pour créer un boudoir et y ajouter un joueur.

        Si un boudoir existe déjà avec uniquement ce joueur et toi,
        n'en crée pas un nouveau.

        Args:
            cible: la personne avec qui créer un boudoir.
        """
        member = ctx.author
        joueur = Joueur.from_member(member)
        autre = await tools.boucle_query_joueur(
            ctx, cible=cible, message="À qui souhaites-tu parler ?"
        )

        if joueur == autre:
            await ctx.send(
                f"Ton boudoir a bien été créé : {ctx.channel.mention}"
            )
            await ctx.send("(tocard)")
            return

        # Recherche si boudoir existant
        boudoir = next((boudoir for boudoir in joueur.boudoirs
                        if set(boudoir.joueurs) == {joueur, autre}), None)
        if boudoir:
            await ctx.reply(f"Ce boudoir existe déjà : {boudoir.chan.mention}")
            return

        await ctx.reply("Création du boudoir...")
        async with ctx.typing():
            nom = f"{joueur.nom} × {autre.nom}"
            boudoir = await _create_boudoir(joueur, nom)
            await boudoir.chan.send(f"{member.mention}, voici ton boudoir !")

        await ctx.send(f"Ton boudoir a bien été créé : {boudoir.chan.mention}")

        mess = await boudoir.chan.send(f"Invitation envoyée à {autre.nom}.")
        asyncio.create_task(_invite(autre, boudoir, mess))
        # On envoie l'invitation en arrière-plan (libération du chan).


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
                                              read_messages=True)
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
