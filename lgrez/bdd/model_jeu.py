"""lg-rez / bdd / Modèle de données

Déclaration de toutes les tables et leurs colonnes

"""

import sqlalchemy

from lgrez import config
from lgrez.bdd import base
from lgrez.bdd.base import (autodoc_Column, autodoc_ManyToOne,
                            autodoc_OneToMany, autodoc_ManyToMany)
from lgrez.bdd.enums import ActionTrigger


# Tables de jonction (pour many-to-manys)

_baseaction_role = sqlalchemy.Table('_baseactions_roles',
    base.TableBase.metadata,
    sqlalchemy.Column('_role_slug', sqlalchemy.ForeignKey('roles.slug')),
    sqlalchemy.Column('_baseaction_slug',
                      sqlalchemy.ForeignKey('baseactions.slug'))
)


# Tables de données

class Role(base.TableBase):
    """Table de données des rôles.

    Cette table est remplie automatiquement à partir du Google Sheet
    "Rôles et actions" par la commande
    :meth:`\!fillroles <.sync.Sync.Sync.fillroles.callback>`.
    """
    slug = autodoc_Column(sqlalchemy.String(32), primary_key=True,
        doc="Identifiant unique du rôle")

    prefixe = autodoc_Column(sqlalchemy.String(8), nullable=False,
        doc="Article du nom du rôle (``\"Le \"``, ``\"La \"``, ``\"L'\"``...)")
    nom = autodoc_Column(sqlalchemy.String(32), nullable=False,
        doc="Nom (avec casse et accents) du rôle")

    _camp_slug = sqlalchemy.Column(sqlalchemy.ForeignKey("camps.slug"),
        nullable=False)
    camp = autodoc_ManyToOne("Camp", back_populates="roles",
        doc="Camp auquel ce rôle est affilié à l'origine\n\n (On peut avoir "
            "``joueur.camp != joueur.role.camp`` si damnation, passage MV...)")

    description_courte = autodoc_Column(sqlalchemy.String(140), nullable=False,
        doc="Description du rôle en une ligne")
    description_longue = autodoc_Column(sqlalchemy.String(2000),
        doc="Règles et background complets du rôle")

    # to-manys
    joueurs = autodoc_OneToMany("Joueur", back_populates="role",
        doc="Joueurs ayant ce rôle")
    base_actions = autodoc_ManyToMany("BaseAction", secondary=_baseaction_role,
        back_populates="roles",
        doc="Modèles d'actions associées")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Role '{self.slug}' ({self.prefixe}{self.nom})>"

    @property
    def nom_complet(self):
        """str: Préfixe + nom du rôle"""
        return f"{self.prefixe}{self.nom}"

    @classmethod
    def default(cls):
        """Retourne le rôle par défaut (non attribué).

        Warning:
            Un rôle de :attr:`.slug` ``"nonattr"`` doit être défini en base.

        Returns:
            ~bdd.Role

        Raises:
            ValueError: rôle ``"nonattr"`` introuvable en base
            RuntimeError: session non initialisée
                (:attr:`.config.session` vaut ``None``)
        """
        role = cls.query.get("nonattr")
        if not role:
            raise ValueError("Pas de rôle pas défaut (`nonattr`) !")
        return role


class Camp(base.TableBase):
    """Table de données des camps, publics et secrets.

    [À FAIRE ==>] Cette table est remplie automatiquement à partir du
    Google Sheet "Rôles et actions" par la commande
    :meth:`\!fillroles <.sync.Sync.Sync.fillroles.callback>`.
    """
    slug = autodoc_Column(sqlalchemy.String(32), primary_key=True,
        doc="Identifiant unique du camp")

    nom = autodoc_Column(sqlalchemy.String(32), nullable=False,
        doc="Nom (affiché) du camp")
    description = autodoc_Column(sqlalchemy.String(140), nullable=False,
        doc="Description (courte) du camp")

    public = autodoc_Column(sqlalchemy.Boolean(), nullable=False, default=True,
        doc="L'existance du camp (et des rôles liés) est connue de tous ?")

    emoji = autodoc_Column(sqlalchemy.String(32),
        doc="Nom de l'emoji associé au camp (doit être le nom d'un "
            "emoji existant sur le serveur)")

    # One-to-manys
    joueurs = autodoc_OneToMany("Joueur", back_populates="camp",
        doc="Joueurs appartenant à ce camp")
    roles = autodoc_OneToMany("Role", back_populates="camp",
        doc="Rôles affiliés à ce camp de base")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Camp '{self.slug}' ({self.nom})>"

    @property
    def discord_emoji(self):
        """discord.Emoji: Emoji Discord correspondant à ce camp

        Raises:
            ValueError: :attr:`.emoji` non défini ou manquant sur le serveur
            ~ready_check.NotReadyError: bot non connecté
                (:attr:`.config.guild` vaut ``None``)
        """
        if not self.emoji:
            raise ValueError(f"{self}.emoji non défini !")

        try:
            return next(e for e in config.guild.emojis if e.name == self.emoji)
        except StopIteration:
            raise ValueError(f"Pas d'emoji :{self.emoji}: "
                             "sur le serveur !") from None

    @property
    def discord_emoji_or_none(self):
        """:class:`discord.Emoji` | ``None``: :attr:`.discord_emoji` si défini

        Raises:
            ~ready_check.NotReadyError: bot non connecté
                (:attr:`.config.guild` vaut ``None``)
        """
        try:
            return self.discord_emoji
        except ValueError:
            return None

    @classmethod
    def default(cls):
        """Retourne le camp par défaut (non attribué).

        Warning:
            Un camp de :attr:`.slug` ``"nonattr"`` doit être défini en base.

        Returns:
            ~bdd.Camp

        Raises:
            ValueError: camp ``"nonattr"`` introuvable en base
            RuntimeError: session non initialisée
                (:attr:`.config.session` vaut ``None``)
        """
        camp = cls.query.get("nonattr")
        if not camp:
            raise ValueError("Pas de camp pas défaut (`nonattr`) !")
        return camp


