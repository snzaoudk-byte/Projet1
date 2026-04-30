from flask import Blueprint, request, jsonify, render_template, current_app
from extensions import db
from models import Electeur, Candidat, Vote, Election
import jwt
import datetime
from functools import wraps

main = Blueprint('main', __name__)


# ============================================================
# DÉCORATEUR — Vérification du token JWT
# ============================================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({"erreur": "Token manquant"}), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=["HS256"]
            )
            # ✅ Récupérer l'électeur connecté depuis le token
            electeur = Electeur.query.get(payload['user_id'])
            if not electeur:
                return jsonify({"erreur": "Utilisateur introuvable"}), 401
            request.current_user = electeur  # disponible dans toutes les routes

        except jwt.ExpiredSignatureError:
            return jsonify({"erreur": "Token expiré, reconnectez-vous"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"erreur": "Token invalide"}), 401

        return f(*args, **kwargs)
    return decorated


# ============================================================
# AUTHENTIFICATION
# ============================================================

@main.route('/login', methods=['POST'])
def login():
    data = request.json

    if not data or 'email' not in data or 'mot_de_passe' not in data:
        return jsonify({"erreur": "Email et mot_de_passe obligatoires"}), 400

    # ✅ Chercher l'électeur dans la base par email
    electeur = Electeur.query.filter_by(email=data['email']).first()

    if not electeur or not electeur.check_password(data['mot_de_passe']):
        return jsonify({"erreur": "Email ou mot de passe incorrect"}), 401

    # ✅ Générer un token unique pour cet électeur
    token = jwt.encode(
        {
            "user_id": electeur.id,
            "nom": electeur.nom,
            "email": electeur.email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        },
        current_app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    return jsonify({
        "message": f"Bienvenue {electeur.nom} !",
        "token": token,
        "electeur": {
            "id": electeur.id,
            "nom": electeur.nom,
            "email": electeur.email
        }
    }), 200


# ============================================================
# PAGE D'ACCUEIL
# ============================================================

@main.route('/')
def index():
    return render_template('index.html')


# ============================================================
# ÉLECTIONS
# ============================================================

@main.route('/elections', methods=['POST'])
@token_required  # ✅ protégé
def create_election():
    data = request.json
    election = Election(titre=data['titre'])
    db.session.add(election)
    db.session.commit()
    return jsonify({"id": election.id, "titre": election.titre}), 201


@main.route('/elections', methods=['GET'])
def list_elections():
    elections = Election.query.all()
    return jsonify([{"id": e.id, "titre": e.titre, "ouverte": e.ouverte} for e in elections])


# ============================================================
# ÉLECTEURS
# ============================================================

@main.route('/electeurs', methods=['POST'])
def create_electeur():
    data = request.json
    if Electeur.query.filter_by(email=data['email']).first():
        return jsonify({"erreur": "Email déjà utilisé"}), 400

    electeur = Electeur(nom=data['nom'], email=data['email'], mot_de_passe="")
    electeur.set_password(data['mot_de_passe'])
    db.session.add(electeur)
    db.session.commit()
    return jsonify({"id": electeur.id, "nom": electeur.nom}), 201


@main.route('/electeurs', methods=['GET'])
@token_required  # ✅ protégé
def list_electeurs():
    electeurs = Electeur.query.all()
    return jsonify([
        {"id": e.id, "nom": e.nom, "email": e.email, "has_voted": e.has_voted}
        for e in electeurs
    ])


# ============================================================
# CANDIDATS
# ============================================================

@main.route('/candidats', methods=['POST'])
@token_required  # ✅ protégé
def create_candidat():
    data = request.json
    candidat = Candidat(nom=data['nom'], election_id=data.get('election_id'))
    db.session.add(candidat)
    db.session.commit()
    return jsonify({"id": candidat.id, "nom": candidat.nom}), 201


@main.route('/candidats', methods=['GET'])
def list_candidats():
    candidats = Candidat.query.all()
    return jsonify([{"id": c.id, "nom": c.nom, "election_id": c.election_id} for c in candidats])


# ============================================================
# VOTE
# ============================================================

@main.route('/vote', methods=['POST'])
@token_required
def voter():
    data = request.json

    # ✅ L'électeur est automatiquement celui connecté via le token
    electeur = request.current_user

    if electeur.has_voted:
        return jsonify({"erreur": "Vous avez déjà voté !"}), 400

    candidat = Candidat.query.get(data['candidat_id'])
    if not candidat:
        return jsonify({"erreur": "Candidat introuvable"}), 404

    vote = Vote(electeur_id=electeur.id, candidat_id=candidat.id)
    db.session.add(vote)
    electeur.has_voted = True
    db.session.commit()
    return jsonify({"message": f"{electeur.nom} a voté pour {candidat.nom} "}), 201


# ============================================================
# RÉSULTATS
# ============================================================

@main.route('/resultats', methods=['GET'])
@token_required  # ✅ protégé
def resultats():
    candidats = Candidat.query.all()
    data = []
    for c in candidats:
        votes = Vote.query.filter_by(candidat_id=c.id).all()
        electeurs = [v.electeur.nom for v in votes]
        data.append({"candidat": c.nom, "votes": len(votes), "electeurs": electeurs})
    data.sort(key=lambda x: x['votes'], reverse=True)
    return jsonify(data)