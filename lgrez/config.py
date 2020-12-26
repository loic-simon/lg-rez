"""config - variables globales"""

import functools

@functools.total_ordering
class NotReady():
    def __init__(self, message="not ready"):
        self._notready = RuntimeError(message)
    def __getattr__(self, attr):
        raise self._notready
    def __setattr__(self, attr, val):
        if attr == "_notready":
            return super().__setattr__(attr, val)
        raise self._notready
    def __delattr__(self, attr):
        raise self._notready
    def __call__(self, *args, **kwargs):
        raise self._notready
    def __eq__(self, other):
        raise self._notready
    def __lt__(self, other):
        raise self._notready
    def __dir__(self, other):
        raise self._notready
    def __iter__(self, other):
        raise self._notready



#: :class:`discord.Guild`: Le serveur Discord sur lequel se déroule la partie
#: Vaut ``None`` avant l'appel à :meth:`LGBot.run`.
guild = None

#: :class:`LGBot`: Le bot en activité
#: Vaut ``None`` avant l'appel à :meth:`LGBot.run`.
bot = None


#: :class:`sqlalchemy.engine.Engine`: Moteur de connection à la BDD
#: Vaut ``None`` avant l'appel à :func:`blocs.bdd.connect`.
engine = None

#: :class:`sqlalchemy.orm.session.Session`: Session de transaction avec la BDD
#: Vaut ``None`` avant l'appel à :func:`blocs.bdd.connect`.
session = None
