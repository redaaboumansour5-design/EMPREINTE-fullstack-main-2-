"""
routes/conges.py
----------------
Gestion des demandes de congé (employé + validation manager/RH).

  POST   /api/conges/demandes
  GET    /api/conges/demandes
  PATCH  /api/conges/demandes/<id>/decider
"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from extensions import db
from models import Conge, Utilisateur
from routes._auth_utils import principal_courant, role_requis
from services.presence_service import jours_conge_decomptables

bp = Blueprint("conges", __name__, url_prefix="/api/conges")


@bp.route("/demandes", methods=["POST"])
@role_requis("declarer_conge")
def creer_demande():
    principal = principal_courant()
    payload = request.get_json(silent=True) or {}
    try:
        date_debut = datetime.strptime(payload["date_debut"], "%Y-%m-%d").date()
        date_fin = datetime.strptime(payload["date_fin"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return jsonify(erreur="date_debut et date_fin (YYYY-MM-DD) sont requis."), 400

    if date_fin < date_debut:
        return jsonify(erreur="date_fin doit être postérieure ou égale à date_debut."), 400

    demande = Conge(
        utilisateur_id=principal.id,
        date_debut=date_debut,
        date_fin=date_fin,
        motif=payload.get("motif", ""),
        statut="SOUMISE",
    )
    db.session.add(demande)
    db.session.commit()
    return jsonify(
        statut="SOUMISE",
        message="Demande de congé envoyée.",
        demande=demande.to_dict(),
    ), 201


@bp.route("/demandes", methods=["GET"])
@role_requis("valider_conge", "declarer_conge")
def lister_demandes():
    principal = principal_courant()
    claims = get_jwt()
    role = claims.get("role")

    query = Conge.query
    if role == "employe":
        query = query.filter(Conge.utilisateur_id == principal.id)
    elif role == "manager":
        query = query.join(Utilisateur, Conge.utilisateur_id == Utilisateur.id).filter(
            Utilisateur.departement_id == principal.departement_id
        )

    statut = request.args.get("statut")
    if statut:
        query = query.filter(Conge.statut == statut.upper())

    demandes = query.order_by(Conge.date_debut.desc()).all()
    return jsonify([d.to_dict() for d in demandes]), 200


@bp.route("/demandes/<int:demande_id>/decider", methods=["PATCH"])
@role_requis("valider_conge")
def decider(demande_id):
    demande = db.session.get(Conge, demande_id)
    if demande is None:
        return jsonify(erreur="Demande introuvable."), 404
    if demande.statut != "SOUMISE":
        return jsonify(erreur="Cette demande a déjà été traitée."), 409

    payload = request.get_json(silent=True) or {}
    decision = payload.get("statut")
    if decision not in ("APPROUVE", "REJETE"):
        return jsonify(erreur="statut doit valoir 'APPROUVE' ou 'REJETE'."), 400

    principal = principal_courant()
    demande.statut = decision
    demande.validateur_id = principal.id if isinstance(principal, Utilisateur) else None
    demande.date_decision = datetime.utcnow()
    demande.commentaire = payload.get("commentaire")
    db.session.commit()

    jours_decomptes = jours_conge_decomptables(demande) if decision == "APPROUVE" else 0
    message = "Congé approuvé." if decision == "APPROUVE" else "Congé rejeté."
    return jsonify(
        statut=decision,
        message=message,
        jours_decomptes=jours_decomptes,
        demande=demande.to_dict(),
    ), 200
