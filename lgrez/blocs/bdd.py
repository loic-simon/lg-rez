"""lg-rez / blocs / Gestion des données

Déclaration de toutes les tables et leurs colonnes, et connection à la BDD

"""

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2

from lgrez.blocs import env


#: Alias de :exc:`sqlalchemy.exc.SQLAlchemyError` : exception de BDD générale
SQLAlchemyError = sqlalchemy.exc.SQLAlchemyError

#: Alias de :exc:`psycopg2.SQLAlchemyError` : erreur levée en cas de perte de connection avec la BDD
#: Seul PostreSQL géré nativement, override DriverOperationalError avec l'équivalent pour un autre driver
DriverOperationalError = psycopg2.OperationalError


Base = declarative_base()
Base.__doc__ = "Classe de base des tables de données, renvoyée par :func:`sqlalchemy.ext.declarative.declarative_base`"
#: :class:`dict`\[:class:`str`, :class:`.Base`\]: Dictionnaire {nom de la base -> table}
Tables = {}


# Objets de connection (créés dans connect)
#: :class:`sqlalchemy.engine.Engine`: Moteur de connection à la BDD
#: Vaut ``None`` avant l'appel à :func:`connect`.
engine = None
#: :class:`sqlalchemy.orm.session.Session`: Session de transaction avec la BDD.
#: Vaut ``None`` avant l'appel à :func:`connect`.
session = None


class _ClassProperty(property):      # https://stackoverflow.com/a/1383402
    """Permet d'utiliser des propriés comme des classmethods (reçoivent la classe comme seul argument)"""
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class _MyTable(object):
    """Classe permettant d'enregister les tables au fur et à mesure de leur déclaration et d'utiliser Table.query au lieu de session.query(Table)"""
    def __init_subclass__(cls, **kwargs):
        """Définit __tablename__ et enregistre la table dans Tables"""
        super().__init_subclass__(**kwargs)
        cls.__tablename__ = cls.__name__.lower()
        Tables[cls.__name__] = cls
        cls.__doc__ += f"\n\nClasse de données (sous-classe de :class:`.Base`) représentant la table ``{cls.__tablename__}``.\n\nTous les attributs ci-dessous sont du type indiqué pour les instances (entrées de BDD), mais de type :class:`sqlalchemy.orm.attributes.InstrumentedAttribute` pour la classe elle-même."       # On adore la doc vraiment

    @classmethod
    def get_query(cls):
        return session.query(cls)

    query = _ClassProperty(get_query)        # Permet d'utiliser Table.query.<...> au lieu de bdd.session.query(Table).<...>



# Définition des tables

class Joueurs(_MyTable, Base): #, tablename="joueurs"
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
    chambre = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)
    #: :class:`str`: statut RP (généralement "vivant", "mort" ou "MV") (NOT NULL, ``len <= 32``)
    statut = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    #: :class:`str`: rôle du joueur : doit correspondre à une valeur de :attr:`Roles.slug` (NOT NULL, ``len <= 32``)
    role = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)
    #: :class:`str`: camp du joueur (généralement "village", "loups", "nécro") (NOT NULL, ``len <= 32``)
    camp = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    #: :class:`bool`: si le joueur participe aux votes du village ou non
    votant_village = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=False)
    #: :class:`bool`: si le joueur participe au vote des loups ou non
    votant_loups = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=False)
    #: :class:`bool`: si le peut agir ou non (chatgarouté...) (NOT NULL)
    role_actif = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=True)

    #: :class:`str`: vote actuel au vote condamné (None si pas de vote en cours) (``len <= 200``)
    #: Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord.
    vote_condamne_ = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)
    #: :class:`str`: vote actuel au vote maire (None si pas de vote en cours) (``len <= 200``)
    #: Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord.
    vote_maire_ = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)
    #: :class:`str`: vote actuel au vote loups (None si pas de vote en cours) (``len <= 200``)
    #: Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord.
    vote_loups_ = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)

    def __repr__(self):
        """Return repr(self)."""
        return f"<Joueurs #{self.discord_id} ({self.nom})>"



