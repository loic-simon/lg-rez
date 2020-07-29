import enum

# Create database connection object

class Joueurs(db.Model):
    """Table de données des joueurs inscrits"""

    discord_id = db.Column(db.BigInteger(), primary_key=True)
    _chan_id = db.Column(db.BigInteger(), nullable=False)
    # inscrit = db.Column(db.Boolean(), nullable=False)

    nom = db.Column(db.String(32), nullable=False)
    chambre = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(32), nullable=False)

    role = db.Column(db.String(32), nullable=False)
    camp = db.Column(db.String(32), nullable=False)

    votant_village = db.Column(db.Boolean(), nullable=False)
    votant_loups = db.Column(db.Boolean(), nullable=False)
    role_actif = db.Column(db.Boolean(), nullable=True)

    _vote_condamne = db.Column(db.String(200), nullable=True)
    _vote_maire = db.Column(db.String(200), nullable=True)
    _vote_loups = db.Column(db.String(200), nullable=True)
    # _action_role = db.Column(db.Text(), nullable=True)

    def __repr__(self):
        """Return repr(self)."""
        return f"<Joueurs ({self.discord_id}/{self.nom})>"

    def __init__(self, discord_id, _chan_id, nom, chambre, statut, role, camp, votant_village, votant_loups, role_actif=None, _vote_condamne=None, _vote_maire=None, _vote_loups=None):
        """Initialize self."""
        self.discord_id = discord_id
        self._chan_id = _chan_id
        # self.inscrit = inscrit

        self.nom = nom
        self.chambre = chambre
        self.statut = statut

        self.role = role
        self.camp = camp

        self.votant_village = votant_village
        self.votant_loups = votant_loups
        self.role_actif = role_actif

        self._vote_condamne = _vote_condamne
        self._vote_maire = _vote_maire
        self._vote_loups = _vote_loups
        # self._action_role = _action_role


class Roles(db.Model) :
    """Table de données des rôles"""

    slug = db.Column(db.String(32), primary_key=True)

    prefixe = db.Column(db.String(8), nullable=False)
    nom = db.Column(db.String(32), nullable=False)

    camp = db.Column(db.String(32), nullable=False)                       # loups, solitaire, nécro, village...

    description_courte = db.Column(db.String(140), nullable=False)
    description_longue = db.Column(db.String(2000), nullable=False)

    # horaire_debut = db.Column(db.Time(), nullable=True)                #Au format HHMM ou None
    # horaire_fin = db.Column(db.Time(), nullable=True)                  #Au format HHMM ou None
    # lieu = db.Column(db.String(32), nullable=True)                        #Distance/Physique/Lieu/Contact/Conditionnel/None/Public

    # type = db.Column(db.String(32), nullable=False)                       #Quotidien, Unique, <Nombre>, Passif, Conditionnel, Hebdomadaire, Bicircadien, Special
    # changement_cible = db.Column(db.Boolean(), nullable=True)              #True, False ou None

    #InteractionNotaire = db.Column(db.String(32), nullable=True)         #Oui, Non, Conditionnel, Potion, Rapport; None si récursif
    #InteractionGardien = db.Column(db.String(32), nullable=True)         #Oui, Non, Conditionnel, Taverne, Feu, MaisonClose, Précis, Cimetière, Loups, None si recursif

    def __init__(self, slug, prefixe, nom, camp, description_courte, description_longue) :
        """Initialize self."""
        self.slug = slug
        self.prefixe = prefixe
        self.nom = nom
        self.camp = camp
        self.description_courte = description_courte
        self.description_longue = description_longue


class BaseActions(db.Model):
    """Table de données des actions définies de bases (non liées à un joueur)"""

    action = db.Column(db.String(32), primary_key=True)

    trigger_debut = db.Column(db.String(32), nullable=True)
    trigger_fin = db.Column(db.String(32), nullable=True)
    instant = db.Column(db.Boolean(), nullable=True)

    heure_debut = db.Column(db.Time(), nullable=True)
    heure_fin = db.Column(db.Time(), nullable=True)

    base_cooldown = db.Column(db.Integer(), nullable=False)
    base_charges = db.Column(db.Integer(), nullable=True)
    refill  = db.Column(db.String(32), nullable=True)

    # role_actif  = db.Column(db.Boolean(), nullable=False) # Définit si l'action est active(peut être utilisé par le joueur, même sous certaines conditions) ou passif (auto, AUCUNE influence du joueur)
    lieu = db.Column(db.String(32), nullable=True) #Distance/Physique/Lieu/Contact/Conditionnel/None/Public
    interaction_notaire = db.Column(db.String(32), nullable=True)         # Oui, Non, Conditionnel, Potion, Rapport; None si récursif
    interaction_gardien = db.Column(db.String(32), nullable=True)         # Oui, Non, Conditionnel, Taverne, Feu, MaisonClose, Précis, Cimetière, Loups, None si recursif
    mage = db.Column(db.String(100), nullable=True)                       #Oui, Non, changement de cible, etc

    changement_cible = db.Column(db.Boolean(), nullable=True)

    def __init__(self, action, trigger_debut=None, trigger_fin=None, instant=None, heure_debut=None, heure_fin=None, base_cooldown=0, base_charges=None, refill=None, lieu=None, interaction_notaire=None, interaction_gardien=None, mage=None, changement_cible=None):
        """Initialize self."""
        self.action = action
        self.trigger_debut = trigger_debut
        self.trigger_fin = trigger_fin
        self.instant = instant
        self.heure_debut = heure_debut
        self.heure_fin = heure_fin
        self.base_cooldown = base_cooldown
        self.base_charges = base_charges
        self.refill = refill
        # self.type = type #Quotidien, Unique, <Nombre>, Passif, Conditionnel, Hebdomadaire, Bicircadien, Special
        self.lieu = lieu
        self.interaction_notaire = interaction_notaire
        self.interaction_gardien = interaction_gardien
        self.mage = mage
        self.changement_cible = changement_cible


