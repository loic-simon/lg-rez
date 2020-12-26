"""lg-rez / blocs / Gestion des données

Déclaration de toutes les tables et leurs colonnes, et connection à la BDD

"""

import enum

import sqlalchemy
from sqlalchemy.ext import declarative
from sqlalchemy import orm
import psycopg2

from lgrez import config
from lgrez.blocs import env


#: Alias de :exc:`sqlalchemy.exc.SQLAlchemyError` : exception de BDD générale
SQLAlchemyError = sqlalchemy.exc.SQLAlchemyError

#: Alias de :exc:`psycopg2.SQLAlchemyError` : erreur levée en cas de perte de connection avec la BDD
#: Seul PostreSQL géré nativement, override DriverOperationalError avec l'équivalent pour un autre driver
DriverOperationalError = psycopg2.OperationalError


class TableMeta(declarative.api.DeclarativeMeta):
    """Métaclasse des tables de données (sous-classe de :class:`sqlalchemy.declarative.api.DeclarativeMeta`)

    Cette métaclasse :
        - définit le nom de la table comme ``cls.__name__.lower() + "s"``,
        - ajoute une note commune aux docstrings de chaque classe,
        - définit la propriété de classe :meth:`Table.query <TableMeta.query>`, raccourci pour ``config.session.query(Table)``
    """
    def __init__(cls, *args, **kwargs):
        """Constructs the data class"""
        if cls.__name__ == "TableBase":
            return

        cls.__tablename__ = cls.__name__.lower() + "s"
        super().__init__(*args, **kwargs)

        cls.__doc__ += f"\n\nClasse de données (sous-classe de :class:`.TableBase`) représentant la table ``{cls.__tablename__}``.\n\nTous les attributs ci-dessous sont du type indiqué pour les instances (entrées de BDD), mais de type :class:`sqlalchemy.orm.attributes.InstrumentedAttribute` pour la classe elle-même."       # On adore la doc vraiment


    @property
    def query(cls):
        """:class:`sqlalchemy.orm.query.Query`: Raccourci pour :attr:`config.session.query <sqlalchemy.orm.session.Session.query>` ``(Table)``

        Raises:
            :exc:`RuntimeError`: session non initialisée (:attr:`config.session` vaut ``None``)
        """
        if not config.session:
            raise RuntimeError("Database session not initialised!")
        return config.session.query(cls)




#: :class:`dict`\[:class:`str`, :class:`TableBase`\]: Dictionnaire ``{nom de la base -> table}``, automatiquement rempli par :attr:`sqlalchemy.ext.declarative.declarative_base` (via le paramètre ``class_registry``)
tables = {}

#:
TableBase = declarative.declarative_base(class_registry=tables, name="TableBase", metaclass=TableMeta)
TableBase.__doc__ = """Classe de base des tables de données (construite par :func:`sqlalchemy.ext.declarative.declarative_base`)"""


# Définition des enums

class Statut(enum.Enum):
    """:class:`~enum.Enum` représentant le statut d'un Joueur"""
    #: Le joueur est en vie !
    vivant = enum.auto()
    #: Le joueur est mort. RIP.
    mort = enum.auto()
    #: Le joueur est Mort-Vivant. Pas de chance.
    MV = enum.auto()
    #: Le joueur est Immortel. Si jamais...
    immortel = enum.auto()


class ActionTrigger(enum.Enum):
    """:class:`~enum.Enum` représentant le déclencheur de l'ouverture/fermeture d'une action"""
    #: Ouverture/fermeture à heure fixe chaque jour
    temporel = enum.auto()
    #: Fermeture un délai donné après l'ouverture
    delta = enum.auto()
    #: Action utilisable en permanence
    perma = enum.auto()
    #: Ouverture au lancement du jeu
    start = enum.auto()
    #: Action automatique, fermeture dès l'ouverture
    auto = enum.auto()
    #: Ouverture à la mort
    mort = enum.auto()
    #: Ouverture/fermeture au !plot cond
    mot_mjs = enum.auto()
    #: À l'ouverture du vote condamné
    open_cond = enum.auto()
    #: À la fermeture du vote condamné
    close_cond = enum.auto()
    #: À l'ouverture du vote du maire
    open_maire = enum.auto()
    #: À la fermeture du vote du maire
    close_maire = enum.auto()
    #: À l'ouverture du vote des loups
    open_loups = enum.auto()
    #: À la fermeture du vote des loups
    close_loups = enum.auto()


