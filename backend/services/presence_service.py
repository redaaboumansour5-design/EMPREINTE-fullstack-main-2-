"""
services/presence_service.py
----------------------------
Source unique de vérité pour le statut de présence employé/jour.

Priorité (du plus fort au plus faible) :
  1. Jour férié marocain        → « férié »
  2. Congé approuvé             → « congé »
  3. Pointage ENTREE VALIDE/EN_ATTENTE → « présent »
  4. Sinon (jour ouvré)         → « absent »

Fuseau horaire : Africa/Casablanca pour les bornes de journée.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable
from zoneinfo import ZoneInfo

from flask import has_app_context

from extensions import db
from models import Conge, Pointage, Teletravail, Utilisateur
from services.feries_service import est_jour_ferie

TZ_CASABLANCA = ZoneInfo("Africa/Casablanca")
HEURE_LIMITE_RETARD = 8 * 60 + 30  # 08:30

STATUT_FERIE = "ferie"
STATUT_CONGE = "conge"
STATUT_PRESENT = "present"
STATUT_ABSENT = "absent"

STATUTS_PRESENCE = (STATUT_FERIE, STATUT_CONGE, STATUT_PRESENT, STATUT_ABSENT)
STATUTS_POINTAGE_PRESENT = ("VALIDE", "EN_ATTENTE")


def aujourd_hui_casablanca() -> date:
    return datetime.now(TZ_CASABLANCA).date()


def est_jour_ouvre(jour: date) -> bool:
    """Jour ouvré = lundi–vendredi, hors jours fériés marocains (dénominateur taux présence)."""
    return jour.weekday() < 5 and not est_jour_ferie(jour)


def est_weekend(jour: date) -> bool:
    return jour.weekday() >= 5


def bornes_jour_casablanca(jour: date) -> tuple[datetime, datetime]:
    """Retourne (début, fin) de la journée Casablanca convertis en UTC naïf."""
    debut_local = datetime.combine(jour, time.min, tzinfo=TZ_CASABLANCA)
    fin_local = debut_local + timedelta(days=1)
    debut_utc = debut_local.astimezone(timezone.utc).replace(tzinfo=None)
    fin_utc = fin_local.astimezone(timezone.utc).replace(tzinfo=None)
    return debut_utc, fin_utc


def jour_casablanca_depuis_utc(dt: datetime) -> date:
    """Convertit un datetime UTC (naïf ou aware) en date locale Casablanca."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_CASABLANCA).date()


def est_en_retard(date_heure: datetime | str) -> bool:
    """Retourne True si l'heure locale de pointage est strictement après 08:30."""
    if isinstance(date_heure, str):
        date_heure = datetime.fromisoformat(date_heure.replace("Z", "+00:00"))
    if date_heure.tzinfo is None:
        date_heure = date_heure.replace(tzinfo=timezone.utc)
    heure_locale = date_heure.astimezone(TZ_CASABLANCA)
    secondes_arrivee = (
        heure_locale.hour * 3600
        + heure_locale.minute * 60
        + heure_locale.second
        + heure_locale.microsecond / 1_000_000
    )
    return secondes_arrivee > HEURE_LIMITE_RETARD * 60


def date_effective_employe(utilisateur: Utilisateur, jour: date) -> bool:
    """True si l'employé fait partie de l'effectif ce jour-là."""
    if utilisateur.date_embauche and jour < utilisateur.date_embauche:
        return False
    return True


def calculer_taux_ponctualite(
    pointages: Iterable[Pointage | object],
    *,
    heure_limite_minutes: int = HEURE_LIMITE_RETARD,
) -> float:
    """Calcule le taux de ponctualité pour une liste de pointages d'entrée."""
    pointages_liste = list(pointages)
    if not pointages_liste:
        return 0.0

    ponctuels = 0
    for pointage in pointages_liste:
        date_heure = getattr(pointage, "date_heure", None)
        if date_heure is None:
            continue
        if heure_limite_minutes == HEURE_LIMITE_RETARD:
            ponctuel = not est_en_retard(date_heure)
        else:
            if date_heure.tzinfo is None:
                date_heure = date_heure.replace(tzinfo=timezone.utc)
            heure_locale = date_heure.astimezone(TZ_CASABLANCA)
            minutes = heure_locale.hour * 60 + heure_locale.minute
            ponctuel = minutes <= heure_limite_minutes
        if ponctuel:
            ponctuels += 1

    return round(ponctuels / len(pointages_liste) * 100, 2)


