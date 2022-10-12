"""lg-rez / features / Commandes annexes

Commandes diverses qu'on ne savait pas où ranger

"""

import random
import requests
import datetime

from discord import app_commands
from akinator.async_aki import Akinator

from lgrez import config, commons
from lgrez.blocs import tools
from lgrez.blocs.journey import DiscordJourney, journey_command
from lgrez.bdd import Joueur, Role, Camp


DESCRIPTION = """Commandes annexes aux usages divers"""

next_roll = None


@app_commands.command()
@journey_command
async def roll(journey: DiscordJourney, *, pattern: str):
    """Lance un ou plusieurs dés, ou tire un nom dans un liste.

    Args:
        pattern: Dés à lancer (XdY [+ ...] [+ Z ...]) OU roll spécial (joueur / vivant / mort / rôle / camp).

    Examples:
        - ``!roll 1d6``           -> lance un dé à 6 faces
        - ``!roll 1d20 +3``       -> lance un dé à 20 faces, ajoute 3 au résultat
        - ``!roll 1d20 + 2d6 -8`` -> lance un dé 20 plus deux dés 6, enlève 8 au résultat
        - ``!roll vivant``        -> choisit un joueur vivant
    """
    global next_roll

    inp = pattern.lower()
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
        result = random.choice(["Voyante", "Protecteur", "Notaire", "Popo de mort", "Chat-garou", "Espion"])
    elif inp in ["taverne", "tavernier"]:
        result = random.choice(["Rôle choisi", "Vrai rôle", "Rôle random"])

    if result:
        if next_roll is not None:
            result = next_roll
            next_roll = None
        await journey.send(result)
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
                raise commons.UserInputError("pattern", f"Pattern de dé non reconnu : {part}")
            # Sécurité
            if abs(nb) > 1000 or faces > 1000000:
                await journey.send.send(
                    "Suite à des abus (coucou Gabin), il est "
                    "interdit de lancer plus de 1000 dés ou "
                    "des dés à plus de 1 million de faces."
                )
                return
            sig = -1 if nb < 0 else 1
            sig_s = "-" if nb < 0 else "+"
            for _ in range(abs(nb)):
                val = random.randrange(faces) + 1
                if next_roll is not None:
                    try:
                        val = int(next_roll)
                    except ValueError:
                        pass
                    else:
                        next_roll = None
                sum += sig * val
                rep += f" {sig_s} {val}₍{tools.sub_chiffre(faces, True)}₎"
        else:
            # Bonus / malus fixe
            try:
                val = int(part)
            except ValueError:
                raise commons.UserInputError("pattern", f"Pattern fixe non reconnu : {part}")
            sum += val
            rep += f" {'-' if val < 0 else '+'} {abs(val)}"
    # Total
    sig = "- " if sum < 0 else ""
    rep += f" = {sig}{tools.emoji_chiffre(abs(sum), True)}"
    rep = rep[3:] if rep.startswith(" +") else rep
    await journey.send(rep)


@app_commands.command()
@tools.mjs_only
@journey_command
async def nextroll(journey: DiscordJourney, *, next: str = None):
    """✨ Shhhhhhhhhhhh.

    Ça sent la magouilleuh
    """
    global next_roll
    next_roll = next
    await journey.send("🤫", ephemeral=True)


@journey_command
@app_commands.command()
async def coinflip(journey: DiscordJourney):
    """Pile ou face ?

    Pile je gagne, face tu perds.
    """
    await journey.send(random.choice(["Pile", "Face"]))


@app_commands.command()
@journey_command
async def ping(journey: DiscordJourney):
    """Envoie un ping au bot, pour vérifier si il est réactif tout ça.

    Pong
    """
    ts_rec = datetime.datetime.now(datetime.timezone.utc)
    delta_rec = ts_rec - journey.created_at
    # Temps de réception = temps entre création message et sa réception

    cont = f" Réception : {delta_rec.total_seconds()*1000:4.0f} ms\n Latence :   {config.bot.latency*1000:4.0f} ms\n"
    *_, mess = await journey.send(f"pong\n" + tools.code_bloc(cont + " (...)"))

    ts_ret = datetime.datetime.now(datetime.timezone.utc)
    delta_ret = ts_ret - mess.created_at
    # Retour information message réponse créé
    delta_env = ts_ret - ts_rec - delta_ret
    # Temps d'envoi = temps entre réception 1er message (traitement quasi instantané)
    # et création 2e, moins temps de retour d'information
    delta_tot = delta_rec + delta_ret + delta_env
    # Total = temps entre création message !pong et réception information réponse envoyée
    await mess.edit(
        content=f"!pong\n"
        + tools.code_bloc(
            cont + f" Envoi :     {delta_env.total_seconds()*1000:4.0f} ms\n"
            f" Retour :    {delta_ret.total_seconds()*1000:4.0f} ms\n"
            f"——————————————————————\n"
            f" Total :     {delta_tot.total_seconds()*1000:4.0f} ms"
        )
    )


@app_commands.command()
@journey_command
async def akinator(journey: DiscordJourney):
    """J'ai glissé chef

    Implémentation directe de https://pypi.org/project/akinator.py
    """
    # Un jour mettre ça dans des embeds avec les https://fr.akinator.com/
    # bundles/elokencesite/images/akitudes_670x1096/<akitude>.png croppées,
    # <akitude> in ["defi", "serein", "inspiration_legere",
    # "inspiration_forte", "confiant", "mobile", "leger_decouragement",
    # "vrai_decouragement", "deception", "triomphe"]
    await journey.send(
        "Vous avez demandé à être mis en relation avec "
        + tools.ital("Akinator : Le Génie du web")
        + ".\nVeuillez patienter..."
    )

    chan = journey.channel
    async with chan.typing():
        # Connexion
        aki = Akinator()
        question = await aki.start_game(language="fr")

    while aki.progression <= 80:
        reponse = await journey.buttons(
            f"({aki.step + 1}) {question}", {"yes": "👍", "idk": "🤷", "no": "👎", "stop": "⏭️"}
        )
        if reponse == "stop":
            break
        question = await aki.answer(reponse)

    await aki.win()

    if await journey.yes_no(
        f"Tu penses à {tools.bold(aki.first_guess['name'])} "
        f"({tools.ital(aki.first_guess['description'])}) !\n"
        f"J'ai bon ?\n{aki.first_guess['absolute_picture_path']}"
    ):
        await chan.send("Yay\nhttps://fr.akinator.com/bundles/elokencesite/images/akitudes_670x1096/triomphe.png")
    else:
        await chan.send("Oof\nhttps://fr.akinator.com/bundles/elokencesite/images/akitudes_670x1096/deception.png")


@app_commands.command()
@journey_command
async def xkcd(journey: DiscordJourney, num: int):
    """J'ai aussi glissé chef, mais un peu moins

    Args:
        num: Numéro de la planche à récupérer.
    """
    rep = requests.get(f"https://xkcd.com/{num}/info.0.json")

    if not rep:
        await journey.send(":x: Paramètre incorrect ou service non accessible.")
        return

    url = rep.json().get("img")
    if not url:
        await journey.send(":x: Paramètre incorrect ou service non accessible.")
        return

    await journey.send(url)
