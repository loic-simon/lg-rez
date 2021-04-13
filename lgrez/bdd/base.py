"""lg-rez / bdd / Briques de connection

Métaclasse et classe de base des tables de données, fonction de connection

"""

import re
import difflib

import sqlalchemy
from sqlalchemy.ext import declarative
import unidecode

from lgrez import config
from lgrez.blocs import env


def _remove_accents(text):
    """Renvoie la chaîne non accentuée.

    Mais conserve les caractères spéciaux (emojis...)
    """
    p = re.compile("([À-ʲΆ-ת])")    # Abracadabrax, c'est moche mais ça marche
    return p.sub(lambda m: unidecode.unidecode(m.group()), text)


# ---- Objets de base des classes de données

class TableMeta(declarative.api.DeclarativeMeta):
    """Métaclasse des tables de données de LG-Rez.

    Sous-classe de :class:`sqlalchemy.declarative.api.DeclarativeMeta`.

    Cette métaclasse :
        - nomme automatiquement la table ``cls.__name__.lower() + "s"``,
        - ajoute une note commune aux docstrings de chaque classe,
        - définit des méthodes et propriétés de classe simplifiant
          l'utilisation des tables.
    """
    def __init__(cls, name, bases, dic, comment=None, **kwargs):
        """Constructs the data class"""
        if name == "TableBase":
            # Ne pas documenter TableBase (pas une vraie table)
            return

        cls.__tablename__ = name.lower() + "s"
        if comment is None:
            comment = cls.__doc__
        super().__init__(name, bases, dic, comment=comment, **kwargs)

        cls._attrs = {n: k for n, k in dic.items() if isinstance(k, (
            sqlalchemy.Column,
            sqlalchemy.orm.relationships.RelationshipProperty,
        ))}

        cls.__doc__ += f"""\n    Note:
        Cette classe est une *classe de données* (sous-classe de
        :class:`.TableBase`) représentant la table ``{cls.__tablename__}`` :

        - Les propriétés et méthodes détaillées dans :class:`.TableMeta`
          sont utilisables (sur la classe uniquement) ;
        - Tous les attributs ci-dessous sont du type indiqué pour les
          instances (entrées de BDD), mais de type
          :class:`sqlalchemy.orm.attributes.InstrumentedAttribute`
          pour la classe elle-même.
        """       # On adore la doc vraiment

    @property
    def query(cls):
        """sqlalchemy.orm.query.Query: Raccourci pour
        ``.config.session.query(Table)``.

        Raises:
            :exc:`ready_check.NotReadyError`: session non initialisée
                (:obj:`.config.session` vaut ``None``)
        """
        return config.session.query(cls)

    @property
    def columns(cls):
        """sqlalchemy.sql.base.ImmutableColumnCollection: Raccourci pour
        ``Table.__table__.columns`` (pseudo-dictionnaire nom -> colonne).

        Comportement global de dictionnaire :

            - ``Table.columns["nom"]`` -> colonne associée ;
            - ``Table.columns.keys()`` -> noms des colonnes ;
            - ``Table.columns.values()`` -> objets Column ;
            - ``Table.columns.items()`` -> tuples (nom, colonne) ;

        MAIS itération sur les colonnes (valeurs du dictionnaire) :

            - ``list(Table.columns)`` -> objets Column ;
            - ``for col in Table.columns`` -> objets Column.
        """
        return cls.__table__.columns

    @property
    def attrs(cls):
        """Mapping[:class:`str`, :class:`sqlalchemy.schema.Column` |\
        :class:`sqlalchemy.orm.RelationshipProperty`]: Attributs de
        données publics des instances (dictionnaire nom -> colonne
        / relationship).
        """
        return cls._attrs

    @property
    def primary_col(cls):
        """sqlalchemy.schema.Column: Colonne clé primaire de la table.

        Raises:
            :exc:`ValueError`: Pas de colonne clé primaire pour cette
                table, ou plusieurs
        """
        cols = cls.__table__.primary_key.columns
        if not cols:
            raise ValueError(f"Pas de clé primaire pour {cls.__name__}")
        if len(cols) > 1:
            raise ValueError("Plusieurs colonnes clés primaires pour "
                             f"{cls.__name__} (clé composite)")
        return next(iter(cols))

    def find_nearest(cls, chaine, col=None, sensi=0.25, filtre=None,
                     solo_si_parfait=True, parfaits_only=True,
                     match_first_word=False):
        """Recherche les plus proches résultats d'une chaîne donnée.

        Args:
            chaine (str): motif à rechercher
            col (:class:`sqlalchemy.schema.Column` | :class:`str`):
                colonne selon laquelle rechercher (défaut : colonne
                primaire). Doit être de type textuel.
            sensi (float): score\* minimal pour retenir une entrée
            filtre (~sqlalchemy.sql.expression.BinaryExpression):
                argument de :meth:`query.filter()
                <sqlalchemy.orm.query.Query.filter>`
                (ex. ``Table.colonne == valeur``)
            solo_si_parfait (bool): si ``True`` (défaut), renvoie
                uniquement le premier élément de score\* ``1`` trouvé
                s'il existe (ignore les autres éléments, même si
                ``>= sensi`` ou même ``1``)
            parfaits_only (bool): si ``True`` (défaut), ne renvoie que
                les éléments de score\* ``1`` si on en trouve au moins
                un (ignore les autres éléments, même si ``>= sensi`` ;
                pas d'effet si ``solo_si_parfait`` vaut ``True``)
            match_first_word (bool): si ``True``, teste aussi
                ``chaine`` vis à vis du premier *mot* (caractères
                précédentla première espace) de chaque entrée, et
                conserve ce score si il est supérieur.

        Returns:
            :class:`list`\[\(:class:`TableBase`, :class:`float`\)\]: Les
            entrées correspondant le mieux à ``chaine``, sous forme de
            liste de tuples ``(element, score*)`` triés par score\*
            décroissant (et ce même si un seul résultat).

        Raises:
            ValueError: ``col`` inexistante ou pas de type textuel
            ~ready_check.NotReadyError: session non initialisée
                (:attr:`.lgrez.config.session` vaut ``None``)

        *\*score* = ratio de :class:`difflib.SequenceMatcher`, i.e.
        proportion de caractères communs aux deux chaînes.

        Note:
            Les chaînes sont comparées sans tenir compte de
            l'accentuation ni de la casse.
        """
        if not col:
            col = cls.primary_col
        elif isinstance(col, str):
            try:
                col = cls.columns[col]
            except LookupError:
                raise ValueError(
                    f"{cls.__name__}.find_nearest: Colonne '{col}' invalide"
                ) from None

        if not isinstance(col.type, sqlalchemy.String):
            raise ValueError(f"{cls.__name__}.find_nearest: "
                             f"Colonne {col.key} pas de type textuel")

        query = cls.query
        if filtre is not None:
            query = query.filter(filtre)

        results = query.all()

        SM = difflib.SequenceMatcher()
        # Première chaîne à comparer : cible, en minuscule et sans accents
        slug1 = _remove_accents(chaine).lower()
        SM.set_seq1(slug1)

        scores = []
        for entry in results:
            slug2 = _remove_accents(getattr(entry, col.key)).lower()

            # On compare chaque élément à la cible (en non accentué)
            SM.set_seq2(slug2)
            score = SM.ratio()          # Taux de ressemblance

            if match_first_word:
                # On compare aussi avec le premier mot, si demandé
                first_word = slug2.split(maxsplit=1)[0]
                SM.set_seq2(first_word)
                score_fw = SM.ratio()
                score = max(score, score_fw)

            if score == 1:
                # Cas particulier : élément demandé correspond exactement
                # à un élément existant
                if solo_si_parfait:
                    # Si demandé, on le renvoie direct
                    return [(entry, score)]
                elif parfaits_only:
                    # Si demandé, on ne renverra que les éléments de score 1
                    sensi = 1

            scores.append((entry, score))

        # On ne garde que les résultats >= sensi, dans l'ordre ;
        # si élément parfait trouvé et parfaits_only, sensi = 1 donc
        # ne renvoie que les parfaits
        bests = [(e, score) for (e, score) in scores if score >= sensi]
        return sorted(bests, key=lambda x: x[1], reverse=True)


