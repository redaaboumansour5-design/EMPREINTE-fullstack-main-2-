"""
routes/demandes.py
------------------
API unifiée pour les demandes de congé ET de télétravail.
Fusionne les endpoints de conges.py et teletravail.py dans une interface unique.

Endpoints :
  GET    /api/demandes          — Liste filtrée (type, statut, période)
  GET    /api/demandes/resume   — Stats combinées
  POST   /api/demandes          — Créer une demande (type = conge | teletravail)
  PATCH  /api/demandes/<int:id>/decider — Valider/refuser (détection auto du type)
"""
from datetime import datetime, date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt

from extensions import db
from models import Conge, Teletravail, Utilisateur
from routes._auth_utils import principal_courant, role_requis
from services.presence_service import (
    aujourd_hui_casablanca,
    jours_conge_decomptables,
)

bp = Blueprint("demandes", __name__, url_prefix="/api/demandes")

# ─── Utilitaires ────────────────────────────────────────────────────────────

def _determiner_perimetre(role: str, principal) -> str:
    """Détermine si l'utilisateur voit ses propres demandes, celles de son département ou toutes."""
    if role == "employe":
        return "mine"
    if role in {"manager", "rh"} and getattr(principal, "departement_id", None):
        return "departement"
    return "all"


def _serialiser_conge(c: Conge) -> dict:
    return {
        "id": c.id,
        "type_demande": "conge",
        "employe": {
            "id": c.employe.id,
            "nom_complet": f"{c.employe.prenom} {c.employe.nom}",
            "matricule": c.employe.matricule,
            "departement": c.employe.departement.nom if c.employe.departement else None,
        },
        "date_debut": c.date_debut.isoformat(),
        "date_fin": c.date_fin.isoformat(),
        "motif": c.motif,
        "statut": c.statut,
        "validateur": (
            f"{c.validateur.prenom} {c.validateur.nom}" if c.validateur else None
        ),
        "date_decision": c.date_decision.isoformat() if c.date_decision else None,
        "commentaire": c.commentaire,
    }


def _serialiser_teletravail(t: Teletravail) -> dict:
    return {
        "id": t.id,
        "type_demande": "teletravail",
        "employe": {
            "id": t.employe.id,
            "nom_complet": f"{t.employe.prenom} {t.employe.nom}",
            "matricule": t.employe.matricule,
            "departement": t.employe.departement.nom if t.employe.departement else None,
        },
        "date_debut": t.date_debut.isoformat(),
        "date_fin": t.date_fin.isoformat(),
        "motif": t.motif,
        "statut": t.statut,
        "validateur": (
            f"{t.validateur.prenom} {t.validateur.nom}" if t.validateur else None
        ),
        "date_decision": t.date_decision.isoformat() if t.date_decision else None,
        "commentaire": t.commentaire,
    }


def _appliquer_filtres(query_conge, query_teletravail):
    """Applique les filtres ?type, ?statut, ?employe_id, ?date_debut, ?date_fin."""
    type_filtre = request.args.get("type")  # "conge", "teletravail", ou None (tous)
    statut = request.args.get("statut")
    employe_id = request.args.get("employe_id", type=int)
    date_debut_str = request.args.get("date_debut")
    date_fin_str = request.args.get("date_fin")

    if statut:
        statut_up = statut.upper()
        query_conge = query_conge.filter(Conge.statut == statut_up)
        query_teletravail = query_teletravail.filter(Teletravail.statut == statut_up)

    if employe_id:
        query_conge = query_conge.filter(Conge.utilisateur_id == employe_id)
        query_teletravail = query_teletravail.filter(Teletravail.utilisateur_id == employe_id)

    if date_debut_str:
        try:
            dd = date.fromisoformat(date_debut_str)
            query_conge = query_conge.filter(Conge.date_debut >= dd)
            query_teletravail = query_teletravail.filter(Teletravail.date_debut >= dd)
        except ValueError:
            pass

    if date_fin_str:
        try:
            df = date.fromisoformat(date_fin_str)
            query_conge = query_conge.filter(Conge.date_fin <= df)
            query_teletravail = query_teletravail.filter(Teletravail.date_fin <= df)
        except ValueError:
            pass

    return query_conge, query_teletravail


# ─── Endpoints ──────────────────────────────────────────────────────────────

