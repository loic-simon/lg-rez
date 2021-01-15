"""lg-rez / Variables globales

Personalisation de différents paramètres et accès global

"""

import discord

from lgrez.blocs import ready_check


#: str: Préfixe des noms des salons de conversation bot.
private_chan_prefix = "conv-bot-"

#: str: Nom de la catégorie des conversations bot, pour l'inscription
#: (sera éventuellement suivi de 2, 3... si plus de 50 joueurs).
private_chan_category_name = "CONVERSATION BOT"


#: str: Date de début de saison (pour information lors de l'inscription).
debut_saison = "32 plopembre"

#: bool: Si ``False``, le processus d'insciption ne demandera pas la
#: chambre des joueurs, qui seront tous inscrits en :attr:`chambre_mj`
#: (et la chambre ne sera pas indiquée dans ``!vivants``).
demande_chambre = True

#: str: Nom par défaut de la :attr:`~.bdd.Joueur.chambre` des joueurs.
chambre_mj = "[chambre MJ]"


#: bool: Si ``True``, le bot appellera :meth:`.LGBot.i_am_alive` toutes
#: les 60 secondes. Ce n'est pas activé par défaut.
output_liveness = False

# Journée en cours (nom sheet)

# STOP keywords


class Role(ready_check.ReadyCheck, check_type=discord.Role):
    """Rôles Discord nécessaires au jeu

    Cette classe dérive de :class:`ready_check.ReadyCheck` :
    accéder aux attributs ci-dessous avant que le bot ne soit connecté
    au serveur lève une :exc:`~ready_check.NotReadyError`.

    Plus précisément, :meth:`.LGBot.on_ready` remplace le nom du rôle
    par l'objet :class:`discord.Role` correspondant : si les noms des
    rôles sur Discord ont été modifiés, indiquer leur nom ici
    (``lgrez.config.Role.x = "nouveau nom"``) avant de lancer le bot,
    sans quoi :meth:`.LGBot.on_ready` lèvera une erreur.

    **Ne pas instancier cette classe.**

    Rôles utilisés (dans l'ordre hiérarchique conseillé) :

    Attributes:
        mj: Maître du Jeu.
            Nom par défaut : "MJ".
        joueur_en_vie: Joueur vivant, pouvant parler publiquement.
            Nom par défaut : "Joueur en vie".
        joueur_mort: Joueur mort, ne pouvant pas parler publiquement.
            Nom par défaut : "Joueur mort".
        maire: Joueur élu Maire, mis en avant et pouvant utiliser @everyone.
            Nom par défaut : "Maire".
        redacteur: Rôle permettant à un joueur d'utiliser les commandes de
            gestion d'IA (voir :class:`features.gestion_ia.GestionIA`). Mettre
            le même nom que le rôle des MJs si vous voulez supprimer ce rôle.
            Nom par défaut : "Rédacteur".
        everyone: Rôle de base. Les joueurs dont le rôle le plus élevé
            est ce rôle (ou moins) seront ignorés par le bot.
            Nom par défaut: "@everyone" (rôle Discord de base)
    """
    mj = "MJ"
    redacteur = "Rédacteur"
    joueur_en_vie = "Joueur en vie"
    joueur_mort = "Joueur mort"
    maire = "Maire"
    everyone = "@everyone"


class Channel(ready_check.ReadyCheck, check_type=discord.TextChannel):
    """Salons Discord nécessaires au jeu

    Cette classe dérive de :class:`ready_check.ReadyCheck` : accéder
    aux attributs ci-dessous avant que le bot ne soit connecté au
    serveur lève une :exc:`~ready_check.NotReadyError`.

    Plus précisément, :meth:`.LGBot.on_ready` remplace le nom du rôle
    par l'objet :class:`discord.TextChannel` correspondant : si les noms
    des salons sur Discord ont été modifiés, indiquer leur nom ici
    (``lgrez.config.Channel.x = "nouveau nom"``) avant de lancer le bot,
    sans quoi :meth:`.LGBot.on_ready` lèvera une erreur.

    **Ne pas instancier cette classe.**

    Salons utilisés (dans l'ordre d'affichage conseillé) :

    Attributes:
        roles: Salon listant les rôles (catégorie Informations).
            Nom par défaut : "roles".
        logs: Salon pour les messages techniques (catégorie réservée aux MJs).
            Nom par défaut : "logs".
        annonces: Salon d'annonces (catégorie Place du village).
            Nom par défaut : "annonces".
        haros: Salon des haros et candidatures (catégorie Place du village).
            Nom par défaut : "haros".
        debats: Salon de discussion principal (catégorie Place du village).
            Nom par défaut : "débats".
    """
    roles = "roles"
    logs = "logs"
    annonces = "annonces"
    haros = "haros"
    debats = "débats"


class Emoji(ready_check.ReadyCheck, check_type=discord.Emoji):
    """Emojis Discord nécessaires au jeu

    Cette classe dérive de :class:`ready_check.ReadyCheck` : accéder
    aux attributs ci-dessous avant que le bot ne soit connecté au
    serveur lève une :exc:`~ready_check.NotReadyError`.

    Plus précisément, :meth:`.LGBot.on_ready` remplace le nom du rôle
    par l'objet :class:`discord.Emoji` correspondant : si les noms
    des emojis sur Discord ont été modifiés, indiquer leur nom ici
    (``lgrez.config.Emoji.x = "nouveau nom"``) avant de lancer le bot,
    sans quoi :meth:`.LGBot.on_ready` lèvera une erreur.

    **Ne pas instancier cette classe.**

    Emojis utilisés (noms par défaut identiques aux noms des attributs) :

    Attributes:
        ha
        ro: Accolés, forment le mot « haro »
        bucher: Représente le vote pour le condamné du jour
        maire: Représente le vote pour le nouveau maire
        lune: Représente le vote des loups
        action: Représente les actions de rôle
        void: Image vide, pour séparations verticales et autres filouteries
    """
    ha = "ha"
    ro = "ro"
    bucher = "bucher"
    maire = "maire"
    action = "action"
    lune = "lune"
    void = "void"


class _ModuleGlobals(ready_check.ReadyCheck):
    """Module-level attributes with not-None ReadyCheck

    (attributes accessed by __getattr__, documented directly in config.rst)
    """
    guild = None
    bot = None
    loop = None
    engine = None
    session = None


# Called when module attribute not found: try to look in _ModuleGlobals
def __getattr__(attr):
    try:
        return getattr(_ModuleGlobals, attr)
    except AttributeError:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{attr}'"
        ) from None
