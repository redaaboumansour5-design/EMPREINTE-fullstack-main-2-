"""
routes/employes.py
----------------------
UC-07 — Gérer employés (Espace RH).
CRUD sur Utilisateur + enrôlement de l'empreinte faciale de référence.
"""
from datetime import datetime
import re
import unicodedata

from flask import Blueprint, jsonify, request

from extensions import db
from models import Utilisateur, Departement, ReconnaissanceFaciale
from routes._auth_utils import role_requis
from services import reconnaissance_service as rs
from services.reconnaissance_service import VisageNonDetecteError, ServiceReconnaissanceIndisponibleError

bp = Blueprint("employes", __name__, url_prefix="/api/employes")

REGEX_MATRICULE = re.compile(r"^[A-Z0-9]{3,10}$")
REGEX_NOM = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[ '-][A-Za-zÀ-ÖØ-öø-ÿ]+)*$")
REGEX_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
REGEX_POSTE = re.compile(r"^[A-Za-z0-9À-ÖØ-öø-ÿ]+(?:[ '-][A-Za-z0-9À-ÖØ-öø-ÿ]+)*$")
REGEX_MOT_DE_PASSE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d\s]).{8,}$")


def _normaliser_texte(valeur):
    return unicodedata.normalize("NFC", valeur.strip()) if isinstance(valeur, str) else valeur


def _erreurs_validation_employe(payload, *, creation=False):
    erreurs = {}
    champs = ("matricule", "nom", "prenom", "email", "poste", "password") if creation else ("nom", "prenom", "email", "poste", "password")
    for champ in champs:
        if champ in payload and isinstance(payload[champ], str):
            payload[champ] = _normaliser_texte(payload[champ])

    if creation and not REGEX_MATRICULE.fullmatch(payload.get("matricule", "")):
        erreurs["matricule"] = "Le matricule doit contenir 3 à 10 lettres majuscules ou chiffres."
    for champ, libelle in (("nom", "nom"), ("prenom", "prénom")):
        if champ in payload and not REGEX_NOM.fullmatch(payload.get(champ, "")):
            erreurs[champ] = f"Le {libelle} contient des caractères invalides."
    if "email" in payload and not REGEX_EMAIL.fullmatch(payload.get("email", "")):
        erreurs["email"] = "L'adresse email n'est pas valide."
    if "password" in payload and not REGEX_MOT_DE_PASSE.fullmatch(payload.get("password", "")):
        erreurs["password"] = "Le mot de passe doit contenir 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial."
    if "poste" in payload and payload["poste"] and not REGEX_POSTE.fullmatch(payload["poste"]):
        erreurs["poste"] = "Le poste accepte les lettres, chiffres, accents, espaces et tirets."
    return erreurs


@bp.route("", methods=["GET"])
@role_requis("gerer_employes", "consulter_equipe")
def lister():
    query = Utilisateur.query

    # Sécurité : un manager ne doit voir que les employés de son département.
    # (Le filtrage côté front n'est pas suffisant.)
    from routes._auth_utils import principal_courant

    principal = principal_courant()
    if principal is not None and getattr(principal, "role", None) == "manager":
        if principal.departement_id is None:
            # Aucun département : on renvoie une liste vide.
            utilisateurs = []
            return jsonify([u.to_dict() for u in utilisateurs]), 200
        query = query.filter(Utilisateur.departement_id == principal.departement_id)

    # HR / Admin : filtrage optionnel par departement_id
    departement_id = request.args.get("departement_id", type=int)
    if departement_id:
        # Si c'est un manager, le filtre principal() a déjà restreint le scope.
        # Garder ce paramètre permet un usage pour RH/Admin uniquement.
        if principal is None or getattr(principal, "role", None) != "manager":
            query = query.filter(Utilisateur.departement_id == departement_id)

    recherche = request.args.get("q")
    if recherche:
        like = f"%{recherche}%"
        query = query.filter(
            db.or_(
                Utilisateur.nom.ilike(like),
                Utilisateur.prenom.ilike(like),
                Utilisateur.matricule.ilike(like),
                Utilisateur.email.ilike(like),
            )
        )

    utilisateurs = query.order_by(Utilisateur.nom).all()
    return jsonify([u.to_dict() for u in utilisateurs]), 200



@bp.route("/<int:utilisateur_id>", methods=["GET"])
@role_requis("gerer_employes", "consulter_equipe")
def obtenir(utilisateur_id):
    utilisateur = db.session.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        return jsonify(erreur="Employé introuvable."), 404
    return jsonify(utilisateur.to_dict()), 200


