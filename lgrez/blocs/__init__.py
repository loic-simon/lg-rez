"""lg-rez / Blocs transversaux

Chaque module de ``lgrez.blocs`` réalise une tâche non liée à une
fonctionnalité spécifique du bot : connection à un service, outils
divers...

"""

import os

dir = os.path.dirname(os.path.realpath(__file__))

__all__ = []
for file in os.listdir(dir):
    if not file.endswith(".py"):
        # Not a Python file
        continue

    name = file[:-3]
    if name.startswith("_"):
        # Private / magic module
        continue

    # Public submodule: add to __all__
    __all__.append(name)
