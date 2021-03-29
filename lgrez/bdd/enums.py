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

    @classmethod
    def open(cls, vote):
        if not isinstance(vote, Vote):
            vote = Vote[vote]
        return cls[f"open_{vote.name}"]

    @classmethod
    def close(cls, vote):
        if not isinstance(vote, Vote):
            vote = Vote[vote]
        return cls[f"close_{vote.name}"]


class CandidHaroType(enum.Enum):
    """:class:`~enum.Enum` pour distinguer un haro d'une candidature.

    Attributes:
        candidature: Candidature à la mairie
        haro: Haro pour le bûcher
    """
    candidature = enum.auto()
    haro = enum.auto()


class Vote(enum.Enum):
    """:class:`~enum.Enum` représentant les différents votes possibles.

    Attributes:
        cond: Vote pour le condamné du jour
        maire: Vote pour le nouveau maire
        loups: Vote pour la victime des loups
    """
    cond = enum.auto()
    maire = enum.auto()
    loups = enum.auto()


class UtilEtat(enum.Enum):
    """:class:`~enum.Enum` représentant l'état d'une utilisation d'action.

    Attributes:
        ouverte: Action utilisable, pas de décision prise
        remplie: Décision prise, encore possibilité de changer
        validee: Décision prise et bloquée (créneau pour agir fini)
        ignoree: Créneau pour agir fini sans qu'une décision soit prise
        contree: Utilisation validée, mais contrée par un évènement externe
    """
    ouverte = enum.auto()
    remplie = enum.auto()
    validee = enum.auto()
    ignoree = enum.auto()
    contree = enum.auto()


class CibleType(enum.Enum):
    """:class:`~enum.Enum` représentant le type de cible d'une action.

    Attributes:
        joueur: La cible doit être un joueur, vivant ou mort
        vivant: La cible doit être un joueur vivant
        mort: La cible doit être un joueur mort
        role: La cible doit être un rôle existant
        camp: La cible doit être un camp (public) existant
        booleen: Oui/non : sert à ue action sans paramètres, à une option...
        texte: Permet d'entrer un texte libre
    """
    joueur = enum.auto()
    vivant = enum.auto()
    mort = enum.auto()
    role = enum.auto()
    camp = enum.auto()
    booleen = enum.auto()
    texte = enum.auto()
