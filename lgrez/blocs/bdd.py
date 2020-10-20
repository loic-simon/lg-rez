import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from lgrez.blocs import env, bdd



Base = declarative_base()
Tables = {}


# Objets de connection (créés dans connect)
engine = None
session = None


class ClassProperty(property):      # https://stackoverflow.com/a/1383402
    """Permet d'utiliser des propriés comme des classmethods (reçoivent la classe comme seul argument)"""
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class MyTable(object):
    def __init_subclass__(cls, **kwargs):
        """Définit __tablename__ et enregistre la table dans Tables"""
        super().__init_subclass__(**kwargs)
        cls.__tablename__ = cls.__name__.lower()
        Tables[cls.__name__] = cls

    @classmethod
    def get_query(cls):
        return bdd.session.query(cls)

    query = ClassProperty(get_query)        # Permet d'utiliser Table.query.<...> au lieu de bdd.session.query(Table).<...>



# Définition des tables

class Joueurs(MyTable, Base): #, tablename="joueurs"
    """Table de données des joueurs inscrits"""

    discord_id = sqlalchemy.Column(sqlalchemy.BigInteger(), primary_key=True)
    _chan_id = sqlalchemy.Column(sqlalchemy.BigInteger(), nullable=False)

    nom = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)
    chambre = sqlalchemy.Column(sqlalchemy.String(200), nullable=False)
    statut = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    role = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)
    camp = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    votant_village = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=False)
    votant_loups = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=False)
    role_actif = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=True)

    _vote_condamne = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)
    _vote_maire = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)
    _vote_loups = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)

    def __repr__(self):
        """Return repr(self)."""
        return f"<Joueurs #{self.discord_id} ({self.nom})>"



class Roles(MyTable, Base): #, tablename="roles"
    """Table de données des rôles"""

    slug = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)

    prefixe = sqlalchemy.Column(sqlalchemy.String(8), nullable=False)
    nom = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    camp = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)                       # loups, solitaire, nécro, village...

    description_courte = sqlalchemy.Column(sqlalchemy.String(140), nullable=False)
    description_longue = sqlalchemy.Column(sqlalchemy.String(2000), nullable=False)

    def __repr__(self):
        """Return repr(self)."""
        return f"<Roles '{self.slug}' ({self.prefixe}{self.nom})>"



class BaseActions(MyTable, Base): #, tablename="base_actions"
    """Table de données des actions définies de bases (non liées à un joueur)"""

    action = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)

    trigger_debut = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    trigger_fin = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)
    instant = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=True)

    heure_debut = sqlalchemy.Column(sqlalchemy.Time(), nullable=True)
    heure_fin = sqlalchemy.Column(sqlalchemy.Time(), nullable=True)

    base_cooldown = sqlalchemy.Column(sqlalchemy.Integer(), nullable=False)
    base_charges = sqlalchemy.Column(sqlalchemy.Integer(), nullable=True)
    refill  = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)

    lieu = sqlalchemy.Column(sqlalchemy.String(32), nullable=True) #Distance/Physique/Lieu/Contact/Conditionnel/None/Public
    interaction_notaire = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)         # Oui, Non, Conditionnel, Potion, Rapport; None si récursif
    interaction_gardien = sqlalchemy.Column(sqlalchemy.String(32), nullable=True)         # Oui, Non, Conditionnel, Taverne, Feu, MaisonClose, Précis, Cimetière, Loups, None si recursif
    mage = sqlalchemy.Column(sqlalchemy.String(100), nullable=True)                       #Oui, Non, changement de cible, etc

    changement_cible = sqlalchemy.Column(sqlalchemy.Boolean(), nullable=True)


    def __repr__(self):
        """Return repr(self)."""
        return f"<BaseActions '{self.action}'>"



class Actions(MyTable, Base): #, tablename="actions"
    """Table de données des actions attribuées (liées à un joueur et actives)"""

    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    player_id = sqlalchemy.Column(sqlalchemy.BigInteger(), nullable=False)
    action = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

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

    _decision = sqlalchemy.Column(sqlalchemy.String(200), nullable=True)


    def __repr__(self):
        """Return repr(self)."""
        return f"<Actions #{self.id} ({self.action}/{self.player_id})>"



class BaseActionsRoles(MyTable, Base): #, tablename="base_action_roles"
    """Table de données mettant en relation les rôles et les actions de base"""

    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    role = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)
    action = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)

    def __repr__(self):
        """Return repr(self)."""
        return f"<BaseActionsRoles #{self.id} ({self.role}/{self.action})>"



class Taches(MyTable, Base): #, tablename="taches"
    """Table de données des tâches planifiées du bot"""

    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime(), nullable=False)
    commande = sqlalchemy.Column(sqlalchemy.String(200), nullable=False)
    action = sqlalchemy.Column(sqlalchemy.Integer(), nullable=True)


    def __repr__(self):
        """Return repr(self)."""
        return f"<Taches #{self.id} ({self.commande})>"



class Triggers(MyTable, Base): #, tablename="triggers"
    """Table de données des mots et expressions déclenchant l'IA du bot"""

    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    trigger = sqlalchemy.Column(sqlalchemy.String(500), nullable=False)
    reac_id = sqlalchemy.Column(sqlalchemy.Integer(), nullable=False)


    def __repr__(self):
        """Return repr(self)."""
        extract = self.trigger.replace('\n', ' ')[:15] + "..."
        return f"<Triggers #{self.id} ({extract})>"



class Reactions(MyTable, Base): #, tablename="reactions"
    """Table de données des réactions d'IA connues du bot"""

    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    reponse = sqlalchemy.Column(sqlalchemy.String(2000), nullable=False)     # Réponse, dans le format personnalisé : "txt <||> txt <&&> <##>react"

    def __repr__(self):
        """Return repr(self)."""
        extract = self.reponse.replace('\n', ' ')[:15] + "..."
        return f"<Reactions #{self.id} ({extract})>"



class CandidHaro(MyTable, Base): #, tablename="candid_haro"
    """Table de données des candidatures et haros en cours  #PhilippeCandidHaro"""

    id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key = True)
    player_id = sqlalchemy.Column(sqlalchemy.BigInteger(), nullable=False)
    type = sqlalchemy.Column(sqlalchemy.String(11), nullable=False)

    def __repr__(self):
        """Return repr(self)."""
        return f"<CandidHaro #{self.id} ({self.player_id/self.type})>"



def connect():
    global engine, session

    LGREZ_DATABASE_URI = env.load("LGREZ_DATABASE_URI")
    engine = sqlalchemy.create_engine(LGREZ_DATABASE_URI)           # Moteur SQL : connexion avec le serveur

    # Création des tables si elles n'existent pas déjà
    Base.metadata.create_all(engine)

    # Ouverture de la session
    Session = sessionmaker(bind=engine)
    session = Session()
