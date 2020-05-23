import enum

# Create database connection object

class Joueurs(db.Model):
    discord_id = db.Column(db.BigInteger(), primary_key=True)
    _chan_id = db.Column(db.String(42), nullable=False)
    # inscrit = db.Column(db.Boolean(), nullable=False)

    nom = db.Column(db.String(32), nullable=False)
    chambre = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(32), nullable=False)

    role = db.Column(db.String(32), nullable=False)
    camp = db.Column(db.String(32), nullable=False)

    votantVillage = db.Column(db.Boolean(), nullable=False)
    votantLoups = db.Column(db.Boolean(), nullable=False)
    roleActif = db.Column(db.Boolean(), nullable=True)
    # debutRole = db.Column(db.Integer(), nullable=True)
    # finRole = db.Column(db.Integer(), nullable=True)

    _voteVillage = db.Column(db.String(200), nullable=True)
    _voteMaire = db.Column(db.String(200), nullable=True)
    _actionRole = db.Column(db.Text(), nullable=True)

    def __repr__(self):
        return f"<Joueurs ({self.discord_id}/{self.nom})>"

    def __init__(self, discord_id, _chan_id, nom, chambre, statut, role, camp, votantVillage, votantLoups, roleActif=None, _voteVillage=None, _voteMaire=None, _actionRole=None):
        self.discord_id = discord_id
        self._chan_id = _chan_id
        # self.inscrit = inscrit

        self.nom = nom
        self.chambre = chambre
        self.statut = statut

        self.role = role
        self.camp = camp

        self.votantVillage = votantVillage
        self.votantLoups = votantLoups
        self.roleActif = roleActif
        # self.debutRole = debutRole
        # self.finRole = finRole

        self._voteVillage = _voteVillage
        self._voteMaire = _voteVillage
        self._actionRole = _voteVillage


class Roles(db.Model) :
    nom_du_role = db.Column(db.String(32), primary_key = True)
    camp = db.Column(db.String(32), nullable = False)                       #Loups, Solitaire, Nécros, Villageois

    description_courte = db.Column(db.String(140), nullable = False)
    description_longue = db.Column(db.String(280), nullable = False)

    horaire_debut = db.Column(db.Integer(), nullable = True)                #Au format HHMM ou None
    horaire_fin = db.Column(db.Integer(), nullable = True)                  #Au format HHMM ou None
    Lieu = db.Column(db.String(32), nullable = True)                        #Distance/Physique/Lieu/Contact/Conditionnel/None/Public

    Type = db.Column(db.String(32), nullable = False)                       #Quotidien, Unique, <Nombre>, Passif, Conditionnel, Hebdomadaire, Bicircadien, Special
    ChangementCible = db.Column(db.Boolean(), nullable = True)              #True, False ou None

    InteractionNotaire = db.Column(db.String(32), nullable = True)         #Oui, Non, Conditionnel, Potion, Rapport; None si récursif
    InteractionGardien = db.Column(db.String(32), nullable = True)         #Oui, Non, Conditionnel, Taverne, Feu, MaisonClose, Précis, Cimetière, Loups, None si recursif

    def __init__(self, nom_du_role, description_courte, description_longue, camp, horaire_debut, horaire_fin, Lieu, Type, ) :
        self.nom_du_role = nom_du_role
        self.camp = camp

        self.description_courte = description_courte
        self.description_longue = description_longue

        self.horaire_debut = horaire_debut
        self.horaire_fin = horaire_fin

        self.Lieu = Lieu
        self.Type = Type

        #self.InteractionGardien = InteractionG
        #self.InteractionNotaire = InteractionN

        #self.ChangementCible = ChangementCible



class BaseActions(db.Models):
    action = db.Column(db.String(64), primary_key = True)
    trigger_debut = db.Column(db.Integer(), nullable = True)
    trigger_fin = db.Column(db.Integer(), nullable = True)

    base_cooldown = db.Column(db.Integer(), nullable = True)
    type  = db.Column(db.String(32), nullable = False) #Quotidien, Unique, <Nombre>, Passif, Conditionnel, Hebdomadaire, Bicircadien, Special
    lieu = db.Column(db.String(32), nullable = True) #Distance/Physique/Lieu/Contact/Conditionnel/None/Public

    interaction_notaire = db.Column(db.String(32), nullable = True)         #Oui, Non, Conditionnel, Potion, Rapport; None si récursif
    interaction_gardien = db.Column(db.String(32), nullable = True)         #Oui, Non, Conditionnel, Taverne, Feu, MaisonClose, Précis, Cimetière, Loups, None si recursif
    mage = db.Column(db.String(32), nullable = True)                       #Oui, Non, changement de cible, etc

    params = db.Column(db.String(32), nullable = True)

    def __init__(self, action, trigger_debut, trigger_fin, base_cooldown, type, lieu, interaction_notaire, interaction_gardien, mage, params):
        self.action = action
        self.trigger_debut = trigger_debut
        self.trigger_fin = trigger_fin

        self.base_cooldown = base_cooldown
        self.type = type #Quotidien, Unique, <Nombre>, Passif, Conditionnel, Hebdomadaire, Bicircadien, Special
        self.lieu = lieu #Distance/Physique/Lieu/Contact/Conditionnel/None/Public

        self.interaction_notaire = interaction_notaire         #Oui, Non, Conditionnel, Potion, Rapport; None si récursif
        self.interaction_gardien = interaction_gardien         #Oui, Non, Conditionnel, Taverne, Feu, MaisonClose, Précis, Cimetière, Loups, None si recursif
        self.mage = mage                       #Oui, Non, changement de cible, etc

        self.params = params



class Actions(db.Models):
    entry_num = db.Column(db.Integer(), primary_key = True)
    discord_id = db.Column(db.BigInteger(), nullable = False)
    action = db.Column(db.String(32), nullable = False)

    cible_id = db.Column(db.BigInteger(), nullable = True)
    cible2_id = db.Column(db.BigInteger(), nullable = True)

    charges = db.Column(db.Integer(), nullable = True)
    cooldown = db.Column(db.Integer(), nullable = True)

    #treated = db.Column(db.Boolean(), nullable = False)

    def __init__(self, entry_num, discord_id, action, cible_id, cible2_id, treated):
        self.entry_num = entry_num #Incrémenter auto
        self.discord_id = discord_id
        self.action = action #Nom de l'action en rapport avec la table BaseActions

        self.cible_id = cible_id
        self.cible2_id = cible2_id

        self.charges = charges      #Nombre de charges restantes (mettre à Null si toujours dispo)
        self.cooldown = cooldown    #Cooldown restant pour l'action (Null si pas de cooldown)

        #self.treated = treated

Tables = {"Joueurs":Joueurs,
          "Roles":Roles,
          "BaseActions":BaseActions,
          "Actions":Actions
          }

db.create_all()