# Dictionnaire {nom de la base -> table}, automatiquement rempli par
# sqlalchemy.ext.declarative.declarative_base
tables = {}


@declarative.as_declarative(class_registry=tables, metaclass=TableMeta)
class TableBase:
    """Classe de base des tables de données.

    (construite par :func:`sqlalchemy.ext.declarative.declarative_base`)
    """
    @property
    def primary_key(self):
        """Any: Clé primaire de l'instance (``id``, ``slug``...).

        Raccourci pour ``getattr(inst, type(inst).primary_col.key)``.

        Raises:
            :exc:`ValueError`: Pas de colonne clé primaire pour la
                table de cette instance, ou plusieurs.
        """
        key = type(self).primary_col.key
        return getattr(self, key)

    @staticmethod
    def update():
        """Applique les modifications en attente en base (commit).

        Toutes les modifications, y compris des autres instances,
        seront enregistrées.

        Globlament équivalent à::

            config.session.commit()

        """
        config.session.commit()

    def add(self, *other):
        """Enregistre l'instance dans la base de donnée et commit.

        Semble équivalent à :meth:`update` si l'instance est déjà
        présente en base.

        Args:
            \*other: autres instances à enregistrer dans le même commit,
                éventuellement. Utilisation recommandée :
                ``<Table>.add(*items)``.

        Examples:
            - ``item.add()``
            - ``<Table>.add(*items)``

        Globlament équivalent à::

            config.session.add(self)
            config.session.add_all(other)

            config.session.commit()
        """
        config.session.add(self)
        if other:
            config.session.add_all(other)

        self.update()

    def delete(self, *other):
        """Supprime l'instance de la base de données et commit.

        Args:
            \*other: autres instances à supprimer dans le même commit,
                éventuellement.

        Examples:
            - ``item.delete()``
            - ``<Table>.delete(*items)``

        Raises:
            sqlalchemy.exc.SAWarning: l'instance a déjà été supprimmée
                (Warning, pas exception : ne bloque pas l'exécution).

        Globlament équivalent à::

            config.session.delete(self)
            for item in others:
                config.session.delete(item)

            config.session.commit()
        """
        config.session.delete(self)
        for item in other:
            config.session.delete(item)

        self.update()


