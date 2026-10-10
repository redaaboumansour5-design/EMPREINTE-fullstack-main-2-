"""
routes/rapports.py
----------------------
UC-10 — Exporter/Importer Excel
UC-11 — Générer rapports  («Contrainte» : uniquement si role == 'rh', comme
         indiqué sur l'association Utilisateur -> Rapport du diagramme de classes)

Les exports sont fournis au format CSV (ouvrable nativement dans Excel).
Pour un vrai .xlsx, ajoutez `openpyxl` et remplacez `_vers_csv` par un writer
openpyxl — la structure des routes reste identique.
"""
import csv
import io
from datetime import date, timedelta, timezone
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import get_jwt

from extensions import db
from models import Conge, Pointage, Utilisateur, Teletravail, Rapport
from routes._auth_utils import principal_courant, role_requis
from services.presence_service import (
    agregats_jour,
    est_jour_ouvre,
    jours_ouvres_recents,
    aujourd_hui_casablanca,
    bornes_jour_casablanca,
    est_en_retard,
    jour_casablanca_depuis_utc,
)

TZ_CASABLANCA = ZoneInfo("Africa/Casablanca")

TZ_CASABLANCA = ZoneInfo("Africa/Casablanca")

bp = Blueprint("rapports", __name__, url_prefix="/api/rapports")


def _reserve_rh(fn):
    """Applique la contrainte du diagramme : «Contrainte» Uniquement si role == 'rh'."""
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get("role") not in ("rh", "administrateur"):
            return jsonify(erreur="Cette action est réservée au rôle RH."), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


def _vers_csv(entetes: list[str], lignes: list[list]) -> Response:
    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM UTF-8 pour un affichage correct des accents dans Excel
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(entetes)
    writer.writerows(lignes)
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )


def _enregistrer_rapport(type_rapport: str, date_debut, date_fin):
    principal = principal_courant()
    rapport = Rapport(
        type=type_rapport, date_debut=date_debut, date_fin=date_fin,
        format="CSV", genere_par_id=principal.id,
    )
    db.session.add(rapport)
    db.session.commit()
    return rapport


@bp.route("/pointages.csv", methods=["GET"])
@role_requis("generer_rapports", "exporter")
@_reserve_rh
def export_pointages():
    pointages = Pointage.query.order_by(Pointage.date_heure.desc()).limit(2000).all()
    lignes = [[
        p.date_heure.replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ_CASABLANCA).strftime("%Y-%m-%d %H:%M"),
        f"{p.utilisateur.prenom} {p.utilisateur.nom}" if p.utilisateur else "",
        p.utilisateur.matricule if p.utilisateur else "",
        p.utilisateur.departement.nom if p.utilisateur and p.utilisateur.departement else "",
        "Télétravail" if p.mode else "Présentiel",
        p.score_confiance if p.score_confiance is not None else "",
        p.statut,
    ] for p in pointages]
    _enregistrer_rapport("pointages", date.today(), date.today())
    return _vers_csv(["Heure", "Employé", "Matricule", "Département", "Méthode", "Score", "Statut"], lignes)


@bp.route("/employes.csv", methods=["GET"])
@role_requis("generer_rapports", "exporter")
@_reserve_rh
def export_employes():
    utilisateurs = Utilisateur.query.order_by(Utilisateur.nom).all()
    lignes = [[
        u.matricule, u.prenom, u.nom, u.email,
        u.departement.nom if u.departement else "", u.poste, u.role,
    ] for u in utilisateurs]
    _enregistrer_rapport("employes", None, None)
    return _vers_csv(["Matricule", "Prénom", "Nom", "Email", "Département", "Poste", "Rôle"], lignes)


@bp.route("/teletravail.csv", methods=["GET"])
@role_requis("generer_rapports", "exporter")
@_reserve_rh
def export_teletravail():
    demandes = Teletravail.query.order_by(Teletravail.date_debut.desc()).all()
    lignes = [[
        f"{d.employe.prenom} {d.employe.nom}", d.employe.matricule,
        d.employe.departement.nom if d.employe.departement else "",
        d.date_debut.isoformat(), d.date_fin.isoformat(), d.motif, d.statut,
    ] for d in demandes]
    _enregistrer_rapport("teletravail", None, None)
    return _vers_csv(
        ["Employé", "Matricule", "Département", "Début", "Fin", "Motif", "Statut"], lignes
    )


