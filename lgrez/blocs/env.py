"""lg-rez / blocs / Lecture des variables d'environnement

"""

import sys
import os

from dotenv import load_dotenv


# À l'import
if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = ".env"

load_dotenv(path)


def load(var_name: str) -> str:
    """Lit une valeur depuis les variables d'environnement.

    Les variables sont recherchées dans les variables d'environnement ;
    à l'import de ce module, celles-ci sont chargées par
    ``dotenv.load_dotenv`` à partir du fichier passé en premier
    argument en ligne de commande (``.env`` par défaut).

    Équivaut globalement à :func:`os.getenv` suivi d'une vérification
    que la variable existe.

    Args:
        var_name: nom de la variable à charger (``LGREZ_...``).

    Returns:
        La valeur de la variable demandée.

    Raises:
        RuntimeError: la variable d'environnement n'est pas définie.
    """
    var = os.getenv(var_name)
    if var is None:
        raise RuntimeError(f"Variable d'environnement {var_name} manquante")
    return var


def __getattr__(attr: str) -> str:
    """Raccourci pour accéder aux variables d'environnement.

    Permet d'utiliser ``blocs.env.VAR_NAME`` comme raccourci pour
    :func:`blocs.env.load(VAR_NAME) <.load>`, à la différence près
    que c'est une exception :exc:`AttributeError` qui sera levée si
    la variable n'est pas définie.
    """
    try:
        return load(attr)
    except RuntimeError:
        raise AttributeError(f"module '{__name__}' has no attribute '{attr}'") from None
