import enum

# Create database connection object

class cache_TDB(db.Model):
    messenger_user_id = db.Column(db.BigInteger(), primary_key=True)
    inscrit = db.Column(db.Boolean(), nullable=False)

    nom = db.Column(db.String(32), nullable=False)
    chambre = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(32), nullable=False)

    role = db.Column(db.String(32), nullable=False)
    camp = db.Column(db.String(32), nullable=False)

    votantVillage = db.Column(db.Boolean(), nullable=False)
    votantLoups = db.Column(db.Boolean(), nullable=False)

    roleActif = db.Column(db.Boolean(), nullable=True)
    debutRole = db.Column(db.Integer(), nullable=True)
    finRole = db.Column(db.Integer(), nullable=True)

    def __repr__(self):
        return f"<cache_TDB ({self.messenger_user_id}/{self.nom})>"

    def __init__(self, messenger_user_id, inscrit, nom, chambre, statut, role, camp, votantVillage, votantLoups, roleActif=None, debutRole=None, finRole=None):
        self.messenger_user_id = messenger_user_id
        self.inscrit = inscrit

        self.nom = nom
        self.chambre = chambre
        self.statut = statut

        self.role = role
        self.camp = camp

        self.votantVillage = votantVillage
        self.votantLoups = votantLoups

        self.roleActif = roleActif
        self.debutRole = debutRole
        self.finRole = finRole


class role_BDD(db.Model) :
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

db.create_all()