# ---- Autodoc objects

def autodoc_Column(*args, doc="", comment=None, **kwargs):
    """Returns Python-side and SQL-side well documented Column.

    Use exactly as :class:`sqlalchemy.Column <sqlalchemy.schema.Column>`.

    Args:
        \*args, \*\*kwargs: passed to :class:`sqlalchemy.schema.Column`.
        doc (str): column description, enhanced with column infos
            (Python and SQL types, if nullable, primary...) and
            passed to ``Column.doc``.
        comment (str): passed to ``Column.comment``; defaults to ``doc``
            (not enhanced). Set it to ``''`` to disable comment creation.

    Returns:
        :class:`sqlalchemy.schema.Column`
    """
    if comment is None:
        comment = doc
    col = sqlalchemy.Column(*args, **kwargs, comment=comment)
    sa_type = (f":class:`{col.type!r} "
               f"<sqlalchemy.types.{type(col.type).__name__}>`")
    py_type = col.type.python_type
    if py_type.__module__ in ("builtins", "lgrez.bdd.enums"):
        py_type_str = py_type.__name__
    elif py_type.__module__.startswith("lgrez.bdd.model_"):
        py_type_str = f"lgrez.bdd.{py_type.__name__}"
    else:
        py_type_str = f"{py_type.__module__}.{py_type.__name__}"
    or_none = " | ``None``" if col.nullable else ""
    primary = " (clé primaire)" if col.primary_key else ""
    autoinc = (" (auto-incrémental)"
               if (col.autoincrement and primary
                   and isinstance(col.type, sqlalchemy.Integer))
               else "")
    nullable = "" if (col.nullable or autoinc) else " (NOT NULL)"
    default = f" (défaut ``{col.default.arg!r}``)" if col.default else ""
    col.doc = (f"{doc}{primary}{autoinc}{nullable}{default}\n\n"
               f"Type SQLAlchemy : {sa_type} / Type SQL : ``{col.type}``\n\n"
               f":type: :class:`{py_type_str}`{or_none}")
    return col


def autodoc_ManyToOne(tablename, *args, doc="", nullable=False, **kwargs):
    """Returns Python-side well documented many-to-one relationship.

    Represents a relationship where each element in this table is
    linked to **one element** in ``tablename``, itself back-refering
    to **several elements** in this table.

    Example: ``Book.editor`` (each book has an editor, an editor
    publishes several books)

    Use exactly as :func:`sqlalchemy.orm.relationship`, plus the
    keyword argument :attr:`nullable` (see below).

    Args:
        \*args, \*\*kwargs: passed to :class:`sqlalchemy.orm.relationship`.
        doc (str): relationship description, enhanced with class name
            and relationship type.
        nullable (bool): indicates whether the relationship can be
            omitted (impacts docs only, default ``False``).

    Returns:
        :class:`sqlalchemy.orm.RelationshipProperty`
    """
    first, sep, rest = doc.partition("\n")
    or_none = " | ``None``" if nullable else ""
    doc = (f":class:`~.bdd.{tablename}`{or_none}: {first} "
           "*(many-to-one relationship)*")
    if not nullable:
        doc += " (NOT NULL)"
    if rest:
        doc += sep + rest

    return sqlalchemy.orm.relationship(tablename, *args, doc=doc, **kwargs)


