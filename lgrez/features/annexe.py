import random
import traceback
import datetime
import asyncio

from discord import Embed
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

        <XdY> dés à lancer + modifieurs, au format {XdY + XdY + ... + Z - Z ... } avec X le nombre de dés, Y le nombre de faces et Z les modifieurs (constants).

        Ex. !roll 1d6           -> lance un dé à 6 faces
            !roll 1d20 +3       -> lance un dé à 20 faces, ajoute 3 au résultat
            !roll 1d20 + 2d6 -8 -> lance un dé 20 plus deux dés 6, enlève 8 au résultat
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
        """Ajoute les membres au chan courant

        *[joueurs] membres à ajouter
        Si *[joueurs] est un seul élément, il peut être de la forme <crit>=<filtre> tel que décrit dans l'aide de !send.
        """
        ts_debut = ctx.message.created_at

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
        """Supprime tous les messages de ce chan

        [N] nombre de messages à supprimer (défaut : tous)
        """
        if N:
            mess = await ctx.send(f"Supprimer les {N} messages les plus récents de ce chan ? (celui-ci inclus)")
        else:
            mess = await ctx.send(f"Supprimer tous les messages de ce chan ?")

        if await tools.yes_no(ctx.bot, mess):
            await ctx.channel.purge(limit=N)


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



    @commands.command(aliases=["tell"])
    @tools.mjs_only
    async def send(self, ctx, cible, *, message):
        """Envoie un message à tous ou certains joueurs (COMMANDE MJ)

        <cible> peut être :
            all                 Tous les joueurs inscrits, vivants et morts
            vivants             Les joueurs en vie
            morts               Les joueurs morts
            <crit>=<filtre>     Les joueurs répondant au critère Joueurs.<crit> == <filtre> :
                                    <crit> peut être nom, chambre, statut, role, camp...
                                    L'ensemble doit être entouré de guillements si <filtre> contient un espace.

        <message> peut contenir un ou plusieurs bouts de code Python à évaluer, entourés d'accolades.
        L'évaluation est faite séparément pour chaque joueur, ce qui permet de personnaliser le message grâce aux variables particulières dépendant du joueur :
            joueur          objet BDD du joueur recevant le message  ==> joueur.nom, joueur.role...
            member          objet discord.Member associé             ==> member.mention
            chan            objet discord.TextChannel du chan privé du joueur

        Attention :
            ctx             objet discord.ext.commands.Context de !send  ==> ctx.author = lanceur de la commande !!!

        Les différentes tables de données sont accessibles sous leur nom (Joueurs, Roles...)
        Il est impossible d'appeller des coroutines (await) dans le code à évaluer.

        Ex. !send all Bonsoir à tous c'est Fanta
            !send vivants Attention {member.mention}, derrière toi c'est affreux !
            !send "role=Servante Dévouée" Çreponse va vous ? Vous êtes bien {joueur.role} ?
        """
        if cible == "all":
            joueurs = Joueurs.query.all()
        elif cible == "vivants":
            joueurs = Joueurs.query.filter_by(statut="vivant").all()
        elif cible == "morts":
            joueurs = Joueurs.query.filter_by(statut="mort").all()
        elif "=" in cible:
            crit, filtre = cible.split("=", maxsplit=1)
            if hasattr(Joueurs, crit):
                joueurs = Joueurs.query.filter(getattr(Joueurs, crit) == filtre).all()
            else:
                await ctx.send(f"Critère \"{crit}\" incorrect. !help {ctx.invoked_with} pour plus d'infos.")
                return
        else:
            await ctx.send(f"Cible \"{cible}\" non reconnue. !help {ctx.invoked_with} pour plus d'infos.")
            return

        if not joueurs:
            await ctx.send(f"Aucun joueur trouvé.")
            return

        await ctx.send(f"{len(joueurs)} trouvé(s), envoi...")
        for joueur in joueurs:
            member = ctx.guild.get_member(joueur.discord_id)
            chan = ctx.guild.get_channel(joueur._chan_id)

            assert member, f"!send : Member associé à {joueur} introuvable"
            assert chan, f"!sed : Chan privé de {joueur} introuvable"

            evaluated_message = tools.eval_accols(message, locals=locals())
            await chan.send(evaluated_message)

        await ctx.send(f"Fini.")


    current_embed = None
    current_helper_embed = None

    @commands.command()
    @tools.mjs_only
    async def embed(self, ctx, key=None, *, val=None):
        """Prépare un embed (message riche) et l'envoie (COMMANDE MJ)

        [key] sous-commande (voir ci-dessous). Si omis, prévisualise le brouillon d'embed actuellement en préparation ;
        [val] valeur associée. Pour les sous-commandes de construction d'élement, supprime ledit élément si omis.

        - Sous-commandes générales :
            !embed create <titre>           Créer un nouveau brouillon d'embed (un seul brouillon en parallèle, pour tous les utilisateurs)
            !embed delete                   Supprimer le brouillon d'embed
            !embed preview                  Voir l'embed sans les rappels de commande
            !embed post [#channel]          Envoyer l'embed sur #channel (chan courant si omis)

        - Sous-commandes de construction d'éléments :
            - Éléments généraux :
                !embed title [titre]
                !embed description [texte]
                !embed url [url*]
                !embed color [#ffffff]      (barre de gauche, code hexadécimal)

            - Auteur :
                !embed author [nom]
                !embed author_url [url*]
                !embed author_icon [url**]

            - Talon :
                !embed footer [texte]
                !embed footer_icon [url**]

            - Images :
                !embed image [url**]        (grande image)
                !embed thumb [url**]        (en haut à droite)

            - Champs : syntaxe spéciale
                !embed field <i> <skey> [val]
                    <i>             Numéro du champ (commençant à 0). Si premier champ non existant, le crée.
                    <skey> =
                        name        Nom du champ
                        value       Valeur du champ
                        delete      Supprime le champ

                Les champs sont (pour l'instant) forcément de type inline (côte à côte).

        * Les URL doivent commencer par http(s):// pour être reconnues comme telles.
        ** Ces URL doivent correspondre à une image.
        """

        if val is None:
            val = Embed.Empty

        emb = self.current_embed                # Récupération de l'embed (stocké dans le cog)

        direct = [                              # Attributs modifiables directement : emb.attr = value
            "title",
            "description",
            "url",
        ]
        method = {                              # Attributs à modifier en appelant une méthode : emb.set_<attr>(value)
            "footer": ("footer", "text"),                           # method[key] = (<attr>, <value>)
            "footer_icon": ("footer", "icon_url"),
            "image": ("image", "url"),
            "thumb": ("thumbnail", "url"),
            "author_url": ("author", "url"),
            "author_icon": ("author", "icon_url"),
        }

        if not emb:                             # Pas d'embed en cours
            if key == "create" and val:
                emb = Embed(title=val)
            else:
                await ctx.send(f"Pas d'embed en préparation. {tools.code('!embed create <titre>')} pour en créer un.")
                return

        elif key in direct:                     # Attributs modifiables directement
            setattr(emb, key, val)

        elif key in method:                     # Attributs à modifier en appelant une méthode
            prop, attr = method[key]
            getattr(emb, f"set_{prop}")(**{attr: val})          # emb.set_<prop>(<attr>=val)

        elif key == "author":                   # Cas particulier
            emb.set_author(name=val) if val else emb.remove_author()

        elif key == "color":                    # Autre cas particulier : conversion couleur en int
            try:
                emb.color = eval(val.replace("#", "0x")) if val else Embed.Empty
            except Exception:
                await ctx.send("Couleur invalide")
                return

        elif key == "field":                    # Cas encore plus particulier
            i_max = len(emb.fields)                 # N fields ==> i_max = N+1
            try:
                i, skey, val = val.split(" ", maxsplit=2)
                i = int(i)
                if i < 0 or i > i_max:
                    await ctx.send("Numéro de field invalide")
                    return
                if skey not in ["name", "value", "delete"]:
                    raise ValueError()
            except Exception:
                await ctx.send("Syntaxe invalide")
                return

            if i == i_max:
                if skey == "name":
                    emb.add_field(name=val, value=f"!embed field {i} value <valeur>")
                elif skey == "value":
                    emb.add_field(name=f"!embed field {i} name <nom>", value=val)
                # emb.add_field(*, name, value, inline=True)

            else:
                if skey == "name":
                    emb.set_field_at(i, name=val, value=emb.fields[i].name)
                elif skey == "value":
                    emb.set_field_at(i, name=emb.fields[i].name, value=val)
                else:
                    emb.remove_field(i)
                # emb.set_field_at(i, *, name, value, inline=True)

        elif key == "delete":
            self.current_embed = None
            await ctx.send(f"Supprimé. {tools.code('!embed create <titre>')} pour en créer un.")
            return

        elif key == "create":
            await ctx.send(f"Déjà un embed en cours de création. Utiliser {tools.code('!embed delete')} pour le supprimer.")

        elif key == "preview":
            await ctx.send("Prévisuatisation :", embed=emb)
            await ctx.send(f"Utiliser {tools.code('!embed post #channel')} pour publier l'embed.")
            return

        elif key == "post":
            if not val:     # channel non précisé
                await ctx.send(embed=emb)
            elif chan := tools.channel(ctx, val, must_be_found=False):
                await chan.send(embed=emb)
                await ctx.send("Et pouf !")
            else:
                await ctx.send(f"Channel inconnu. Réessaye en le mentionnant ({tools.code('#channel')})")
            return

        elif key is not None:
            await ctx.send(f"Option {key} incorrecte : utiliser {tools.code('!help embed')} pour en savoir plus.")
            return


        h_emb = emb.copy()
        if not emb.title:
            h_emb.title = "!embed title <titre>"
        if not emb.description:
            h_emb.description = "!embed description <description>"
        if not emb.footer:
            h_emb.set_footer(text="!embed footer <footer>")
        if not emb.author:
            h_emb.set_author(name="!embed author <auteur>")

        i_max = len(emb.fields)                 # N fields ==> i_max = N+1
        h_emb.add_field(name=f"!embed field {i_max} name <nom>", value=f"!embed field {i_max} value <nom>")

        await ctx.send("Embed en préparation :", embed=h_emb)
        await ctx.send(f"Utiliser {tools.code('!embed preview')} pour prévisualiser l'embed.\n"
                       f"Autres options : {tools.code('!embed color <#xxxxxx> / url <url> / image <url> / thumb <url> / author_url <url> / footer_icon <url>')}")

        self.current_embed = emb
