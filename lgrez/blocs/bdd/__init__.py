
import sqlalchemy
import psycopg2

from lgrez.blocs.bdd import base, model
from lgrez.blocs.bdd.model import *


#: __all__ = toutes les classes de données publiques
__all__ = [nom for nom in base.tables if not nom.startswith("_")]

#:
tables = base.tables
#:
TableBase = base.TableBase
#:
TableMeta = base.TableMeta
#: 
connect = base.connect

#: Alias de :exc:`sqlalchemy.exc.SQLAlchemyError` : exception de BDD générale
SQLAlchemyError = sqlalchemy.exc.SQLAlchemyError

#: Alias de :exc:`psycopg2.SQLAlchemyError` : erreur levée en cas de perte de connection avec la BDD
#: Seul PostreSQL géré nativement, override DriverOperationalError avec l'équivalent pour un autre driver
DriverOperationalError = psycopg2.OperationalError
