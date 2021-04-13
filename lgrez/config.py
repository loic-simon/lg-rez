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

#: str: Nom de la catégorie des boudoirs
#: (sera éventuellement suivi de 2, 3... si plus de 50 boudoirs).
boudoirs_category_name = "BOUDOIRS"


#: str: Date de début de saison (pour information lors de l'inscription).
debut_saison = "32 plopembre"

#: bool: Si ``False``, le processus d'insciption ne demandera pas la
#: chambre des joueurs, qui seront tous inscrits en :attr:`chambre_mj`
#: (et la chambre ne sera pas indiquée dans ``!vivants``).
demande_chambre = True

#: str: Nom par défaut de la :attr:`~.bdd.Joueur.chambre` des joueurs.
chambre_mj = "[chambre MJ]"

async def additional_inscription_step(member, chan):
    """Coroutine permettant d'ajouter des étapes au processus d'inscription.

    Cette coroutine est appelée par :func:`.features.inscription.main`
    juste avant l'inscription en base. Si elle renvoie `False`,
    l'inscription est annulée ; si elle ne renvoie rien ou une autre
    valeur, elle continue selon le processus habituel.

    Args:
        member (discord.Member): membre en cours d'inscription.
        chan (discord.TextChannel): chan perso créé pour l'inscription.

    Returns:
        Si ``False``, annule l'inscription.
    """
    pass


#: bool: Si ``True``, le bot appellera :meth:`.LGBot.i_am_alive` toutes
#: les 60 secondes. Ce n'est pas activé par défaut.
output_liveness = False


#: str: :attr:`~.bdd.Role.slug` du rôle par défaut, attribué aux
#: joueurs lors de l'inscription (renvoyé par :meth:`.bdd.Role.default`).
#: Doit correspodre à un rôle existant (défini dans le GSheet *Rôles et
#: actions*).
default_role_slug = "nonattr"

#: str: :attr:`~.bdd.Camp.slug` du camp par défaut, attribué aux
#: joueurs lors de l'inscription (renvoyé par :meth:`.bdd.Camp.default`).
#: Doit correspodre à un camp existant (défini dans le GSheet *Rôles et
#: actions*).
default_camp_slug = "nonattr"


#: str: Nom de la feuille du *Tableau de bord* contenant l'état actuel
#: des joueurs, sur laquelle sont effectuées les modifications.
tdb_main_sheet = "Journée en cours"

#: str: Nom de la feuille du *Tableau de bord* contenant les résultats
#: des votes (après corrections manuelles éventuelles).
tdb_votes_sheet = "Journée en cours"

#: int: Numéro de la ligne de la feuille principale
#: (:attr:`~lgrez.config.tdb_main_sheet`)
#: du *Tableau de bord* contenant les noms des colonnes (commençant de 1).
tdb_header_row = 3

#: str: Nom de la colonne de la feuille principale
#: (:attr:`~lgrez.config.tdb_main_sheet`)
#: du *Tableau de bord* contenant les IDs Discord des joueurs.
tdb_id_column = "A"

#: tuple[str]: Noms de la première et de la dernière colonne de la zone de
#: la feuille principale (:attr:`~lgrez.config.tdb_main_sheet`) du *Tableau
#: de bord* contenant les informations (colonnes de la BDD) des joueurs.
tdb_main_columns = ("J", "Q")

#: tuple[str]: Noms de la première et de la dernière colonne de la zone de
#: la feuille principale (:attr:`~lgrez.config.tdb_main_sheet`) du *Tableau
#: de bord* contenant l'ancien état des informations des joueurs
#: (avant ``!sync``).
tdb_tampon_columns = ("B", "I")


#: int: Nombre maximal de modèles de ciblages (:class:`.bdd.BaseCiblage`)
#: renseignés pour chaque modèle d'action (:class:`.bdd.BaseAction`), à
#: droite de la feuille ``baseactions`` du GSheet *Rôles et actions*.
max_ciblages_per_action = 3


#: str: :attr:`.bdd.BaseAction.slug` de l'action de base permettant
#: de modifier un vote (rôle de l'*Intigant* dans le jeu PCéen).
#: Cette baseaction doit avoir deux ciblages de slugs "cible" et "vote".
modif_vote_baseaction = "modification-vote"

#: str: :attr:`.bdd.BaseAction.slug` de l'action de base permettant
#: d'ajouter un/des vote(s) (rôle du *Corbeau* dans le jeu PCéen).
ajout_vote_baseaction = "ajout-vote"

#: int: Nombre de votes ajoutés par l'action :attr:`ajout_vote_baseaction`.
n_ajouts_votes = 2


#: str: Nom de la feuille du GSheet *Données brûtes* où enregistrer
#: les votes brutes pour le condamné du jour.
db_votecond_sheet = "votecond_brut"

#: str: Nom de la feuille du GSheet *Données brûtes* où enregistrer
#: les votes brutes pour le nouveau maire.
db_votemaire_sheet = "votemaire_brut"

#: str: Nom de la feuille du GSheet *Données brûtes* où enregistrer
#: les votes brutes pour le vote des loups.
db_voteloups_sheet = "voteloups_brut"

#: str: Nom de la feuille du GSheet *Données brûtes* où enregistrer
#: les actions effectuées.
db_actions_sheet = "actions_brut"


#: list[str]: Mots-clés (en minuscule) utilisables (quelque soit la casse)
#: pour arrêter une commande en cours d'exécution.
stop_keywords = ["stop", "!stop"]


#: list[str]: Mots-clés de rechargement (dans :attr:`.bdd.BaseAction.refill`)
#: permettant de recharger une action à son nombre de charges initial.
refills_full = ["weekends"]

#: list[str]: Mots-clés de rechargement (dans :attr:`.bdd.BaseAction.refill`)
#: permettant de recharger une action de une charge.
refills_one = ["forgeron", "rebouteux", "divin"]

#: list[str]: Mots-clés de rechargement (dans :attr:`.bdd.BaseAction.refill`)
#: à utiliser par le MJ pour ajouter une charge à une action.
refills_divins = ["divin"]



class Role(ready_check.ReadyCheck, check_type=discord.Role):
    """Rôles Discord nécessaires au jeu

    Cette classe dérive de :class:`.ready_check.ReadyCheck` :
    accéder aux attributs ci-dessous avant que le bot ne soit connecté
    au serveur lève une :exc:`~.ready_check.NotReadyError`.

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

    Cette classe dérive de :class:`.ready_check.ReadyCheck` : accéder
    aux attributs ci-dessous avant que le bot ne soit connecté au
    serveur lève une :exc:`~.ready_check.NotReadyError`.

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
    roles = "rôles"
    logs = "logs"
    annonces = "annonces"
    haros = "haros"
    debats = "débats"


class Emoji(ready_check.ReadyCheck, check_type=discord.Emoji):
    """Emojis Discord nécessaires au jeu

    Cette classe dérive de :class:`.ready_check.ReadyCheck` : accéder
    aux attributs ci-dessous avant que le bot ne soit connecté au
    serveur lève une :exc:`~.ready_check.NotReadyError`.

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

    webhook = None


# Variable interne, pour suivi des objets manquants (ne pas changer)
_missing_objects = 0


# Called when module attribute not found: try to look in _ModuleGlobals
def __getattr__(attr):
    try:
        return getattr(_ModuleGlobals, attr)
    except AttributeError:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{attr}'"
        ) from None