class CandidHaroType(enum.Enum):
    """:class:`~enum.Enum` pour distinguer un haro d'une candidature"""
    #: Candidature à la mairie
    candidature = enum.auto()
    #: Haro pour le bûcher
    haro = enum.auto()



# Tables de jonction (pour many-to-manys)

_baseaction_role = sqlalchemy.Table('_baseactions_roles', TableBase.metadata,
    sqlalchemy.Column('_role_slug', sqlalchemy.String(32), sqlalchemy.ForeignKey('roles.slug')),
    sqlalchemy.Column('_baseaction_id', sqlalchemy.String(32), sqlalchemy.ForeignKey('baseactions.slug'))
)


# Tables de données

class Joueur(TableBase):
    """Table de données des joueurs inscrits

    Les instances de cette classe correspondent aux lignes du Tableau de bord ; elles sont crées par l'inscription (:func:`.inscription.main`) et synchronisées par :meth:`\!sync <.sync.Sync.Sync.sync.callback>`.
    """
    #: :class:`int` : ID Discord du joueur (clé primaire)
    discord_id = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)
    #: :class:`int`: ID du chan privé Discord du joueur (NOT NULL)
    #: Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord.
    chan_id_ = sqlalchemy.Column(sqlalchemy.BigInteger(), nullable=False)

    #: :class:`str`: nom du joueur (demandé à l'inscription) (NOT NULL, ``len <= 32``)
    nom = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)
    #: :class:`str`: emplacement du joueur (demandé à l'inscription) (``len <= 200``)
    chambre = sqlalchemy.Column(sqlalchemy.String(200))
    #: :class:`Statut`: statut RP (NOT NULL)
    statut = sqlalchemy.Column(sqlalchemy.Enum(Statut), nullable=False)

    _role_slug = sqlalchemy.Column(sqlalchemy.String(32), sqlalchemy.ForeignKey("roles.slug"), nullable=False)
    #: :class:`Role`: rôle du joueur (Many-to-one avec :attr:`Role.slug`)
    role = sqlalchemy.orm.relationship("Role", back_populates="joueurs")

    _camp_slug = sqlalchemy.Column(sqlalchemy.String(32), sqlalchemy.ForeignKey("camps.slug"), nullable=False)
    #: :class:`Camp`: camp du joueur (Many-to-one avec :attr:`Camp.slug`)
    camp = sqlalchemy.orm.relationship("Camp", back_populates="joueurs")

    #: :class:`bool`: si le joueur participe aux votes du village ou non
    votant_village = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=False)
    #: :class:`bool`: si le joueur participe au vote des loups ou non
    votant_loups = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=False)
    #: :class:`bool`: si le joueur peut agir ou non (chatgarouté...) (NOT NULL)
    role_actif = sqlalchemy.Column(sqlalchemy.Boolean())

    #: :class:`str`: vote actuel au vote condamné (None si pas de vote en cours) (``len <= 200``, NOT NULL, default: ``True``)
    #: Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord.
    vote_condamne_ = sqlalchemy.Column(sqlalchemy.String(200), nullable=False, default=True)
    #: :class:`str`: vote actuel au vote maire (None si pas de vote en cours) (``len <= 200``, NOT NULL, default: ``True``)
    #: Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord.
    vote_maire_ = sqlalchemy.Column(sqlalchemy.String(200), nullable=False, default=True)
    #: :class:`str`: vote actuel au vote loups (None si pas de vote en cours) (``len <= 200``, NOT NULL, default: ``False``)
    #: Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord.
    vote_loups_ = sqlalchemy.Column(sqlalchemy.String(200), nullable=False, default=False)

    #: :class:`list`\[:class:`Action`\]: actions pour ce joueur (one-to-many)
    actions = sqlalchemy.orm.relationship("Action", back_populates="joueur")
    #: :class:`list`\[:class:`CandidHaro`\]: candidatures et haros contre ce joueur (one-to-many)
    candidharos = sqlalchemy.orm.relationship("CandidHaro", back_populates="joueur")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Joueur #{self.discord_id} ({self.nom})>"

    @property
    def member(self):
        """:class:`discord.Member`: Membre Discord correspondant ce Joueur

        Raises:
            :exc:`ValueError`: pas de membre correspondant
            :exc:`RuntimeError`: bot non connecté (:attr:`config.guild` vaut ``None``)
        """
        if not config.guild:
            raise RuntimeError("Joueur.member : bot non connecté !")
        result = config.guild.get_member(self.discord_id)
        if not result:
            raise ValueError(f"Joueur.member : pas de membre pour `{self}` !")

        return result

    @property
    def private_chan(self):
        """:class:`discord.TextChannel`: Channel privé (conversation bot) du joueur

        Raises:
            :exc:`ValueError`: pas de channel correspondant
            :exc:`RuntimeError`: bot non connecté (:attr:`.config.guild` vaut ``None``)
        """
        if not config.guild:
            raise RuntimeError("Joueur.private_chan : bot non connecté !")
        result = config.guild.get_channel(self.chan_id_)
        if not result:
            raise ValueError(f"Joueur.private_chan : pas de chan pour `{self}` !")

        return result

    @classmethod
    def from_member(cls, member):
        """Retourne le Joueur (instance de cette classe) correspondant à un membre (classmethod)

        Args:
            member (:class:`discord.Member`): le membre concerné

        Returns:
            :class:`Joueur`

        Raises:
            :exc:`ValueError`: membre introuvable en base
            :exc:`RuntimeError`: session non initialisée (:attr:`config.session` vaut ``None``)
        """
        joueur = cls.query.get(member.id)
        if not joueur:
            raise ValueError(f"Joueur.from_member : pas de joueur en base pour `{member}` !")

        return joueur



