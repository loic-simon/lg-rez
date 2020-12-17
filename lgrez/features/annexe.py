"""lg-rez / features / Commandes annexes

Commandes diverses qu'on ne savait pas où ranger

"""

import random
import requests
import traceback
import datetime
import asyncio

from discord.ext import commands
from akinator.async_aki import Akinator
import akinator

from lgrez.blocs import tools
from lgrez.blocs.bdd import session, Joueurs


class Annexe(commands.Cog):
    """Annexe - Commandes annexes aux usages divers"""

    @commands.command()
    async def roll(self, ctx, *, XdY):
        """Lance un ou plusieurs dés

        Args:
            XdY: dés à lancer + modifieurs, au format ``XdY + XdY + ... + Z - Z ...`` avec X le nombre de dés, Y le nombre de faces et Z les modifieurs (constants).

        Examples:
            - ``!roll 1d6``           -> lance un dé à 6 faces
            - ``!roll 1d20 +3``       -> lance un dé à 20 faces, ajoute 3 au résultat
            - ``!roll 1d20 + 2d6 -8`` -> lance un dé 20 plus deux dés 6, enlève 8 au résultat
        """
        dices = XdY.replace(' ', '').replace('-', '+-').split('+')        # "1d6 + 5 - 2" -> ["1d6", "5", "-2"]
        r = ""
        s = 0
        try:
            for dice in dices:
                if 'd' in dice:
                    nb, faces = dice.split('d', maxsplit=1)
                    for i in range(int(nb)):
                        v = random.randrange(int(faces)) + 1
                        s += v
                        r += f" + {v}₍{tools.sub_chiffre(int(faces), True)}₎"
                else:
                    v = int(dice)
                    s += v
                    r += f" {'-' if v < 0 else '+'} {abs(v)}"
            r += f" = {tools.emoji_chiffre(s, True)}"
        except Exception:
            await ctx.send(f"Pattern non reconu. Utilisez {tools.code('!help roll')} pour plus d'informations.")
        else:
            await tools.send_blocs(ctx, r[3:])


    @commands.command(aliases=["cf", "pf"])
    async def coinflip(self, ctx):
        """Renvoie le résultat d'un tirage à Pile ou Face (aléatoire)

        Pile je gagne, face tu perds.
        """
        await ctx.send(random.choice(["Pile", "Face"]))


    @commands.command(aliases=["pong"])
    async def ping(self, ctx):
        """Envoie un ping au bot

        Pong
        """
        ts_rec = datetime.datetime.utcnow()
        delta_rec = ts_rec - ctx.message.created_at     # Temps de réception = temps entre création message et sa réception
        pingpong = ctx.invoked_with.replace("i", "x").replace("I", "X").replace("o", "i").replace("O", "I").replace("x", "o").replace("X", "O")
        cont = (
            f" Réception : {delta_rec.total_seconds()*1000:4.0f} ms\n"
            f" Latence :   {ctx.bot.latency*1000:4.0f} ms\n"
        )
        mess = await ctx.send(f"!{pingpong}\n" + tools.code_bloc(cont + " (...)"))

        ts_ret = datetime.datetime.utcnow()
        delta_ret = ts_ret - mess.created_at            # Retour information message réponse créé
        delta_env = ts_ret - ts_rec - delta_ret         # Temps d'envoi = temps entre réception 1er message (traitement quasi instantané) et création 2e, moins temps de retour d'information
        delta_tot = delta_rec + delta_ret + delta_env   # Total = temps entre création message !pong et réception information réponse envoyée
        await mess.edit(content=f"!{pingpong}\n" + tools.code_bloc(cont +
            f" Envoi :     {delta_env.total_seconds()*1000:4.0f} ms\n"
            f" Retour :    {delta_ret.total_seconds()*1000:4.0f} ms\n"
            f"——————————————————————\n"
            f" Total :     {delta_tot.total_seconds()*1000:4.0f} ms"
        ))


    @commands.command()
    @tools.mjs_only
    async def addhere(self, ctx, *joueurs):
        """Ajoute les membres au chan courant (COMMANDE MJ)

        Args:
            *joueurs: membres à ajouter, chacun entouré par des guillemets si nom + prénom

        Si ``*joueurs`` est un seul élément, il peut être de la forme ``<crit>=<filtre>`` tel que décrit dans l'aide de ``!send``.
        """
        ts_debut = ctx.message.created_at - datetime.timedelta(microseconds=1)

        if len(joueurs) == 1 and "=" in joueurs[0]:      # Si critère : on remplace joueurs
            crit, filtre = joueurs[0].split("=", maxsplit=1)
            if hasattr(Joueurs, crit):
                joueurs = Joueurs.query.filter(getattr(Joueurs, crit) == filtre).all()
            else:
                await ctx.send(f"Critère \"{crit}\" incorrect. !help {ctx.invoked_with} pour plus d'infos.")
                return
        else:                                           # Sinon, si noms / mentions
            joueurs = [await tools.boucle_query_joueur(ctx, cible) for cible in joueurs]

        for joueur in joueurs:
            member = ctx.guild.get_member(joueur.discord_id)
            assert member, f"Member {joueur} introuvable"
            await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
            await ctx.send(f"{joueur.nom} ajouté")

        mess = await ctx.send("Fini, purge les messages ?")
        if await tools.yes_no(ctx.bot, mess):
            await ctx.channel.purge(after=ts_debut)


    @commands.command()
    @tools.mjs_only
    async def purge(self, ctx, N=None):
        """Supprime tous les messages de ce chan (COMMANDE MJ)

        Args:
            N: nombre de messages à supprimer (défaut : tous)
        """
        if N:
            mess = await ctx.send(f"Supprimer les {N} messages les plus récents de ce chan ? (celui-ci inclus)")
        else:
            mess = await ctx.send(f"Supprimer tous les messages de ce chan ?")

        if await tools.yes_no(ctx.bot, mess):
            await ctx.channel.purge(limit=int(N) if N else None)


    @commands.command()
    async def akinator(self, ctx):
        """J'ai glissé chef

        Implémentation directe de https://pypi.org/project/akinator.py
        """
        # Un jour mettre ça dans des embeds avec les https://fr.akinator.com/bundles/elokencesite/images/akitudes_670x1096/<akitude>.png croppées, <akitude> in ["defi", "serein", "inspiration_legere", "inspiration_forte", "confiant", "mobile", "leger_decouragement", "vrai_decouragement", "deception", "triomphe"]
        await ctx.send(f"Vous avez demandé à être mis en relation avec {tools.ital('Akinator : Le Génie du web')}.\nVeuillez patienter...")
        async with ctx.typing():
            # Connection
            aki = Akinator()
            question = await aki.start_game(language="fr")

        exit = False
        while not exit and aki.progression <= 80:
            mess = await ctx.send(f"({aki.step + 1}) {question}")
            reponse = await tools.wait_for_react_clic(ctx.bot, mess, {"👍":"yes", "🤷":"idk", "👎":"no", "⏭️":"stop"})
            if reponse == "stop":
                exit = True
            else:
                async with ctx.typing():
                    question = await aki.answer(reponse)

        async with ctx.typing():
            await aki.win()

        mess = await ctx.send(f"Tu penses à {tools.bold(aki.first_guess['name'])} ({tools.ital(aki.first_guess['description'])}) !\nJ'ai bon ?\n{aki.first_guess['absolute_picture_path']}")
        if await tools.yes_no(ctx.bot, mess):
            await ctx.send("Yay\nhttps://fr.akinator.com/bundles/elokencesite/images/akitudes_670x1096/triomphe.png")
        else:
            await ctx.send("Oof\nhttps://fr.akinator.com/bundles/elokencesite/images/akitudes_670x1096/deception.png")


    @commands.command()
    async def xkcd(self, ctx, N):
        """J'ai aussi glissé chef, mais un peu moins

        Args:
            N: numéro du comic
        """
        async with ctx.typing():
            r = requests.get(f"https://xkcd.com/{N}/info.0.json")

        if not r:
            await ctx.send("Paramètre incorrect ou service non accessible.")
            return

        url = r.json().get("img")
        if not url:
            await ctx.send("Paramètre incorrect ou service non accessible.")
            return

        await ctx.send(url)