class Roles(_MyTable, Base): #, tablename="roles"
    """Table de données des rôles

    Cette table est remplie automatiquement à partir du Google Sheet "Rôles et actions" par la commande :meth:`\!fillroles <.sync.Sync.Sync.fillroles.callback>`.
    """

    #: :class:`str`: identifiant unique du rôle (clé primaire, ``len <= 32``)
    slug = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)

    #: :class:`str`: article du nom du rôle (``"Le"``, ``"La"``, ``"L'"``...) (NOT NULL, ``len <= 8``)
    prefixe = sqlalchemy.Column(sqlalchemy.String(8), nullable=False)
    #: :class:`str`: nom du rôle (NOT NULL, ``len <= 32``)
    nom = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    #: :class:`str`: camp de base du rôle (NOT NULL, ``len <= 32``)
    camp = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)                       # loups, solitaire, nécro, village...

    #: :class:`str`: description en une ligne (NOT NULL, ``len <= 140``)
    description_courte = sqlalchemy.Column(sqlalchemy.String(140), nullable=False)
    #: :class:`str`: règles et background complets (NOT NULL, ``len <= 2000``)
    description_longue = sqlalchemy.Column(sqlalchemy.String(2000), nullable=False)

    def __repr__(self):
        """Return repr(self)."""
        return f"<Roles '{self.slug}' ({self.prefixe}{self.nom})>"



class BaseActions(_MyTable, Base): #, tablename="base_actions"
    """Table de données des actions définies de bases (non liées à un joueur)

    Cette table est remplie automatiquement à partir du Google Sheet "Rôles et actions" par la commande :meth:`\!fillroles <.remplissage_bdd.RemplissageBDD.RemplissageBDD.fillroles.callback>`.
    """
    #: :class:`str`: slug identifiant uniquement l'action (primary key, ``len <= 2000``)
    action = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)

    #: :class:`str`: type de déclencheur du début de l'action (``"temporel"``, ``"mort"``, ...) (NOT NULL, ``len <= 2000``)
    trigger_debut = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    #: :class:`str`: type de déclencheur de la fin (NOT NULL, ``len <= 2000``)
    trigger_fin = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    #: :class:`bool`: si l'action est instantannée (conséquences dès la prise de décision) ou non (conséquence à la fin du créneau d'action)
    instant = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=True)

    #: :class:`datetime.time`: si :attr:`.trigger_debut` vaut ``"temporel"`` ou ``"delta"``, l'horaire / la durée associée
    heure_debut = sqlalchemy.Column(sqlalchemy.Time(), nullable=True)
    #: :class:`datetime.time`: si :attr:`.trigger_fin` vaut ``"temporel"`` ou ``"delta"``, l'horaire / la durée associée
    heure_fin = sqlalchemy.Column(sqlalchemy.Time(), nullable=True)

    #: :class:`int`: temps de rechargement entre deux utilisations du pouvoir (``0`` si pas de cooldown) (NOT NULL)
    base_cooldown = sqlalchemy.Column(sqlalchemy.Integer(), nullable=False)
    #: :class:`int`: nombre de charges initiales du pouvoir (``None`` si illimitée)
    base_charges = sqlalchemy.Column(sqlalchemy.Integer(), nullable=True)
    #: :class:`str`: évènements pouvant recharger le pouvoir, séparés par des virgules (parmi ``"weekends"``, ``"forgeron"``, ...) (NOT NULL, ``len <= 32``)
    refill  = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)

    #: :class:`str`: attribut informatif (Distance/Physique/Lieu/Contact/Conditionnel/None/Public) (``len <= 32``)
    lieu = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    #: :class:`str`: attribut informatif (Oui, Non, Conditionnel, Potion, Rapport; None si récursif) (``len <= 32``)
    interaction_notaire = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    #: :class:`str`: attribut informatif (Oui, Non, Conditionnel, Taverne, Feu, MaisonClose, Précis, Cimetière, Loups, None si recursif) (``len <= 32``)
    interaction_gardien = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    #: :class:`str`: attribut informatif (Oui, Non, changement de cible, etc) (``len <= 100`` 32)
    mage = sqlalchemy.Column(sqlalchemy.String(100), nullable=True)

    #: :class:`bool`: si la cible doit changer entre deux utilisations consécutives (informatif uniquement pour l'instant)
    changement_cible = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=True)


    def __repr__(self):
        """Return repr(self)."""
        return f"<BaseActions '{self.action}'>"



