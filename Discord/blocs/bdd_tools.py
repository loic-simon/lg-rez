import datetime
from sqlalchemy.orm.attributes import flag_modified     # Permet de "signaler" les entrées modifiées, à commit en base


def modif(item, col, value):
    setattr(item, col, value)
    flag_modified(item, col)

def transtype(value, col, SQL_type, nullable):      # Utilitaire : type un input brut (BDD, POST, GET...) selon le type de sa colonne
    try:
        if value in (None, '', 'None', 'none', 'Null', 'null', 'not set', 'non défini'):
            if nullable:
                return None
            else:
                raise ValueError
        elif SQL_type == "String":
            return str(value)
        elif SQL_type in ("Integer", "BigInteger"):
            return int(value)
        elif SQL_type == "Boolean":
            if value in [True, 1] or (isinstance(value, str) and value.lower() in ['true', 'vrai', 'on', 'oui', 'yes']):
                return True
            elif value in [False, 0] or (isinstance(value, str) and value.lower() in ['false', 'faux', 'off', 'non', 'no']):
                return False
            else:
                raise ValueError()
        elif SQL_type == "Time":
            h, m = value.split(':')
            return datetime.time(int(h), int(m))
        else:
            raise KeyError(f"unknown column type for column '{col}': '{SQL_type}'")
    except (ValueError, TypeError):
        raise ValueError(f"Valeur '{value}' incorrecte pour la colonne '{col}' (type '{SQL_type}'/{'NOT NULL' if not nullable else ''})")


def get_cols(table):                    # Renvoie la liste des colonnes de la table
    raw_cols = table.__table__.columns
    return [col.key for col in raw_cols]
    
def get_primary_col(table):             # Renvoie la colonne étant une clé primaire de la table
    raw_cols = table.__table__.columns
    return [col.key for col in raw_cols if col.primary_key][0]

def get_SQL_types(table, detail=False):  # Renvoie un dictionnaire {colonne: type SQL} pour la table
    raw_cols = table.__table__.columns
    if detail:                              # detail = True ==> types "VARCHAR(N)", "INTEGER"...
        return {col.key:col.type for col in raw_cols}
    else:                                   # detail = False ==> types "String", "Integer"...
        return {col.key:type(col.type).__name__ for col in raw_cols}

def get_SQL_nullable(table):               # Renvoie un dictionnaire {colonne: accepte les NULL ? (bool)} pour la table
    raw_cols = table.__table__.columns
    return {col.key:col.nullable for col in raw_cols}