def _conge_approuve_pour_jour(
    utilisateur_id: int,
    jour: date,
    conges_par_utilisateur: dict[int, list[Conge]] | None = None,
) -> bool:
    if conges_par_utilisateur is not None:
        for conge in conges_par_utilisateur.get(utilisateur_id, []):
            if conge.statut == "APPROUVE" and conge.date_debut <= jour <= conge.date_fin:
                return True
        return False

    if not has_app_context():
        return False

    return (
        Conge.query.filter(
            Conge.utilisateur_id == utilisateur_id,
            Conge.statut == "APPROUVE",
            Conge.date_debut <= jour,
            Conge.date_fin >= jour,
        ).first()
        is not None
    )


def _teletravail_approuve_pour_jour(
    utilisateur_id: int,
    jour: date,
    teletravails_par_utilisateur: dict[int, list[Teletravail]] | None = None,
) -> bool:
    if teletravails_par_utilisateur is not None:
        for teletravail in teletravails_par_utilisateur.get(utilisateur_id, []):
            if teletravail.statut == "APPROUVE" and teletravail.date_debut <= jour <= teletravail.date_fin:
                return True
        return False

    if not has_app_context():
        return False

    return (
        Teletravail.query.filter(
            Teletravail.utilisateur_id == utilisateur_id,
            Teletravail.statut == "APPROUVE",
            Teletravail.date_debut <= jour,
            Teletravail.date_fin >= jour,
        ).first()
        is not None
    )


def _pointage_entree_pour_jour(
    utilisateur_id: int,
    jour: date,
    pointages_par_utilisateur: dict[int, list[Pointage]] | None = None,
) -> Pointage | None:
    if pointages_par_utilisateur is not None:
        for pointage in pointages_par_utilisateur.get(utilisateur_id, []):
            if pointage.type == "ENTREE" and pointage.statut in STATUTS_POINTAGE_PRESENT:
                return pointage
        return None

    if not has_app_context():
        return None

    debut, fin = bornes_jour_casablanca(jour)
    return (
        Pointage.query.filter(
            Pointage.utilisateur_id == utilisateur_id,
            Pointage.date_heure >= debut,
            Pointage.date_heure < fin,
            Pointage.type == "ENTREE",
            Pointage.statut.in_(STATUTS_POINTAGE_PRESENT),
        )
        .order_by(Pointage.date_heure.asc())
        .first()
    )


def statut_jour(
    utilisateur_id: int,
    jour: date,
    *,
    utilisateur: Utilisateur | None = None,
    conges_par_utilisateur: dict[int, list[Conge]] | None = None,
    pointages_par_utilisateur: dict[int, list[Pointage]] | None = None,
    teletravails_par_utilisateur: dict[int, list[Teletravail]] | None = None,
) -> dict:
    """
    Détermine le statut de présence pour un employé et une date.

    Returns:
        dict avec clés ``statut`` et ``a_valider`` (True si pointage EN_ATTENTE).
    """
    if utilisateur is None:
        utilisateur = db.session.get(Utilisateur, utilisateur_id) if has_app_context() else None

    if utilisateur is None or not date_effective_employe(utilisateur, jour):
        return {"statut": None, "a_valider": False, "hors_effectif": True}

    if est_weekend(jour):
        return {"statut": None, "a_valider": False, "hors_effectif": True, "weekend": True}

    if est_jour_ferie(jour):
        return {"statut": STATUT_FERIE, "a_valider": False, "hors_effectif": False}

    if _conge_approuve_pour_jour(utilisateur_id, jour, conges_par_utilisateur):
        return {"statut": STATUT_CONGE, "a_valider": False, "hors_effectif": False}

    if _teletravail_approuve_pour_jour(utilisateur_id, jour, teletravails_par_utilisateur):
        return {
            "statut": STATUT_PRESENT,
            "a_valider": False,
            "hors_effectif": False,
            "teletravail": True,
        }

    pointage = _pointage_entree_pour_jour(
        utilisateur_id, jour, pointages_par_utilisateur
    )
    if pointage is not None:
        return {
            "statut": STATUT_PRESENT,
            "a_valider": pointage.statut == "EN_ATTENTE",
            "hors_effectif": False,
            "pointage": pointage,
        }

    return {"statut": STATUT_ABSENT, "a_valider": False, "hors_effectif": False}


def _charger_conges(
    utilisateur_ids: Iterable[int],
    date_debut: date,
    date_fin: date,
) -> dict[int, list[Conge]]:
    ids = list(utilisateur_ids)
    if not ids or not has_app_context():
        return {}

    conges = (
        Conge.query.filter(
            Conge.utilisateur_id.in_(ids),
            Conge.statut == "APPROUVE",
            Conge.date_debut <= date_fin,
            Conge.date_fin >= date_debut,
        )
        .all()
    )
    resultat: dict[int, list[Conge]] = {uid: [] for uid in ids}
    for conge in conges:
        resultat[conge.utilisateur_id].append(conge)
    return resultat