class Actions(_MyTable, Base): #, tablename="actions"
    """Table de données des actions attribuées (liées à un joueur et actives)

    Les instances doivent être enregistrées via :func:`.gestion_actions.open_action` et supprimées via :func:`.gestion_actions.close_action`.
    """
    #: :class:`int`: identifiant unique de l'action, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    #: :class:`int`: clé étrangère liée à :attr:`.Joueurs.id` (NOT NULL)
    player_id = sqlalchemy.Column(sqlalchemy.BigInteger(), nullable=False)
    #: :class:`str`: clé étrangère liée à :attr:`.BaseActions.slug` (NOT NULL, ``len <= 32``)
    action = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    #: et ``trigger_fin``, ``instant``, ``heure_debut``, ``heure_fin``, ``instant``, ``heure_debut``, ``heure_fin``, ``cooldown``, ``charges``, ``refill``, ``lieu``, ``interaction_notaire``, ``interaction_gardien``, ``mage``, ``changement_cible`` sont les mêmes que pour :class:`.Actions`.
    trigger_debut = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    trigger_fin = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    instant = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=True)

    heure_debut = sqlalchemy.Column(sqlalchemy.Time(), nullable=True)
    heure_fin = sqlalchemy.Column(sqlalchemy.Time(), nullable=True)

    cooldown = sqlalchemy.Column(sqlalchemy.Integer(), nullable=False)
    charges = sqlalchemy.Column(sqlalchemy.Integer(), nullable=True)
    refill  = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)

    lieu = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    interaction_notaire = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    interaction_gardien = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    mage = sqlalchemy.Column(sqlalchemy.String(100), nullable=True)
    changement_cible = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=True)

    #: Décision prise par le joueur pour l'action actuelle (``None`` si action non en cours). Le ``_`` final indique que ce champ n'est pas synchnisé avec le Tableau de bord. (``len <= 200``)
    decision_ = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)


    def __repr__(self):
        """Return repr(self)."""
        return f"<Actions #{self.id} ({self.action}/{self.player_id})>"



class BaseActionsRoles(_MyTable, Base): #, tablename="base_action_roles"
    """Table de données mettant en relation les rôles et les actions de base

    Cette table est remplie automatiquement à partir du Google Sheet "Rôles et actions" par la commande :meth:`\!fillroles <.remplissage_bdd.RemplissageBDD.RemplissageBDD.fillroles.callback>`.
    """
    #: :class:`int`: identifiant unique de l'action, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    #: :class:`str`: clé étrangère liée à :attr:`.Roles.slug` (NOT NULL, ``len <= 32``)
    role = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)
    #: :class:`str`: clé étrangère liée à :attr:`.BaseActions.slug` (NOT NULL, ``len <= 32``)
    action = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    def __repr__(self):
        """Return repr(self)."""
        return f"<BaseActionsRoles #{self.id} ({self.role}/{self.action})>"



class Taches(_MyTable, Base): #, tablename="taches"
    """Table de données des tâches planifiées du bot

    Les instances doivent être enregistrées via :func:`.taches.add_task` et supprimées via :func:`.taches.cancel_task`.
    """
    #: :class:`int`: identifiant unique de la tâche, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    #: :class:`datetime.datetime`: moment où sera exécutée la tâche (NOT NULL)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime(), nullable=False)
    #: :class:`str`: texte à envoyer via le webhook (généralement une commande) (NOT NULL, ``len <= 200``)
    commande = sqlalchemy.Column(sqlalchemy.String(2000), nullable=False)
    #: :class:`int`: si la tâche est liée à une action, clé étrangère liée à :attr:`.Actions.id`
    action = sqlalchemy.Column(sqlalchemy.Integer(), nullable=True)


    def __repr__(self):
        """Return repr(self)."""
        return f"<Taches #{self.id} ({self.commande})>"