class BaseAction(base.TableBase):
    """Table de données des actions définies de base (non liées à un joueur).

    Cette table est remplie automatiquement à partir du Google Sheet
    "Rôles et actions" par la commande :meth:`\!fillroles
    <.remplissage_bdd.RemplissageBDD.RemplissageBDD.fillroles.callback>`.
    """
    slug = autodoc_Column(sqlalchemy.String(32), primary_key=True,
        doc="Identifiant unique de l'action")

    trigger_debut = autodoc_Column(sqlalchemy.Enum(ActionTrigger),
        nullable=False,
        doc="Mode de déclenchement de l'ouverture de l'action")
    trigger_fin = autodoc_Column(sqlalchemy.Enum(ActionTrigger),
        nullable=False,
        doc="Mode de déclenchement de la clôture de l'action")
    instant = autodoc_Column(sqlalchemy.Boolean(), nullable=False,
        doc="L'action est instantannée (conséquence dès la prise de décision)"
            " ou non (conséquence à la fin du créneau d'action)")

    heure_debut = autodoc_Column(sqlalchemy.Time(),
        doc="Si :attr:`.trigger_debut` vaut "
            ":attr:`~ActionTrigger.temporel`, l'horaire associé")
    heure_fin = autodoc_Column(sqlalchemy.Time(),
        doc="Si :attr:`.trigger_fin` vaut\n"
            "- :attr:`~ActionTrigger.temporel` : l'horaire associé ;\n"
            "- :attr:`~ActionTrigger.delta`, l'intervalle associé")

    base_cooldown = autodoc_Column(sqlalchemy.Integer(), nullable=False,
        doc="Temps de rechargement entre deux utilisations du pouvoir "
            "(``0`` si pas de cooldown)", default=0)
    base_charges = autodoc_Column(sqlalchemy.Integer(),
        doc="Nombre de charges initiales du pouvoir (``None`` si illimité)")
    refill = autodoc_Column(sqlalchemy.String(32),
        doc="Évènements pouvant recharger l'action, séparés par des virgules "
            "(``\"weekends\"``, ``\"forgeron\"``, ``\"rebouteux\"``...)")

    lieu = autodoc_Column(sqlalchemy.String(100),
        doc="*Attribut informatif, non exploité dans la version actuelle "
            "(Distance/Physique/Lieu/Contact/Conditionnel/None/Public)*")
    interaction_notaire = autodoc_Column(sqlalchemy.String(100),
        doc="*Attribut informatif, non exploité dans la version actuelle "
            "(Oui/Non/Conditionnel/Potion/Rapport ; None si récursif)*")
    interaction_gardien = autodoc_Column(sqlalchemy.String(100),
        doc="*Attribut informatif, non exploité dans la version actuelle "
            "(Oui/Non/Conditionnel/Taverne/Feu/MaisonClose/Précis/"
            "Cimetière/Loups ; None si récursif)*")
    mage = autodoc_Column(sqlalchemy.String(100),
        doc="*Attribut informatif, non exploité dans la version actuelle "
            "(Oui/Non/Changement de cible/...)*")
    changement_cible = autodoc_Column(sqlalchemy.Boolean(),
        doc="*Attribut informatif, non exploité dans la version actuelle "
            "(si la cible doit changer entre deux utilisations consécutives)*")

    # -to-manys
    actions = autodoc_OneToMany("Action", back_populates="base",
        doc="Actions déroulant de cette base")
    roles = autodoc_ManyToMany("Role", secondary=_baseaction_role,
        back_populates="base_actions",
        doc="Rôles ayant cette action de base")

    def __repr__(self):
        """Return repr(self)."""
        return f"<BaseAction '{self.action}'>"
