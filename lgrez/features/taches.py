"""lg-rez / features / Tâches planifiées

Planification, liste, annulation, exécution de tâches planifiées

"""

import datetime
import asyncio
import time

from discord.ext import commands

from lgrez.blocs import env, webhook, bdd, tools
from lgrez.blocs.bdd import Taches, Actions, Joueurs


_last_time = None       # Temps (time.time) du derner envoi de webhook

def execute(tache, loop):
    """Exécute une tâche planifiée

    Args:
        tache (:class:`.bdd.Taches`): tâche planifiée arrivée à exécution
        loop (:class:`asyncio.AbstractEventLoop`): boucle d'évènements du bot

    Envoie un webhook (variable d'environnement ``LGREZ_WEBHOOK_URL``) avec la commande (:attr:`.bdd.Taches.commande`) et nettoie

    Limitation interne de 2 secondes minimum entre deux appels (reprogramme si appelé trop tôt), pour se conformer à la rate limit Discord (30 messages / minute) et ne pas engoncer la loop
    """
    global _last_time

    if _last_time and (time.time() - _last_time) < 2:      # Moins de deux secondes depuis le dernier envoi
        loop.call_later(2, execute, tache, loop)        # on interdit l'envoi du webhook
        return

    _last_time = time.time()

    LGREZ_WEBHOOK_URL = env.load("LGREZ_WEBHOOK_URL")
    if webhook.send(tache.commande, url=LGREZ_WEBHOOK_URL):     # envoi webhook OK
        bdd.session.delete(tache)
        bdd.session.commit()
    else:
        # On réessaie dans 2 secondes
        loop.call_later(2, execute, tache, loop)


def add_task(bot, timestamp, commande, action=None):
    """Crée une nouvelle tâche planifiée sur le bot + en base, renvoie l'objet Tâche

    Args:
        bot (:class:`.LGBot`): bot connecté
        timestamp (:class:`datetime.datetime`): timestamp de la tâche à ajouter
        commande (:class:`str`): commande à exécuter à ``timestamp``
        action (:class:`int`): si tâche planifiée liée à une commande, son ID (:attr:`.bdd.Actions.id`)

    Returns:
        :class:`.bdd.Taches`

    (fonction pour usage ici et dans d'autres features)
    """
    now = datetime.datetime.now()
    tache = Taches(timestamp=timestamp, commande=commande, action=action)

    bdd.session.add(tache)                                                           # Enregistre la tâche en BDD
    bdd.session.commit()

    TH = bot.loop.call_later((timestamp - now).total_seconds(), execute, tache, bot.loop)     # Programme la tâche (appellera execute(tache, loop) à timestamp)
    bot.tasks[tache.id] = TH        # TaskHandler, pour pouvoir cancel

    return tache


def cancel_task(bot, tache):
    """Supprime (annule) une tâche (fonction pour usage ici et dans d'autres features)

    Args:
        bot (:class:`.LGBot`): bot connecté
        tache (:class:`.bdd.Taches`): tâche à annuler
    """
    bot.tasks[tache.id].cancel()        # Annulation (objet TaskHandler)
    bdd.session.delete(tache)            # Suppression en base
    bdd.session.commit()
    del bot.tasks[tache.id]             # Suppression TaskHandler


