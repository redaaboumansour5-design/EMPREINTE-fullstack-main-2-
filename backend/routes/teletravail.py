"""
routes/teletravail.py
-------------------------
UC-04 — Déclarer télétravail (employé)
UC-06 — Valider télétravail (manager)

Reproduit le diagramme de séquence "Demande & Validation de Télétravail" :
  1. POST /api/teletravail/demandes            (employé soumet -> statut SOUMISE)
  2. GET  /api/teletravail/demandes?statut=SOUMISE  (manager consulte son équipe)
  3. PATCH /api/teletravail/demandes/<id>/decider   (manager approuve/rejette)
"""
from datetime import datetime, date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from extensions import db
from models import Teletravail, Utilisateur
from routes._auth_utils import principal_courant, role_requis

bp = Blueprint("teletravail", __name__, url_prefix="/api/teletravail")


@bp.route("/demandes", methods=["POST"])
@role_requis("declarer_teletravail")
def creer_demande():
    """+declarerTeletravail(demande) : void — POST /api/teletravail/demandes"""
    principal = principal_courant()
    payload = request.get_json(silent=True) or {}
    try:
        date_debut = datetime.strptime(payload["date_debut"], "%Y-%m-%d").date()
        date_fin = datetime.strptime(payload["date_fin"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return jsonify(erreur="date_debut et date_fin (YYYY-MM-DD) sont requis."), 400

    if date_fin < date_debut:
        return jsonify(erreur="date_fin doit être postérieure ou égale à date_debut."), 400

    demande = Teletravail(
        utilisateur_id=principal.id,
        date_debut=date_debut,
        date_fin=date_fin,
        motif=payload.get("motif", ""),
        statut="SOUMISE",
    )
    db.session.add(demande)
    db.session.commit()
    return jsonify(statut="SOUMISE", message="Demande envoyée au manager.", demande=demande.to_dict()), 201


@bp.route("/demandes", methods=["GET"])
@role_requis("valider_teletravail", "declarer_teletravail")
def lister_demandes():
    """GET /api/teletravail/demandes?statut=SOUMISE&managerId=@id"""
    principal = principal_courant()
    claims = get_jwt()
    role = claims.get("role")

    query = Teletravail.query
    if role == "employe":
        query = query.filter(Teletravail.utilisateur_id == principal.id)
    elif role == "manager":
        query = query.join(Utilisateur, Teletravail.utilisateur_id == Utilisateur.id).filter(
            Utilisateur.departement_id == principal.departement_id
        )
    # rh / administrateur : vision globale (aucun filtre)

    statut = request.args.get("statut")
    if statut:
        query = query.filter(Teletravail.statut == statut.upper())

    demandes = query.order_by(Teletravail.date_debut.desc()).all()
    return jsonify([d.to_dict() for d in demandes]), 200


@bp.route("/demandes/<int:demande_id>/decider", methods=["PATCH"])
@role_requis("valider_teletravail")
def decider(demande_id):
    """
    PATCH /api/teletravail/demandes/{id}/decider
    Body : { "statut": "APPROUVE" | "REJETE", "commentaire": "..." (optionnel) }
    """
    demande = db.session.get(Teletravail, demande_id)
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

    # Si la demande est APPROUVÉE : autoriser le télétravail pour l'employé
    if decision == "APPROUVE":
        # Sécurité: éviter un 500 si la relation n'est pas résolue
        # (ex: problème de mapping/DB, employé supprimé, etc.)
        if getattr(demande, "employe", None) is not None:
            demande.employe.teletravail_autorise = True
        else:
            employe = db.session.get(Utilisateur, demande.utilisateur_id)
            if employe is None:
                return jsonify(erreur="Employé introuvable pour cette demande."), 404
            employe.teletravail_autorise = True


    db.session.commit()

    message = "Demande approuvée avec succès" if decision == "APPROUVE" else "Demande rejetée"
    return jsonify(statut=decision, message=message, demande=demande.to_dict()), 200


@bp.route("/resume", methods=["GET"])
@role_requis("valider_teletravail", "declarer_teletravail")
def resume():
    """Compteurs pour les 3 chips du dashboard (en attente / approuvées ce mois / rejetées ce mois)."""
    principal = principal_courant()
    claims = get_jwt()
    role = claims.get("role")

    query = Teletravail.query
    if role == "employe":
        query = query.filter(Teletravail.utilisateur_id == principal.id)
    elif role == "manager":
        query = query.join(Utilisateur, Teletravail.utilisateur_id == Utilisateur.id).filter(
            Utilisateur.departement_id == principal.departement_id
        )

    debut_mois = date.today().replace(day=1)
    en_attente = query.filter(Teletravail.statut == "SOUMISE").count()
    approuvees_mois = query.filter(
        Teletravail.statut == "APPROUVE", Teletravail.date_decision >= debut_mois
    ).count()
    rejetees_mois = query.filter(
        Teletravail.statut == "REJETE", Teletravail.date_decision >= debut_mois
    ).count()
    return jsonify(en_attente=en_attente, approuvees_ce_mois=approuvees_mois, rejetees_ce_mois=rejetees_mois), 200
