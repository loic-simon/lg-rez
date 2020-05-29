import enum

# Create database connection object

class Joueurs(db.Model):
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

    _vote_village = db.Column(db.String(200), nullable=True)
    _vote_maire = db.Column(db.String(200), nullable=True)
    _action_role = db.Column(db.Text(), nullable=True)

    def __repr__(self):
        return f"<Joueurs ({self.discord_id}/{self.nom})>"

    def __init__(self, discord_id, _chan_id, nom, chambre, statut, role, camp, votant_village, votant_loups, role_actif=None, _vote_village=None, _vote_maire=None, _action_role=None):
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

        self._vote_village = _vote_village
        self._vote_maire = _vote_village
        self._action_role = _vote_village


class Roles(db.Model) :
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
        self.slug = slug
        self.prefixe = prefixe
        self.nom = nom
        self.camp = camp
        self.description_courte = description_courte
        self.description_longue = description_longue


class BaseActions(db.Model):
    action = db.Column(db.String(32), primary_key=True)
    
    trigger_debut = db.Column(db.String(32), nullable=False)
    trigger_fin = db.Column(db.String(32), nullable=False)
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

    def __init__(self, action, trigger_debut, trigger_fin, instant=None, heure_debut=None, heure_fin=None, base_cooldown=0, base_charges=None, refill=None, lieu=None, interaction_notaire=None, interaction_gardien=None, mage=None, changement_cible=None):
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
    entry_num = db.Column(db.Integer(), primary_key=True)
    player_id = db.Column(db.BigInteger(), nullable=False)
    action = db.Column(db.String(32), nullable=False)

    cible_id = db.Column(db.BigInteger(), nullable=True)
    cible2_id = db.Column(db.BigInteger(), nullable=True)

    charges = db.Column(db.Integer(), nullable=True) #Nombrede charges RESTANTES sur l'action, infini si None
    cooldown = db.Column(db.Integer(), nullable=False) #Cooldown restant à l'action, 0=utilisable, None=toujours utilisable

    #treated = db.Column(db.Boolean(), nullable=False)

    def __init__(self, player_id, action, cible_id, cible2_id, charges, cooldown):
        self.player_id = player_id
        self.action = action #Nom de l'action en rapport avec la table BaseActions

        self.cible_id = cible_id
        self.cible2_id = cible2_id

        self.charges = charges      #Nombre de charges restantes (mettre à Null si toujours dispo)
        self.cooldown = cooldown    #Cooldown restant pour l'action (Null si pas de cooldown)

        #self.treated = treated


class BaseActionsRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    role = db.Column(db.String(32), nullable=False)
    action = db.Column(db.String(32), nullable=False)

    def __init__(self, id, role, action):
        self.id = id
        self.role = role
        self.action = action


Tables = {"Joueurs":Joueurs,
          "Roles":Roles,
          "BaseActions":BaseActions,
          "Actions":Actions,
          "BaseActionsRoles": BaseActionsRoles,
          }

db.create_all()
