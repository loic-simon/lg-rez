"""lg-rez / bdd / Modèle de données

Déclaration de toutes les tables et leurs colonnes

"""

import datetime
import time

import sqlalchemy

from lgrez import config
from lgrez.bdd import base, ActionTrigger
from lgrez.bdd.base import (autodoc_Column, autodoc_ManyToOne,
                            autodoc_OneToMany, autodoc_DynamicOneToMany)
from lgrez.bdd.enums import UtilEtat
from lgrez.blocs import env, webhook


# Tables de données

class Action(base.TableBase):
    """Table de données des actions attribuées (liées à un joueur).

    Les instances doivent être enregistrées via
    :func:`.gestion_actions.add_action` et supprimées via
    :func:`.gestion_actions.delete_action`.
    """
    id = autodoc_Column(sqlalchemy.Integer(), primary_key=True,
        doc="Identifiant unique de l'action, sans signification")

    _joueur_id = sqlalchemy.Column(sqlalchemy.ForeignKey("joueurs.discord_id"),
        nullable=False)
    joueur = autodoc_ManyToOne("Joueur", back_populates="actions",
        doc="Joueur concerné")

    _base_slug = sqlalchemy.Column(sqlalchemy.ForeignKey("baseactions.slug"),
        nullable=False)
    base = autodoc_ManyToOne("BaseAction", back_populates="actions",
        doc="Action de base")

    cooldown = autodoc_Column(sqlalchemy.Integer(), nullable=False, default=0,
        doc="Nombre d'ouvertures avant disponiblité de l'action")
    charges = autodoc_Column(sqlalchemy.Integer(),
        doc="Nombre de charges restantes (``None`` si illimité)")

    decision_ = autodoc_Column(sqlalchemy.String(200),
        doc="Décision prise par le joueur pour l'action actuelle (``None`` "
            "si action pas en cours). *(le ``_`` final n'indique rien de "
            "très pertinent, vivement que ça dégage)*")

    # One-to-manys
    taches = autodoc_OneToMany("Tache", back_populates="action",
        doc="Tâches liées à cette action")

    utilisations = autodoc_DynamicOneToMany("Utilisation",
        back_populates="action",
        doc="Utilisations de cette action")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Action #{self.id} ({self.base}/{self.joueur})>"


class Utilisation(base.TableBase):
    """Table de données des utilisations des actions.

    Les instances sont enregistrées via :meth:`\!open
    <.open_close.OpenClose.OpenClose.open.callback>` ;
    elles n'ont pas vocation à être supprimées.
    """
    id = autodoc_Column(sqlalchemy.BigInteger(), primary_key=True,
        doc="Identifiant unique de l'utilisation, sans signification")

    _action_id = sqlalchemy.Column(sqlalchemy.ForeignKey("actions.id"),
        nullable=False)
    action = autodoc_ManyToOne("Action", back_populates="utilisations",
        doc="Action utilisée")

    etat = autodoc_Column(sqlalchemy.Enum(UtilEtat), nullable=False,
        default=UtilEtat.ouverte,
        doc="État de l'utilisation")

    ts_open = autodoc_Column(sqlalchemy.DateTime(),
        doc="Timestamp d'ouverture de l'utilisation")
    ts_close = autodoc_Column(sqlalchemy.DateTime(),
        doc="Timestamp de fermeture de l'utilisation")
    ts_decision = autodoc_Column(sqlalchemy.DateTime(),
        doc="Timestamp du dernier remplissage de l'utilisation")

    # One-to-manys
    taches = autodoc_OneToMany("Tache", back_populates="utilisation",
        doc="Tâches liées à cette utilisation")
    ciblages = autodoc_OneToMany("Ciblage", back_populates="utilisation",
        doc="Cibles désignées dans cette utilisation")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Utilisation #{self.id} ({self.action})>"


class Ciblage(base.TableBase):
    """Table de données des cibles désignées dans les utilisations d'actions.

    Les instances sont enregistrées via :meth:`\!action
    <.voter_agir.VoterAgir.VoterAgir.action.callback>` ;
    elles n'ont pas vocation à être supprimées.
    """
    id = autodoc_Column(sqlalchemy.Integer(), primary_key=True,
        doc="Identifiant unique du ciblage, sans signification")

    _base_id = sqlalchemy.Column(sqlalchemy.ForeignKey("baseciblages.id"),
        nullable=False)
    base = autodoc_ManyToOne("BaseCiblage", back_populates="ciblages",
        doc="Modèle de ciblage (lié au modèle d'action)")

    _utilisation_id = sqlalchemy.Column(sqlalchemy.ForeignKey(
        "utilisations.id"), nullable=False)
    utilisation = autodoc_ManyToOne("Utilisation", back_populates="ciblages",
        doc="Utilisation où ce ciblage a été fait")

    _joueur_id = sqlalchemy.Column(sqlalchemy.ForeignKey(
        "joueurs.discord_id"), nullable=True)
    joueur = autodoc_ManyToOne("Joueur", back_populates="ciblages",
        nullable=True, doc="Joueur désigné, si ``base.type`` vaut "
        ":attr:`~.bdd.CibleType.joueur`, :attr:`~.bdd.CibleType.vivant` "
        "ou :attr:`~.bdd.CibleType.mort`")

    _role_slug = sqlalchemy.Column(sqlalchemy.ForeignKey(
        "roles.slug"), nullable=True)
    role = autodoc_ManyToOne("Role", back_populates="ciblages",
        nullable=True, doc="Rôle désigné, si ``base.type`` vaut "
        ":attr:`~.bdd.CibleType.role`")

    _camp_slug = sqlalchemy.Column(sqlalchemy.ForeignKey(
        "camps.slug"), nullable=True)
    camp = autodoc_ManyToOne("Camp", back_populates="ciblages",
        nullable=True, doc="Camp désigné, si ``base.type`` vaut "
        ":attr:`~.bdd.CibleType.camp`")

    booleen = autodoc_Column(sqlalchemy.Boolean(),
        doc="Valeur, si ``base.type`` vaut :attr:`~.bdd.CibleType.booleen`")
    texte = autodoc_Column(sqlalchemy.String(1000),
        doc="Valeur, si ``base.type`` vaut :attr:`~.bdd.CibleType.texte`")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Ciblage #{self.id} ({self.base}/{self.utilisation})>"