class Role(TableBase):
    """Table de données des rôles

    Cette table est remplie automatiquement à partir du Google Sheet "Rôles et actions" par la commande :meth:`\!fillroles <.sync.Sync.Sync.fillroles.callback>`.
    """
    #: :class:`str`: identifiant unique du rôle (clé primaire, ``len <= 32``)
    slug = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)

    #: :class:`str`: article du nom du rôle (``"Le"``, ``"La"``, ``"L'"``...) (NOT NULL, ``len <= 8``)
    prefixe = sqlalchemy.Column(sqlalchemy.String(8), nullable=False)
    #: :class:`str`: nom du rôle (NOT NULL, ``len <= 32``)
    nom = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    _camp_slug = sqlalchemy.Column(sqlalchemy.String(32), sqlalchemy.ForeignKey("camps.slug"), nullable=False)
    #: :class:`Camp`: camp du joueur (Many-to-one avec :attr:`Camp.slug`)
    camp = sqlalchemy.orm.relationship("Camp", back_populates="roles")

    #: :class:`str`: description en une ligne (NOT NULL, ``len <= 140``)
    description_courte = sqlalchemy.Column(sqlalchemy.String(140), nullable=False)
    #: :class:`str`: règles et background complets (NOT NULL, ``len <= 2000``)
    description_longue = sqlalchemy.Column(sqlalchemy.String(2000), nullable=False)

    # One-to-manys
    #: :class:`list`\[:class:`Role`\]: joueurs ayant ce rôle (one-to-many)
    joueurs = sqlalchemy.orm.relationship("Joueur", back_populates="role")
    #: :class:`list`\[:class:`BaseAction`\]: modèles d'actions associées (many-to-many)
    base_actions = sqlalchemy.orm.relationship("BaseAction", secondary=_baseaction_role, back_populates="roles")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Role '{self.slug}' ({self.prefixe}{self.nom})>"

    @property
    def nom_complet(self):
        """:class:`str`: Préfixe + nom du rôle"""
        return f"{self.prefixe}{self.nom}"

    @classmethod
    def default(cls):
        """:class:`Role`: Role (instance de cette classe) par défaut (non attribué)

        Warning:
            Un rôle de ``slug`` ``"nonattr"`` doit être défini en base.

        Raises:
            :exc:`ValueError`: rôle ``"nonattr"`` introuvable en base
            :exc:`RuntimeError`: session non initialisée (:attr:`config.session` vaut ``None``)
        """
        role = cls.query.get("nonattr")
        if not role:
            raise ValueError("Pas de rôle pas défaut (`nonattr`) !")
        return role



