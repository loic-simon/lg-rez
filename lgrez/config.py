"""lg-rez / Variables globales

Personnalisation de différents paramètres et accès global

"""

import json
import pkgutil
import typing

import discord
import readycheck
import sqlalchemy
import sqlalchemy.orm

from lgrez.blocs import structure

if typing.TYPE_CHECKING:
    from lgrez.bot import LGBot


#: dict[str, Any]: Structure du serveur utilisée par /setup (serveur,
#: rôles, salons, emojis). Voir le fichier ```server_structure.json``
#: (valeur par défaut) pour les possibilités de personnalisation.
server_structure = json.loads(pkgutil.get_data("lgrez", "server_structure.json"))


#: Préfixe des noms des salons de conversation bot.
private_chan_prefix: str = "conv-bot-"

#: Nom de la catégorie des conversations bot, pour l'inscription
#: (sera éventuellement suivi de 2, 3... si plus de 50 joueurs).
#: Devrait correspondre à au nom de la catégorie correspondante dans
#: :attr:`server_structure` ``["categories"]``
private_chan_category_name = None  # Deduced from server_structure

#: Nom de la catégorie des boudoirs
#: (sera éventuellement suivi de 2, 3... si plus de 50 boudoirs).
#: Devrait correspondre à au nom de la catégorie correspondante dans
#: :attr:`server_structure` ``["categories"]``
boudoirs_category_name = None  # Deduced from server_structure

#: Nom de la catégorie des boudoirs devenus inutiles
#: (sera éventuellement suivi de 2, 3... si plus de 50 boudoirs).
#: Devrait correspondre à au nom de la catégorie correspondante dans
#: :attr:`server_structure` ``["categories"]``
old_boudoirs_category_name = None  # Deduced from server_structure


#: Date de début de saison (pour information lors de l'inscription).
debut_saison: str = "32 plopembre"

#: Si ``False``, le processus d'inscription ne demandera pas la
#: chambre des joueurs, qui seront tous inscrits en :attr:`chambre_mj`
#: (et la chambre ne sera pas indiquée dans ``!vivants``).
demande_chambre: bool = True

#: Nom par défaut de la :attr:`~.bdd.Joueur.chambre` des joueurs.
chambre_mj: str = "[chambre MJ]"


async def additional_inscription_step(
    journey,  # blocs.journey.DiscordJourney
    member: discord.Member,
    chan: discord.TextChannel,
) -> bool | None:
    """Coroutine permettant d'ajouter des étapes au processus d'inscription.

    Cette coroutine est appelée par :func:`.features.inscription.main`
    juste avant l'inscription en base. Si elle renvoie `False`,
    l'inscription est annulée ; si elle ne renvoie rien ou une autre
    valeur, elle continue selon le processus habituel.

    Args:
        member: Membre en cours d'inscription.
        chan: Chan perso créé pour l'inscription.

    Returns:
        Si ``False``, annule l'inscription.
    """
    pass


#: Si ``True``, le bot appellera :meth:`.LGBot.i_am_alive` toutes
#: les 60 secondes. Ce n'est pas activé par défaut.
output_liveness: bool = False


#: :attr:`~.bdd.Role.slug` du rôle par défaut, attribué aux
#: joueurs lors de l'inscription (renvoyé par :meth:`.bdd.Role.default`).
#: Doit correspondre à un rôle existant (défini dans le GSheet *Rôles et
#: actions*).
default_role_slug: str = "nonattr"

#: :attr:`~.bdd.Camp.slug` du camp par défaut, attribué aux
#: joueurs lors de l'inscription (renvoyé par :meth:`.bdd.Camp.default`).
#: Doit correspondre à un camp existant (défini dans le GSheet *Rôles et
#: actions*).
default_camp_slug: str = "nonattr"


#: Nom de la feuille du *Tableau de bord* contenant l'état actuel
#: des joueurs, sur laquelle sont effectuées les modifications.
tdb_main_sheet: str = "Journée en cours"