@bp.route("", methods=["POST"])
@role_requis("gerer_employes")
def creer():
    """
    +gererEmployes(action, e: Employe) : void — création.
    Body : { matricule, nom, prenom, email, password, telephone, role,
             poste, date_embauche (YYYY-MM-DD), departement_id }
    """
    payload = request.get_json(silent=True) or {}
    champs_requis = ["matricule", "nom", "prenom", "email", "password", "role"]
    manquants = [c for c in champs_requis if not payload.get(c)]
    if manquants:
        return jsonify(erreur=f"Champs manquants : {', '.join(manquants)}"), 400

    erreurs_validation = _erreurs_validation_employe(payload, creation=True)
    if erreurs_validation:
        return jsonify(erreur="Certains champs sont invalides.", champs=erreurs_validation), 400

    if payload["role"] not in ("employe", "manager", "rh"):
        return jsonify(erreur="role doit être employe, manager ou rh."), 400

    if Utilisateur.query.filter_by(email=payload["email"]).first():
        return jsonify(erreur="Cet email est déjà utilisé."), 409
    if Utilisateur.query.filter_by(matricule=payload["matricule"]).first():
        return jsonify(erreur="Ce matricule est déjà utilisé."), 409

    utilisateur = Utilisateur(
        matricule=payload["matricule"],
        nom=payload["nom"],
        prenom=payload["prenom"],
        email=payload["email"],
        telephone=payload.get("telephone"),
        role=payload["role"],
        poste=payload.get("poste"),
        departement_id=payload.get("departement_id"),
        date_embauche=(
            datetime.strptime(payload["date_embauche"], "%Y-%m-%d").date()
            if payload.get("date_embauche") else None
        ),
    )

    # Règle : 1 département -> 1 seul manager
    if utilisateur.role == "manager" and utilisateur.departement_id:
        dept = db.session.get(Departement, utilisateur.departement_id)
        if dept and dept.responsable_id is not None:
            # Si le département a déjà un manager différent, on bloque
            if dept.responsable_id != utilisateur.id:
                return (
                    jsonify(
                        erreur="Conflit d'affectation : ce département est déjà géré par un autre manager."
                    ),
                    409,
                )

    utilisateur.set_password(payload["password"])
    db.session.add(utilisateur)
    db.session.commit()

    # Si c'est bien un manager, on assigne ce manager comme responsable du département
    if utilisateur.role == "manager" and utilisateur.departement_id:
        dept = db.session.get(Departement, utilisateur.departement_id)
        if dept:
            dept.responsable_id = utilisateur.id
            db.session.commit()

    return jsonify(utilisateur.to_dict()), 201


@bp.route("/<int:utilisateur_id>", methods=["PUT", "PATCH"])
@role_requis("gerer_employes")
def modifier(utilisateur_id):
    utilisateur = db.session.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        return jsonify(erreur="Employé introuvable."), 404

    payload = request.get_json(silent=True) or {}
    erreurs_validation = _erreurs_validation_employe(payload)
    if erreurs_validation:
        return jsonify(erreur="Certains champs sont invalides.", champs=erreurs_validation), 400
    for champ in ("nom", "prenom", "telephone", "poste", "role", "departement_id"):
        if champ in payload:
            setattr(utilisateur, champ, payload[champ])
    if payload.get("date_embauche"):
        utilisateur.date_embauche = datetime.strptime(payload["date_embauche"], "%Y-%m-%d").date()
    if payload.get("password"):
        utilisateur.set_password(payload["password"])

    db.session.commit()
    return jsonify(utilisateur.to_dict()), 200


@bp.route("/<int:utilisateur_id>", methods=["DELETE"])
@role_requis("gerer_employes")
def supprimer(utilisateur_id):
    utilisateur = db.session.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        return jsonify(erreur="Employé introuvable."), 404
    db.session.delete(utilisateur)
    db.session.commit()
    return "", 204


@bp.route("/<int:utilisateur_id>/empreinte", methods=["POST"])
@role_requis("gerer_employes")
def enroler_empreinte(utilisateur_id):
    """
    Enrôlement biométrique initial (UC-07, préalable indispensable à UC-02) :
    capture une photo de référence et enregistre son embedding FaceNet.
    Body : { "photo": "data:image/jpeg;base64,..." }
    """
    utilisateur = db.session.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        return jsonify(erreur="Employé introuvable."), 404

    photo = (request.get_json(silent=True) or {}).get("photo")
    if not photo:
        return jsonify(erreur="Champ 'photo' manquant."), 400

    try:
        resultat = rs.generer_embedding(photo, detector_backend="opencv")
    except VisageNonDetecteError as exc:
        return jsonify(erreur=str(exc), code="VISAGE_NON_RECONNU"), 422
    except ServiceReconnaissanceIndisponibleError as exc:
        return jsonify(erreur=str(exc), code="SERVICE_INDISPONIBLE"), 503

    empreinte = utilisateur.empreinte or ReconnaissanceFaciale(utilisateur_id=utilisateur.id)
    empreinte.set_embedding(resultat.embedding)
    empreinte.modele = resultat.modele
    db.session.add(empreinte)
    db.session.commit()
    return jsonify(empreinte.to_dict()), 201


@bp.route("/departements", methods=["GET"])
@role_requis("gerer_employes", "consulter_equipe")
def lister_departements():
    return jsonify([d.to_dict() for d in Departement.query.order_by(Departement.nom).all()]), 200