class Camp(TableBase):
    """Table de données des camps

    [À FAIRE ==>] Cette table est remplie automatiquement à partir du Google Sheet "Rôles et actions" par la commande :meth:`\!fillroles <.sync.Sync.Sync.fillroles.callback>`.
    """
    #: :class:`str`: identifiant unique du rôle (clé primaire, ``len <= 32``)
    slug = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)

    #: :class:`str`: nom (affiché) du camp (NOT NULL, ``len <= 32``)
    nom = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)
    #: :class:`str`: description du camp (NOT NULL, ``len <= 500``)
    description = sqlalchemy.Column(sqlalchemy.String(140), nullable=False)

    #: :class:`bool`: si l'existance du camp (et des rôles liés) est connue de tous (NOT NULL, default: ``True``)
    public = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=False, default=True)

    #: :class:`str`: nom de l'emoji associé au camp (NOT NULL, ``len <= 32``)
    emoji = sqlalchemy.Column(sqlalchemy.String(32))

    # One-to-manys
    #: :class:`list`\[:class:`Joueur`\]: joueurs dans ce camp (one-to-many)
    joueurs = sqlalchemy.orm.relationship("Joueur", back_populates="camp")
    #: :class:`list`\[:class:`Role`\]: joueurs ayant ce rôle (one-to-many)
    roles = sqlalchemy.orm.relationship("Role", back_populates="camp")

    def __repr__(self):
        """Return repr(self)."""
        return f"<Camp '{self.slug}' ({self.nom})>"

    @classmethod
    def default(cls):
        """:class:`Camp`: Camp (instance de cette classe) par défaut (non attribué)

        Warning:
            Un camp de ``slug`` ``"nonattr"`` doit être défini en base.

        Raises:
            :exc:`ValueError`: camp ``"nonattr"`` introuvable en base
            :exc:`RuntimeError`: session non initialisée (:attr:`config.session` vaut ``None``)
        """
        camp = cls.query.get("nonattr")
        if not camp:
            raise ValueError("Pas de camp pas défaut (`nonattr`) !")
        return camp




class BaseAction(TableBase):
    """Table de données des actions définies de bases (non liées à un joueur)

    Cette table est remplie automatiquement à partir du Google Sheet "Rôles et actions" par la commande :meth:`\!fillroles <.remplissage_bdd.RemplissageBDD.RemplissageBDD.fillroles.callback>`.
    """
    #: :class:`str`: slug identifiant uniquement l'action (primary key, ``len <= 2000``)
    slug = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)

    #: :class:`ActionTrigger`: type de déclencheur du début de l'action (NOT NULL)
    trigger_debut = sqlalchemy.Column(sqlalchemy.Enum(ActionTrigger))
    #: :class:`ActionTrigger`: type de déclencheur de la fin (NOT NULL)
    trigger_fin = sqlalchemy.Column(sqlalchemy.Enum(ActionTrigger))
    #: :class:`bool`: si l'action est instantannée (conséquences dès la prise de décision) ou non (conséquence à la fin du créneau d'action)
    instant = sqlalchemy.Column(sqlalchemy.Boolean())

    #: :class:`datetime.time`: si :attr:`.trigger_debut` vaut :attr:`~ActionTrigger.temporel`, l'horaire associée
    heure_debut = sqlalchemy.Column(sqlalchemy.Time())
    #: :class:`datetime.time`: si :attr:`.trigger_debut` vaut :attr:`~ActionTrigger.temporel` ou :attr:`~ActionTrigger.delta`, l'horaire / la durée associée
    heure_fin = sqlalchemy.Column(sqlalchemy.Time())

    #: :class:`int`: temps de rechargement entre deux utilisations du pouvoir (``0`` si pas de cooldown) (NOT NULL)
    base_cooldown = sqlalchemy.Column(sqlalchemy.Integer(), nullable=False)
    #: :class:`int`: nombre de charges initiales du pouvoir (``None`` si illimitée)
    base_charges = sqlalchemy.Column(sqlalchemy.Integer())
    #: :class:`str`: évènements pouvant recharger le pouvoir, séparés par des virgules (parmi ``"weekends"``, ``"forgeron"``, ...) (NOT NULL, ``len <= 32``)
    refill  = sqlalchemy.Column(sqlalchemy.String(32))

    #: :class:`str`: attribut informatif (Distance/Physique/Lieu/Contact/Conditionnel/None/Public) (``len <= 32``)
    lieu = sqlalchemy.Column(sqlalchemy.String(32))
    #: :class:`str`: attribut informatif (Oui, Non, Conditionnel, Potion, Rapport; None si récursif) (``len <= 32``)
    interaction_notaire = sqlalchemy.Column(sqlalchemy.String(32))
    #: :class:`str`: attribut informatif (Oui, Non, Conditionnel, Taverne, Feu, MaisonClose, Précis, Cimetière, Loups, None si recursif) (``len <= 32``)
    interaction_gardien = sqlalchemy.Column(sqlalchemy.String(32))
    #: :class:`str`: attribut informatif (Oui, Non, changement de cible, etc) (``len <= 100`` 32)
    mage = sqlalchemy.Column(sqlalchemy.String(100))

    #: :class:`bool`: si la cible doit changer entre deux utilisations consécutives (informatif uniquement pour l'instant)
    changement_cible = sqlalchemy.Column(sqlalchemy.Boolean())

    #: :class:`list`\[:class:`Action`\]: actions déroulant de cette base (one-to-many)
    actions = sqlalchemy.orm.relationship("Action", back_populates="base")
    #: :class:`list`\[:class:`Role`\]: rôles ayant cette actions de base (many-to-many)
    roles = sqlalchemy.orm.relationship("Role", secondary=_baseaction_role, back_populates="base_actions")


    def __repr__(self):
        """Return repr(self)."""
        return f"<BaseAction '{self.action}'>"



