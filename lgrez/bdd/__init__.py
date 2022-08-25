"""lg-rez / Gestion des données

Déclaration de toutes les tables, colonnes, méthodes, et connection à la BDD

"""

import sqlalchemy
import psycopg2

from lgrez.bdd import base
from lgrez.bdd.enums import Statut, ActionTrigger, CandidHaroType, Vote, UtilEtat, CibleType
from lgrez.bdd.model_joueurs import Joueur, CandidHaro, Boudoir, Bouderie
from lgrez.bdd.model_jeu import Role, Camp, BaseAction, BaseCiblage
from lgrez.bdd.model_actions import Action, Utilisation, Ciblage, Tache
from lgrez.bdd.model_ia import Reaction, Trigger

# All tables and enums directly accessible via bdd.<name>


#: __all__ = toutes les classes de données publiques
__all__ = [nom for nom in base.tables if not nom.startswith("_")]


tables = base.tables

connect = base.connect

SQLAlchemyError = sqlalchemy.exc.SQLAlchemyError

DriverOperationalError = psycopg2.OperationalError