def _charger_teletravails(
    utilisateur_ids: Iterable[int],
    date_debut: date,
    date_fin: date,
) -> dict[int, list[Teletravail]]:
    ids = list(utilisateur_ids)
    if not ids or not has_app_context():
        return {}

    teletravails = (
        Teletravail.query.filter(
            Teletravail.utilisateur_id.in_(ids),
            Teletravail.statut == "APPROUVE",
            Teletravail.date_debut <= date_fin,
            Teletravail.date_fin >= date_debut,
        ).all()
    )
    resultat: dict[int, list[Teletravail]] = {uid: [] for uid in ids}
    for teletravail in teletravails:
        resultat[teletravail.utilisateur_id].append(teletravail)
    return resultat


def _charger_pointages(
    utilisateur_ids: Iterable[int],
    date_debut: date,
    date_fin: date,
) -> dict[int, dict[date, Pointage]]:
    ids = list(utilisateur_ids)
    if not ids or not has_app_context():
        return {}

    debut_dt, _ = bornes_jour_casablanca(date_debut)
    _, fin_dt = bornes_jour_casablanca(date_fin + timedelta(days=1))

    pointages = (
        Pointage.query.filter(
            Pointage.utilisateur_id.in_(ids),
            Pointage.date_heure >= debut_dt,
            Pointage.date_heure < fin_dt,
            Pointage.type == "ENTREE",
            Pointage.statut.in_(STATUTS_POINTAGE_PRESENT),
        )
        .order_by(Pointage.date_heure.asc())
        .all()
    )

    par_utilisateur_date: dict[int, dict[date, Pointage]] = {uid: {} for uid in ids}
    for pointage in pointages:
        jour_local = jour_casablanca_depuis_utc(pointage.date_heure)
        par_utilisateur_date[pointage.utilisateur_id][jour_local] = pointage
    return par_utilisateur_date


def _pointages_par_jour(
    pointages_index: dict[int, dict[date, Pointage]],
    utilisateur_id: int,
    jour: date,
) -> dict[int, list[Pointage]] | None:
    pointage = pointages_index.get(utilisateur_id, {}).get(jour)
    if pointage is None:
        return None
    return {utilisateur_id: [pointage]}


@dataclass
class AgregatsJour:
    effectif: int = 0
    presents: int = 0
    absents: int = 0
    conges: int = 0
    feries: int = 0
    presentiel: int = 0
    teletravail: int = 0
    retards: int = 0
    en_attente_validation: int = 0
    jours_ouvre: bool = True
    details: list[dict] = field(default_factory=list)


def agregats_jour(
    utilisateurs: list[Utilisateur],
    jour: date,
    *,
    conges_cache: dict[int, list[Conge]] | None = None,
    pointages_cache: dict[int, dict[date, Pointage]] | None = None,
    teletravails_cache: dict[int, list[Teletravail]] | None = None,
) -> AgregatsJour:
    """Agrège les statuts pour une liste d'employés et une date."""
    actifs = [u for u in utilisateurs if date_effective_employe(u, jour)]
    resultat = AgregatsJour(effectif=len(actifs), jours_ouvre=est_jour_ouvre(jour))

    if est_weekend(jour):
        resultat.jours_ouvre = False
        return resultat

    if est_jour_ferie(jour):
        resultat.jours_ouvre = False
        resultat.feries = len(actifs)
        for utilisateur in actifs:
            resultat.details.append(
                {"utilisateur_id": utilisateur.id, "statut": STATUT_FERIE, "a_valider": False}
            )
        return resultat

    if conges_cache is None:
        conges_cache = _charger_conges([u.id for u in actifs], jour, jour)
    if pointages_cache is None:
        pointages_cache = _charger_pointages([u.id for u in actifs], jour, jour)
    if teletravails_cache is None:
        teletravails_cache = _charger_teletravails([u.id for u in actifs], jour, jour)

    for utilisateur in actifs:
        info = statut_jour(
            utilisateur.id,
            jour,
            utilisateur=utilisateur,
            conges_par_utilisateur=conges_cache,
            pointages_par_utilisateur=_pointages_par_jour(
                pointages_cache, utilisateur.id, jour
            ),
            teletravails_par_utilisateur=teletravails_cache,
        )
        statut = info["statut"]
        resultat.details.append(
            {
                "utilisateur_id": utilisateur.id,
                "statut": statut,
                "a_valider": info.get("a_valider", False),
            }
        )

        if statut == STATUT_FERIE:
            resultat.feries += 1
        elif statut == STATUT_CONGE:
            resultat.conges += 1
        elif statut == STATUT_PRESENT:
            resultat.presents += 1
            if info.get("a_valider"):
                resultat.en_attente_validation += 1
            if info.get("teletravail"):
                resultat.teletravail += 1
            else:
                pointage = info.get("pointage") or pointages_cache.get(utilisateur.id, {}).get(jour)
                if pointage:
                    if pointage.mode:
                        resultat.teletravail += 1
                    else:
                        resultat.presentiel += 1
                        if est_en_retard(pointage.date_heure):
                            resultat.retards += 1
        elif statut == STATUT_ABSENT:
            resultat.absents += 1

    return resultat


