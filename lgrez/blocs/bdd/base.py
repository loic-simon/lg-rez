"""lg-rez / blocs / Gestion des données

Déclaration de toutes les tables et leurs colonnes, et connection à la BDD

"""

import difflib

import sqlalchemy
from sqlalchemy.ext import declarative

# from lgrez import config
from lgrez.blocs import env


def _remove_accents(s):
    """Renvoie la chaîne non accentuée, mais conserve les caractères spéciaux (emojis...)
    """
    p = re.compile("([À-ʲΆ-ת])")      # Abracadabrax, c'est moche mais ça marche
    return p.sub(lambda c: unidecode.unidecode(c.group()), s)


class TableMeta(declarative.api.DeclarativeMeta):
    """Métaclasse des tables de données (sous-classe de :class:`sqlalchemy.declarative.api.DeclarativeMeta`)

    Cette métaclasse :
        - définit le nom de la table comme ``cls.__name__.lower() + "s"``,
        - ajoute une note commune aux docstrings de chaque classe,
        - définit des méthodes et propriétés de classe simplifiant l'utilisation des tables.
    """
    def __init__(cls, *args, **kwargs):
        """Constructs the data class"""
        if cls.__name__ == "TableBase":
            # Ne pas documenter TableBase (pas une vraie table)
            return

        cls.__tablename__ = cls.__name__.lower() + "s"
        super().__init__(*args, **kwargs)

        cls.__doc__ += f"""\n    Note:
        Cette classe est une *classe de données* (sous-classe de :class:`.TableBase`) représentant la table ``{cls.__tablename__}`` :

        - Les propriétés et méthodes détaillées dans :class:`.TableMeta` sont utilisables (sur la classe uniquement) ;
        - Tous les attributs ci-dessous sont du type indiqué pour les instances (entrées de BDD), mais de type :class:`sqlalchemy.orm.attributes.InstrumentedAttribute` pour la classe elle-même.
        """       # On adore la doc vraiment

    @property
    def query(cls):
        """:class:`sqlalchemy.orm.query.Query`: Raccourci pour ``config.session.query(Table)``

        Raises:
            :exc:`RuntimeError`: session non initialisée (:attr:`config.session` vaut ``None``)
        """
        if not config.session:
            raise RuntimeError("Database session not initialised!")
        return config.session.query(cls)

    @property
    def columns(cls):
        """Sequence\[:class:`sqlalchemy.Column`\]: Raccourci pour ``Table.__table__.columns``"""
        return cls.__table__.columns

    @property
    def primary_col(cls):
        """:class:`sqlalchemy.Column`: Colonne clé primaire de la table

        Raises:
            :exc:`ValueError`: Pas de colonne clé primaire pour cette table, ou plusieurs
        """
        cols = cls.__table__.primary_key.columns
        if not cols:
            raise ValueError(f"Pas de clé primaire pour {cls.__name__}")
        if len(cols) > 1:
            raise ValueError(f"Plusieurs colonnes clés primaires pour {cls.__name__} (clé composite)")
        return next(iter(cols))

    def find_nearest(cls, chaine, col=None, sensi=0.25, filtre=None,
                     solo_si_parfait=True, parfaits_only=True,
                     match_first_word=False):
        """Recherche le(s) plus proche(s) résultat(s) d'une chaîne donnée dans la table

        Args:
            chaine (:class:`str`): motif à rechercher
            col (:class:`sqlalchemy.Column` | :class:`str`): colonne selon laquelle rechercher (défaut : colonne primaire). Doit être de type textuel (``col.type`` instance de :class:`sqlalchemy.String`)
            sensi (:class:`float`): ratio minimal pour retenir une entrée
            filtre (:class:`sqlalchemy.sql.elements.BinaryExpression`): argument de :meth:`~sqlalchemy.orm.query.Query.filter` (ex. ``Table.colonne == valeur``)
            solo_si_parfait (:class:`bool`): si ``True`` (défaut), renvoie uniquement le premier élément de score\* ``1`` trouvé s'il existe (ignore les autres éléments, même si ``>= sensi`` ou même ``1``)
            parfaits_only (:class:`bool`): si ``True`` (défaut), ne renvoie que les éléments de score\* ``1`` si on en trouve au moins un (ignore les autres éléments, même si ``>= sensi`` ; pas d'effet si ``solo_si_parfait`` vaut ``True``)
            match_first_word (:class:`bool`): si ``True``, teste aussi ``chaine`` vis à vis du premier *mot* (caractères précédent la première espace) de chaque entrée, et conserve ce score si il est supérieur (``cls.col`` doit être de type ``String``).

        Returns:
            :class:`list`\[\(:class:`.bdd.Base`, :class:`float`\)\]: La/les entrée(s) correspondant le mieux à ``chaine``, sous forme de liste de tuples ``(element, score*)`` triés par score\* décroissant

        Raises:
            :exc:`KeyError`: ``col`` inexistante ou pas de type textuel

        \*Score = ratio de :class:`difflib.SequenceMatcher`, i.e. proportion de caractères communs aux deux chaînes

        Note:
            Les chaînes sont comparées sans tenir compte de l'accentuation ni de la casse.
        """
        if not col:
            col = cls.primary_key
        elif isinstance(col, sqlalchemy.Column):
            col = col.key

        if col not in cls.columns_names:
            raise KeyError(f"Colonne {col} invalide pour {cls}")
        if not isinstance(cls.columns_types[col], sqlalchemy.String):
            raise KeyError(f"Colonne {cls}.{col} pas de type textuel")

        query = cls.query
        if filtre:
            query = query.filter(filtre)

        results = query.all()

        SM = difflib.SequenceMatcher()                  # Création du comparateur de chaînes
        slug1 = _remove_accents(chaine).lower()         # Cible en minuscule et sans accents
        SM.set_seq1(slug1)                              # Première chaîne à comparer : cible demandée

        scores = []
        for entry in results:
            slug2 = _remove_accents(getattr(entry, col)).lower()

            SM.set_seq2(slug2)          # Pour chaque élément, on compare la cible à son nom (en non accentué)
            score = SM.ratio()          # On calcule la ressemblance

            if match_first_word:        # On compare aussi avec le premier mot, si demandé
                first_word = slug2.split(maxsplit=1)[0]
                SM.set_seq2(first_word)
                score_fw = SM.ratio()
                score = max(score, score_fw)

            if score == 1:              # Cas particulier : élément demandé correspondant exactement à un en BDD
                if solo_si_parfait:             # Si demandé, on le renvoie direct
                    return [(entry, score)]
                elif parfaits_only:             # Sinon, si demandé, on ne renverra que les éléments de score 1
                    sensi = 1

            scores.append((entry, score))

        bests = [(e, score) for (e, score) in scores if score >= sensi]
        # Meilleurs résultats, dans l'ordre ; si élément parfait trouvé et parfaits_only, sensi = 1 donc ne renvoie que les parfaits
        return sorted(bests, key=lambda x: x[1], reverse=True)