@bp.route("", methods=["GET"])
@role_requis("valider_conge", "declarer_conge", "declarer_teletravail", "valider_teletravail")
def lister_demandes():
    """Liste unifiée des demandes, triée par date_debut décroissante."""
    principal = principal_courant()
    claims = get_jwt()
    role = claims.get("role")

    type_filtre = request.args.get("type")  # "conge", "teletravail", None

    q_conge = Conge.query
    q_teletravail = Teletravail.query

    perimetre = _determiner_perimetre(role, principal)

    if perimetre == "mine":
        q_conge = q_conge.filter(Conge.utilisateur_id == principal.id)
        q_teletravail = q_teletravail.filter(Teletravail.utilisateur_id == principal.id)
    elif perimetre == "departement" and principal.departement_id:
        q_conge = q_conge.join(Utilisateur, Conge.utilisateur_id == Utilisateur.id).filter(
            Utilisateur.departement_id == principal.departement_id
        )
        q_teletravail = q_teletravail.join(Utilisateur, Teletravail.utilisateur_id == Utilisateur.id).filter(
            Utilisateur.departement_id == principal.departement_id
        )

    q_conge, q_teletravail = _appliquer_filtres(q_conge, q_teletravail)

    resultats = []

    if type_filtre in (None, "conge"):
        for c in q_conge.order_by(Conge.date_debut.desc()).all():
            resultats.append(_serialiser_conge(c))

    if type_filtre in (None, "teletravail"):
        for t in q_teletravail.order_by(Teletravail.date_debut.desc()).all():
            resultats.append(_serialiser_teletravail(t))

    # Tri global par date_debut décroissante
    resultats.sort(key=lambda r: r["date_debut"], reverse=True)

    return jsonify(resultats), 200


@bp.route("/resume", methods=["GET"])
@role_requis("valider_conge", "declarer_conge", "declarer_teletravail", "valider_teletravail")
def resume():
    """Stats combinées : en_attente, approuvees_ce_mois, rejetees_ce_mois + breakdown par type."""
    principal = principal_courant()
    claims = get_jwt()
    role = claims.get("role")

    aujourd = aujourd_hui_casablanca()
    debut_mois = aujourd.replace(day=1)

    # Périmètre
    def _filtrer_scope(query_conge, query_teletravail):
        perimetre = _determiner_perimetre(role, principal)
        if perimetre == "mine":
            query_conge = query_conge.filter(Conge.utilisateur_id == principal.id)
            query_teletravail = query_teletravail.filter(Teletravail.utilisateur_id == principal.id)
        elif perimetre == "departement" and principal.departement_id:
            query_conge = query_conge.join(Utilisateur, Conge.utilisateur_id == Utilisateur.id).filter(
                Utilisateur.departement_id == principal.departement_id
            )
            query_teletravail = query_teletravail.join(Utilisateur, Teletravail.utilisateur_id == Utilisateur.id).filter(
                Utilisateur.departement_id == principal.departement_id
            )
        return query_conge, query_teletravail

    # --- Congés ---
    qc, _ = _filtrer_scope(Conge.query, Teletravail.query)
    conges_soumises = qc.filter(Conge.statut == "SOUMISE").count()
    conges_approuvees_mois = qc.filter(
        Conge.statut == "APPROUVE",
        Conge.date_decision >= debut_mois,
    ).count()
    conges_rejetees_mois = qc.filter(
        Conge.statut == "REJETE",
        Conge.date_decision >= debut_mois,
    ).count()

    # --- Télétravail ---
    _, qt = _filtrer_scope(Conge.query, Teletravail.query)
    teletravail_soumises = qt.filter(Teletravail.statut == "SOUMISE").count()
    teletravail_approuvees_mois = qt.filter(
        Teletravail.statut == "APPROUVE",
        Teletravail.date_decision >= debut_mois,
    ).count()
    teletravail_rejetees_mois = qt.filter(
        Teletravail.statut == "REJETE",
        Teletravail.date_decision >= debut_mois,
    ).count()

    total_en_attente = conges_soumises + teletravail_soumises
    total_approuvees = conges_approuvees_mois + teletravail_approuvees_mois
    total_rejetees = conges_rejetees_mois + teletravail_rejetees_mois

    return jsonify({
        "en_attente": total_en_attente,
        "approuvees_ce_mois": total_approuvees,
        "rejetees_ce_mois": total_rejetees,
        "details": {
            "conge": {
                "en_attente": conges_soumises,
                "approuvees_ce_mois": conges_approuvees_mois,
                "rejetees_ce_mois": conges_rejetees_mois,
            },
            "teletravail": {
                "en_attente": teletravail_soumises,
                "approuvees_ce_mois": teletravail_approuvees_mois,
                "rejetees_ce_mois": teletravail_rejetees_mois,
            },
        },
    }), 200


