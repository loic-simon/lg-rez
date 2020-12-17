"""lg-rez / blocs / Outils pour tables de données

Modification, récupération d'informations sur la structure de la table...

"""

import datetime
import re

import difflib
import unidecode
from sqlalchemy.orm.attributes import flag_modified     # Permet de "signaler" les entrées modifiées, à commit en base

def _remove_accents(s):
    """Renvoie la chaîne non accentuée, mais conserve les caractères spéciaux (emojis...)
    """
    p = re.compile("([À-ʲΆ-ת])")      # Abracadabrax, c'est moche mais ça marche
    return p.sub(lambda c: unidecode.unidecode(c.group()), s)


def modif(item, col, value):
    """Utilitaire : fait ``<item>.<col> = <value>`` et le marque (:func:`~sqlalchemy.orm.attributes.flag_modified`) pour le commit

    Args:
        item (:class:`.bdd.Base`): entrée de BDD à modifier
        col (:class:`str`): colonne à modifier (doit être un attribut valide de la table)
        value (``type(`item`.`col`)``): nouvelle valeur
    """
    setattr(item, col, value)
    flag_modified(item, col)


def transtype(value, col, SQL_type, nullable):
    """Utilitaire : type un input brut selon le type de sa colonne

    Args:
        value (:class:`object`):        valeur à transtyper
        col (:class:`str`):             nom de la colonne associée
        SQL_type (:class:`str`):        type SQL associé, (tel que retourné par :func:`.get_SQL_types` avec ``detail=False``). Types pris en charge : ``"String"``, ``"Integer"``, ``"BigInteger"``, ``"Boolean"``, ``"Time"``, ``"DateTime"``
        nullable (:class:`bool`):       ``True`` si la value peut être ``None`` (cf :func:`.get_SQL_nullable`), ``False`` sinon

    Returns:
        L'objet Python correspondant au type de la colonne (:class:`str`, :class:`int`, :class:`bool`, :class:`datetime.time`, :class:`datetime.datetime`) ou ``None`` (si autorisé)

    Raises:
        ``ValueError``: si la conversion n'est pas possible (ou si ``value`` vaut ``None`` et ``nullable`` est ``False``)
        ``KeyError``: pour un type de colonne non pris en compte
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
    """Renvoie la liste des noms des colonnes d'une table

    Args:
        table (:class:`.bdd.Base` subclass): table de données

    Returns:
        :class:`list`\[:class:`str`\]
    """
    raw_cols = table.__table__.columns
    return [col.key for col in raw_cols]


def get_primary_col(table):
    """Renvoie le nom de la colonne clé primaire de <table>

    Args:
        table (:class:`.bdd.Base` subclass): table de données

    Returns:
        :class:`str`
    """
    raw_cols = table.__table__.columns
    return [col.key for col in raw_cols if col.primary_key][0]


def get_SQL_types(table, detail=False):
    """Renvoie un dictionnaire {colonne: type SQL}

    Args:
        table (:class:`.bdd.Base` subclass): table de données
        detail (:class:`bool`):

            - Si ``True``, renvoie l'objet type SQL (``col.type``, :class:`sqlalchemy.sql.sqltypes`) : ``String(length=32)``, ``BigInteger``...
            - Si ``False``, renvoie le nom du type (``col.type.__name__``) : ``"String"``, ``"BigInteger"``...

    Returns:
        - :class:`dict`\[:class:`str`, :class:`str`\] (``detail`` ``False``)

    Returns:
        - :class:`dict`\[:class:`str`, :class:`type`\] (``detail`` ``True``)
    """
    raw_cols = table.__table__.columns
    if detail:
        return {col.key: col.type for col in raw_cols}
    else:
        return {col.key: type(col.type).__name__ for col in raw_cols}


def get_SQL_nullable(table):
    """Renvoie un dictionnaire {colonne: accepte les NULL ?}

    Args:
        table (:class:`.bdd.Base` subclass): table de données

    Returns:
        - :class:`dict`\[:class:`str`, :class:`bool`\]
    """
    raw_cols = table.__table__.columns
    return {col.key: col.nullable for col in raw_cols}


def find_nearest(chaine, table, sensi=0.25, filtre=None, carac=None, solo_si_parfait=True, match_first_word=False):
    """Recherche le(s) plus proche résultat(s) dans une table

    Args:
        chaine (:class:`str`): motif à rechercher
        table (:class:`.bdd.Base` subclass): table de données dans laquelle rechercher
        sensi (:class:`float`): ratio minimal pour retenir une entrée
        filtre (:class:`sqlalchemy.sql.elements.BinaryExpression`): argument de :meth:`~sqlalchemy.orm.query.Query.filter` (``Table.colonne == valeur``)
        carac (:class:`str`): colonne selon laquelle rechercher (défaut : colonne primaire de la table)
        solo_si_parfait (:class:`bool`): si ``True``, renvoie uniquement le premier élément de score ``1`` trouvé s'il existe (ignore les autres éléments, même si ``>= sensi``)
        match_first_word (:class:`bool`): si ``True``, teste aussi ``chaine`` vis à vis du premier *mot* (caractères précédent la première espace) de chaque entrée, et conserve ce score si il est supérieur (``table.carac`` doit être de type ``String``).

    Returns:
        :class:`list`\[\(:class:`.bdd.Base`, :class:`float`\)\]: La/les entrée(s) correspondant le mieux à ``chaine``, sous forme de liste de tuples ``(element, score*)`` triés par score\* décroissant

    \*Score = ratio de :class:`difflib.SequenceMatcher`, i.e. proportion de caractères communs aux deux chaînes
    """
    SM = difflib.SequenceMatcher()                      # Création du comparateur de chaînes
    slug1 = _remove_accents(chaine).lower()             # Cible en minuscule et sans accents
    SM.set_seq1(slug1)                                  # Première chaîne à comparer : cible demandée

    if not filtre:
        query = table.query.all()
    else:
        query = table.query.filter(filtre).all()

    scores = []
    if not carac:
        carac = get_primary_col(table)

    for entry in query:
        slug2 = _remove_accents(getattr(entry, carac)).lower()

        SM.set_seq2(slug2)                              # Pour chaque élément, on compare la cible à son nom (en non accentué)
        score = SM.ratio()                              # On calcule la ressemblance

        if match_first_word:
            SM.set_seq2(slug2.split(maxsplit=1)[0])
            scorep = SM.ratio()
            if scorep > score:
                score = scorep

        if score == 1:          # Cas particulier : élément demandé correspondant exactement à un en BDD
            if solo_si_parfait:             # Si demandé, on le renvoie direct
                return [(entry, score)]
            else:                           # Sinon, on ne renverra que les éléments de score 1
                sensi = 1

        scores.append((entry, score))


    bests = [(entry, score) for (entry, score) in sorted(scores, key=lambda x: x[1], reverse=True) if score >= sensi]
    # Meilleurs résultats, dans l'ordre ; si élément parfait trouvé, sensi = 1 donc ne renvoie que les parfaits
    return bests
