import unittest
from unittest import mock

import sqlalchemy

from lgrez import config
from lgrez.bdd import base
from test import mock_discord, mock_bdd, mock_env



class TestBaseFunctions(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.base functions."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test__remove_accents(self):
        """Unit tests for base._remove_accents function."""
        # def _remove_accents(text)
        _remove_accents = base._remove_accents
        samples = {
            "": "",
            "allo": "allo",
            "AllO": "AllO",
            "énorme ÉNORME": "enorme ENORME",
            "àéïìùÀÉÏÌÙ‰": "aeiiuAEIIU‰",
            "énorme?♥♦♣♠": "enorme?♥♦♣♠",
        }
        for sample, result in samples.items():
            self.assertEqual(_remove_accents(sample), result)


    # Objets d'autodoc partiellement couverts seulement :
    # vérification que l'objet SQLAlchemy correspondant est correctement
    # appelé (à part doc et comment), pas que la doc est cohérente

    @mock.patch("sqlalchemy.Column")
    def test_autodoc_Column(self, col_patch):
        """Unit tests for base.autodoc_Column function."""
        # def autodoc_Column(*args, doc="", comment=None, **kwargs)
        autodoc_Column = base.autodoc_Column
        args = [mock.Mock() for i in range(5)]
        kwargs = {str(i): mock.Mock() for i in range(5)}
        col_patch.return_value.configure_mock(**{
            "type.python_type.__name__": "a"})
        col = autodoc_Column(*args, **kwargs)
        col_patch.assert_called_once_with(*args, **kwargs, comment=mock.ANY)
        self.assertIs(col, col_patch.return_value)

    @mock.patch("sqlalchemy.orm.relationship")
    def test_autodoc_ManyToOne(self, rsp_patch):
        """Unit tests for base.autodoc_ManyToOne function."""
        # def autodoc_ManyToOne(tablename, *args, doc="", **kwargs)
        autodoc_ManyToOne = base.autodoc_ManyToOne
        args = [mock.Mock() for i in range(5)]
        kwargs = {str(i): mock.Mock() for i in range(5)}
        rsp = autodoc_ManyToOne("ozy", *args, **kwargs)
        rsp_patch.assert_called_once_with("ozy", *args, **kwargs, doc=mock.ANY)
        self.assertIs(rsp, rsp_patch.return_value)

    @mock.patch("sqlalchemy.orm.relationship")
    def test_autodoc_OneToMany(self, rsp_patch):
        """Unit tests for base.autodoc_OneToMany function."""
        # def autodoc_OneToMany(tablename, *args, doc="", **kwargs)
        autodoc_OneToMany = base.autodoc_OneToMany
        args = [mock.Mock() for i in range(5)]
        kwargs = {str(i): mock.Mock() for i in range(5)}
        rsp = autodoc_OneToMany("ozy", *args, **kwargs)
        rsp_patch.assert_called_once_with("ozy", *args, **kwargs, doc=mock.ANY)
        self.assertIs(rsp, rsp_patch.return_value)

    @mock.patch("sqlalchemy.orm.relationship")
    def test_autodoc_ManyToMany(self, rsp_patch):
        """Unit tests for base.autodoc_ManyToMany function."""
        # def autodoc_ManyToMany(tablename, *args, doc="", **kwargs)
        autodoc_ManyToMany = base.autodoc_ManyToMany
        args = [mock.Mock() for i in range(5)]
        kwargs = {str(i): mock.Mock() for i in range(5)}
        rsp = autodoc_ManyToMany("ozy", *args, **kwargs)
        rsp_patch.assert_called_once_with("ozy", *args, **kwargs, doc=mock.ANY)
        self.assertIs(rsp, rsp_patch.return_value)


    @mock_env.patch_env(LGREZ_DATABASE_URI="oh!<3")
    @mock.patch("sqlalchemy.create_engine")
    @mock.patch("sqlalchemy.orm.sessionmaker")
    @mock.patch("lgrez.bdd.base.TableBase")
    def test_connect(self, tb_patch, sm_patch, ce_patch):
        """Unit tests for base.connect function."""
        # def connect()
        connect = base.connect
        del config.session, config.engine
        connect()
        ce_patch.assert_called_once_with("oh!<3", pool_pre_ping=True)
        self.assertEqual(config.engine, ce_patch.return_value)
        tb_patch.metadata.create_all.assert_called_once_with(config.engine)
        sm_patch.assert_called_once_with(bind=config.engine)
        self.assertEqual(config.session, sm_patch.return_value.return_value)



class TestTableMeta(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.base.TableMeta methods."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test___init__(self):
        """Unit tests for TableMeta.__init__ method."""
        # def __init__(cls, name, bases, dic, comment=None, **kwargs)
        __init__ = base.TableMeta.__init__
        cls = mock.MagicMock(base.TableMeta)
        cls.__doc__ = "hophop"

        # basic
        with mock.patch("sqlalchemy.ext.declarative.api"
                        ".DeclarativeMeta.__init__") as dm_patch:
            __init__(cls, "TestTab", (), {})
        self.assertEqual(cls.__tablename__, "testtabs")
        dm_patch.assert_called_once_with("TestTab", (), {}, comment="hophop")
        self.assertEqual(cls._attrs, {})
        self.assertTrue(cls.__doc__.startswith("hophop\n"))
        self.assertIn("testtabs", cls.__doc__)

        # complex
        cls.__doc__ = "haphap"
        bases = mock.Mock()
        dic = {
            "ah": 1,
            "allo": mock.Mock(),
            "coucou": mock.Mock(sqlalchemy.Column),
            "kuku": mock.Mock(sqlalchemy.orm.relationships.RelationshipProperty),
        }
        with mock.patch("sqlalchemy.ext.declarative.api"
                        ".DeclarativeMeta.__init__") as dm_patch:
            __init__(cls, "PoPoPo", bases, dic, "keuwa", a=2, z="a")
        self.assertEqual(cls.__tablename__, "popopos")
        dm_patch.assert_called_once_with("PoPoPo", bases, dic,
                                         comment="keuwa", a=2, z="a")
        self.assertEqual(cls._attrs, {"coucou": dic["coucou"],
                                      "kuku": dic["kuku"]})
        self.assertTrue(cls.__doc__.startswith("haphap\n"))
        self.assertIn("popopos", cls.__doc__)

        # TableBase
        with mock.patch("sqlalchemy.ext.declarative.api"
                        ".DeclarativeMeta.__init__") as dm_patch:
            __init__(cls, "TableBase", (), {})
        self.assertNotEqual(cls.__tablename__, "tablebases")
        dm_patch.assert_not_called()


    def test_query(self):
        """Unit tests for TableMeta.query property."""
        # @property def query(cls)
        query = base.TableMeta.query
        cls = mock.MagicMock(base.TableMeta)
        q = query.fget(cls)
        config.session.query.assert_called_once_with(cls)
        self.assertEqual(q, config.session.query.return_value)
        self.assertIsNone(query.fset)       # read-only
        self.assertIsNone(query.fdel)

    def test_columns(self):
        """Unit tests for TableMeta.columns property."""
        # @property def columns(cls)
        columns = base.TableMeta.columns
        cls = mock.MagicMock(base.TableMeta, __table__=mock.Mock())
        cols = columns.fget(cls)
        self.assertEqual(cols, cls.__table__.columns)
        self.assertIsNone(columns.fset)       # read-only
        self.assertIsNone(columns.fdel)

    def test_attrs(self):
        """Unit tests for TableMeta.attrs property."""
        # @property def attrs(cls)
        attrs = base.TableMeta.attrs
        ats = mock.MagicMock(base.TableMeta, __table__=mock.Mock(),
                             _attrs=mock.Mock())
        cols = attrs.fget(ats)
        self.assertEqual(cols, ats._attrs)
        self.assertIsNone(attrs.fset)       # read-only
        self.assertIsNone(attrs.fdel)

    def test_primary_col(self):
        """Unit tests for TableMeta.primary_col property."""
        # @property def primary_col(cls)
        primary_col = base.TableMeta.primary_col
        cls = mock.MagicMock(base.TableMeta, __table__=mock.Mock())
        # no cols
        cls.__table__.primary_key.columns = {}
        with self.assertRaises(ValueError):
            primary_col.fget(cls)
        # > 1 col
        cls.__table__.primary_key.columns = {"baa", "klklklk"}
        with self.assertRaises(ValueError):
            primary_col.fget(cls)
        # 1 col
        cls.__table__.primary_key.columns = {"bzzzkt"}
        pcol = primary_col.fget(cls)
        self.assertEqual(pcol, "bzzzkt")
        # assert read-only
        self.assertIsNone(primary_col.fset)
        self.assertIsNone(primary_col.fdel)


    @mock.patch("difflib.SequenceMatcher")
    def test_find_nearest(self, sm_patch):
        """Unit tests for TableMeta.find_nearest method."""
        # def find_nearest(cls, chaine, col=None, sensi=0.25, filtre=None,
        #                  solo_si_parfait=True, parfaits_only=True,
        #                  match_first_word=False)
        find_nearest = base.TableMeta.find_nearest
        cls = mock.MagicMock(base.TableMeta, __table__=mock.Mock())
        matcher = sm_patch.return_value

        # bad col name
        cls.columns = {"b": 1, "c": 2}
        with self.assertRaises(ValueError) as cm:
            find_nearest(cls, "qwa", col="a")
        self.assertIn("Colonne 'a' invalide", cm.exception.args[0])
        sm_patch.assert_not_called()
        cls.query.assert_not_called()

        # bad col type
        with self.assertRaises(ValueError) as cm:
            find_nearest(cls, "qwa", col=mock.Mock(sqlalchemy.Column,
                                                   type=sqlalchemy.Integer()))
        self.assertIn("pas de type textuel", cm.exception.args[0])
        sm_patch.assert_not_called()
        cls.query.assert_not_called()

        # no results
        col = mock.Mock(sqlalchemy.Column, type=sqlalchemy.String())
        cls.query.all.return_value = []
        results = find_nearest(cls, "qwa", col=col)
        sm_patch.assert_called_once()
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        cls.query.all.assert_called_once()
        cls.reset_mock()
        self.assertEqual(results, [])

        # no results, filtre
        cls.query.filter.return_value.all.return_value = []
        filtre = mock.Mock()
        results = find_nearest(cls, "qwa", col=col, filtre=filtre)
        sm_patch.assert_called_once()
        sm_patch.reset_mock()
        cls.query.filter.assert_called_once_with(filtre)
        cls.query.all.assert_not_called()
        cls.query.filter.return_value.all.assert_called_once()
        cls.reset_mock()
        self.assertEqual(results, [])

        # one result, exact
        col = mock.Mock(sqlalchemy.Column, key="ab", type=sqlalchemy.String())
        ret = [mock.Mock(ab="Qwà")]
        cls.query.all.return_value = ret
        matcher.ratio.return_value = 1
        results = find_nearest(cls, "Qwà", col=col)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        matcher.set_seq2.assert_called_once_with("qwa")
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[0], 1)])

        # one result, approx
        matcher.ratio.return_value = 0.337
        results = find_nearest(cls, "qwà", col=col)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        matcher.set_seq2.assert_called_once_with("qwa")
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[0], 0.337)])

        # one result, under sensi
        matcher.ratio.return_value = 0.337
        results = find_nearest(cls, "qwà", col=col, sensi=0.5)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        matcher.set_seq2.assert_called_once_with("qwa")
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [])

        # no results, col = default
        cls.primary_col = mock.Mock(sqlalchemy.Column, key="gzzt",
                                    type=sqlalchemy.String())
        matcher.ratio.return_value = 0.6
        ret = [mock.Mock(gzzt="Qwà")]
        cls.query.all.return_value = ret
        results = find_nearest(cls, "qwà")
        sm_patch.assert_called_once()
        sm_patch.reset_mock()
        cls.reset_mock()
        self.assertEqual(results, [(ret[0], 0.6)])

        # several results, none exact
        scores = [
            ("qwa", 0.6),
            ("st2", 0.2),
            ("st3", 0.9),
        ]
        ret = [mock.Mock(ab=key) for key, _ in scores]
        cls.query.all.return_value = ret
        matcher.ratio.side_effect = [score for _, score in scores]
        results = find_nearest(cls, "qwà", col=col)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 3)
        matcher.set_seq2.assert_has_calls([mock.call(k) for k, _ in scores])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[2], 0.9), (ret[0], 0.6)])

        # several results, one exact / solo_si_parfait
        scores = [
            ("qwa", 0.6),
            ("st2", 0.2),
            ("st3", 1),
            ("st4", 0.7),
        ]
        ret = [mock.Mock(ab=key) for key, _ in scores]
        cls.query.all.return_value = ret
        matcher.ratio.side_effect = [score for _, score in scores]
        results = find_nearest(cls, "qwà", col=col)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 3)
        matcher.set_seq2.assert_has_calls([mock.call(k)
                                           for k, _ in scores[:3]])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[2], 1)])

        # several results, one exact / not solo_si_parfait
        matcher.ratio.side_effect = [score for _, score in scores]
        results = find_nearest(cls, "qwà", col=col, solo_si_parfait=False)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 4)
        matcher.set_seq2.assert_has_calls([mock.call(k) for k, _ in scores])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[2], 1)])

        # several results, one exact / not solo_si_parfait nor parfaits_only
        matcher.ratio.side_effect = [score for _, score in scores]
        results = find_nearest(cls, "qwà", col=col, solo_si_parfait=False,
                               parfaits_only=False)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 4)
        matcher.set_seq2.assert_has_calls([mock.call(k) for k, _ in scores])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[2], 1), (ret[3], 0.7), (ret[0], 0.6)])

        # several results, two exacts / solo_si_parfait
        scores = [
            ("qwa", 0.6),
            ("st2", 0.2),
            ("st3", 1),
            ("st4", 0.7),
            ("st5", 1),
            ("st6", 0.1),
        ]
        ret = [mock.Mock(ab=key) for key, _ in scores]
        cls.query.all.return_value = ret
        matcher.ratio.side_effect = [score for _, score in scores]
        results = find_nearest(cls, "qwà", col=col)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 3)
        matcher.set_seq2.assert_has_calls([mock.call(k)
                                          for k, _ in scores[:3]])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[2], 1)])

        # several results, two exacts / not solo_si_parfait
        matcher.ratio.side_effect = [score for _, score in scores]
        results = find_nearest(cls, "qwà", col=col, solo_si_parfait=False)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 6)
        matcher.set_seq2.assert_has_calls([mock.call(k) for k, _ in scores])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[2], 1), (ret[4], 1)])

        # several results, two exacts / not solo_si_parfait nor parfaits_only
        matcher.ratio.side_effect = [score for _, score in scores]
        results = find_nearest(cls, "qwà", col=col, solo_si_parfait=False,
                               parfaits_only=False)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 6)
        matcher.set_seq2.assert_has_calls([mock.call(k) for k, _ in scores])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[2], 1), (ret[4], 1),
                                   (ret[3], 0.7), (ret[0], 0.6)])


        # several results, match_first_word
        scores = [
            ("qwa", 0.6, 0.6),
            ("st2 wiii", 0.2, 1),
            ("st3", 1, 1),
            ("st4 ola", 0.7, 0.9),
            ("st5 ak", 1, 0.7),
            ("st6 hpp", 0.1, 0.6),
            ("st7 hpp", 0.2, 0.1),
            ("st8 hpp", 0.8, 0.1),
        ]
        ret = [mock.Mock(ab=key) for key, *_ in scores]
        cls.query.all.return_value = ret
        matcher.ratio.side_effect = [sc for _, *scs in scores for sc in scs]
        results = find_nearest(cls, "qwà", col=col, match_first_word=True)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 4)
        matcher.set_seq2.assert_has_calls([mock.call(k)
                                           for k, *_ in scores[:2]])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[1], 1)])

        # several results, match_first_word / two exacts / not solo_si_parfait
        matcher.ratio.side_effect = [sc for _, *scs in scores for sc in scs]
        results = find_nearest(cls, "qwà", col=col, match_first_word=True,
                               solo_si_parfait=False)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 16)
        matcher.set_seq2.assert_has_calls([
            mock.call(sc) for key, *_ in scores
            for sc in [key, key.split(maxsplit=1)[0]]
        ])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[1], 1), (ret[2], 1), (ret[4], 1)])

        # several results, match_first_word / two exacts /
        #                  not solo_si_parfait nor parfaits_only
        matcher.ratio.side_effect = [sc for _, *scs in scores for sc in scs]
        results = find_nearest(cls, "qwà", col=col, match_first_word=True,
                               solo_si_parfait=False, parfaits_only=False)
        sm_patch.assert_called_once()
        matcher.set_seq1.assert_called_once_with("qwa")
        self.assertEqual(matcher.set_seq2.call_count, 16)
        matcher.set_seq2.assert_has_calls([
            mock.call(sc) for key, *_ in scores
            for sc in [key, key.split(maxsplit=1)[0]]
        ])
        sm_patch.reset_mock()
        cls.query.filter.assert_not_called()
        self.assertEqual(results, [(ret[1], 1), (ret[2], 1), (ret[4], 1),
                                   (ret[3], 0.9), (ret[7], 0.8),
                                   (ret[0], 0.6), (ret[5], 0.6)])



