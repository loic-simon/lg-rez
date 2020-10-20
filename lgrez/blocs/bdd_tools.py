import datetime
import re

import difflib
import unidecode
from sqlalchemy.orm.attributes import flag_modified     # Permet de "signaler" les entrées modifiées, à commit en base

def remove_accents(s):
    """Renvoie la chaîne non accentuée, mais conserve les caractères spéciaux (emojis...)"""
    p = re.compile("([À-ʲΆ-ת])")      # Abracadabrax, c'est moche mais ça marche
    return p.sub(lambda c: unidecode.unidecode(c.group()), s)


def modif(item, col, value):
    """Utilitaire : fait <item>.<col> = <value> et le marque (flag_modified) pour le commit"""
    setattr(item, col, value)
    flag_modified(item, col)


def transtype(value, col, SQL_type, nullable):
    """Utilitaire : type un input brut (BDD, POST, GET...) selon le type de sa colonne

    <value>         valeur à transtyper (tous)
    <col>           nom de la colonne associée
    <SQL_type>      type SQL associé. Types pris en compte : "String", "Integer", "BigInteger", "Boolean", "Time", "DateTime"
    <nullable>      True si la value peut être None, False sinon

    Renvoie l'objet Python correspondant au type de la colonne (str, int, bool, datetime.time, datetime.datetime) ou None si autorisé
    Raise ValueError si la conversion n'est pas possible (ou si None et nullable is False), KeyError pour un type de colonne non pris en compte
    """
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
        elif SQL_type == "Time":                # hh:mm
            try:
                h, m, _ = value.split(':')
            except ValueError:
                h, m = value.split(':')
            return datetime.time(hour=int(h), minute=int(m))
        elif SQL_type == "DateTime":            # aaaa-mm-jjThh:mm
            date, time = value.split('T')
            aaaa, mm, jj = date.split('-')
            h, m = time.split(':')
            return datetime.datetime(year=int(aaaa), month=int(mm), day=int(jj), hour=int(h), minute=int(m))
        else:
            raise KeyError(f"unknown column type for column '{col}': '{SQL_type}'")
    except (ValueError, TypeError):
        raise ValueError(f"Valeur '{value}' incorrecte pour la colonne '{col}' (type '{SQL_type}'/{'NOT NULL' if not nullable else ''})")


def get_cols(table):
    """Renvoie la liste des colonnes de <table>"""
    raw_cols = table.__table__.columns
    return [col.key for col in raw_cols]


def get_primary_col(table):
    """Renvoie le nom de la colonne clé primaire de <table>"""
    raw_cols = table.__table__.columns
    return [col.key for col in raw_cols if col.primary_key][0]


def get_SQL_types(table, detail=False):
    """Renvoie un dictionnaire {colonne (str): type SQL (str)} pour <table>"""
    raw_cols = table.__table__.columns
    if detail:                              # detail = True ==> types "VARCHAR(N)", "INTEGER"...
        return {col.key: col.type for col in raw_cols}
    else:                                   # detail = False ==> types "String", "Integer"...
        return {col.key: type(col.type).__name__ for col in raw_cols}


def get_SQL_nullable(table):
    """Renvoie un dictionnaire {colonne (str): accepte les NULL ? (bool)} pour <table>"""
    raw_cols = table.__table__.columns
    return {col.key: col.nullable for col in raw_cols}


async def find_nearest(chaine, table, sensi=0.25, filtre=None, carac=None, solo_si_parfait=True):
    """Recherche le(s) plus proche résultat(s) dans une table

    Renvoie le/les éléments de <table> correspondant le mieux à <chaine> (selon la colonne <carac>, défaut : colonne primaire de la table), répondant à <filtre> (défaut : tous) sous forme de liste de tuples (element, score*) triés par score* décroissant, en se limitant aux scores* supérieurs à <sensi>.

    Si <solo_si_parfait> (défaut), renvoie uniquement le premier élément de score 1 trouvé s'il existe (ignore les autres éléments, même si >= sensi)

    *Score = ratio de difflib.SequenceMatcher, i.e. proportion de caractères communs aux deux chaînes
    """
    SM = difflib.SequenceMatcher()                      # Création du comparateur de chaînes
    slug1 = remove_accents(chaine).lower()              # Cible en minuscule et sans accents
    SM.set_seq1(slug1)                                  # Première chaîne à comparer : cible demandée

    if not filtre:
        query = table.query.all()
    else:
        query = table.query.filter(filtre).all()

    scores = []
    if not carac:
        carac = get_primary_col(table)

    for entry in query:
        slug2 = remove_accents(getattr(entry, carac)).lower()

        SM.set_seq2(slug2)                              # Pour chaque élément, on compare la cible à son nom (en non accentué)
        score = SM.ratio()                              # On calcule la ressemblance

        if carac == "nom":          # CP Prénom Nom : on test sur prénom only aussi
            SM.set_seq2(slug2.split(maxsplit=1)[0])
            scorep = SM.ratio()
            if scorep > score:
                score = scorep

        if score == 1 and solo_si_parfait:              # Cas particulier : élément demandé correspondant exactement à un en BDD
            return [(entry, score)]
        scores.append((entry, score))

    # Si pas d'élément correspondant parfaitement
    bests = [(entry, score) for (entry, score) in sorted(scores, key=lambda x: x[1], reverse=True) if score >= sensi]  # Meilleurs noms, dans l'ordre
    return bests
