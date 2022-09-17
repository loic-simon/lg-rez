"""lg-rez / bdd / Briques de connection

Métaclasse et classe de base des tables de données, fonction de connection

"""

from __future__ import annotations

from collections import abc
import json
import re
import difflib
import typing
from typing import Any, Callable, Generic

import discord
import sqlalchemy
import sqlalchemy.ext.asyncio
import sqlalchemy.orm
import unidecode

from lgrez import config
from lgrez.blocs import env


def _remove_accents(text: str) -> str:
    """Renvoie la chaîne non accentuée.

    Mais conserve les caractères spéciaux (emojis...)
    """
    p = re.compile("([À-ʲΆ-ת])")  # Abracadabrax, c'est moche mais ça marche
    return p.sub(lambda m: unidecode.unidecode(m.group()), text)


# ---- Objets de base des classes de données
# Dictionnaire {nom de la base -> table}, automatiquement rempli par
# sqlalchemy.orm.declarative_base
tables = {}

mapper_registry = sqlalchemy.orm.registry(class_registry=tables)


class TableMeta(sqlalchemy.orm.DeclarativeMeta):
    """Métaclasse des tables de données de LG-Rez.

    Sous-classe de :class:`sqlalchemy.orm.decl_api.DeclarativeMeta`.

    Cette métaclasse :
        - nomme automatiquement la table ``cls.__name__.lower() + "s"``,
        - ajoute une note commune aux docstrings de chaque classe,
        - définit des méthodes et propriétés de classe simplifiant
          l'utilisation des tables.
    """

    def __init__(cls, name: str, bases: tuple, dic: dict, comment: str | None = None, **kwargs) -> None:
        """Constructs the data class"""
        if name == "TableBase":
            # Ne pas documenter TableBase (pas une vraie table)
            return

        cls.__tablename__ = name.lower() + "s"
        if comment is None:
            comment = cls.__doc__

        cls.registry = mapper_registry
        # dic["registry"] = mapper_registry  # un peu de magie noire...
        super().__init__(name, bases, dic, comment=comment, **kwargs)

        cls._attrs = {
            n: k
            for n, k in dic.items()
            if isinstance(
                k,
                (
                    sqlalchemy.Column,
                    sqlalchemy.orm.relationships.RelationshipProperty,
                ),
            )
        }

        cls.__doc__ += f"""\n    Note:
        Cette classe est une *classe de données* (sous-classe de
        :class:`.TableBase`) représentant la table ``{cls.__tablename__}`` :

        - Les propriétés et méthodes détaillées dans :class:`.TableMeta`
          sont utilisables (sur la classe uniquement) ;
        - Tous les attributs ci-dessous sont du type indiqué pour les
          instances (entrées de BDD), mais de type
          :class:`sqlalchemy.orm.attributes.InstrumentedAttribute`
          pour la classe elle-même.
        """  # On adore la doc vraiment

    @property
    def columns(cls) -> sqlalchemy.sql.base.ImmutableColumnCollection:
        """Raccourci pour ``Table.__table__.columns`` (mapping nom -> colonne).

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
    def attrs(cls) -> abc.Mapping[str, sqlalchemy.schema.Column | sqlalchemy.orm.RelationshipProperty]:
        """: Attributs de données publics des instances.

        (dictionnaire nom -> colonne / relationship)
        """
        return cls._attrs

    @property
    def primary_col(cls) -> sqlalchemy.schema.Column:
        """Colonne clé primaire de la table.

        Raises:
            :exc:`ValueError`: Pas de colonne clé primaire pour cette
                table, ou plusieurs
        """
        cols = cls.__table__.primary_key.columns
        if not cols:
            raise ValueError(f"Pas de clé primaire pour {cls.__name__}")
        if len(cols) > 1:
            raise ValueError("Plusieurs colonnes clés primaires pour " f"{cls.__name__} (clé composite)")
        return next(iter(cols))

    async def find_nearest(
        cls,
        chaine: str,
        col: sqlalchemy.schema.Column | str | None = None,
        sensi: float = 0.25,
        filtre: sqlalchemy.sql.expression.BinaryExpression | None = None,
        solo_si_parfait: bool = True,
        parfaits_only: bool = True,
        match_first_word: bool = False,
    ) -> list[tuple[TableBase, float]]:
        """Recherche les plus proches résultats d'une chaîne donnée.

        Args:
            chaine: motif à rechercher
            col: colonne selon laquelle rechercher (défaut : colonne primaire). Doit être de type textuel.
            sensi: score\* minimal pour retenir une entrée
            filtre: clause de filtrage à appliquer (ex. ``Table.colonne == valeur``)
            solo_si_parfait: si ``True`` (défaut), renvoie uniquement le premier élément de score\* ``1`` trouvé
                s'il existe (ignore les autres éléments, même si ``>= sensi`` ou même ``1``)
            parfaits_only: si ``True`` (défaut), ne renvoie que les éléments de score\* ``1`` si on en trouve
                au moins un (ignore les autres éléments, même si ``>= sensi`` ;
                pas d'effet si ``solo_si_parfait`` vaut ``True``)
            match_first_word: si ``True``, teste aussi ``chaine`` vis à vis du premier *mot* de chaque entrée
                (caractères précédent la première espace), et conserve ce score si il est supérieur.

        Returns:
            Les entrées correspondant le mieux à ``chaine``, sous forme de liste de tuples ``(element, score*)``
            triés par score\* décroissant (et ce même si un seul résultat).

        Raises:
            ValueError: ``col`` inexistante ou pas de type textuel
            ~readycheck.NotReadyError: session non initialisée (:attr:`.lgrez.config.session` vaut ``None``)

        *\*score* = ratio de :class:`difflib.SequenceMatcher` (proportion de caractères communs aux deux chaînes).

        Note:
            Les chaînes sont comparées sans tenir compte de l'accentuation ni de la casse.
        """
        if not col:
            col = cls.primary_col
        elif isinstance(col, str):
            try:
                col = cls.columns[col]
            except LookupError:
                raise ValueError(f"{cls.__name__}.find_nearest: Colonne '{col}' invalide") from None

        if not isinstance(col.type, sqlalchemy.String):
            raise ValueError(f"{cls.__name__}.find_nearest: " f"Colonne {col.key} pas de type textuel")

        select = Data.select(cls)
        if filtre is not None:
            select = select.where(filtre)

        results = await select.all()

        SM = difflib.SequenceMatcher()
        # Première chaîne à comparer : cible, en minuscule et sans accents
        slug1 = _remove_accents(chaine).lower()
        SM.set_seq1(slug1)

        scores = []
        for entry in results:
            slug2 = _remove_accents(getattr(entry, col.key)).lower()

            # On compare chaque élément à la cible (en non accentué)
            SM.set_seq2(slug2)
            score = SM.ratio()  # Taux de ressemblance

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


@mapper_registry.as_declarative_base(metaclass=TableMeta)
class TableBase:
    """Classe de base des tables de données.

    (construite par :func:`sqlalchemy.orm.registry.generate_base`)
    """

    @property
    def primary_key(self) -> int | str:
        """Clé primaire de l'instance (``id``, ``slug``...).

        Raccourci pour ``getattr(inst, type(inst).primary_col.key)``.

        Raises:
            :exc:`ValueError`: Pas de colonne clé primaire pour la
                table de cette instance, ou plusieurs.
        """
        key = type(self).primary_col.key
        return getattr(self, key)

    _T = typing.TypeVar("_T", bound="TableBase")


# ---- Autodoc objects


def autodoc_Column(*args, doc: str = "", comment: str | None = None, **kwargs) -> sqlalchemy.Column:
    """Returns Python-side and SQL-side well documented Column.

    Use exactly as :class:`sqlalchemy.Column <sqlalchemy.schema.Column>`.

    Args:
        \*args, \*\*kwargs: passed to :class:`sqlalchemy.schema.Column`.
        doc: column description, enhanced with column infos
            (Python and SQL types, if nullable, primary...) and
            passed to ``Column.doc``.
        comment: passed to ``Column.comment``; defaults to ``doc``
            (not enhanced). Set it to ``''`` to disable comment creation.

    Returns:
        La colonne annotée.
    """
    if comment is None:
        comment = doc
    col = sqlalchemy.Column(*args, **kwargs, comment=comment)
    sa_type = f":class:`{col.type!r} " f"<sqlalchemy.types.{type(col.type).__name__}>`"
    py_type = col.type.python_type
    if py_type.__module__ in ("builtins", "lgrez.bdd.enums"):
        py_type_str = py_type.__name__
    elif py_type.__module__.startswith("lgrez.bdd.model_"):
        py_type_str = f"lgrez.bdd.{py_type.__name__}"
    else:
        py_type_str = f"{py_type.__module__}.{py_type.__name__}"
    or_none = " | ``None``" if col.nullable else ""
    primary = " (clé primaire)" if col.primary_key else ""
    autoinc = (
        " (auto-incrémental)" if (col.autoincrement and primary and isinstance(col.type, sqlalchemy.Integer)) else ""
    )
    nullable = "" if (col.nullable or autoinc) else " (NOT NULL)"
    default = f" (défaut ``{col.default.arg!r}``)" if col.default else ""
    col.doc = (
        f"{doc}{primary}{autoinc}{nullable}{default}\n\n"
        f"Type SQLAlchemy : {sa_type} / Type SQL : ``{col.type}``\n\n"
        f":type: :class:`{py_type_str}`{or_none}"
    )
    return col


def autodoc_ManyToOne(
    tablename: str, *args, doc: str = "", nullable: bool = False, lazy="joined", **kwargs
) -> sqlalchemy.orm.RelationshipProperty:
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
        doc: relationship description, enhanced with class name
            and relationship type.
        nullable: indicates whether the relationship can be
            omitted (impacts docs only, default ``False``).

    Returns:
        The annotated relationship.
    """
    first, sep, rest = doc.partition("\n")
    or_none = " | ``None``" if nullable else ""
    doc = f":class:`~.bdd.{tablename}`{or_none}: {first} *(many-to-one relationship)*"
    if not nullable:
        doc += " (NOT NULL)"
    if rest:
        doc += sep + rest

    return sqlalchemy.orm.relationship(tablename, *args, doc=doc, lazy=lazy, **kwargs)


def autodoc_OneToMany(tablename: str, *args, doc: str = "", **kwargs) -> sqlalchemy.orm.RelationshipProperty:
    """Returns Python-side well documented one-to-many relationship.

    Represents a relationship where each element in this table is
    linked to **several elements** in ``tablename``, itself back-
    refering to **one element** in this table.

    Example: ``Editor.books`` (an editor publishes several books,
    each book has an editor)

    Use exactly as :func:`sqlalchemy.orm.relationship`.

    Args:
        \*args, \*\*kwargs: passed to :class:`sqlalchemy.orm.relationship`.
        doc: relationship description, enhanced with class name
            and relationship type.

    Returns:
        The annotated relationship.
    """
    first, sep, rest = doc.partition("\n")
    doc = f"Sequence[~bdd.{tablename}]: {first} *(one-to-many relationship)*"
    if rest:
        doc += sep + rest

    return sqlalchemy.orm.relationship(tablename, *args, doc=doc, **kwargs)


def autodoc_DynamicOneToMany(tablename: str, *args, doc: str = "", **kwargs) -> sqlalchemy.orm.RelationshipProperty:
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
        doc: relationship description, enhanced with class name
            and relationship type.

    Returns:
        The annotated relationship.
    """
    first, sep, rest = doc.partition("\n")
    doc = f"~sqlalchemy.orm.query.Query[~bdd.{tablename}]: {first} *(dynamic one-to-many relationship)*"
    if rest:
        doc += sep + rest

    return sqlalchemy.orm.dynamic_loader(tablename, *args, doc=doc, **kwargs)


def autodoc_ManyToMany(tablename: str, *args, doc: str = "", **kwargs) -> sqlalchemy.orm.RelationshipProperty:
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
        The annotated relationship.
    """
    first, sep, rest = doc.partition("\n")
    doc = f"Sequence[~bdd.{tablename}]: {first} *(many-to-many relationship)*"
    if rest:
        doc += sep + rest

    return sqlalchemy.orm.relationship(tablename, *args, doc=doc, **kwargs)


# ---- Connection function


class _DiscordObjectsEncoder(json.JSONEncoder):
    def default(self, obj):
        match obj:
            case discord.abc.GuildChannel() | discord.app_commands.AppCommandChannel():
                return {"__discord_type__": "channel", "__discord_id__": obj.id}
            case discord.Member():
                return {"__discord_type__": "member", "__discord_id__": obj.id}
            case discord.Role():
                return {"__discord_type__": "role", "__discord_id__": obj.id}
            case _:
                # Let the base class default method raise the TypeError
                return super().default(obj)


class _DiscordObjectsDecoder(json.JSONDecoder):
    def __init__(self, *, object_hook: Callable[[dict[str, Any]], Any] | None = None, **kwargs) -> None:
        self._object_hook = object_hook or (lambda dic: dic)
        super().__init__(object_hook=self.discord_object_hook, **kwargs)

    def discord_object_hook(self, dic: dict[str, Any]):
        object_id = dic.get("__discord_id__", 0)
        match dic.get("__discord_type__"):
            case None:
                return self._object_hook(dic)
            case "channel":
                return config.guild.get_channel(object_id)
            case "member":
                return config.guild.get_member(object_id)
            case "role":
                return config.guild.get_role(object_id)
            case other:
                raise ValueError(f"Unhandled __discord_type__ in custom JSON: {other}")


async def connect() -> Callable[[], sqlalchemy.ext.asyncio.AsyncSession]:
    """Se connecte à la base de données et prépare les objets connectés.

    - Utilise la variable d'environment ``LGREZ_DATABASE_URI``
    - Crée les tables si nécessaire
    - Prépare :obj:`.config.engine` et :obj:`.config.session`
    """
    LGREZ_DATABASE_URI = env.load("LGREZ_DATABASE_URI")
    # Moteur SQL : connexion avec le serveur
    config.engine = sqlalchemy.ext.asyncio.create_async_engine(
        LGREZ_DATABASE_URI,
        pool_pre_ping=True,
        json_serializer=_DiscordObjectsEncoder().encode,
        json_deserializer=_DiscordObjectsDecoder().decode,
    )

    async with config.engine.begin() as conn:
        await conn.run_sync(TableBase.metadata.create_all)

    # Création des tables si elles n'existent pas déjà
    return sqlalchemy.orm.sessionmaker(
        bind=config.engine, expire_on_commit=False, class_=sqlalchemy.ext.asyncio.AsyncSession
    )


_T = typing.TypeVar("_T", bound=TableMeta)


class Select(Generic[_T]):
    def __init__(self, table: type[_T]) -> None:
        self.table = table
        self.statement: sqlalchemy.sql.expression.Select = sqlalchemy.select(table)

    def where(self, *clauses: sqlalchemy.sql.expression.BinaryExpression) -> Select[_T]:
        self.statement.where(*clauses)
        return self

    def order_by(self, *columns: sqlalchemy.sql.expression.ColumnElement) -> Select[_T]:
        self.statement.order_by(*columns)
        return self

    async def _scalars(self, statement: sqlalchemy.sql.expression.Select) -> sqlalchemy.engine.ScalarResult:
        return await config.session.scalars(statement)

    async def all(self) -> list[_T]:
        result = await self._scalars(self.statement)
        return result.all()


class Data:
    @staticmethod
    def select(table: type[_T]) -> Select[_T]:
        return Select(table)

    @staticmethod
    async def get(table: type[_T], id) -> _T | None:
        return await config.session.get(table, id)

    @staticmethod
    async def commit() -> None:
        await config.session.commit()

    @staticmethod
    async def add(*objects: _T, commit: bool = True) -> None:
        config.session.add_all(objects)
        if commit:
            await Data.commit()

    @staticmethod
    async def delete(*objects: _T, commit: bool = True) -> None:
        for object in objects:
            await config.session.delete(object)
        if commit:
            await Data.commit()
