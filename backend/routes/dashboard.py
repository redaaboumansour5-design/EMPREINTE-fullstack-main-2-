"""
routes/dashboard.py
-----------------------
UC-09 — Dashboard & statistiques (Espace Manager/RH/Administration).
Toutes les valeurs proviennent de ``presence_service`` (source unique de vérité).
"""
from flask import Blueprint, jsonify, request

from models import Utilisateur, Departement
from routes._auth_utils import role_requis, principal_courant
from services.presence_service import (
    agregats_jour,
    agregats_periode,
    aujourd_hui_casablanca,
    jours_ouvres_recents,
    taux_presence_departement,
)

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _utilisateurs_perimetre(principal) -> list[Utilisateur]:
    role = getattr(principal, "role", "administrateur")
    if role == "employe":
        return [principal]
    if role == "manager" and principal.departement_id:
        return list(principal.departement.utilisateurs)
    return Utilisateur.query.all()


@bp.route("/vue-ensemble", methods=["GET"])
@role_requis("consulter_dashboard")
def vue_ensemble():
    principal = principal_courant()
    aujourd_hui = aujourd_hui_casablanca()
    utilisateurs = _utilisateurs_perimetre(principal)
    ag = agregats_jour(utilisateurs, aujourd_hui)

    denominateur = ag.effectif - ag.feries - ag.conges
    if denominateur > 0:
        taux = round(ag.presents / denominateur * 100, 1)
    elif ag.jours_ouvre:
        taux = 100.0 if ag.absents == 0 else 0.0
    else:
        taux = 0.0

    return jsonify(
        effectif_total=ag.effectif,
        presents=ag.presents,
        presentiel=ag.presentiel,
        teletravail=ag.teletravail,
        retards=ag.retards,
        absences=ag.absents,
        conges=ag.conges,
        feries=ag.feries,
        en_attente_validation=ag.en_attente_validation,
        jours_ouvre=ag.jours_ouvre,
        taux_presence=taux,
        date=aujourd_hui.isoformat(),
    ), 200


@bp.route("/tendance", methods=["GET"])
@role_requis("consulter_dashboard")
def tendance():
    """Série des N derniers jours ouvrés : présentiel / télétravail / congé / absence."""
    nb_jours = min(request.args.get("jours", default=10, type=int), 60)
    utilisateurs = _utilisateurs_perimetre(principal_courant())
    jours = jours_ouvres_recents(nb_jours)

    serie = []
    for jour in jours:
        ag = agregats_jour(utilisateurs, jour)
        serie.append({
            "date": jour.isoformat(),
            "presentiel": ag.presentiel,
            "teletravail": ag.teletravail,
            "conge": ag.conges,
            "ferie": ag.feries,
            "absence": ag.absents,
            "en_attente_validation": ag.en_attente_validation,
        })
    return jsonify(serie), 200


@bp.route("/par-departement", methods=["GET"])
@role_requis("consulter_dashboard")
def par_departement():
    aujourd_hui = aujourd_hui_casablanca()
    principal = principal_courant()
    role = getattr(principal, "role", "administrateur")

    if role == "manager":
        if not principal.departement:
            return jsonify([]), 200
        dept = principal.departement
        return jsonify([{
            "departement": dept.nom,
            "taux_presence": taux_presence_departement(list(dept.utilisateurs), aujourd_hui),
            "effectif": len(dept.utilisateurs),
        }]), 200

    if role == "employe":
        membres = principal.departement.utilisateurs if principal.departement else []
        effectif = len(membres) if membres else 1
        taux = taux_presence_departement(list(membres), aujourd_hui) if membres else 0
        return jsonify([{
            "departement": principal.departement.nom if principal.departement else "—",
            "taux_presence": taux,
            "effectif": effectif,
        }]), 200

    resultats = []
    for departement in Departement.query.all():
        membres = list(departement.utilisateurs)
        if not membres:
            continue
        resultats.append({
            "departement": departement.nom,
            "taux_presence": taux_presence_departement(membres, aujourd_hui),
            "effectif": len(membres),
        })
    resultats.sort(key=lambda r: r["taux_presence"], reverse=True)
    return jsonify(resultats), 200


@bp.route("/reconnaissance", methods=["GET"])
@role_requis("consulter_dashboard")
def reconnaissance():
    """Statistiques du moteur de reconnaissance faciale pour la journée en cours."""
    from datetime import datetime, timedelta
    from models import Pointage

    principal = principal_courant()
    role = getattr(principal, "role", "administrateur")
    aujourd_hui = aujourd_hui_casablanca()
    debut = datetime.combine(aujourd_hui, datetime.min.time())
    fin = debut + timedelta(days=1)

    if role == "employe":
        utilisateur_ids = [principal.id]
    elif role == "manager" and principal.departement_id:
        utilisateur_ids = [u.id for u in principal.departement.utilisateurs]
    else:
        utilisateur_ids = None

    query = Pointage.query.filter(Pointage.date_heure >= debut, Pointage.date_heure < fin)
    if utilisateur_ids is not None:
        query = query.filter(Pointage.utilisateur_id.in_(utilisateur_ids))

    pointages_jour = query.all()
    total = len(pointages_jour)
    valide = sum(1 for p in pointages_jour if p.statut == "VALIDE")
    en_attente = sum(1 for p in pointages_jour if p.statut == "EN_ATTENTE")
    rejete = sum(1 for p in pointages_jour if p.statut == "REJETE")

    bornes_bins = [round(0.2 + i * 0.1, 2) for i in range(9)]
    histogramme = []
    for i in range(len(bornes_bins) - 1):
        bas, haut = bornes_bins[i], bornes_bins[i + 1]
        compte = sum(
            1 for p in pointages_jour
            if p.score_confiance is not None and bas <= p.score_confiance < haut
        )
        histogramme.append({"min": bas, "max": haut, "count": compte})

    return jsonify(
        scans_aujourd_hui=total,
        valide=valide,
        en_attente=en_attente,
        rejete=rejete,
        taux_reussite=round((valide + en_attente) / total * 100, 1) if total else None,
        histogramme=histogramme,
        temps_moyen_ms=None,
    ), 200
