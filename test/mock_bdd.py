import asyncio
import functools

from lgrez import bdd, config
from test import mock_env


class _PatchDB():
    def __enter__(self):
        self.old_session = config.session
        self.old_engine = config.engine
        env_patch = mock_env.patch_env(LGREZ_DATABASE_URI="sqlite://")
        self.env_patcher = env_patch.__enter__()
        bdd.connect()
        return self

    def __exit__(self, etype=None, eval=None, tb=None):
        config.session.close()
        config.engine.dispose()
        self.env_patcher.__exit__(etype, eval, tb)
        config.session = self.old_session
        config.engine = self.old_engine

    def __call__(self, func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def newfunc(*args, **kwargs):
                self.__enter__()
                try:
                    await func(*args, **kwargs)
                finally:
                    self.__exit__()
        else:
            @functools.wraps(func)
            def newfunc(*args, **kwargs):
                self.__enter__()
                try:
                    func(*args, **kwargs)
                finally:
                    self.__exit__()

        return newfunc


def patch_db(func=None):
    """Patch database with an in-memory empty SQLite database.

    Patch `LGREZ_DATABASE_URI` environment variable, then calls
    `bdd.connect()` to make `config.session` and `config.engine` refer
    to the newly-created database (and restores them at exit time).

    Can be used as a function decorator or context manager, as for
    `unittest.mock.patch`.
    """
    if callable(func):
        # @patch_db directly used as decorator (no parenthesis)
        return _PatchDB()(func)
    else:
        return _PatchDB()



def add_campsroles(n_camps=1, n_roles=1):
    """Ajoute `n_camps` camps et `n_roles` rôles à la BDD.

    Le premier camp/rôle ajouté est toujours celui par défaut
    (`config.default_camp/role_slug`), puis camp1, camp2...

    Retourne un tuple (liste des camps, liste des rôles).
    """
    camps = [bdd.Camp(slug=config.default_camp_slug, nom="defaut")]
    for i in range(1, n_camps):
        camps.append(bdd.Camp(slug=f"camp{i}",
                              nom=f"Camp{i}",
                              emoji=f"emoji{i}"))

    config.session.add_all(camps)

    roles = [bdd.Role(slug=config.default_role_slug, nom="defaut",
                      camp=bdd.Camp.default())]
    for i in range(1, n_roles):
        roles.append(bdd.Role(slug=f"role{i}",
                              nom=f"Role{i}",
                              camp=camps[i % n_camps]))

    config.session.add_all(roles)

    return camps, roles
