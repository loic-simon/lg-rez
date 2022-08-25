"""lg-rez / bdd / Modèle de données

Déclaration de toutes les tables et leurs colonnes

"""

from __future__ import annotations

import datetime
import typing

import discord
import sqlalchemy
from sqlalchemy.ext.hybrid import hybrid_property

from lgrez import config
from lgrez.bdd import base
from lgrez.bdd.base import autodoc_Column, autodoc_ManyToOne, autodoc_OneToMany, autodoc_DynamicOneToMany
from lgrez.bdd.enums import Statut, CandidHaroType, Vote
from lgrez.blocs import tools

if typing.TYPE_CHECKING:
    from lgrez.bdd import Role, Camp, Action, Ciblage


# Tables de données


class Joueur(base.TableBase):
    """Table de données des joueurs inscrits.

    Les instances de cette classe correspondent aux lignes du Tableau de
    bord ; elles sont crées par l'inscription (:func:`.inscription.main`)
    et synchronisées par :meth:`\!sync <.sync.Sync.Sync.sync.callback>`.
    """

    discord_id: int = autodoc_Column(
        sqlalchemy.BigInteger(),
        primary_key=True,
        autoincrement=False,
        doc="ID Discord du joueur",
    )
    chan_id_: int = autodoc_Column(
        sqlalchemy.BigInteger(),
        nullable=False,
        doc="ID du chan privé Discord du joueur. *(le ``_`` final indique ,"
        "que ce champ n'est pas synchronisé avec le Tableau de bord)*",
    )

    nom: str = autodoc_Column(
        sqlalchemy.String(32),
        nullable=False,
        doc="Nom du joueur (demandé à l'inscription)",
    )
    chambre: str | None = autodoc_Column(
        sqlalchemy.String(200),
        doc="Emplacement du joueur (demandé à l'inscription)",
    )
    statut: Statut = autodoc_Column(
        sqlalchemy.Enum(Statut),
        nullable=False,
        default=Statut.vivant,
        doc="Statut RP",
    )

    _role_slug = sqlalchemy.Column(
        sqlalchemy.ForeignKey("roles.slug"),
        nullable=False,
        default=lambda: config.default_role_slug,
    )
    role: Role = autodoc_ManyToOne(
        "Role",
        back_populates="joueurs",
        doc="Rôle du joueur (défaut :meth:`.bdd.Role.default`)",
    )

    _camp_slug = sqlalchemy.Column(
        sqlalchemy.ForeignKey("camps.slug"),
        nullable=False,
        default=lambda: config.default_camp_slug,
    )
    camp: Camp = autodoc_ManyToOne(
        "Camp",
        back_populates="joueurs",
        doc="Camp du joueur (défaut :meth:`.bdd.Camp.default`)",
    )

    votant_village: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=True,
        doc="Le joueur participe aux votes du village ?",
    )
    votant_loups: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=False,
        doc="Le joueur participe au vote des loups ?",
    )
    role_actif: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=True,
        doc="Le joueur peut agir ? (pas chatgarouté...)",
    )

    # One-to-manys
    actions: list[Action] = autodoc_OneToMany(
        "Action",
        back_populates="joueur",
        doc="Actions pour ce joueur",
    )
    candidharos: list[CandidHaro] = autodoc_OneToMany(
        "CandidHaro",
        back_populates="joueur",
        doc="Candidatures et haros de/contre ce joueur",
    )
    bouderies: list[Bouderie] = autodoc_OneToMany(
        "Bouderie",
        back_populates="joueur",
        doc="Appartenances aux boudoirs de ce joueur",
    )
    ciblages: list[Ciblage] = autodoc_DynamicOneToMany(
        "Ciblage",
        back_populates="joueur",
        doc="Ciblages prenant ce joueur pour cible",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<Joueur #{self.discord_id} ({self.nom})>"

    def __str__(self) -> str:
        """Return str(self)."""
        return str(self.nom)

    @property
    def member(self) -> discord.Member:
        """Membre Discord correspondant à ce Joueur.

        Raises:
            ValueError: pas de membre correspondant
            ~readycheck.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        result = config.guild.get_member(self.discord_id)
        if not result:
            raise ValueError(f"Joueur.member : pas de membre pour `{self}` !")

        return result

    @property
    def private_chan(self) -> discord.TextChannel:
        """Channel privé (conversation bot) du joueur.

        Raises:
            ValueError: pas de channel correspondant
            ~readycheck.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        result = config.guild.get_channel(self.chan_id_)
        if not result:
            raise ValueError("Joueur.private_chan : " f"pas de chan pour `{self}` !")

        return result

    @property
    def actions_actives(self) -> list[Action]:
        """Sous-ensemble de :attr:`actions` restreint aux actions actives.

        Élimine aussi les actions de vote (sans base).
        """
        return [ac for ac in self.actions if ac.active and not ac.vote]

    @property
    def boudoirs(self) -> list[Boudoir]:
        """Boudoirs où est ce jour (read-only)"""
        return [boud.boudoir for boud in self.bouderies]

    @hybrid_property
    def est_vivant(self) -> bool:
        """Le joueur est en vie ou MVtisé ?

        Raccourci pour
        ``joueur.statut in {Statut.vivant, Statut.MV}``

        Propriété hybride (voir :attr:`.Action.is_open` pour plus d'infos)
        """
        return self.statut in {Statut.vivant, Statut.MV}

    @est_vivant.expression
    def est_vivant(cls) -> sqlalchemy.sql.selectable.Exists:
        return cls.statut.in_({Statut.vivant, Statut.MV})

    @hybrid_property
    def est_mort(self) -> bool:
        """Le joueur est mort ?

        Raccourci pour ``joueur.statut == Statut.mort``

        Propriété hybride (voir :attr:`.Action.is_open` pour plus d'infos)
        """
        return self.statut == Statut.mort

    @est_mort.expression
    def est_mort(cls) -> sqlalchemy.sql.selectable.Exists:
        return cls.statut == Statut.mort

    @classmethod
    def from_member(cls, member: discord.Member) -> Joueur:
        """Récupère le Joueur (instance de BDD) lié à un membre Discord.

        Args:
            member: le membre concerné.

        Returns:
            Le joueur correspondant.

        Raises:
            ValueError: membre introuvable en base
            ~readycheck.NotReadyError: session non initialisée
                (:obj:`.config.session` vaut ``None``)
        """
        joueur = cls.query.get(member.id)
        if not joueur:
            raise ValueError("Joueur.from_member : " f"pas de joueur en base pour `{member}` !")

        return joueur

    def action_vote(self, vote: Vote) -> Action:
        """Retourne l'"action de vote" voulue pour ce joueur.

        Args:
            vote: vote pour lequel récupérer l'action.

        Returns:
            L'action permettant au joueur de voter.

        Raises:
            RuntimeError: action non existante
        """
        if not isinstance(vote, Vote):
            vote = Vote[vote]
        try:
            return next(act for act in self.actions if act.vote == vote)
        except StopIteration:
            raise RuntimeError(f"{self} : pas d'action de vote {vote.name} ! ``!cparti`` a bien été appelé ?") from None


class CandidHaro(base.TableBase):
    """Table de données des candidatures et haros en cours #PhilippeCandidHaro.

    Les instances sont enregistrées via :meth:`\!haro
    <.actions_publiques.ActionsPubliques.ActionsPubliques.haro.callback>`
    / :meth:`\!candid
    <.actions_publiques.ActionsPubliques.ActionsPubliques.candid.callback>`
    et supprimées via :meth:`\!wipe
    <.actions_publiques.ActionsPubliques.ActionsPubliques.wipe.callback>`.
    """

    id: int = autodoc_Column(
        sqlalchemy.Integer(),
        primary_key=True,
        doc="Identifiant unique du candidharo, sans signification",
    )

    _joueur_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey("joueurs.discord_id"),
        nullable=False,
    )
    joueur: Joueur = autodoc_ManyToOne(
        "Joueur",
        back_populates="candidharos",
        doc="Joueur concerné (candidat ou haroté)",
    )

    type: CandidHaroType = autodoc_Column(
        sqlalchemy.Enum(CandidHaroType),
        nullable=False,
        doc="Haro ou candidature ?",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<CandidHaro #{self.id} ({self.joueur}/{self.type})>"


class Boudoir(base.TableBase):
    """Table de données des boudoirs sur le serveur.

    Les instances de cette classe sont crées, modifiées et supprimées par
    :meth:`\!boudoir <.chans.GestionChans.GestionChans.boudoir.callback>`.
    """

    chan_id: int = autodoc_Column(
        sqlalchemy.BigInteger(),
        primary_key=True,
        autoincrement=False,
        doc="ID Discord du salon",
    )

    nom: str = autodoc_Column(
        sqlalchemy.String(32),
        nullable=False,
        doc="Nom du boudoir (demandé à la création)",
    )
    ts_created: datetime.datetime = autodoc_Column(
        sqlalchemy.DateTime(),
        nullable=False,
        doc="Timestamp de la création",
    )

    # One-to-manys
    bouderies: list[Bouderie] = autodoc_OneToMany(
        "Bouderie",
        back_populates="boudoir",
        doc="Appartenances à ce boudoir",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<Boudoir #{self.chan_id} ({self.nom})>"

    @property
    def chan(self) -> discord.TextChannel:
        """Salon Discord correspondant à ce boudoir.

        Raises:
            ValueError: pas de membre correspondant
            ~readycheck.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        result = config.guild.get_channel(self.chan_id)
        if not result:
            raise ValueError(f"Boudoir.chan : pas de chan pour {self} !")

        return result

    @property
    def joueurs(self) -> list[Joueur]:
        """Joueurs présents dans ce boudoir (read-only)"""
        return [bouderie.joueur for bouderie in self.bouderies]

    @property
    def gerant(self) -> Joueur:
        """Membre du boudoir ayant les droits de gestion.

        Raises:
            ValueError: pas de membre avec les droits de gestion
        """
        try:
            return next(bouderie.joueur for bouderie in self.bouderies if bouderie.gerant)
        except StopIteration:
            raise ValueError(f"Pas de membre gérant le boudoir *{self.nom}*")

    async def add_joueur(self, joueur: Joueur, gerant: bool = False) -> bool:
        """Ajoute un joueur sur le boudoir.

        Crée la :class:`.Bouderie` correspondante et modifie les
        permissions du salon.

        Args:
            joueur: Le joueur à ajouter.
            gerant: Si le joueur doit être ajouté avec les
                permissions de gérant.

        Returns:
            ``True`` si le joueur a été ajouté, ``False`` si il y était
            déjà / le boudoir est fermé.
        """
        if joueur in self.joueurs:
            # Joueur déjà dans le boudoir
            return False
        if not self.joueurs and not gerant:
            # Boudoir fermé (plus de joueurs) et pas ajout comme gérant
            return False

        now = datetime.datetime.now()
        Bouderie(boudoir=self, joueur=joueur, gerant=gerant, ts_added=now, ts_promu=now if gerant else None).add()
        await self.chan.set_permissions(joueur.member, read_messages=True)

        # Sortie du cimetière le cas échéant
        if tools.in_multicateg(self.chan.category, config.old_boudoirs_category_name):
            await self.chan.send(tools.ital("[Ce boudoir contient au moins deux joueurs vivants, désarchivage...]"))
            categ = await tools.multicateg(config.boudoirs_category_name)
            await self.chan.edit(category=categ)
        return True

    async def remove_joueur(self, joueur: Joueur) -> None:
        """Retire un joueur du boudoir.

        Supprime la :class:`.Bouderie` correspondante et modifie les
        permissions du salon.

        Args:
            joueur: Le joueur à ajouter.
        """
        Bouderie.query.filter_by(boudoir=self, joueur=joueur).one().delete()
        await self.chan.set_permissions(joueur.member, overwrite=None)
        # Déplacement dans le cimetière si nécessaire
        vivants = [jr for jr in self.joueurs if jr.est_vivant]
        if len(vivants) < 2:
            if tools.in_multicateg(self.chan.category, config.old_boudoirs_category_name):
                # Boudoir déjà au cimetière
                return
            await self.chan.send(tools.ital("[Ce boudoir contient moins de deux joueurs vivants, archivage...]"))
            categ = await tools.multicateg(config.old_boudoirs_category_name)
            await self.chan.edit(category=categ)

    @classmethod
    def from_channel(cls, channel: discord.TextChannel) -> Boudoir:
        """Récupère le Boudoir (instance de BDD) lié à un salon Discord.

        Args:
            channel: le salon concerné.

        Returns:
            Le salon correspondant.

        Raises:
            ValueError: boudoir introuvable en base
            ~readycheck.NotReadyError: session non initialisée
                (:obj:`.config.session` vaut ``None``)
        """
        boudoir = cls.query.get(channel.id)
        if not boudoir:
            raise ValueError("Boudoir.from_channel : " f"pas de boudoir en base pour `{channel.mention}` !")

        return boudoir


class Bouderie(base.TableBase):
    """Table de données des appartenances aux boudoirs du serveur.

    Table d'association entre :class:`.Joueur` et :class:`.Boudoir`.

    Les instances de cette classe sont crées, modifiées et supprimées par
    :meth:`\!boudoir <.chans.GestionChans.GestionChans.boudoir.callback>`.
    """

    id: int = autodoc_Column(
        sqlalchemy.Integer(),
        primary_key=True,
        doc="Identifiant unique de la bouderie, sans signification",
    )

    _joueur_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey("joueurs.discord_id"),
        nullable=False,
    )
    joueur: Joueur = autodoc_ManyToOne(
        "Joueur",
        back_populates="bouderies",
        doc="Joueur concerné",
    )

    _boudoir_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey("boudoirs.chan_id"),
        nullable=False,
    )
    boudoir: Boudoir = autodoc_ManyToOne(
        "Boudoir",
        back_populates="bouderies",
        doc="Boudoir concerné",
    )

    gerant: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=False,
        doc="Si le joueur a les droits de gestion du boudoir",
    )

    ts_added: datetime.datetime = autodoc_Column(
        sqlalchemy.DateTime(),
        nullable=False,
        doc="Timestamp de l'ajout du joueur au boudoir",
    )
    ts_promu: datetime.datetime | None = autodoc_Column(
        sqlalchemy.DateTime(),
        doc="Timestamp de la promotion en gérant, le cas échéant",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<Bouderie #{self.id} ({self.joueur}/{self.boudoir})>"