class GestionTaches(commands.Cog):
    """GestionTaches - Commandes de planification, exécution, annulation de tâches"""

    @commands.command()
    @tools.mjs_only
    async def taches(self, ctx):
        """Liste les tâches en attente (COMMANDE MJ)

        Affiche les commandes en attente d'exécution (dans la table :class:`.bdd.Taches`) et le timestamp d'exécution associé.
        Lorsque la tâche est liée à une action, affiche le nom de l'action et du joueur concerné.
        """
        async with ctx.typing():
            taches = Taches.query.order_by(Taches.timestamp).all()
            LT = ""
            for tache in taches:
                LT += f"\n{str(tache.id).ljust(5)} {tache.timestamp.strftime('%d/%m/%Y %H:%M:%S')}    {tache.commande.ljust(25)} "
                if tache.action and (action := Actions.query.get(tache.action)):
                    joueur = Joueurs.query.get(action.player_id)
                    assert joueur, f"!taches : joueur d'ID {action.player_id} introuvable"
                    LT += f"{action.action.ljust(20)} {joueur.nom}"

            mess = ("Tâches en attente : \n\nID    Timestamp              Commande                  Action               Joueur"
                    f"\n{'-'*105}{LT}\n\n"
                    "Utilisez !cancel <ID> pour annuler une tâche.") if LT else "Aucune tâche en attente."

        await tools.send_code_blocs(ctx, mess)


    @commands.command(aliases=["doat"])
    @tools.mjs_only
    async def planif(self, ctx, quand, *, commande):
        """Planifie une tâche au moment voulu (COMMANDE MJ)

        Args:
            quand: format ``[<J>/<M>[/<AAAA>]-]<H>:<M>[:<S>]``, avec ``<J>`` (jours), ``<M>`` (mois), ``<AAAA>`` (année sur 4 chiffres), ``<H>`` (heures) et ``<M>`` (minutes) des entiers et ``<S>`` (secondes) un entier ou un flottant, optionnel (défaut : ``0``)
                La date est optionnelle (défaut : date du jour). Si elle est précisée, elle doit être **séparée de l'heure par un tiret** et l'année peut être omise (défaut : année actuelle) ;
            commande: commande à exécuter (commençant par un ``!``). La commande sera exécutée PAR UN WEBHOOK dans LE CHAN ``#logs`` : toutes les commandes qui sont liées au joueur ou réservées au chan privé sont à proscrire (ou doivent a minima être précédées de ``!doas cible``)

        Cette commande repose sur l'architecture en base de données, ce qui garantit l'exécution de la tâche même si le bot plante entre temps.

        Si le bot est down à l'heure d'exécution prévue, la commande sera exécutée dès le bot de retour en ligne.

        Si la date est dans le passé, la commande est exécutée immédiatement.

        Examples:
            - ``!planif 18:00 !close maire``
            - ``!planif 13/06-10:00 !open maire``
            - ``!planif 13/06/2020-10:00 !open maire``
            - ``!planif 23:25:12 !close maire``
        """
        now = datetime.datetime.now()

        if "/" in quand:            # Date précisée
            date, time = quand.split("-")
            J, MA = date.split("/", maxsplit=1)
            day = int(J)
            if "/" in MA:           # Année précisée
                M, A = MA.split("/")
                month = int(M)
                year = int(A)
            else:
                month = int(MA)
                year = now.year
            date = datetime.date(year=year, month=month, day=day)
        else:
            date = now.date()
            time = quand

        H, MS = time.split(":", maxsplit=1)
        hour = int(H)
        if ":" in MS:               # Secondes précisées
            M, S = MS.split(":")
            minute = int(M)
            second = int(S)
        else:
            minute = int(MS)
            second = 0
        time = datetime.time(hour=hour, minute=minute, second=second)

        ts = datetime.datetime.combine(date, time)

        action_id = None            # ID de l'action associée à la tâche (utile pour propagation à la suppression de l'action)
        try:
            quoi, id = commande.split(" ")
            if quoi in ["!open", "!close", "!remind"]:
                action_id = int(id)
        except ValueError:
            pass

        if ts < datetime.datetime.now():
            mess = await ctx.send("Date dans le passé ==> exécution immédiate ! On valide ?")
            if not await tools.yes_no(ctx.bot, mess):
                await ctx.send("Mission aborted.")
                return

        tache = add_task(ctx.bot, ts, commande, action=action_id)
        await ctx.send(f"{tools.code(commande)} planifiée pour le {tools.code(ts.strftime('%d/%m/%Y %H:%M:%S'))}.\n{tools.code(f'!cancel {tache.id}')} pour annuler.")



    @commands.command(aliases=["retard", "doin"])
    @tools.mjs_only
    async def delay(self, ctx, duree, *, commande):
        """Exécute une commande après XhYmZs (COMMANDE MJ)

        Args:
            quand: format ``[<X>h][<Y>m][<Z>s]``, avec ``<X>`` (heures) et ``<Y>`` (minutes) des entiers et ``<Z>`` (secondes) un entier ou un flottant. Chacune des trois composantes est optionnelle, mais au moins une d'entre elle doit être présente ;
            commande: commande à exécuter (commençant par un ``!``). La commande sera exécutée PAR UN WEBHOOK dans LE CHAN ``#logs`` : toutes les commandes qui sont liées au joueur ou réservées au chan privé sont à proscrire (ou doivent a minima être précédées d'un ``!doas <cible>``)

        Cette commande repose sur l'architecture en base de données, ce qui garantit l'exécution de la commande même si le bot plante entre temps.

        Si le bot est down à l'heure d'exécution prévue, la commande sera exécutée dès le bot de retour en ligne.

        Examples:
            - ``!delay 2h !close maire``
            - ``!delay 1h30m !doas @moi !vote Yacine Oussar``
        """
        secondes = 0
        try:
            if "h" in duree.lower():
                h, duree = duree.split("h")
                secondes += 3600*int(h)
            if "m" in duree.lower():
                m, duree = duree.split("m")
                secondes += 60*int(m)
            if "s" in duree.lower():
                s, duree = duree.split("s")
                secondes += float(s)
        except Exception as e:
            raise commands.BadArgument("<duree>") from e

        if duree or not secondes:
            raise commands.BadArgument("<duree>")

        ts = datetime.datetime.now() + datetime.timedelta(seconds=secondes)
        action_id = None            # ID de l'action associée à la tâche (utile pour propagation à la suppression de l'action)
        try:
            quoi, id = commande.split(" ")
            if quoi in ["!open", "!close", "!remind"]:
                action_id = int(id)
        except ValueError:
            pass

        add_task(ctx.bot, ts, commande, action=action_id)

        await ctx.send(f"Commande {tools.code(commande)} planifiée pour le {tools.code(ts.strftime('%d/%m/%Y %H:%M:%S'))}")


    @commands.command()
    @tools.mjs_only
    async def cancel(self, ctx, *ids):
        """Annule une ou plusieurs tâche(s) planifiée(s) (COMMANDE MJ)

        Args:
            *ids: IDs des tâches à annuler, séparées par des espaces.

        Utiliser ``!taches`` pour voir la liste des IDs.
        """
        taches = [tache for id in ids if id.isdigit() and (tache := Taches.query.get(int(id)))]
        if taches:
            message = await ctx.send("Annuler les tâches :\n" + "\n".join([f" - {tools.code(tache.timestamp.strftime('%d/%m/%Y %H:%M:%S'))} > {tools.code(tache.commande)}" for tache in taches]))
            if await tools.yes_no(ctx.bot, message):
                for tache in taches:
                    cancel_task(ctx.bot, tache)

                await ctx.send("Tâche(s) annulée(s).")
            else:
                await ctx.send("Mission aborted.")
        else:
            await ctx.send(f"Aucune tâche trouvée.")