#: Nom de la feuille du *Tableau de bord* contenant les résultats
#: des votes (après corrections manuelles éventuelles).
tdb_votes_sheet: str = "Journée en cours"

#: Numéro de la ligne de la feuille principale
#: (:attr:`~lgrez.config.tdb_main_sheet`)
#: du *Tableau de bord* contenant les noms des colonnes (commençant de 1).
tdb_header_row: int = 3

#: Nom de la colonne de la feuille principale
#: (:attr:`~lgrez.config.tdb_main_sheet`)
#: du *Tableau de bord* contenant les IDs Discord des joueurs.
tdb_id_column: str = "A"

#: Noms de la première et de la dernière colonne de la zone de
#: la feuille principale (:attr:`~lgrez.config.tdb_main_sheet`) du *Tableau
#: de bord* contenant les informations (colonnes de la BDD) des joueurs.
tdb_main_columns: tuple[str, str] = ("J", "Q")

#: Noms de la première et de la dernière colonne de la zone de
#: la feuille principale (:attr:`~lgrez.config.tdb_main_sheet`) du *Tableau
#: de bord* contenant l'ancien état des informations des joueurs
#: (avant ``!sync``).
tdb_tampon_columns: tuple[str, str] = ("B", "I")


#: Nombre maximal de modèles de ciblages (:class:`.bdd.BaseCiblage`)
#: renseignés pour chaque modèle d'action (:class:`.bdd.BaseAction`), à
#: droite de la feuille ``baseactions`` du GSheet *Rôles et actions*.
max_ciblages_per_action: int = 3


#: :attr:`.bdd.BaseAction.slug` de l'action de base permettant
#: de modifier un vote (rôle de l'*Intrigant* dans le jeu PCéen).
#: Cette baseaction doit avoir deux ciblages de slugs "cible" et "vote".
modif_vote_baseaction: str = "modification-vote"

#: :attr:`.bdd.BaseAction.slug` de l'action de base permettant
#: d'ajouter un/des vote(s) (rôle du *Corbeau* dans le jeu PCéen).
ajout_vote_baseaction: str = "ajout-vote"

#: Nombre de votes ajoutés par l'action :attr:`ajout_vote_baseaction`.
n_ajouts_votes: int = 2


#: Nom de la feuille du GSheet *Données brûtes* où enregistrer
#: les votes brutes pour le condamné du jour.
db_votecond_sheet: str = "votecond_brut"

#: Nom de la feuille du GSheet *Données brûtes* où enregistrer
#: les votes brutes pour le nouveau maire.
db_votemaire_sheet: str = "votemaire_brut"

#: Nom de la feuille du GSheet *Données brûtes* où enregistrer
#: les votes brutes pour le vote des loups.
db_voteloups_sheet: str = "voteloups_brut"

#: Nom de la feuille du GSheet *Données brûtes* où enregistrer
#: les actions effectuées.
db_actions_sheet: str = "actions_brut"


#: Mots-clés (en minuscule) utilisables (quelque soit la casse)
#: pour arrêter une commande en cours d'exécution.
stop_keywords: list[str] = ["stop", "!stop"]


#: Mots-clés de rechargement (dans :attr:`.bdd.BaseAction.refill`)
#: permettant de recharger une action à son nombre de charges initial.
refills_full: list[str] = ["weekends"]

#: Mots-clés de rechargement (dans :attr:`.bdd.BaseAction.refill`)
#: permettant de recharger une action de une charge.
refills_one: list[str] = ["forgeron", "rebouteux", "divin"]

#: Mots-clés de rechargement (dans :attr:`.bdd.BaseAction.refill`)
#: à utiliser par le MJ pour ajouter une charge à une action.
refills_divins: list[str] = ["divin"]