#: :class:`dict`\[:class:`str`, :class:`TableBase`\]: Dictionnaire ``{nom de la base -> table}``, automatiquement rempli par :attr:`sqlalchemy.ext.declarative.declarative_base` (via le paramètre ``class_registry``)
tables = {}

#:
TableBase = declarative.declarative_base(class_registry=tables, name="TableBase", metaclass=TableMeta)
TableBase.__doc__ = """Classe de base des tables de données (construite par :func:`sqlalchemy.ext.declarative.declarative_base`)"""


def connect():
    """Se connecte à la base de données (variable d'environment ``LGREZ_DATABASE_URI``), crée les tables si nécessaire, construit :attr:`config.engine` et ouvre :attr:`config.session`"""

    LGREZ_DATABASE_URI = "postgresql://lg-rez:#^Wc8Kex2P6L@postgresql-lg-rez.alwaysdata.net/lg-rez_test"
    # LGREZ_DATABASE_URI = env.load("LGREZ_DATABASE_URI")
    config.engine = sqlalchemy.create_engine(LGREZ_DATABASE_URI, pool_pre_ping=True)           # Moteur SQL : connexion avec le serveur

    # Création des tables si elles n'existent pas déjà
    TableBase.metadata.create_all(config.engine)

    # Ouverture de la session
    Session = sqlalchemy.orm.sessionmaker(bind=config.engine)
    config.session = Session()
