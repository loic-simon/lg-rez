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


db.create_all()

class role_BDD(db.Model) :
    nom_du_role = db.Column(db.String(32), primary_key = True)
    description_courte = db.Column(db.String(140), nullable = False)
    description_longue = db.Column(db.String(280), nullable = False)
    camp = db.Column(db.String(32), nullable = False)
    horaire_debut = db.Column(db.Integer(), nullable = False)
    horaire_fin = db.Column(db.Integer(), nullable = False)
    interaction = db.Column(None) #NON