class TestTableBase(unittest.IsolatedAsyncioTestCase):
    """Unit tests for lgrez.bdd.base.TableBase methods."""

    def setUp(self):
        mock_discord.mock_config()

    def tearDown(self):
        mock_discord.unmock_config()

    def test_primary_key(self):
        """Unit tests for TableBase.primary_key method."""
        # @property def primary_key(self)
        primary_key = base.TableBase.primary_key
        class SomeTable(mock.MagicMock):
            primary_col = mock.Mock(key="gzzt")
        slf = SomeTable()   # Table instance
        res = primary_key.fget(slf)
        self.assertEqual(res, slf.gzzt)
        self.assertIsNone(primary_key.fset)       # read-only
        self.assertIsNone(primary_key.fdel)

    def test_update(self):
        """Unit tests for TableBase.update method."""
        # @staticmethod def update()
        update = base.TableBase.update
        update()
        config.session.commit.assert_called_once()

    def test_add(self):
        """Unit tests for TableBase.add method."""
        # def add(self, *other)
        add = base.TableBase.add
        # one
        slf = mock.Mock(base.TableBase)     # Table instance
        add(slf)
        config.session.add.assert_called_once_with(slf)
        slf.update.assert_called_once()
        config.session.reset_mock()
        # several
        slf = mock.Mock(base.TableBase)     # Table instance
        other = tuple(mock.Mock(base.TableBase) for i in range(5))
        add(slf, *other)
        config.session.add.assert_called_once_with(slf)
        config.session.add_all.assert_called_once_with(other)
        slf.update.assert_called_once()
        config.session.reset_mock()

    def test_delete(self):
        """Unit tests for TableBase.delete method."""
        # def delete(self, *other)
        delete = base.TableBase.delete
        # one
        slf = mock.Mock(base.TableBase)     # Table instance
        delete(slf)
        config.session.delete.assert_called_once_with(slf)
        slf.update.assert_called_once()
        config.session.reset_mock()
        # several
        slf = mock.Mock(base.TableBase)     # Table instance
        other = [mock.Mock(base.TableBase) for i in range(5)]
        delete(slf, *other)
        self.assertEqual(config.session.delete.call_count, 6)
        config.session.delete.assert_has_calls(
            [mock.call(item) for item in [slf] + other], any_order=True)
        slf.update.assert_called_once()
        config.session.reset_mock()