class Tache(base.TableBase):
    """Table de données des tâches planifiées du bot.

    Les instances doivent être enregistrées via :meth:`.add`
    et supprimées via :func:`.delete`.
    """
    id = autodoc_Column(sqlalchemy.Integer(), primary_key=True,
        doc="Identifiant unique de la tâche, sans signification")
    timestamp = autodoc_Column(sqlalchemy.DateTime(), nullable=False,
        doc="Moment où exécuter la tâche")
    commande = autodoc_Column(sqlalchemy.String(2000), nullable=False,
        doc="Texte à envoyer via le webhook (généralement une commande)")

    _action_id = sqlalchemy.Column(sqlalchemy.ForeignKey("actions.id"),
        nullable=True)
    action = autodoc_ManyToOne("Action", back_populates="taches",
        nullable=True,
        doc="Si la tâche est liée à une action, action concernée")

    _utilisation_id = sqlalchemy.Column(sqlalchemy.ForeignKey(
        "utilisations.id"), nullable=True)
    utilisation = autodoc_ManyToOne("Utilisation", back_populates="taches",
        nullable=True,
        doc="Si la tâche est liée à une utilisation, utilisation concernée")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Tache #{self.id} ({self.commande})>"

    @property
    def handler(self):
        """asyncio.TimerHandle: Représentation dans le bot de la tâche.

        Proxy pour :attr:`config.bot.tasks[self.id] <.LGBot.tasks>`,
        en lecture, écriture et suppression (``del``).

        Raises:
            RuntimeError: tâche non enregistrée dans le bot.
        """
        try:
            return config.bot.tasks[self.id]
        except KeyError:
            raise RuntimeError(f"Tâche {self} non enregistrée dans le bot !")

    @handler.setter
    def handler(self, value):
        if self.id is None:
            raise RuntimeError("Tache.handler: Tache.id non défini (commit ?)")
        config.bot.tasks[self.id] = value

    @handler.deleter
    def handler(self):
        try:
            del config.bot.tasks[self.id]
        except KeyError:
            pass

    def execute(self):
        """Exécute la tâche planifiée (méthode appellée par la loop).

        Envoie un webhook (variable d'environnement ``LGREZ_WEBHOOK_URL``)
        avec comme message :attr:`.commande`, puis

          - si l'envoi est un succès, supprime la tâche (et son handler);
          - sinon, se ré-appelle dans 2 secondes.

        Limitation interne de 2 secondes minimum entre deux appels
        (ré-appelle si appelée trop tôt), pour se conformer à la rate
        limit Discord (30 messages / minute) et ne pas engoncer la loop.
        """
        if webhook._last_time and (time.time() - webhook._last_time) < 2:
            # Moins de deux secondes depuis le dernier envoi :
            # on interdit l'envoi du webhook
            config.loop.call_later(2, self.execute)
            return

        webhook._last_time = time.time()

        LGREZ_WEBHOOK_URL = env.load("LGREZ_WEBHOOK_URL")
        if webhook.send(self.commande, url=LGREZ_WEBHOOK_URL):
            # Envoi webhook OK
            self.delete()
        else:
            # Problème d'envoi : on réessaie dans 2 secondes
            config.loop.call_later(2, self.execute)

    def register(self):
        """Programme l'exécution de la tâche dans la loop du bot."""
        now = datetime.datetime.now()
        delay = (self.timestamp - now).total_seconds()
        TH = config.loop.call_later(delay, self.execute)
        # Programme la tâche (appellera tache.execute() à timestamp)
        self.handler = TH               # TimerHandle, pour pouvoir cancel

    def cancel(self):
        """Annule et nettoie la tâche planifiée (sans la supprimer en base).

        Si la tâche a déjà été exécutée, ne fait que nettoyer le handler.
        """
        try:
            self.handler.cancel()       # Annule la task (objet TimerHandle)
            # (pas d'effet si la tâche a déjà été exécutée)
        except RuntimeError:            # Tache non enregistrée
            pass
        else:
            del self.handler

    def add(self, *other):
        """Enregistre la tâche sur le bot et en base.

        Globalement équivalent à un appel à :meth:`.register` (pour
        chaque élément le cas échéant) avant l'ajout en base habituel
        (:meth:`TableBase.add <.bdd.base.TableBase.add>`).

        Args:
            \*other: autres instances à ajouter dans le même commit,
                éventuellement.
        """
        super().add(*other)             # Enregistre tout en base

        self.register()                 # Enregistre sur le bot
        for item in other:              # Les autres aussi
            item.register()


    def delete(self, *other):
        """Annule la tâche planifiée et la supprime en base.

        Globalement équivalent à un appel à :meth:`.cancel` (pour
        chaque élément le cas échéant) avant la suppression en base
        habituelle (:meth:`TableBase.add <.bdd.base.TableBase.add>`).

        Args:
            \*other: autres instances à supprimer dans le même commit,
                éventuellement.
        """
        self.cancel()                   # Annule la tâche
        for item in other:              # Les autres aussi
            item.cancel()

        super().delete(*other)          # Supprime tout en base
