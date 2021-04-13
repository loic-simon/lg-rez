"""lg-rez / bdd / Modèle de données

Déclaration de toutes les tables et leurs colonnes

"""

import asyncio
import datetime
import time

import sqlalchemy
from sqlalchemy.ext.hybrid import hybrid_property

from lgrez import config
from lgrez.bdd import base, ActionTrigger
from lgrez.bdd.base import (autodoc_Column, autodoc_ManyToOne,
                            autodoc_OneToMany, autodoc_DynamicOneToMany)
from lgrez.bdd.enums import UtilEtat, CibleType, Vote


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

    _base_slug = sqlalchemy.Column(sqlalchemy.ForeignKey("baseactions.slug"))
    base = autodoc_ManyToOne("BaseAction", back_populates="actions",
        nullable=True,
        doc="Action de base (``None`` si action de vote)")

    vote = autodoc_Column(sqlalchemy.Enum(Vote),
        doc="Si action de vote, vote concerné")

    active = autodoc_Column(sqlalchemy.Boolean(), nullable=False, default=True,
        doc="Si l'action est actuellement utilisable (False = archives)")

    cooldown = autodoc_Column(sqlalchemy.Integer(), nullable=False, default=0,
        doc="Nombre d'ouvertures avant disponiblité de l'action")
    charges = autodoc_Column(sqlalchemy.Integer(),
        doc="Nombre de charges restantes (``None`` si illimité)")

    # One-to-manys
    taches = autodoc_OneToMany("Tache", back_populates="action",
        doc="Tâches liées à cette action")

    utilisations = autodoc_DynamicOneToMany("Utilisation",
        back_populates="action",
        doc="Utilisations de cette action")

    def __init__(self, *args, **kwargs):
        """Initialize self."""
        n_args = (("base" in kwargs) + ("_base_slug" in kwargs)
                  + ("vote" in kwargs))
        if not n_args:
            raise ValueError("bdd.Action: 'base'/'_base_slug' or 'vote' "
                             "keyword-only argument must be specified")
        elif n_args > 1:
            raise ValueError("bdd.Action: 'base'/'_base_slug' and 'vote' "
                             "keyword-only argument cannot both be specified")
        super().__init__(*args, **kwargs)

    def __repr__(self):
        """Return repr(self)."""
        return f"<Action #{self.id} ({self.base or self.vote}/{self.joueur})>"

    @property
    def utilisation_ouverte(self):
        """:class:`~bdd.Utilisation` | ``None``: Utilisation de l'action
        actuellement ouverte.

        Vaut ``None`` si aucune action n'a actuellement l'état
        :attr:`~bdd.UtilEtat.ouverte` ou :attr:`~bdd.UtilEtat.remplie`.

        Raises:
            RuntimeError: plus d'une action a actuellement l'état
            :attr:`~bdd.UtilEtat.ouverte` ou :attr:`~bdd.UtilEtat.remplie`.
        """
        filtre = Utilisation.etat.in_({UtilEtat.ouverte, UtilEtat.remplie})
        try:
            return self.utilisations.filter(filtre).one_or_none()
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise ValueError(
                f"Plusieurs utilisations ouvertes pour `{self}` !"
            )

    @property
    def derniere_utilisation(self):
        """:class:`~bdd.Utilisation` | ``None``:: Dernière utilisation de
        cette action (temporellement).

        Considère l'utilisation ouverte le cas échéant, sinon la
        dernière utilisation par timestamp de fermeture descendant
        (quelque soit son état, y comprs :attr:`~.bdd.UtilEtat.contree`).

        Vaut ``None`` si l'action n'a jamais été utilisée.

        Raises:
            RuntimeError: plus d'une action a actuellement l'état
            :attr:`~bdd.UtilEtat.ouverte` ou :attr:`~bdd.UtilEtat.remplie`.
        """
        return (
            self.utilisation_ouverte
            or self.utilisations.order_by(Utilisation.ts_close.desc()).first()
        )

    @property
    def decision(self):
        """str: Description de la décision de la dernière utilisation.

        Considère l'utilisation ouverte le cas échéant, sinon la
        dernière utilisation par timestamp de fermeture descendant.

        Vaut :attr:`.Utilisation.decision`, ou ``"<N/A>"`` si il n'y a
        aucune utilisation de cette action.

        Raises:
            RuntimeError: plus d'une action a actuellement l'état
            :attr:`~bdd.UtilEtat.ouverte` ou :attr:`~bdd.UtilEtat.remplie`.
        """
        util = self.derniere_utilisation
        if util:
            return util.decision
        else:
            return "<N/A>"

    @hybrid_property
    def is_open(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (classe):
        L'action est ouverte (l'utilisateur peut interagir) ?

        *I.e.* l'action a au moins une utilisation
        :attr:`~.bdd.UtilEtat.ouverte` ou :attr:`~.bdd.UtilEtat.remplie`.

        Propriété hybride (:class:`sqlalchemy.ext.hybrid.hybrid_property`) :

            - Sur l'instance, renvoie directement la valeur booléenne ;
            - Sur la classe, renvoie la clause permettant de déterminer
              si l'action est en attente.

        Examples::

            action.is_open          # bool
            Joueur.query.filter(Joueur.actions.any(Action.is_open)).all()
        """
        return bool(self.utilisations.filter(Utilisation.is_open).all())

    @is_open.expression
    def is_open(cls):
        return cls.utilisations.any(Utilisation.is_open)

    @hybrid_property
    def is_waiting(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (classe):
        L'action est ouverte et aucune décision n'a été prise ?

        *I.e.* la clause a au moins une utilisation
        :attr:`~.bdd.UtilEtat.ouverte`.

        Propriété hybride (voir :attr:`.is_open` pour plus d'infos)
        """
        return bool(self.utilisations.filter(Utilisation.is_waiting).all())

    @is_waiting.expression
    def is_waiting(cls):
        return cls.utilisations.any(Utilisation.is_waiting)


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
    ciblages = autodoc_OneToMany("Ciblage", back_populates="utilisation",
        doc="Cibles désignées dans cette utilisation")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Utilisation #{self.id} ({self.action}/{self.etat})>"

    def open(self):
        """Ouvre cette utilisation.

        Modifie son :attr:`etat`, définit :attr:`ts_open` au temps
        actuel, et update.
        """
        self.etat = UtilEtat.ouverte
        self.ts_open = datetime.datetime.now()
        self.update()

    def close(self):
        """Clôture cette utilisation.

        Modifie son :attr:`etat`, définit :attr:`ts_close` au temps
        actuel, et update.
        """
        if self.etat == UtilEtat.remplie:
            self.etat = UtilEtat.validee
        else:
            self.etat = UtilEtat.ignoree
        self.ts_close = datetime.datetime.now()
        self.update()

    def ciblage(self, slug):
        """Renvoie le ciblage de base de slug voulu.

        Args:
            slug (str): Doit correspondre à un des slugs des bases
                des :attr:`ciblages` de l'utilisation.

        Returns:
            :class:`.bdd.Ciblage`

        Raises:
            ValueError: slug non trouvé dans les :attr:`ciblages`
        """
        try:
            return next(cib for cib in self.ciblages if cib.base.slug == slug)
        except StopIteration:
            raise ValueError(
                f"{self} : pas de ciblage de slug '{slug}'"
            ) from None

    @property
    def cible(self):
        """:class:`~bdd.Joueur` | ``None``: Joueur ciblé par l'utilisation,
        si applicable.

        Cet attribut n'est accessible que si l'utilisation est d'un vote
        ou d'une action définissant un et une seul ciblage de type
        :attr:`~bdd.CibleType.joueur`, :attr:`~bdd.CibleType.vivant`
        ou :attr:`~bdd.CibleType.mort`.

        Vaut ``None`` si l'utilisation a l'état
        :attr:`~bdd.UtilEtat.ouverte` ou :attr:`~bdd.UtilEtat.ignoree`.

        Raises:
            ValueError: l'action ne remplit pas les critères évoqués
            ci-dessus
        """
        if self.action.vote:
            # vote : un BaseCiblage implicite de type CibleType.vivants
            return self.ciblages[0].joueur if self.ciblages else None
        else:
            base_ciblages = self.action.base.base_ciblages
            bc_joueurs = [bc for bc in base_ciblages
                          if bc.type in [CibleType.joueur, CibleType.vivant,
                                         CibleType.mort]]
            if len(bc_joueurs) != 1:
                raise ValueError (f"L'utilisation {self} n'a pas une et "
                                  "une seule cible de type joueur")

            base_ciblage = bc_joueurs[0]
            try:
                ciblage = next(cib for cib in self.ciblages
                               if cib.base == base_ciblage)
            except StopIteration:
                return None         # Pas de ciblage fait

            return ciblage.joueur

    @property
    def decision(self):
        """str: Description de la décision de cette utilisation.

        Complète le template de :.bdd.BaseAction.decision_format` avec
        les valeurs des ciblages de l'utilisation.

        Vaut ``"Ne rien faire"`` si l'utilisation n'a pas de ciblages,
        et :attr:`.cible` dans le cas d'un vote.
        """
        if not self.action.base:
            return str(self.cible)

        if not self.ciblages:
            return "Ne rien faire"

        template = self.action.base.decision_format
        data = {ciblage.base.slug: ciblage.valeur_descr
                for ciblage in self.ciblages}
        try:
            return template.format(**data)
        except KeyError:
            return template

    @hybrid_property
    def is_open(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (classe):
        L'utilisation est ouverte (l'utilisateur peut interagir) ?

        Raccourci pour
        ``utilisation.etat in {UtilEtat.ouverte, UtilEtat.remplie}``

        Propriété hybride (voir :attr:`.Action.is_open` pour plus d'infos)
        """
        return (self.etat in {UtilEtat.ouverte, UtilEtat.remplie})

    @is_open.expression
    def is_open(cls):
        return cls.etat.in_({UtilEtat.ouverte, UtilEtat.remplie})

    @hybrid_property
    def is_waiting(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (classe):
        L'utilisation est ouverte et aucune décision n'a été prise ?

        Raccourci pour ``utilisation.etat == UtilEtat.ouverte``

        Propriété hybride (voir :attr:`.Action.is_open` pour plus d'infos)
        """
        return (self.etat == UtilEtat.ouverte)

    @hybrid_property
    def is_filled(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (classe):
        L'utilisation est remplie (l'utilisateur a interagi avec) ?

        Raccourci pour
        ``utilisation.etat in {UtilEtat.remplie, UtilEtat.validee,
        UtilEtat.contree}``

        Propriété hybride (voir :attr:`.Action.is_open` pour plus d'infos)
        """
        return (self.etat in {UtilEtat.remplie, UtilEtat.validee,
                              UtilEtat.contree})

    @is_filled.expression
    def is_filled(cls):
        return cls.etat.in_({UtilEtat.remplie, UtilEtat.validee,
                             UtilEtat.contree})


class Ciblage(base.TableBase):
    """Table de données des cibles désignées dans les utilisations d'actions.

    Les instances sont enregistrées via :meth:`\!action
    <.voter_agir.VoterAgir.VoterAgir.action.callback>` ;
    elles n'ont pas vocation à être supprimées.
    """
    id = autodoc_Column(sqlalchemy.Integer(), primary_key=True,
        doc="Identifiant unique du ciblage, sans signification")

    _base_id = sqlalchemy.Column(sqlalchemy.ForeignKey("baseciblages._id"))
    base = autodoc_ManyToOne("BaseCiblage", back_populates="ciblages",
        nullable=True,
        doc="Modèle de ciblage (lié au modèle d'action). Vaut ``None`` pour "
            "un ciblage de vote")

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

    @property
    def _val_attr(self):
        """Nom de l'attribut stockant la valeur du ciblage"""
        if (not self.base       # vote
            or self.base.type in {CibleType.joueur, CibleType.vivant,
                                  CibleType.mort}):
            return "joueur"
        elif self.base.type == CibleType.role:
            return "role"
        elif self.base.type == CibleType.camp:
            return "camp"
        elif self.base.type == CibleType.booleen:
            return "booleen"
        elif self.base.type == CibleType.texte:
            return "texte"
        else:
            raise ValueError(f"Ciblage de type inconnu : {self.base.type}")

    @property
    def valeur(self):
        """:class:`~bdd.Joueur` | :class:`~bdd.Role`| :class:`~bdd.Camp`
        | :class:`bool` | :class:`str`: Valeur du ciblage, selon son type.

        Propriété en lecture et écriture.

        Raises:
            ValueError: ciblage de type inconnu
        """
        return getattr(self, self._val_attr)

    @valeur.setter
    def valeur(self, value):
        setattr(self, self._val_attr, value)

    @property
    def valeur_descr(self):
        """str: Description de la valeur du ciblage.

        Si :attr:`valeur` vaut ``None``, renvoie ``<N/A>``

        Raises:
            ValueError: ciblage de type inconnu
        """
        if self.valeur is None:
            return "<N/A>"

        if (not self.base       # vote
            or self.base.type in {CibleType.joueur, CibleType.vivant,
                                  CibleType.mort}):
            return self.joueur.nom
        elif self.base.type == CibleType.role:
            return self.role.nom_complet
        elif self.base.type == CibleType.camp:
            return self.camp.nom
        elif self.base.type == CibleType.booleen:
            return "Oui" if self.booleen else "Non"
        else:
            return self.texte


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

    async def send_webhook(self, tries=0):
        """Exécute la tâche (coroutine programmée par :meth:`execute`).

        Envoie un webhook (:obj:`.config.webhook`) de contenu
        :attr:`commande`.

        Si une exception quelconque est levée par l'envoi du webhook,
        re-programme l'exécution de la tâche (:meth:`execute`) 2 secondes
        après ; ce jusqu'à 5 fois, après quoi un message d'alerte est
        envoyé dans :attr:`.config.Channel.logs`.

        Si aucune exception n'est levée (succès), supprime la tâche.

        Args:
            tries (int): Numéro de l'essai d'envoi actuellement en cours
        """
        try:
            await config.webhook.send(self.commande)
        except Exception as exc:
            if tries < 5:
                # On réessaie
                config.loop.call_later(2, self.execute, tries + 1)
            else:
                await config.Channel.logs.send(
                    f"{config.Role.mj.mention} ALERT: impossible  "
                    f"d'envoyer un webhook (5 essais, erreur : "
                    f"```{type(exc).__name__}: {exc})```\n"
                    f"Commande non envoyée : `{self.commande}`"
                )
        else:
            self.delete()

    def execute(self, tries=0):
        """Exécute la tâche planifiée (méthode appellée par la loop).

        Programme :meth:`send_webhook` pour exécution immédiate.

        Args:
            tries (int): Numéro de l'essai d'envoi actuellement en cours,
                passé à :meth:`send_webhook`.
        """
        asyncio.create_task(self.send_webhook(tries=tries))
        # programme la coroutine pour exécution immédiate

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
