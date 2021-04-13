"""lg-rez / features / Tâches planifiées

Planification, liste, annulation, exécution de tâches planifiées

"""

import datetime

from discord.ext import commands

from lgrez.blocs import tools
from lgrez.bdd import Tache, Action


class GestionTaches(commands.Cog):
    """Commandes de planification, exécution, annulation de tâches"""

    @commands.command()
    @tools.mjs_only
    async def taches(self, ctx):
        """Liste les tâches en attente (COMMANDE MJ)

        Affiche les commandes en attente d'exécution (dans la table
        :class:`.bdd.Tache`) et le timestamp d'exécution associé.
        Lorsque la tâche est liée à une action, affiche le nom de
        l'action et du joueur concerné.
        """
        async with ctx.typing():
            lst = Tache.query.order_by(Tache.timestamp).all()
            LT = ""
            for tache in lst:
                LT += (
                    f"\n{str(tache.id).ljust(5)} "
                    f"{tache.timestamp.strftime('%d/%m/%Y %H:%M:%S')}    "
                    f"{tache.commande.ljust(25)} ")
                if (action := tache.action):
                    LT += f"{action.base.slug.ljust(20)} {action.joueur.nom}"

            if LT:
                mess = (
                    "Tâches en attente : \n\nID    Timestamp              "
                    "Commande                  Action               Joueur"
                    f"\n{'-'*105}{LT}\n\n"
                    "Utilisez !cancel <ID> pour annuler une tâche."
                )
            else:
                mess = "Aucune tâche en attente."

        await tools.send_code_blocs(ctx, mess)


    @commands.command(aliases=["doat"])
    @tools.mjs_only
    async def planif(self, ctx, quand, *, commande):
        """Planifie une tâche au moment voulu (COMMANDE MJ)

        Args:
            quand: format ``[<J>/<M>[/<AAAA>]-]<H>:<M>[:<S>]``,
                avec ``<J>``, ``<M>``, ``<AAAA>``, ``<H>`` et ``<M>``
                des entiers et ``<S>`` un entier/flottant optionnel.
                La date est optionnelle (défaut : date du jour).
                Si elle est précisée, elle doit être **séparée de
                l'heure par un tiret** et l'année peut être omise ;
            commande: commande à exécuter (commençant par un ``!``).
                La commande sera exécutée PAR UN WEBHOOK dans LE CHAN
                ``#logs`` : toutes les commandes qui sont liées au
                joueur ou réservées au chan privé sont à proscrire
                (ou doivent a minima être précédées de ``!doas cible``)

        Cette commande repose sur l'architecture en base de données,
        ce qui garantit l'exécution de la tâche même si le bot plante
        entre temps.

        Si le bot est down à l'heure d'exécution prévue, la commande
        sera exécutée dès le bot de retour en ligne.

        Si la date est dans le passé, la commande est exécutée
        immédiatement.

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

        action_id = None
        # ID de l'action associée à la tâche le cas échéant
        try:
            quoi, id = commande.split()
            if quoi in ["!open", "!close", "!remind"]:
                action_id = int(id)
        except ValueError:
            pass

        if ts < datetime.datetime.now():
            mess = await ctx.send(
                "Date dans le passé ==> exécution immédiate ! On valide ?"
            )
            if not await tools.yes_no(mess):
                await ctx.send("Mission aborted.")
                return

        tache = Tache(timestamp=ts,
                      commande=commande,
                      action=Action.query.get(action_id))
        tache.add()         # Planifie la tâche
        await ctx.send(
            f"{tools.code(commande)} planifiée pour le "
            f"{tools.code(ts.strftime('%d/%m/%Y %H:%M:%S'))}.\n"
            f"{tools.code(f'!cancel {tache.id}')} pour annuler."
        )


    @commands.command(aliases=["retard", "doin"])
    @tools.mjs_only
    async def delay(self, ctx, duree, *, commande):
        """Exécute une commande après XhYmZs (COMMANDE MJ)

        Args:
            quand: format ``[<X>h][<Y>m][<Z>s]``, avec ``<X>`` (heures)
                et ``<Y>`` (minutes) des entiers et ``<Z>`` (secondes)
                un entier ou un flottant. Chacune des trois composantes
                est optionnelle, mais au moins une doit être présente ;
            commande: commande à exécuter (commençant par un ``!``).
                La commande sera exécutée PAR UN WEBHOOK dans LE CHAN
                ``#logs`` : toutes les commandes qui sont liées au
                joueur ou réservées au chan privé sont à proscrire
                (ou doivent être précédées d'un ``!doas <cible>``).

        Cette commande repose sur l'architecture en base de données,
        ce qui garantit l'exécution de la commande même si le bot plante
        entre temps.

        Si le bot est down à l'heure d'exécution prévue, la commande
        sera exécutée dès le bot de retour en ligne.

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
        action_id = None
        # ID de l'action associée à la tâche le cas échéant
        try:
            quoi, id = commande.split(" ")
            if quoi in ["!open", "!close", "!remind"]:
                action_id = int(id)
        except ValueError:
            pass

        tache = Tache(timestamp=ts,
                      commande=commande,
                      action=Action.query.get(action_id))
        tache.add()         # Planifie la tâche

        await ctx.send(
            f"Commande {tools.code(commande)} planifiée pour le "
            f"{tools.code(ts.strftime('%d/%m/%Y %H:%M:%S'))}\n"
            f"{tools.code(f'!cancel {tache.id}')} pour annuler."
        )


    @commands.command()
    @tools.mjs_only
    async def cancel(self, ctx, *ids):
        """Annule une ou plusieurs tâche(s) planifiée(s) (COMMANDE MJ)

        Args:
            *ids: IDs des tâches à annuler, séparées par des espaces.

        Utiliser ``!taches`` pour voir la liste des IDs.
        """
        taches = []
        for id in ids:
            if id.isdigit() and (tache := Tache.query.get(int(id))):
                taches.append(tache)

        if not taches:
            await ctx.send("Aucune tâche trouvée.")
            return

        message = await ctx.send("Annuler les tâches :\n" + "\n".join([
            f" - {tools.code(tache.timestamp.strftime('%d/%m/%Y %H:%M:%S'))} "
            f"> {tools.code(tache.commande)}" for tache in taches
        ]))
        if not await tools.yes_no(message):
            await ctx.send("Mission aborted.")
            return

        Tache.delete(*taches)       # Annule les tâches
        await ctx.send("Tâche(s) annulée(s).")