#: Indique si le bot est prêt (:meth:`.LGBot.on_ready` appelé)
#: N'est pas conçu pour être changé manuellement.
is_ready: bool = False

#: bool: Indique si le serveur est construit (``/setup`` appelé)
#: N'est pas conçu pour être changé manuellement.
is_setup = True


class Role(readycheck.ReadyCheck, check_type=discord.Role):
    """Rôles Discord nécessaires au jeu

    Cette classe dérive de :class:`readycheck.ReadyCheck` :
    accéder aux attributs ci-dessous avant que le bot ne soit connecté
    au serveur lève une :exc:`~readycheck.NotReadyError`.

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

    # Default attributes values will be deduced from server_structure.
    mj: discord.Role = None
    redacteur: discord.Role = None
    joueur_en_vie: discord.Role = None
    joueur_mort: discord.Role = None
    maire: discord.Role = None
    everyone: discord.Role = "@everyone"


class Channel(readycheck.ReadyCheck, check_type=discord.TextChannel):
    """Salons Discord nécessaires au jeu

    Cette classe dérive de :class:`readycheck.ReadyCheck` : accéder
    aux attributs ci-dessous avant que le bot ne soit connecté au
    serveur lève une :exc:`~readycheck.NotReadyError`.

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

    # Default attributes values will be deduced from server_structure.
    roles: discord.TextChannel = None
    logs: discord.TextChannel = None
    annonces: discord.TextChannel = None
    haros: discord.TextChannel = None
    debats: discord.TextChannel = None


class Emoji(readycheck.ReadyCheck, check_type=discord.Emoji):
    """Emojis Discord nécessaires au jeu

    Cette classe dérive de :class:`readycheck.ReadyCheck` : accéder
    aux attributs ci-dessous avant que le bot ne soit connecté au
    serveur lève une :exc:`~readycheck.NotReadyError`.

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

    # Default attributes values will be deduced from server_structure.
    ha: discord.Emoji = None
    ro: discord.Emoji = None
    bucher: discord.Emoji = None
    maire: discord.Emoji = None
    action: discord.Emoji = None
    lune: discord.Emoji = None
    void: discord.Emoji = None


def set_config_from_server_structure() -> None:
    """Deduce some configuration values from server structure.

    Call this function after customizing :attr:`.server_structure`,
    but BEFORE launching the bot! Should never be called at runtime.
    """
    global private_chan_category_name
    global boudoirs_category_name
    global old_boudoirs_category_name

    structure.check_server_structure(server_structure, Role, Channel, Emoji)

    categories = server_structure["categories"]
    private_chan_category_name = categories["private_chan"]["name"]
    boudoirs_category_name = categories["boudoirs"]["name"]
    old_boudoirs_category_name = categories["old_boudoirs"]["name"]
    for role in Role:
        if role == "everyone":
            continue
        setattr(Role, role, server_structure["roles"][role]["name"])
    if (base_role := server_structure["base_role"]) == "@everyone":
        Role.everyone = "@everyone"
    else:
        Role.everyone = server_structure["roles"][base_role]["name"]
    for channel in Channel:
        setattr(
            Channel,
            channel,
            next(chan for categ in categories.values() for slug, chan in categ["channels"].items() if slug == channel)[
                "name"
            ],
        )
    for emoji in Emoji:
        setattr(Emoji, emoji, server_structure["emojis"]["required"][emoji])


set_config_from_server_structure()  # First deduction at import time


guild: discord.Guild
bot: "LGBot"
engine: sqlalchemy.engine.Engine
session: sqlalchemy.orm.Session
webhook: discord.Webhook


class _ModuleGlobals(readycheck.ReadyCheck):
    """Module-level attributes with not-None ReadyCheck

    (attributes accessed by __getattr__, documented directly in config.rst)
    """

    guild = None
    bot = None
    commands_tree = None
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
        raise AttributeError(f"module '{__name__}' has no attribute '{attr}'") from None