@bp.route("", methods=["POST"])
@role_requis("declarer_conge", "declarer_teletravail")
def creer_demande():
    """Crée une demande (congé ou télétravail) selon le champ type_demande."""
    principal = principal_courant()
    payload = request.get_json(silent=True) or {}

    type_demande = payload.get("type_demande")
    if type_demande not in ("conge", "teletravail"):
        return jsonify(erreur="type_demande doit valoir 'conge' ou 'teletravail'."), 400

    try:
        date_debut = datetime.strptime(payload["date_debut"], "%Y-%m-%d").date()
        date_fin = datetime.strptime(payload["date_fin"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return jsonify(erreur="date_debut et date_fin (YYYY-MM-DD) sont requis."), 400

    if date_fin < date_debut:
        return jsonify(erreur="date_fin doit être postérieure ou égale à date_debut."), 400

    motif = payload.get("motif", "")
    details = []

    if type_demande == "conge":
        type_conge = payload.get("type_conge")
        justificatif = payload.get("justificatif")
        if type_conge:
            details.append(f"Type de congé: {type_conge}")
        if justificatif:
            details.append(f"Justificatif: {justificatif}")
        if motif:
            details.append(motif)
        motif_final = " | ".join(details) if details else motif
        demande = Conge(
            utilisateur_id=principal.id,
            date_debut=date_debut,
            date_fin=date_fin,
            motif=motif_final,
            statut="SOUMISE",
        )
        db.session.add(demande)
        db.session.commit()
        return jsonify(
            type_demande="conge",
            statut="SOUMISE",
            message="Demande de congé envoyée.",
            demande=_serialiser_conge(demande),
        ), 201

    # télétravail
    recurrence = payload.get("recurrence")
    lieu_teletravail = payload.get("lieu_teletravail")
    if recurrence:
        details.append(f"Récurrence: {recurrence}")
    if lieu_teletravail:
        details.append(f"Lieu: {lieu_teletravail}")
    if motif:
        details.append(motif)
    motif_final = " | ".join(details) if details else motif
    demande = Teletravail(
        utilisateur_id=principal.id,
        date_debut=date_debut,
        date_fin=date_fin,
        motif=motif_final,
        statut="SOUMISE",
    )
    db.session.add(demande)
    db.session.commit()
    return jsonify(
        type_demande="teletravail",
        statut="SOUMISE",
        message="Demande de télétravail envoyée.",
        demande=_serialiser_teletravail(demande),
    ), 201


@bp.route("/<int:demande_id>/decider", methods=["PATCH"])
@role_requis("valider_conge", "valider_teletravail")
def decider(demande_id):
    """Valide ou refuse une demande (détection auto : Conge ou Teletravail)."""
    payload = request.get_json(silent=True) or {}
    decision = payload.get("statut")
    if decision not in ("APPROUVE", "REJETE"):
        return jsonify(erreur="statut doit valoir 'APPROUVE' ou 'REJETE'."), 400

    # Chercher d'abord dans Conge
    demande = db.session.get(Conge, demande_id)
    type_demande = "conge"

    if demande is None:
        demande = db.session.get(Teletravail, demande_id)
        type_demande = "teletravail"

    if demande is None:
        return jsonify(erreur="Demande introuvable."), 404

    if demande.statut != "SOUMISE":
        return jsonify(erreur="Cette demande a déjà été traitée."), 409

    principal = principal_courant()
    demande.statut = decision
    demande.validateur_id = principal.id if isinstance(principal, Utilisateur) else None
    demande.date_decision = datetime.utcnow()
    demande.commentaire = payload.get("commentaire")
    db.session.commit()

    jours_decomptes = 0
    if type_demande == "conge" and decision == "APPROUVE":
        jours_decomptes = jours_conge_decomptables(demande)

    message = "Demande approuvée." if decision == "APPROUVE" else "Demande rejetée."

    serialisee = (
        _serialiser_conge(demande) if type_demande == "conge"
        else _serialiser_teletravail(demande)
    )

    return jsonify(
        type_demande=type_demande,
        statut=decision,
        message=message,
        jours_decomptes=jours_decomptes,
        demande=serialisee,
    ), 200