def autodoc_OneToMany(tablename, *args, doc="", **kwargs):
    """Returns Python-side well documented one-to-many relationship.

    Represents a relationship where each element in this table is
    linked to **several elements** in ``tablename``, itself back-
    refering to **one element** in this table.

    Example: ``Editor.books`` (an editor publishes several books,
    each book has an editor)

    Use exactly as :func:`sqlalchemy.orm.relationship`.

    Args:
        \*args, \*\*kwargs: passed to :class:`sqlalchemy.orm.relationship`.
        doc (str): relationship description, enhanced with class name
            and relationship type.

    Returns:
        :class:`sqlalchemy.orm.RelationshipProperty`
    """
    first, sep, rest = doc.partition("\n")
    doc = f"Sequence[~bdd.{tablename}]: {first} *(one-to-many relationship)*"
    if rest:
        doc += sep + rest

    return sqlalchemy.orm.relationship(tablename, *args, doc=doc, **kwargs)


def autodoc_DynamicOneToMany(tablename, *args, doc="", **kwargs):
    """Returns Python-side well documented dynamic one-to-many relationship.

    Represents a relationship where each element in this table is
    linked to **a lot of elements** in ``tablename``, itself back-
    refering to **one element** in this table.

    The difference with :func:`~.autodoc_OneToMany` is that items are NOT
    accessible directly through class attribute, which returns a query
    that but must be fetched first:

    Examples: ``Editor.books.all()``, ``Editor.books.filter_by(...).one()``

    Use exactly as :func:`sqlalchemy.orm.dynamic_loader`.

    Args:
        \*args, \*\*kwargs: passed to :class:`sqlalchemy.orm.dynamic_loader`.
        doc (str): relationship description, enhanced with class name
            and relationship type.

    Returns:
        :class:`sqlalchemy.orm.RelationshipProperty`
    """
    first, sep, rest = doc.partition("\n")
    doc = (f"~sqlalchemy.orm.query.Query[~bdd.{tablename}]: {first} "
           "*(dynamic one-to-many relationship)*")
    if rest:
        doc += sep + rest

    return sqlalchemy.orm.dynamic_loader(tablename, *args, doc=doc, **kwargs)


def autodoc_ManyToMany(tablename, *args, doc="", **kwargs):
    """Returns Python-side well documented many-to-many relationship.

    Represents a relationship where each element in this table is
    linked to **several elements** in ``tablename``, itself back-
    refering to **several elements** in this table.

    Example: ``Book.authors`` (each book has several authors, an
    author writes several books)

    Use exactly as :func:`sqlalchemy.orm.relationship`.

    Args:
        \*args, \*\*kwargs: passed to :class:`sqlalchemy.orm.relationship`.
        doc (str): relationship description, enhanced with class name
            and relationship type.

    Returns:
        :class:`sqlalchemy.orm.RelationshipProperty`
    """
    first, sep, rest = doc.partition("\n")
    doc = f"Sequence[~bdd.{tablename}]: {first} *(many-to-many relationship)*"
    if rest:
        doc += sep + rest

    return sqlalchemy.orm.relationship(tablename, *args, doc=doc, **kwargs)


# ---- Connection function

def connect():
    """Se connecte à la base de données et prépare les objets connectés.

    - Utilise la variable d'environment ``LGREZ_DATABASE_URI``
    - Crée les tables si nécessaire
    - Prépare :obj:`.config.engine` et :obj:`.config.session`
    """
    LGREZ_DATABASE_URI = env.load("LGREZ_DATABASE_URI")
    # Moteur SQL : connexion avec le serveur
    config.engine = sqlalchemy.create_engine(LGREZ_DATABASE_URI,
                                             pool_pre_ping=True)

    # Création des tables si elles n'existent pas déjà
    TableBase.metadata.create_all(config.engine)

    # Ouverture de la session
    Session = sqlalchemy.orm.sessionmaker(bind=config.engine)
    config.session = Session()
