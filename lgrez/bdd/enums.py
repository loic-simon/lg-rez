"""lg-rez / bdd / Enums

Déclaration des énumérations utilisées

"""

import enum


# Définition des enums

class Statut(enum.Enum):
    """:class:`~enum.Enum` représentant le statut RP d'un Joueur.

    Attributes:
        vivant: Le joueur est en vie !
        mort: Le joueur est mort. RIP.
        MV: Le joueur est Mort-Vivant. Pas de chance.
        immortel: Le joueur est Immortel. Si jamais...
    """
    vivant = enum.auto()
    mort = enum.auto()
    MV = enum.auto()
    immortel = enum.auto()


class ActionTrigger(enum.Enum):
    """:class:`~enum.Enum` : Déclencheur de l'ouverture/fermeture d'une Action.

    Attributes:
        temporel: Ouverture/fermeture à heure fixe chaque jour
        delta: Fermeture un délai donné après l'ouverture
        perma: Action utilisable en permanence
        start: Ouverture au lancement du jeu
        auto: Action automatique, fermeture dès l'ouverture
        mort: Ouverture à la mort
        mot_mjs: Ouverture/fermeture au !plot cond
        open_cond: À l'ouverture du vote condamné
        close_cond: À la fermeture du vote condamné
        open_maire: À l'ouverture du vote du maire
        close_maire: À la fermeture du vote du maire
        open_loups: À l'ouverture du vote des loups
        close_loups: À la fermeture du vote des loups
    """
    temporel = enum.auto()
    delta = enum.auto()
    perma = enum.auto()
    start = enum.auto()
    auto = enum.auto()
    mort = enum.auto()
    mot_mjs = enum.auto()
    open_cond = enum.auto()
    close_cond = enum.auto()
    open_maire = enum.auto()
    close_maire = enum.auto()
    open_loups = enum.auto()
    close_loups = enum.auto()


class CandidHaroType(enum.Enum):
    """:class:`~enum.Enum` pour distinguer un haro d'une candidature.

    Attributes:
        candidature: Candidature à la mairie
        haro: Haro pour le bûcher
    """
    candidature = enum.auto()
    haro = enum.auto()
