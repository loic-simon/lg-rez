"""lg-rez / bdd / Modèle de données

Déclaration de toutes les tables et leurs colonnes

"""

from __future__ import annotations

import datetime
import typing

import discord
import sqlalchemy

from lgrez import config
from lgrez.bdd import base
from lgrez.bdd.base import (
    autodoc_Column,
    autodoc_ManyToOne,
    autodoc_OneToMany,
    autodoc_DynamicOneToMany,
    autodoc_ManyToMany,
)
from lgrez.bdd.enums import ActionTrigger, CibleType

if typing.TYPE_CHECKING:
    from lgrez.bdd import Joueur, Action, Ciblage


# Tables de jonction (pour many-to-manys)

_baseaction_role = sqlalchemy.Table(
    "_baseactions_roles",
    base.TableBase.metadata,
    sqlalchemy.Column("_role_slug", sqlalchemy.ForeignKey("roles.slug")),
    sqlalchemy.Column("_baseaction_slug", sqlalchemy.ForeignKey("baseactions.slug")),
    sqlalchemy.schema.UniqueConstraint("_role_slug", "_baseaction_slug"),
)


# Tables de données


class Role(base.TableBase):
    """Table de données des rôles.

    Cette table est remplie automatiquement à partir du Google Sheet
    "Rôles et actions" par la commande
    :meth:`\!fillroles <.sync.Sync.Sync.fillroles.callback>`.
    """

    slug: str = autodoc_Column(
        sqlalchemy.String(32),
        primary_key=True,
        doc="Identifiant unique du rôle",
    )

    prefixe: str = autodoc_Column(
        sqlalchemy.String(8),
        nullable=False,
        default="",
        doc='Article du nom du rôle (``"Le "``, ``"La "``, ``"L\'"``...)',
    )
    nom: str = autodoc_Column(
        sqlalchemy.String(32),
        nullable=False,
        doc="Nom (avec casse et accents) du rôle",
    )

    _camp_slug = sqlalchemy.Column(
        sqlalchemy.ForeignKey("camps.slug"),
        nullable=False,
    )
    camp: Camp = autodoc_ManyToOne(
        "Camp",
        back_populates="roles",
        doc="Camp auquel ce rôle est affilié à l'origine\n\n (On peut avoir "
        "``joueur.camp != joueur.role.camp`` si damnation, passage MV...)",
    )

    actif: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=True,
        doc="Rôle actif ? (affiché dans la liste des rôles, etc)",
    )

    description_courte: str = autodoc_Column(
        sqlalchemy.String(140),
        nullable=False,
        default="",
        doc="Description du rôle en une ligne",
    )
    description_longue: str = autodoc_Column(
        sqlalchemy.String(1800),
        nullable=False,
        default="",
        doc="Règles et background complets du rôle",
    )

    # to-manys
    joueurs: list[Joueur] = autodoc_OneToMany(
        "Joueur",
        back_populates="role",
        doc="Joueurs ayant ce rôle",
    )
    ciblages: list[Ciblage] = autodoc_DynamicOneToMany(
        "Ciblage",
        back_populates="role",
        doc="Ciblages prenant ce rôle pour cible",
    )
    base_actions: list[BaseAction] = autodoc_ManyToMany(
        "BaseAction",
        secondary=_baseaction_role,
        back_populates="roles",
        doc="Modèles d'actions associées",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<Role '{self.slug}' ({self.prefixe}{self.nom})>"

    def __str__(self) -> str:
        """Return str(self)."""
        return self.nom_complet

    @property
    def nom_complet(self) -> str:
        """Préfixe + nom du rôle"""
        return f"{self.prefixe}{self.nom}"

    @property
    def embed(self) -> discord.Embed:
        """Embed Discord présentant le rôle et ses actions."""
        emb = discord.Embed(
            title=f"**{self.nom_complet}** – {self.description_courte}", description=self.description_longue
        )
        if emoji := self.camp.discord_emoji_or_none:
            emb.set_thumbnail(url=emoji.url)
        for ba in self.base_actions:
            emb.add_field(name=f"{config.Emoji.action} Action : {ba.slug}", value=ba.temporalite)
        return emb

    @classmethod
    def default(cls) -> Role:
        """Retourne le rôle par défaut (celui avant attribution).

        Warning:
            Un rôle de :attr:`.slug` :obj:`.config.default_role_slug`
            doit être défini en base.

        Returns:
            Le rôle par défaut.

        Raises:
            ValueError: rôle introuvable en base
            RuntimeError: session non initialisée
                (:obj:`.config.session` vaut ``None``)
        """
        slug = config.default_role_slug
        role = cls.query.get(slug)
        if not role:
            raise ValueError(
                "Rôle par défaut (de slug "
                f'`lgrez.config.default_role_slug = "{slug}"`) non '
                "défini (dans le GSheet Rôles et actions) "
                "ou non chargé (`!fillroles`) !"
            )
        return role


class Camp(base.TableBase):
    """Table de données des camps, publics et secrets.

    Cette table est remplie automatiquement à partir du Google Sheet
    "Rôles et actions" par la commande
    :meth:`\!fillroles <.sync.Sync.Sync.fillroles.callback>`.
    """

    slug: str = autodoc_Column(
        sqlalchemy.String(32),
        primary_key=True,
        doc="Identifiant unique du camp",
    )

    nom: str = autodoc_Column(
        sqlalchemy.String(32),
        nullable=False,
        doc="Nom (affiché) du camp",
    )
    description: str = autodoc_Column(
        sqlalchemy.String(1000),
        nullable=False,
        default="",
        doc="Description (courte) du camp",
    )

    public: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=True,
        doc="L'existence du camp (et des rôles liés) est connue de tous ?",
    )

    emoji: str | None = autodoc_Column(
        sqlalchemy.String(32),
        doc="Nom de l'emoji associé au camp (doit être le nom d'un emoji existant sur le serveur)",
    )

    # One-to-manys
    joueurs: list[Joueur] = autodoc_OneToMany(
        "Joueur",
        back_populates="camp",
        doc="Joueurs appartenant à ce camp",
    )
    roles: list[Role] = autodoc_OneToMany(
        "Role",
        back_populates="camp",
        doc="Rôles affiliés à ce camp de base",
    )
    ciblages: list[Ciblage] = autodoc_DynamicOneToMany(
        "Ciblage",
        back_populates="camp",
        doc="Ciblages prenant ce camp pour cible",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<Camp '{self.slug}' ({self.nom})>"

    def __str__(self) -> str:
        """Return str(self)."""
        return str(self.nom)

    @property
    def discord_emoji(self) -> discord.Emoji:
        """Emoji Discord correspondant à ce camp

        Raises:
            ValueError: :attr:`.emoji` non défini ou manquant sur le serveur
            ~readycheck.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        if not self.emoji:
            raise ValueError(f"{self}.emoji non défini !")

        try:
            return next(e for e in config.guild.emojis if e.name == self.emoji)
        except StopIteration:
            raise ValueError(f"Pas d'emoji :{self.emoji}: sur le serveur !") from None

    @property
    def discord_emoji_or_none(self) -> discord.Emoji | None:
        """:attr:`.discord_emoji` si défini

        Raises:
            ~readycheck.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        try:
            return self.discord_emoji
        except ValueError:
            return None

    @property
    def embed(self) -> discord.Embed:
        """Embed Discord présentant le camp."""
        emb = discord.Embed(
            title=f"Camp : {self.nom}",
            description=self.description,
            color=0x64B9E9,
        )
        if emoji := self.discord_emoji_or_none:
            emb.set_image(url=emoji.url)
        return emb

    @classmethod
    def default(cls) -> Camp:
        """Retourne le camp par défaut (celui avant attribution).

        Warning:
            Un camp de :attr:`.slug` :obj:`.config.default_camp_slug`
            doit être défini en base.

        Returns:
            Le camp par défaut.

        Raises:
            ValueError: camp introuvable en base
            RuntimeError: session non initialisée
                (:obj:`.config.session` vaut ``None``)
        """
        slug = config.default_camp_slug
        camp = cls.query.get(slug)
        if not camp:
            raise ValueError(
                "Camp par défaut (de slug "
                f'lgrez.config.default_camp_slug = "{slug}") non '
                "défini (dans le GSheet Rôles et actions) ou non "
                f"chargé (`!fillroles`) !"
            )
        return camp


class BaseAction(base.TableBase):
    """Table de données des actions définies de base (non liées à un joueur).

    Cette table est remplie automatiquement à partir du Google Sheet
    "Rôles et actions" par la commande :meth:`\!fillroles
    <.remplissage_bdd.RemplissageBDD.RemplissageBDD.fillroles.callback>`.
    """

    slug: str = autodoc_Column(
        sqlalchemy.String(32),
        primary_key=True,
        doc="Identifiant unique de l'action",
    )

    trigger_debut: ActionTrigger = autodoc_Column(
        sqlalchemy.Enum(ActionTrigger),
        nullable=False,
        default=ActionTrigger.perma,
        doc="Mode de déclenchement de l'ouverture de l'action",
    )
    trigger_fin: ActionTrigger = autodoc_Column(
        sqlalchemy.Enum(ActionTrigger),
        nullable=False,
        default=ActionTrigger.perma,
        doc="Mode de déclenchement de la clôture de l'action",
    )
    instant: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=False,
        doc="L'action est instantannée (conséquence dès la prise de décision),"
        " ou non (conséquence à la fin du créneau d'action)",
    )

    heure_debut: datetime.time | None = autodoc_Column(
        sqlalchemy.Time(),
        doc="Si :attr:`.trigger_debut` vaut :attr:`~ActionTrigger.temporel`, l'horaire associé",
    )
    heure_fin: datetime.time | None = autodoc_Column(
        sqlalchemy.Time(),
        doc="Si :attr:`.trigger_fin` vaut\n,"
        "- :attr:`~ActionTrigger.temporel` : l'horaire associé ;\n"
        "- :attr:`~ActionTrigger.delta`, l'intervalle associé",
    )

    base_cooldown: int = autodoc_Column(
        sqlalchemy.Integer(),
        nullable=False,
        default=0,
        doc="Temps de rechargement entre deux utilisations du pouvoir (``0`` si pas de cooldown)",
    )
    base_charges: int | None = autodoc_Column(
        sqlalchemy.Integer(),
        doc="Nombre de charges initiales du pouvoir (``None`` si illimité)",
    )
    refill: str = autodoc_Column(
        sqlalchemy.String(32),
        nullable=False,
        default="",
        doc="Évènements pouvant recharger l'action, séparés par des virgules ,"
        '(``"weekends"``, ``"forgeron"``, ``"rebouteux"``...)',
    )

    lieu: str | None = autodoc_Column(
        sqlalchemy.String(100),
        doc="*Attribut informatif, non exploité dans la version actuelle ,"
        "(Distance/Physique/Lieu/Contact/Conditionnel/None/Public)*",
    )
    interaction_notaire: str | None = autodoc_Column(
        sqlalchemy.String(100),
        doc="*Attribut informatif, non exploité dans la version actuelle ,"
        "(Oui/Non/Conditionnel/Potion/Rapport ; None si récursif)*",
    )
    interaction_gardien: str | None = autodoc_Column(
        sqlalchemy.String(100),
        doc="*Attribut informatif, non exploité dans la version actuelle ,"
        "(Oui/Non/Conditionnel/Taverne/Feu/MaisonClose/Précis/"
        "Cimetière/Loups ; None si récursif)*",
    )
    mage: str | None = autodoc_Column(
        sqlalchemy.String(100),
        doc="*Attribut informatif, non exploité dans la version actuelle (Oui/Non/Changement de cible/...)*",
    )

    decision_format: str = autodoc_Column(
        sqlalchemy.String(200),
        nullable=False,
        default="",
        doc="Description des utilisations de ces action, sous forme de ,"
        "texte formaté avec les noms des :attr:`.BaseCiblage.slug` "
        "entre accolades (exemple : ``Tuer {cible}``)",
    )

    # -to-manys
    actions: list[Action] = autodoc_OneToMany(
        "Action",
        back_populates="base",
        doc="Actions déroulant de cette base",
    )
    base_ciblages: list[BaseCiblage] = autodoc_OneToMany(
        "BaseCiblage",
        back_populates="base_action",
        cascade="all, delete-orphan",
        order_by="BaseCiblage.prio",
        doc="Ciblages de ce modèle d'action (triés par priorité)",
    )
    roles: list[Role] = autodoc_ManyToMany(
        "Role",
        secondary=_baseaction_role,
        back_populates="base_actions",
        doc="Rôles ayant cette action de base",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<BaseAction '{self.slug}'>"

    def __str__(self) -> str:
        """Return str(self)."""
        return str(self.slug)

    @property
    def temporalite(self) -> str:
        """Phrase décrivant le mode d'utilisation / timing de l'action."""

        def _time_to_heure(tps):
            if not tps:
                return ""
            if tps.hour == 0:
                return f"{tps.minute} min"
            if tps.minute > 0:
                return f"{tps.hour}h{tps.minute:02}"
            return f"{tps.hour}h"

        rep = ""
        # Périodicité
        if self.trigger_debut == ActionTrigger.perma:
            rep += "N'importe quand"
        elif self.trigger_debut == ActionTrigger.start:
            rep += "Au lancement de la partie"
        elif self.trigger_debut == ActionTrigger.mort:
            rep += "À la mort"
        else:
            if self.base_cooldown:
                rep += f"Tous les {self.base_cooldown + 1} jours "
            else:
                rep += "Tous les jours "

            # Fenêtre
            if self.trigger_debut == ActionTrigger.mot_mjs:
                rep += "à l'annonce des résultats du vote"
            elif self.trigger_debut == ActionTrigger.open_cond:
                rep += "pendant le vote condamné"
            elif self.trigger_debut == ActionTrigger.open_maire:
                rep += "pendant le vote pour le maire"
            elif self.trigger_debut == ActionTrigger.open_loups:
                rep += "pendant le vote des loups"
            elif self.trigger_debut == ActionTrigger.close_cond:
                rep += "à la fermeture du vote condamné"
            elif self.trigger_debut == ActionTrigger.close_maire:
                rep += "à la fermeture du vote pour le maire"
            elif self.trigger_debut == ActionTrigger.close_loups:
                rep += "à la fermeture du vote des loups"
            elif self.trigger_debut == ActionTrigger.temporel:
                if self.trigger_fin == ActionTrigger.temporel:
                    rep += f"de {_time_to_heure(self.heure_debut)}"
                else:
                    rep += f"à {_time_to_heure(self.heure_debut)}"

        # Fermeture
        if self.trigger_fin == ActionTrigger.delta:
            rep += f" – {_time_to_heure(self.heure_fin)} pour agir"
        elif self.trigger_fin == ActionTrigger.temporel:
            rep += f" à {_time_to_heure(self.heure_fin)}"

        # Autres caractères
        if self.instant:
            rep += f" (conséquence instantanée)"
        if self.base_charges:
            rep += f" – {self.base_charges} fois"
        if "weekends" in self.refill:
            rep += f" par semaine"

        return rep


class BaseCiblage(base.TableBase):
    """Table de données des modèles de ciblages des actions de base.

    Cette table est remplie automatiquement à partir du Google Sheet
    "Rôles et actions" par la commande :meth:`\!fillroles
    <.remplissage_bdd.RemplissageBDD.RemplissageBDD.fillroles.callback>`.
    """

    id: int = autodoc_Column(
        sqlalchemy.Integer(),
        primary_key=True,
        doc="Identifiant unique du modèle de ciblage, sans signification",
    )

    _baseaction_slug = sqlalchemy.Column(
        sqlalchemy.ForeignKey("baseactions.slug"),
        nullable=False,
    )
    base_action: BaseAction = autodoc_ManyToOne(
        "BaseAction",
        back_populates="base_ciblages",
        doc="Modèle d'action définissant ce ciblage",
    )

    slug: str = autodoc_Column(
        sqlalchemy.String(32),
        nullable=False,
        default="unique",
        doc="Identifiant de la cible dans le modèle d'action",
    )
    type: CibleType = autodoc_Column(
        sqlalchemy.Enum(CibleType),
        nullable=False,
        default=CibleType.texte,
        doc="Message d'interaction au joueur au moment de choisir la cible",
    )

    prio: int = autodoc_Column(
        sqlalchemy.Integer(),
        nullable=False,
        default=1,
        doc="Ordre (relatif) d'apparition du ciblage lors du ``!action`` ,"
        "\n\nSi deux ciblages ont la même priorité, ils seront considérés "
        "comme ayant une signification symétrique (notamment, si "
        ":attr:`doit_changer` vaut ``True``, tous les membres du groupe "
        "devront changer) ; l'ordre d'apparition dépend alors de leur "
        ":attr:`slug`, par ordre alphabétique (``cible1`` < ``cible2``).",
    )

    phrase: str = autodoc_Column(
        sqlalchemy.String(1000),
        nullable=False,
        default="Cible ?",
        doc="Message d'interaction au joueur au moment de choisir la cible",
    )

    obligatoire: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=True,
        doc="Si le ciblage doit obligatoirement être renseigné",
    )
    doit_changer: bool = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=False,
        doc="Si la cible doit changer d'une utilisation à l'autre.\n\n,"
        "Si la dernière utilisation est ignorée ou contrée, il n'y a "
        "pas de contrainte.",
    )

    # one-to-manys
    ciblages: list[Ciblage] = autodoc_DynamicOneToMany(
        "Ciblage",
        back_populates="base",
        doc="Ciblages déroulant de cette base",
    )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<BaseCiblage #{self.id} ({self.base_action}/{self.slug})>"
