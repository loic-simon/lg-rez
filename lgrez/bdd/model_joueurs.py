"""lg-rez / bdd / Modèle de données

Déclaration de toutes les tables et leurs colonnes

"""

import datetime

import sqlalchemy
from sqlalchemy.ext.hybrid import hybrid_property

from lgrez import config
from lgrez.bdd import base
from lgrez.bdd.base import (autodoc_Column, autodoc_ManyToOne,
                            autodoc_OneToMany, autodoc_DynamicOneToMany)
from lgrez.bdd.enums import Statut, CandidHaroType, Vote


# Tables de données

class Joueur(base.TableBase):
    """Table de données des joueurs inscrits.

    Les instances de cette classe correspondent aux lignes du Tableau de
    bord ; elles sont crées par l'inscription (:func:`.inscription.main`)
    et synchronisées par :meth:`\!sync <.sync.Sync.Sync.sync.callback>`.
    """
    discord_id = autodoc_Column(sqlalchemy.BigInteger(), primary_key=True,
        autoincrement=False, doc="ID Discord du joueur")
    chan_id_ = autodoc_Column(sqlalchemy.BigInteger(), nullable=False,
        doc="ID du chan privé Discord du joueur. *(le ``_`` final indique "
            "que ce champ n'est pas synchnisé avec le Tableau de bord)*")

    nom = autodoc_Column(sqlalchemy.String(32), nullable=False,
        doc="Nom du joueur (demandé à l'inscription)")
    chambre = autodoc_Column(sqlalchemy.String(200),
        doc="Emplacement du joueur (demandé à l'inscription)")
    statut = autodoc_Column(sqlalchemy.Enum(Statut), nullable=False,
        default=Statut.vivant, doc="Statut RP")

    _role_slug = sqlalchemy.Column(sqlalchemy.ForeignKey("roles.slug"),
        nullable=False, default=lambda: config.default_role_slug)
    role = autodoc_ManyToOne("Role", back_populates="joueurs",
        doc="Rôle du joueur (défaut :meth:`.bdd.Role.default`)")

    _camp_slug = sqlalchemy.Column(sqlalchemy.ForeignKey("camps.slug"),
        nullable=False, default=lambda: config.default_camp_slug)
    camp = autodoc_ManyToOne("Camp", back_populates="joueurs",
        doc="Camp du joueur (défaut :meth:`.bdd.Camp.default`)")

    votant_village = autodoc_Column(sqlalchemy.Boolean(), nullable=False,
        default=True, doc="Le joueur participe aux votes du village ?")
    votant_loups = autodoc_Column(sqlalchemy.Boolean(), nullable=False,
        default=False, doc="Le joueur participe au vote des loups ?")
    role_actif = autodoc_Column(sqlalchemy.Boolean(), nullable=False,
        default=True, doc="Le joueur peut agir ? (pas chatgarouté...)")

    # One-to-manys
    actions = autodoc_OneToMany("Action", back_populates="joueur",
        doc="Actions pour ce joueur")
    candidharos = autodoc_OneToMany("CandidHaro", back_populates="joueur",
        doc="Candidatures et haros de/contre ce joueur")
    bouderies = autodoc_OneToMany("Bouderie", back_populates="joueur",
        doc="Appartenances aux boudoirs de ce joueur")
    ciblages = autodoc_DynamicOneToMany("Ciblage", back_populates="joueur",
        doc="Ciblages prenant ce joueur pour cible")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Joueur #{self.discord_id} ({self.nom})>"

    def __str__(self):
        """Return str(self)."""
        return str(self.nom)

    @property
    def member(self):
        """discord.Member: Membre Discord correspondant à ce Joueur.

        Raises:
            ValueError: pas de membre correspondant
            ~ready_check.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        result = config.guild.get_member(self.discord_id)
        if not result:
            raise ValueError(f"Joueur.member : pas de membre pour `{self}` !")

        return result

    @property
    def private_chan(self):
        """discord.TextChannel: Channel privé (conversation bot) du joueur.

        Raises:
            ValueError: pas de channel correspondant
            ~ready_check.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        result = config.guild.get_channel(self.chan_id_)
        if not result:
            raise ValueError("Joueur.private_chan : "
                             f"pas de chan pour `{self}` !")

        return result

    @property
    def actions_actives(self):
        """Sequence[.bdd.Action]: Sous-ensemble de :attr:`actions` restreint
        aux actions actives.

        Élimine aussi les actions de vote (sans base).
        """
        return [ac for ac in self.actions if ac.active and not ac.vote]

    @property
    def boudoirs(self):
        """Sequence[.Boudoir]: Boudoirs où est ce jour (read-only)"""
        return [boud.boudoir for boud in self.bouderies]

    @hybrid_property
    def est_vivant(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (classe):
        Le joueur est en vie ou MVtisé ?

        Raccourci pour
        ``joueur.statut in {Statut.vivant, Statut.MV}``

        Propriété hybride (voir :attr:`.Action.is_open` pour plus d'infos)
        """
        return (self.statut in {Statut.vivant, Statut.MV})

    @est_vivant.expression
    def est_vivant(cls):
        return cls.statut.in_({Statut.vivant, Statut.MV})

    @hybrid_property
    def est_mort(self):
        """:class:`bool` (instance)
        / :class:`sqlalchemy.sql.selectable.Exists` (classe):
        Le joueur est mort ?

        Raccourci pour ``joueur.statut == Statut.mort``

        Propriété hybride (voir :attr:`.Action.is_open` pour plus d'infos)
        """
        return (self.statut == Statut.mort)

    @classmethod
    def from_member(cls, member):
        """Récupère le Joueur (instance de BDD) lié à un membre Discord.

        Args:
            member (discord.Member): le membre concerné

        Returns:
            Joueur: Le joueur correspondant.

        Raises:
            ValueError: membre introuvable en base
            ~ready_check.NotReadyError: session non initialisée
                (:obj:`.config.session` vaut ``None``)
        """
        joueur = cls.query.get(member.id)
        if not joueur:
            raise ValueError("Joueur.from_member : "
                             f"pas de joueur en base pour `{member}` !")

        return joueur

    def action_vote(self, vote):
        """Retourne l'"action de vote" voulue pour ce joueur.

        Args:
            vote (.bdd.Vote): vote pour lequel récupérer l'action

        Returns:
            :class:`~bdd.Action`

        Raises:
            RuntimeError: action non existante
        """
        if not isinstance(vote, Vote):
            vote = Vote[vote]
        try:
            return next(act for act in self.actions if act.vote == vote)
        except StopIteration:
            raise RuntimeError(f"{self} : pas d'action de vote {vote.name} ! "
                               "!cparti a bien été appelé ?") from None


class CandidHaro(base.TableBase):
    """Table de données des candidatures et haros en cours #PhilippeCandidHaro.

    Les instances sont enregistrées via :meth:`\!haro
    <.actions_publiques.ActionsPubliques.ActionsPubliques.haro.callback>`
    / :meth:`\!candid
    <.actions_publiques.ActionsPubliques.ActionsPubliques.candid.callback>`
    et supprimées via :meth:`\!wipe
    <.actions_publiques.ActionsPubliques.ActionsPubliques.wipe.callback>`.
    """
    id = autodoc_Column(sqlalchemy.Integer(), primary_key=True,
        doc="Identifiant unique du candidharo, sans signification")

    _joueur_id = sqlalchemy.Column(sqlalchemy.ForeignKey("joueurs.discord_id"),
        nullable=False)
    joueur = autodoc_ManyToOne("Joueur", back_populates="candidharos",
        doc="Joueur concerné (candidat ou haroté)")

    type = autodoc_Column(sqlalchemy.Enum(CandidHaroType), nullable=False,
        doc="Haro ou candidature ?")

    def __repr__(self):
        """Return repr(self)."""
        return f"<CandidHaro #{self.id} ({self.joueur}/{self.type})>"


class Boudoir(base.TableBase):
    """Table de données des boudoirs sur le serveur.

    Les instances de cette classe sont crées, modifiées et supprimées par
    :meth:`\!boudoir <.chans.GestionChans.GestionChans.boudoir.callback>`.
    """
    chan_id = autodoc_Column(sqlalchemy.BigInteger(), primary_key=True,
        autoincrement=False, doc="ID Discord du salon")

    nom = autodoc_Column(sqlalchemy.String(32), nullable=False,
        doc="Nom du boudoir (demandé à la création)")
    ts_created = autodoc_Column(sqlalchemy.DateTime(), nullable=False,
        doc="Timestamp de la création")

    # One-to-manys
    bouderies = autodoc_OneToMany("Bouderie", back_populates="boudoir",
        doc="Appartenances à ce boudoir")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Boudoir #{self.chan_id} ({self.nom})>"

    @property
    def chan(self):
        """discord.TextChannel: Salon Discord correspondant à ce boudoir.

        Raises:
            ValueError: pas de membre correspondant
            ~ready_check.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        result = config.guild.get_channel(self.chan_id)
        if not result:
            raise ValueError(f"Boudoir.chan : pas de chan pour {self} !")

        return result

    @property
    def joueurs(self):
        """Sequence[.Joueur]: Joueurs présents dans ce boudoir (read-only)"""
        return [boud.joueur for boud in self.bouderies]

    @property
    def gerant(self):
        """.bdd.Joueur: Membre du boudoir ayant les droits de gestion.

        Raises:
            ValueError: pas de membre avec les droits de gestion
        """
        try:
            return next(boud.joueur for boud in self.bouderies if boud.gerant)
        except StopIteration:
            raise ValueError(f"Pas de membre gérant le boudoir *{self.name}*")

    async def add_joueur(self, joueur, gerant=False):
        """Ajoute un joueur sur le boudoir.

        Crée la :class:`.Bouderie` correspondante et modifie les
        permissions du salon.

        Args:
            joueur (.Joueur): Le joueur à ajouter.
            gerant (bool): Si le joueur doit être ajouté avec les
                permissions de gérant.
        """
        now = datetime.datetime.now()
        Bouderie(boudoir=self, joueur=joueur, gerant=gerant,
                 ts_added=now, ts_promu=now if gerant else None).add()
        await self.chan.set_permissions(joueur.member, read_messages=True)

    async def remove_joueur(self, joueur):
        """Retire un joueur du boudoir.

        Supprime la :class:`.Bouderie` correspondante et modifie les
        permissions du salon.

        Args:
            joueur (.Joueur): Le joueur à ajouter.
        """
        Bouderie.query.filter_by(boudoir=self, joueur=joueur).one().delete()
        await self.chan.set_permissions(joueur.member, overwrite=None)

    @classmethod
    def from_channel(cls, channel):
        """Récupère le Boudoir (instance de BDD) lié à un salon Discord.

        Args:
            channel (discord.TextChannel): le salon concerné

        Returns:
            .Boudoir: Le salon correspondant.

        Raises:
            ValueError: boudoir introuvable en base
            ~ready_check.NotReadyError: session non initialisée
                (:obj:`.config.session` vaut ``None``)
        """
        boudoir = cls.query.get(channel.id)
        if not boudoir:
            raise ValueError("Boudoir.from_channel : "
                             f"pas de boudoir en base pour `{channel.mention}` !")

        return boudoir


class Bouderie(base.TableBase):
    """Table de données des appartenances aux boudoirs du serveur.

    Table d'association entre :class:`.Joueur` et :class:`.Boudoir`.

    Les instances de cette classe sont crées, modifiées et supprimées par
    :meth:`\!boudoir <.chans.GestionChans.GestionChans.boudoir.callback>`.
    """
    id = autodoc_Column(sqlalchemy.Integer(), primary_key=True,
        doc="Identifiant unique de la bouderie, sans signification")

    _joueur_id = sqlalchemy.Column(sqlalchemy.ForeignKey("joueurs.discord_id"),
        nullable=False)
    joueur = autodoc_ManyToOne("Joueur", back_populates="bouderies",
        doc="Joueur concerné")

    _boudoir_id = sqlalchemy.Column(sqlalchemy.ForeignKey("boudoirs.chan_id"),
        nullable=False)
    boudoir = autodoc_ManyToOne("Boudoir", back_populates="bouderies",
        doc="Boudoir concerné")

    gerant = autodoc_Column(sqlalchemy.Boolean(), nullable=False,
        default=False,
        doc="Si le joueur a les droits de gestion du boudoir")

    ts_added = autodoc_Column(sqlalchemy.DateTime(), nullable=False,
        doc="Timestamp de l'ajout du joueur au boudoir")
    ts_promu = autodoc_Column(sqlalchemy.DateTime(),
        doc="Timestamp de la promotion en gérant, le cas échéant")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Bouderie #{self.id} ({self.joueur}/{self.boudoir})>"