class Action(TableBase):
    """Table de données des actions attribuées (liées à un joueur et actives)

    Les instances doivent être enregistrées via :func:`.gestion_actions.open_action` et supprimées via :func:`.gestion_actions.close_action`.
    """
    #: :class:`int`: identifiant unique de l'action, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)

    _joueur_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("joueurs.discord_id"), nullable=False)
    #: :class:`Joueur`: joueur concerné (many-to-one avec :attr:`Joueur.discord_id`)
    joueur = sqlalchemy.orm.relationship("Joueur", back_populates="actions")

    _base_slug = sqlalchemy.Column(sqlalchemy.String(32), sqlalchemy.ForeignKey("baseactions.slug"), nullable=False)
    #: :class:`BaseAction`: action de base (many-to-one avec :attr:`BaseAction.slug`)
    base = sqlalchemy.orm.relationship("BaseAction", back_populates="actions")

    #: :class:`int`: nombre d'ouvertures avant disponiblité de l'action (NOT NULL)
    cooldown = sqlalchemy.Column(sqlalchemy.Integer(), nullable=False)
    #: :class:`int`: nombre de charges restantes
    charges = sqlalchemy.Column(sqlalchemy.Integer())

    #: :class:`str`: Décision prise par le joueur pour l'action actuelle (``None`` si action non en cours).
    #: Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord. (``len <= 200``)
    decision_ = sqlalchemy.Column(sqlalchemy.String(200))

    #: :class:`list`\[:class:`Tache`\]: tâches liées à cette action (one-to-many)
    taches = sqlalchemy.orm.relationship("Tache", back_populates="action")


    def __repr__(self):
        """Return repr(self)."""
        return f"<Action #{self.id} ({self.base}/{self.joueur})>"



class Tache(TableBase):
    """Table de données des tâches planifiées du bot

    Les instances doivent être enregistrées via :func:`.taches.add_task` et supprimées via :func:`.taches.cancel_task`.
    """
    #: :class:`int`: identifiant unique de la tâche, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    #: :class:`datetime.datetime`: moment où sera exécutée la tâche (NOT NULL)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime(), nullable=False)
    #: :class:`str`: texte à envoyer via le webhook (généralement une commande) (NOT NULL, ``len <= 200``)
    commande = sqlalchemy.Column(sqlalchemy.String(2000), nullable=False)

    _action_id = sqlalchemy.Column(sqlalchemy.Integer(), sqlalchemy.ForeignKey("actions.id"), nullable=False)
    #: :class:`Action`: si la tâche est liée à une action, action concernée (many-to-one avec :attr:`Action.id`)
    action = sqlalchemy.orm.relationship("Action", back_populates="taches")


    def __repr__(self):
        """Return repr(self)."""
        return f"<Tache #{self.id} ({self.commande})>"



