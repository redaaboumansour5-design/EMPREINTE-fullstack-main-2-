"""routes/dashboard_mois.py
---------------------------
Statistiques mensuelles pour le tableau de bord (source : presence_service).

Endpoint: GET /api/dashboard/mois
"""
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify

from models import Pointage
from routes._auth_utils import role_requis, principal_courant
from routes.dashboard import _utilisateurs_perimetre
from services.presence_service import (
    agregats_periode,
    aujourd_hui_casablanca,
    bornes_jour_casablanca,
    calculer_taux_ponctualite,
    est_jour_ouvre,
    jour_casablanca_depuis_utc,
)

bp = Blueprint("dashboard_mois", __name__, url_prefix="/api/dashboard")


def _bornes_mois(aujourd_hui: date):
    debut = aujourd_hui.replace(day=1)
    if debut.month == 12:
        fin = debut.replace(year=debut.year + 1, month=1, day=1)
    else:
        fin = debut.replace(month=debut.month + 1, day=1)
    return debut, fin


@bp.route("/mois", methods=["GET"])
@role_requis("consulter_dashboard")
def mois():
    principal = principal_courant()
    role = getattr(principal, "role", "administrateur")
    aujourd_hui = aujourd_hui_casablanca()
    debut_mois, fin_mois = _bornes_mois(aujourd_hui)
    fin_periode = min(aujourd_hui, fin_mois - timedelta(days=1))

    utilisateurs = _utilisateurs_perimetre(principal)
    ag = agregats_periode(utilisateurs, debut_mois, fin_periode)

    # Jours présentiel / télétravail = nombre d'entrées sur jours ouvrés
    ids = [u.id for u in utilisateurs]
    debut_dt, _ = bornes_jour_casablanca(debut_mois)
    _, fin_dt = bornes_jour_casablanca(fin_periode + timedelta(days=1))

    pointages = (
        Pointage.query.filter(
            Pointage.utilisateur_id.in_(ids),
            Pointage.date_heure >= debut_dt,
            Pointage.date_heure < fin_dt,
            Pointage.type == "ENTREE",
            Pointage.statut.in_(("VALIDE", "EN_ATTENTE")),
        ).all()
        if ids
        else []
    )

    jours_presentiel = set()
    jours_teletravail = set()
    for pointage in pointages:
        jour = jour_casablanca_depuis_utc(pointage.date_heure)
        if not est_jour_ouvre(jour):
            continue
        if pointage.mode:
            jours_teletravail.add(jour)
        else:
            jours_presentiel.add(jour)

    # Ponctualité sur 30 jours (présentiel uniquement)
    debut_30 = aujourd_hui - timedelta(days=30)
    _, fin_30_dt = bornes_jour_casablanca(aujourd_hui + timedelta(days=1))
    debut_30_dt, _ = bornes_jour_casablanca(debut_30)

    pointages_30 = (
        Pointage.query.filter(
            Pointage.utilisateur_id.in_(ids),
            Pointage.date_heure >= debut_30_dt,
            Pointage.date_heure < fin_30_dt,
            Pointage.type == "ENTREE",
            Pointage.statut.in_(("VALIDE", "EN_ATTENTE")),
            Pointage.mode == False,  # noqa: E712
        ).all()
        if ids
        else []
    )

    taux_ponctualite = calculer_taux_ponctualite(pointages_30)

    effectif_total = len(utilisateurs) if role != "employe" else 1

    resume_mois = {
        "jours_presentiel": len(jours_presentiel),
        "jours_teletravail": len(jours_teletravail),
        "retards": ag.retards,
        "absences": ag.absents,
        "conges": ag.conges,
        "feries": ag.feries,
        "en_attente_validation": ag.en_attente_validation,
    }

    return jsonify(
        effectif_total=effectif_total,
        presents=ag.presents,
        taux_presence=ag.taux_presence,
        jours_presentiel=len(jours_presentiel),
        jours_teletravail=len(jours_teletravail),
        retards=ag.retards,
        absences=ag.absents,
        conges=ag.conges,
        feries=ag.feries,
        en_attente_validation=ag.en_attente_validation,
        jours_ouvres=ag.jours_ouvres,
        resume_mois=resume_mois,
        taux_ponctualite_30j=taux_ponctualite,
        periode_debut=debut_mois.isoformat(),
        periode_fin=fin_periode.isoformat(),
    ), 200