class Actions(db.Model):
    """Table de données des actions attribuées (liées à un joueur et actives)"""

    id = db.Column(db.Integer(), primary_key=True)
    player_id = db.Column(db.BigInteger(), nullable=False)
    action = db.Column(db.String(32), nullable=False)

    trigger_debut = db.Column(db.String(32), nullable=True)
    trigger_fin = db.Column(db.String(32), nullable=True)
    instant = db.Column(db.Boolean(), nullable=True)

    heure_debut = db.Column(db.Time(), nullable=True)
    heure_fin = db.Column(db.Time(), nullable=True)

    cooldown = db.Column(db.Integer(), nullable=False)
    charges = db.Column(db.Integer(), nullable=True)
    refill  = db.Column(db.String(32), nullable=True)

    lieu = db.Column(db.String(32), nullable=True)
    interaction_notaire = db.Column(db.String(32), nullable=True)
    interaction_gardien = db.Column(db.String(32), nullable=True)
    mage = db.Column(db.String(100), nullable=True)
    changement_cible = db.Column(db.Boolean(), nullable=True)

    # _cible_id = db.Column(db.BigInteger(), nullable=True)
    # _cible2_id = db.Column(db.BigInteger(), nullable=True)
    _decision = db.Column(db.String(200), nullable=True)

    #treated = db.Column(db.Boolean(), nullable=False)

    def __init__(self, *, id=None, player_id, action, trigger_debut=None, trigger_fin=None, instant=None, heure_debut=None, heure_fin=None, cooldown=0, charges=None, refill=None, lieu=None, interaction_notaire=None, interaction_gardien=None, mage=None, changement_cible=None, _decision=None):
        """Initialize self."""
        self.id = id
        self.player_id = player_id
        self.action = action                # Nom de l'action en rapport avec la table BaseActions
        self.trigger_debut = trigger_debut
        self.trigger_fin = trigger_fin
        self.instant = instant              #Est-ce que l'action a des conséquences instantanées ?
        self.heure_debut = heure_debut
        self.heure_fin = heure_fin
        self.cooldown = cooldown            # Cooldown restant pour l'action (0 = action disponible)
        self.charges = charges              # Nombre de charges restantes (mettre à Null si toujours dispo)
        self.refill = refill                #Comment l'action peut-elle être refill
        self.lieu = lieu
        self.interaction_notaire = interaction_notaire
        self.interaction_gardien = interaction_gardien
        self.mage = mage
        self.changement_cible = changement_cible
        # self._cible_id = _cible_id
        # self._cible2_id = _cible2_id
        self._decision = _decision
        # self.treated = treated


class BaseActionsRoles(db.Model):
    """Table de données mettant en relation les rôles et les actions de base"""

    id = db.Column(db.Integer(), primary_key=True)
    role = db.Column(db.String(32), nullable=False)
    action = db.Column(db.String(32), nullable=False)

    def __init__(self, id, role, action):
        """Initialize self."""
        self.id = id
        self.role = role
        self.action = action


class Taches(db.Model):
    """Table de données des tâches planifiées du bot"""

    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), nullable=False)
    commande = db.Column(db.String(200), nullable=False)
    action = db.Column(db.Integer(), nullable=True)

    def __init__(self, *, id=None, timestamp, commande, action=False):
        """Initialize self."""
        self.id = id
        self.timestamp = timestamp
        self.commande = commande
        self.action = action


class Triggers(db.Model):
    """Table de données des mots et expressions déclenchant l'IA du bot"""

    id = db.Column(db.Integer(), primary_key=True)
    trigger = db.Column(db.String(500), nullable=False)
    reac_id = db.Column(db.Integer(), nullable=False)

    def __init__(self, *, id=None, trigger, reac_id):
        """Initialize self."""
        self.id = id                # Si None : auto-incrément
        self.trigger = trigger
        self.reac_id = reac_id


class Reactions(db.Model):
    """Table de données des réactions d'IA connues du bot"""

    id = db.Column(db.Integer(), primary_key=True)
    reponse = db.Column(db.String(2000), nullable=False)     # Réponse, dans le format personnalisé : "txt <||> txt <&&> <##>react"

    def __init__(self, *, id=None, reponse=None):
        """Initialize self."""
        self.id = id                # Si None : auto-incrément
        self.reponse = reponse


class CandidHaro(db.Model):
    """Table de données des candidatures et haros en cours  #PhilippeCandidHaro"""

    id = db.Column(db.Integer(), primary_key = True)
    player_id = db.Column(db.BigInteger(), nullable=False)
    type = db.Column(db.String(11), nullable=False)

    def __init__(self, *, id=None, player_id, type):
        """Initialize self."""
        self.id = id
        self.player_id = player_id
        self.type = type


Tables = {"Joueurs":Joueurs,        # Dictionnaire {nom de la table: Table}
          "Roles":Roles,
          "BaseActions":BaseActions,
          "Actions":Actions,
          "BaseActionsRoles": BaseActionsRoles,
          "Taches": Taches,
          "Triggers": Triggers,
          "Reactions": Reactions,
          "CandidHaro":CandidHaro
          }

db.create_all()