@dataclass
class AgregatsPeriode:
    jours_ouvres: int = 0
    presents: int = 0
    absents: int = 0
    conges: int = 0
    feries: int = 0
    presentiel: int = 0
    teletravail: int = 0
    retards: int = 0
    en_attente_validation: int = 0
    taux_presence: float = 0.0


def _iterer_jours(date_debut: date, date_fin: date) -> list[date]:
    jours = []
    curseur = date_debut
    while curseur <= date_fin:
        jours.append(curseur)
        curseur += timedelta(days=1)
    return jours


def agregats_periode(
    utilisateurs: list[Utilisateur],
    date_debut: date,
    date_fin: date,
) -> AgregatsPeriode:
    """Agrège les statuts sur une période (jours ouvrés uniquement pour le taux)."""
    ids = [u.id for u in utilisateurs]
    conges_cache = _charger_conges(ids, date_debut, date_fin)
    pointages_cache = _charger_pointages(ids, date_debut, date_fin)
    teletravails_cache = _charger_teletravails(ids, date_debut, date_fin)

    resultat = AgregatsPeriode()
    slots_ouvres = 0

    for jour in _iterer_jours(date_debut, date_fin):
        actifs = [u for u in utilisateurs if date_effective_employe(u, jour)]

        if est_weekend(jour):
            continue

        if est_jour_ferie(jour):
            resultat.feries += len(actifs)
            continue

        slots_ouvres += len(actifs)

        ag = agregats_jour(
            actifs,
            jour,
            conges_cache=conges_cache,
            pointages_cache=pointages_cache,
            teletravails_cache=teletravails_cache,
        )
        resultat.presents += ag.presents
        resultat.absents += ag.absents
        resultat.conges += ag.conges
        resultat.feries += ag.feries
        resultat.presentiel += ag.presentiel
        resultat.teletravail += ag.teletravail
        resultat.retards += ag.retards
        resultat.en_attente_validation += ag.en_attente_validation

    resultat.jours_ouvres = slots_ouvres
    denominateur = slots_ouvres - resultat.feries - resultat.conges
    if denominateur > 0:
        resultat.taux_presence = round(resultat.presents / denominateur * 100, 1)
    elif slots_ouvres > 0:
        resultat.taux_presence = 100.0 if resultat.absents == 0 else 0.0

    return resultat


def jours_ouvres_recents(nb_jours: int, reference: date | None = None) -> list[date]:
    """Retourne les N derniers jours ouvrés (lun–ven, fériés inclus comme jours calendaires)."""
    reference = reference or aujourd_hui_casablanca()
    jours: list[date] = []
    curseur = reference
    while len(jours) < nb_jours:
        if curseur.weekday() < 5:
            jours.append(curseur)
        curseur -= timedelta(days=1)
    jours.reverse()
    return jours


def taux_presence_departement(
    membres: list[Utilisateur],
    jour: date,
) -> float:
    """Taux de présence d'un département pour un jour ouvré."""
    if not est_jour_ouvre(jour):
        return 0.0
    ag = agregats_jour(membres, jour)
    denominateur = ag.effectif - ag.feries - ag.conges
    if denominateur <= 0:
        return 100.0 if ag.absents == 0 else 0.0
    return round(ag.presents / denominateur * 100, 1)


def jours_conge_decomptables(conge: Conge) -> int:
    """
    Jours de congé décomptés du solde : exclut les jours fériés marocains.
    """
    if conge.statut != "APPROUVE":
        return 0
    compte = 0
    curseur = conge.date_debut
    while curseur <= conge.date_fin:
        if curseur.weekday() < 5 and not est_jour_ferie(curseur):
            compte += 1
        curseur += timedelta(days=1)
    return compte
