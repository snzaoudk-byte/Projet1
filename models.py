from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash



class Election(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    titre     = db.Column(db.String(200), nullable=False)
    ouverte   = db.Column(db.Boolean, default=True)

    
    candidats = db.relationship('Candidat', backref='election', lazy=True)

    def __repr__(self):
        return f"<Election {self.titre}>"


class Electeur(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    nom           = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe  = db.Column(db.String(200), nullable=False)


    has_voted     = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Hash le mot de passe avant de le stocker"""
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.mot_de_passe, password)

    def __repr__(self):
        return f"<Electeur {self.nom}>"

class Candidat(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    nom         = db.Column(db.String(100), nullable=False)


    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=True)

    def __repr__(self):
        return f"<Candidat {self.nom}>"


class Vote(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    electeur_id  = db.Column(db.Integer, db.ForeignKey('electeur.id'), nullable=False)
    candidat_id  = db.Column(db.Integer, db.ForeignKey('candidat.id'), nullable=False)

    electeur = db.relationship('Electeur', backref='votes')
    candidat = db.relationship('Candidat', backref='votes_recus')

    def __repr__(self):
        return f"<Vote electeur={self.electeur_id} → candidat={self.candidat_id}>"