class Reaction(TableBase):
    """Table de données des réactions d'IA connues du bot

    Les instances doivent être enregistrées via :meth:`\!addIA <.IA.GestionIA.GestionIA.addIA.callback>` et supprimées via :meth:`\!modifIA <.IA.GestionIA.GestionIA.modifIA.callback>`.
    """
    #: :class:`int`: identifiant unique de la réaction, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    #: :class:`str`: réponse, suivant le format (mini-langage) personnalisé (``"txt <||> txt <&&> <##>react"``) (NOT NULL, <2000)
    reponse = sqlalchemy.Column(sqlalchemy.String(2000), nullable=False)

    #: :class:`list`\[:class:`Trigger`\]: déclencheurs associés (many-to-one)
    triggers = sqlalchemy.orm.relationship("Trigger", back_populates="reaction")

    def __repr__(self):
        """Return repr(self)."""
        extract = self.reponse.replace('\n', ' ')[:15] + "..."
        return f"<Reaction #{self.id} ({extract})>"



class Trigger(TableBase):
    """Table de données des mots et expressions déclenchant l'IA du bot

    Les instances doivent être enregistrées via :meth:`\!addIA <.IA.GestionIA.GestionIA.addIA.callback>` et supprimées via :meth:`\!modifIA <.IA.GestionIA.GestionIA.modifIA.callback>`.
    """
    #: :class:`int`: identifiant unique du trigger, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    #: :class:`str`: mots-clés / expressions, séparés par des ``;`` éventuellement (NOT NULL, ``len <= 500``)
    trigger = sqlalchemy.Column(sqlalchemy.String(500), nullable=False)

    _reac_id = sqlalchemy.Column(sqlalchemy.Integer(), sqlalchemy.ForeignKey("reactions.id"), nullable=False)
    #: :class:`Reaction`: réaction associée (one-to-many avec :attr:`Reaction.id`)
    reaction = sqlalchemy.orm.relationship("Reaction", back_populates="triggers")


    def __repr__(self):
        """Return repr(self)."""
        extract = self.trigger.replace('\n', ' ')[:15] + "..."
        return f"<Trigger #{self.id} ({extract})>"



class CandidHaro(TableBase):
    """Table de données des candidatures et haros en cours  #PhilippeCandidHaro

    Les instances doivent être enregistrées via :meth:`\!haro <.actions_publiques.ActionsPubliques.ActionsPubliques.haro.callback>` / :meth:`\!candid <.actions_publiques.ActionsPubliques.ActionsPubliques.candid.callback>` et supprimées via :meth:`\!wipe <.actions_publiques.ActionsPubliques.ActionsPubliques.wipe.callback>`.
    """
    #: :class:`int`: identifiant unique de la réaction, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key = True)

    _joueur_id = sqlalchemy.Column(sqlalchemy.BigInteger(), sqlalchemy.ForeignKey("joueurs.discord_id"), nullable=False)
    #: :class:`Joueur`: joueur concerné (many-to-one avec :attr:`Joueur.discord_id`)
    joueur = sqlalchemy.orm.relationship("Joueur", back_populates="candidharos")

    #: :class:`CandidHaroType`: ``"haro"`` ou ``"candidature"``
    type = sqlalchemy.Column(sqlalchemy.Enum(CandidHaroType), nullable=False)

    def __repr__(self):
        """Return repr(self)."""
        return f"<CandidHaro #{self.id} ({self.player_id}/{self.type})>"



# __all__ = toutes les classes de données
__all__ = [nom for nom in tables if not nom.startswith("_")]


def connect():
    """Se connecte à la base de données (variable d'environment ``LGREZ_DATABASE_URI``), crée les tables si nécessaire, construit :attr:`config.engine` et ouvre :attr:`config.session`"""

    LGREZ_DATABASE_URI = env.load("LGREZ_DATABASE_URI")
    engine = sqlalchemy.create_engine(LGREZ_DATABASE_URI, pool_pre_ping=True)           # Moteur SQL : connexion avec le serveur

    # Création des tables si elles n'existent pas déjà
    TableBase.metadata.create_all(engine)

    # Ouverture de la session
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    config.session = Session()
