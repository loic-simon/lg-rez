"""lg-rez / features / Commandes annexes

Commandes diverses qu'on ne savait pas où ranger

"""

import random
import requests
import datetime

from discord.ext import commands
from akinator.async_aki import Akinator

from lgrez.blocs import tools
from lgrez.bdd import Joueur, Role, Camp


class Annexe(commands.Cog):
    """Commandes annexes aux usages divers"""
    next_roll = None

    @commands.command()
    async def roll(self, ctx, *, XdY):
        """Lance un ou plusieurs dés

        Args:
            XdY: dés à lancer + modifieurs, au format
                ``XdY + XdY + ... + Z - Z ...`` avec X le nombre de dés,
                Y le nombre de faces et Z les modifieurs (constants) ;
                OU roll spécial : ``joueur`` / ``vivant`` / ``mort`` /
                ``rôle`` / ``camp``.

        Examples:
            - ``!roll 1d6``           -> lance un dé à 6 faces
            - ``!roll 1d20 +3``       -> lance un dé à 20 faces,
              ajoute 3 au résultat
            - ``!roll 1d20 + 2d6 -8`` -> lance un dé 20 plus deux dés 6,
              enlève 8 au résultat
            - ``!roll vivant``        -> choisit un joueur vivant
        """
        inp = XdY.lower()
        # Rolls spéciaux
        result = None
        if inp in ["joueur", "joueurs"]:
            result = random.choice(Joueur.query.all()).nom
        elif inp in ["vivant", "vivants"]:
            jr = random.choice(Joueur.query.filter(Joueur.est_vivant).all())
            result = jr.nom
        elif inp in ["mort", "morts"]:
            jr = random.choice(Joueur.query.filter(Joueur.est_mort).all())
            result = jr.nom
        elif inp in ["role", "rôle", "roles", "rôles"]:
            role = random.choice(Role.query.filter_by(actif=True).all())
            result = role.nom_complet
        elif inp in ["camp", "camps"]:
            result = random.choice(Camp.query.filter_by(public=True).all()).nom
        elif inp in ["ludo", "ludopathe"]:
            result = random.choice(["Voyante", "Protecteur", "Notaire",
                                    "Popo de mort", "Chat-garou", "Espion"])
        elif inp in ["taverne", "tavernier"]:
            result = random.choice(["Rôle choisi", "Vrai rôle", "Rôle random"])

        if result:
            if self.next_roll is not None:
                result = self.next_roll
                self.next_roll = None
            await ctx.reply(result)
            return

        parts = inp.replace(" ", "").replace("-", "+-").split("+")
        # "1d6 + 5 - 2" -> ["1d6", "5", "-2"]
        sum = 0
        rep = ""
        for part in parts:
            if not part:
                continue
            if "d" in part:
                # Lancer de dé
                nb, _, faces = part.partition("d")
                try:
                    nb, faces = int(nb), int(faces)
                    if faces < 1:
                        raise ValueError
                except ValueError:
                    raise commands.UserInputError(
                        f"Pattern de dé non reconu : {part}"
                    )
                # Sécurité
                if abs(nb) > 1000 or faces > 1000000:
                    await ctx.reply(
                        "Suite à des abus (coucou Gabin), il est "
                        "interdit de lancer plus de 1000 dés ou "
                        "des dés à plus de 1 million de faces."
                    )
                    return
                sig = -1 if nb < 0 else 1
                sig_s = "-" if nb < 0 else "+"
                for _ in range(abs(nb)):
                    val = random.randrange(faces) + 1
                    if self.next_roll is not None:
                        try:
                            val = int(self.next_roll)
                        except ValueError:
                            pass
                        else:
                            self.next_roll = None
                    sum += sig * val
                    rep += f" {sig_s} {val}₍{tools.sub_chiffre(faces, True)}₎"
            else:
                # Bonus / malus fixe
                try:
                    val = int(part)
                except ValueError:
                    raise commands.UserInputError(
                        f"Pattern fixe non reconu : {part}"
                    )
                sum += val
                rep += f" {'-' if val < 0 else '+'} {abs(val)}"
        # Total
        sig = "- " if sum < 0 else ""
        rep += f" = {sig}{tools.emoji_chiffre(abs(sum), True)}"
        rep = rep[3:] if rep.startswith(" +") else rep
        await tools.send_blocs(ctx, rep)


    @commands.command()
    @tools.mjs_only
    async def nextroll(self, ctx, *, next=None):
        """✨ Shhhhhhhhhhhh.

        Ça sent la magouilleuh
        """
        self.next_roll = next
        await ctx.message.add_reaction("🤫")


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

        Warning:
            Commande en bêta, non couverte par les tests unitaires.
        """
        ts_rec = datetime.datetime.utcnow()
        delta_rec = ts_rec - ctx.message.created_at
        # Temps de réception = temps entre création message et sa réception
        pingpong = ctx.invoked_with.replace("i", "x").replace("I", "X")
        pingpong = pingpong.replace("o", "i").replace("O", "I")
        pingpong = pingpong.replace("x", "o").replace("X", "O")

        cont = (
            f" Réception : {delta_rec.total_seconds()*1000:4.0f} ms\n"
            f" Latence :   {ctx.bot.latency*1000:4.0f} ms\n"
        )
        mess = await ctx.send(
            f"!{pingpong}\n" + tools.code_bloc(cont + " (...)")
        )

        ts_ret = datetime.datetime.utcnow()
        delta_ret = ts_ret - mess.created_at
        # Retour information message réponse créé
        delta_env = ts_ret - ts_rec - delta_ret
        # Temps d'envoi = temps entre réception 1er message (traitement quasi
        # instantané) et création 2e, moins temps de retour d'information
        delta_tot = delta_rec + delta_ret + delta_env
        # Total = temps entre création message !pong et réception information
        # réponse envoyée
        await mess.edit(content=f"!{pingpong}\n" + tools.code_bloc(
            cont +
            f" Envoi :     {delta_env.total_seconds()*1000:4.0f} ms\n"
            f" Retour :    {delta_ret.total_seconds()*1000:4.0f} ms\n"
            f"——————————————————————\n"
            f" Total :     {delta_tot.total_seconds()*1000:4.0f} ms"
        ))


    @commands.command()
    async def akinator(self, ctx):
        """J'ai glissé chef

        Implémentation directe de https://pypi.org/project/akinator.py

        Warning:
            Commande en bêta, non couverte par les tests unitaires.
        """
        # Un jour mettre ça dans des embeds avec les https://fr.akinator.com/
        # bundles/elokencesite/images/akitudes_670x1096/<akitude>.png croppées,
        # <akitude> in ["defi", "serein", "inspiration_legere",
        # "inspiration_forte", "confiant", "mobile", "leger_decouragement",
        # "vrai_decouragement", "deception", "triomphe"]
        await ctx.send(
            "Vous avez demandé à être mis en relation avec "
            + tools.ital("Akinator : Le Génie du web")
            + ".\nVeuillez patienter..."
        )
        async with ctx.typing():
            # Connexion
            aki = Akinator()
            question = await aki.start_game(language="fr")

        exit = False
        while not exit and aki.progression <= 80:
            mess = await ctx.send(f"({aki.step + 1}) {question}")
            reponse = await tools.wait_for_react_clic(
                mess,
                {"👍": "yes", "🤷": "idk", "👎": "no", "⏭️": "stop"}
            )
            if reponse == "stop":
                exit = True
            else:
                async with ctx.typing():
                    question = await aki.answer(reponse)

        async with ctx.typing():
            await aki.win()

        mess = await ctx.send(
            f"Tu penses à {tools.bold(aki.first_guess['name'])} "
            f"({tools.ital(aki.first_guess['description'])}) !\n"
            f"J'ai bon ?\n{aki.first_guess['absolute_picture_path']}"
        )
        if await tools.yes_no(mess):
            await ctx.send(
                "Yay\nhttps://fr.akinator.com/bundles/elokencesite"
                "/images/akitudes_670x1096/triomphe.png"
            )
        else:
            await ctx.send(
                "Oof\nhttps://fr.akinator.com/bundles/elokencesite"
                "/images/akitudes_670x1096/deception.png"
            )


    @commands.command()
    async def xkcd(self, ctx, N):
        """J'ai aussi glissé chef, mais un peu moins

        Args:
            N: numéro du comic

        Warning:
            Commande en bêta, non couverte par les tests unitaires.
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