class Reactions(_MyTable, Base): #, tablename="reactions"
    """Table de données des réactions d'IA connues du bot

    Les instances doivent être enregistrées via :meth:`\!addIA <.IA.GestionIA.GestionIA.addIA.callback>` et supprimées via :meth:`\!modifIA <.IA.GestionIA.GestionIA.modifIA.callback>`.
    """
    #: :class:`int`: identifiant unique de la réaction, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    #: :class:`str`: réponse, suivant le format (mini-langage) personnalisé (``"txt <||> txt <&&> <##>react"``) (NOT NULL, <2000)
    reponse = sqlalchemy.Column(sqlalchemy.String(2000), nullable=False)

    def __repr__(self):
        """Return repr(self)."""
        extract = self.reponse.replace('\n', ' ')[:15] + "..."
        return f"<Reactions #{self.id} ({extract})>"



class Triggers(_MyTable, Base): #, tablename="triggers"
    """Table de données des mots et expressions déclenchant l'IA du bot

    Les instances doivent être enregistrées via :meth:`\!addIA <.IA.GestionIA.GestionIA.addIA.callback>` et supprimées via :meth:`\!modifIA <.IA.GestionIA.GestionIA.modifIA.callback>`.
    """
    #: :class:`int`: identifiant unique du trigger, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    #: :class:`str`: mots-clés / expressions, séparés par des ``;`` éventuellement (NOT NULL, ``len <= 500``)
    trigger = sqlalchemy.Column(sqlalchemy.String(500), nullable=False)
    #: :class:`int`: réaction associée, clé étrangère de :attr:`.Reactions.id` (NOT NULL)
    reac_id = sqlalchemy.Column(sqlalchemy.Integer(), nullable=False)


    def __repr__(self):
        """Return repr(self)."""
        extract = self.trigger.replace('\n', ' ')[:15] + "..."
        return f"<Triggers #{self.id} ({extract})>"



class CandidHaro(_MyTable, Base): #, tablename="candid_haro"
    """Table de données des candidatures et haros en cours  #PhilippeCandidHaro

    Les instances doivent être enregistrées via :meth:`\!haro <.actions_publiques.ActionsPubliques.ActionsPubliques.haro.callback>` / :meth:`\!candid <.actions_publiques.ActionsPubliques.ActionsPubliques.candid.callback>` et supprimées via :meth:`\!wipe <.actions_publiques.ActionsPubliques.ActionsPubliques.wipe.callback>`.
    """
    #: :class:`int`: identifiant unique de la réaction, sans signification (auto-incrémental) (primary key)
    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key = True)
    #: :class:`int`: joueur associé, clé étrangère de :attr:`.Joueurs.discord_id` (NOT NULL)
    player_id = sqlalchemy.Column(sqlalchemy.BigInteger(), nullable=False)
    #: :class:`str`: ``"haro"`` ou ``"candidature"`` (flemme de ``enum`` mais faudrait, vraiment) (NOT NULL, ``len <= 11``)
    type = sqlalchemy.Column(sqlalchemy.String(11), nullable=False)

    def __repr__(self):
        """Return repr(self)."""
        return f"<CandidHaro #{self.id} ({self.player_id}/{self.type})>"



def connect():
    """Se connecte à la base de données (variable d'environment ``LGREZ_DATABASE_URI``), crée les tables si nécessaire, construit :attr:`.bdd.engine` et ouvre :attr:`.bdd.session`"""
    global engine, session

    LGREZ_DATABASE_URI = env.load("LGREZ_DATABASE_URI")
    engine = sqlalchemy.create_engine(LGREZ_DATABASE_URI, pool_pre_ping=True)           # Moteur SQL : connexion avec le serveur

    # Création des tables si elles n'existent pas déjà
    Base.metadata.create_all(engine)

    # Ouverture de la session
    Session = sessionmaker(bind=engine)
    session = Session()