@bp.route("/demandes.csv", methods=["GET"])
@role_requis("generer_rapports", "exporter")
@_reserve_rh
def export_demandes():
    """Export CSV unifié des demandes (congé + télétravail) avec colonne 'Type de demande'."""
    conges = Conge.query.order_by(Conge.date_debut.desc()).all()
    teletravails = Teletravail.query.order_by(Teletravail.date_debut.desc()).all()

    lignes = []
    for c in conges:
        lignes.append([
            "Congé",
            f"{c.employe.prenom} {c.employe.nom}",
            c.employe.matricule,
            c.employe.departement.nom if c.employe.departement else "",
            c.date_debut.isoformat(),
            c.date_fin.isoformat(),
            c.motif or "",
            c.statut,
        ])
    for t in teletravails:
        lignes.append([
            "Télétravail",
            f"{t.employe.prenom} {t.employe.nom}",
            t.employe.matricule,
            t.employe.departement.nom if t.employe.departement else "",
            t.date_debut.isoformat(),
            t.date_fin.isoformat(),
            t.motif or "",
            t.statut,
        ])

    # Trier par date_debut décroissante
    lignes.sort(key=lambda r: r[4], reverse=True)

    _enregistrer_rapport("demandes", None, None)
    return _vers_csv(
        ["Type de demande", "Employé", "Matricule", "Département", "Début", "Fin", "Motif", "Statut"],
        lignes,
    )


@bp.route("/absences.csv", methods=["GET"])
@role_requis("generer_rapports", "exporter")
@_reserve_rh
def export_absences():
    """Export CSV des absences par jour sur les 30 derniers jours ouvrés."""
    utilisateurs = Utilisateur.query.order_by(Utilisateur.nom, Utilisateur.prenom).all()
    jours = [
        jour
        for jour in jours_ouvres_recents(30, aujourd_hui_casablanca())
        if est_jour_ouvre(jour)
    ]

    lignes = []
    for jour in jours:
        agregats = agregats_jour(utilisateurs, jour)
        lignes.append([
            jour.isoformat(),
            agregats.effectif,
            agregats.presents,
            agregats.absents,
            agregats.conges,
            agregats.feries,
        ])

    _enregistrer_rapport("absences", jours[0] if jours else None, jours[-1] if jours else None)
    return _vers_csv(
        ["Date", "Effectif", "Présents", "Absences", "Congés", "Jours fériés"],
        lignes,
    )


@bp.route("/absences-detail.csv", methods=["GET"])
@role_requis("generer_rapports", "exporter")
@_reserve_rh
def export_absences_detail():
    """Export CSV des employés absents sur les 30 derniers jours ouvrés."""
    utilisateurs = Utilisateur.query.order_by(Utilisateur.nom, Utilisateur.prenom).all()
    lignes = []
    jours = [jour for jour in jours_ouvres_recents(30, aujourd_hui_casablanca()) if est_jour_ouvre(jour)]
    for jour in jours:
        agregats = agregats_jour(utilisateurs, jour)
        absents = {detail["utilisateur_id"] for detail in agregats.details if detail["statut"] == "absent"}
        lignes.extend([
            [utilisateur.nom, utilisateur.prenom, jour.isoformat()]
            for utilisateur in utilisateurs
            if utilisateur.id in absents
        ])
    _enregistrer_rapport("absences-detail", jours[0] if jours else None, jours[-1] if jours else None)
    return _vers_csv(["Nom", "Prénom", "Date d'absence"], lignes)


@bp.route("/retards-detail.csv", methods=["GET"])
@role_requis("generer_rapports", "exporter")
@_reserve_rh
def export_retards_detail():
    """Export CSV des entrées valides pointées strictement après 08:30."""
    aujourd_hui = aujourd_hui_casablanca()
    debut = aujourd_hui.replace(day=1)
    debut_dt, _ = bornes_jour_casablanca(debut)
    _, fin_dt = bornes_jour_casablanca(aujourd_hui + timedelta(days=1))
    pointages = Pointage.query.filter(
        Pointage.date_heure >= debut_dt,
        Pointage.date_heure < fin_dt,
        Pointage.type == "ENTREE",
        Pointage.statut.in_(("VALIDE", "EN_ATTENTE")),
    ).order_by(Pointage.date_heure.desc()).all()
    lignes = []
    for pointage in pointages:
        if est_en_retard(pointage.date_heure) and pointage.utilisateur:
            heure_locale = pointage.date_heure.replace(tzinfo=timezone.utc).astimezone(TZ_CASABLANCA)
            lignes.append([
                pointage.utilisateur.nom,
                pointage.utilisateur.prenom,
                jour_casablanca_depuis_utc(pointage.date_heure).isoformat(),
                heure_locale.strftime("%H:%M:%S"),
            ])
    _enregistrer_rapport("retards-detail", debut, aujourd_hui)
    return _vers_csv(["Nom", "Prénom", "Date", "Heure de pointage"], lignes)


@bp.route("/historique", methods=["GET"])
@role_requis("generer_rapports")
@_reserve_rh
def historique_rapports():
    rapports = Rapport.query.order_by(Rapport.date_generation.desc()).limit(50).all()
    return jsonify([r.to_dict() for r in rapports]), 200
