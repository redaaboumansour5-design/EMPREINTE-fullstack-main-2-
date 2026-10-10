"""
routes/pointage.py
----------------------
UC-02 — Pointer par caméra (+ seuils de configuration dynamiques)
UC-03 — Consulter son pointage / UC-08 — Consulter pointages (Manager/RH)

Reproduit fidèlement le diagramme de séquence "Pointage avec Seuils
Configuration Dynamiques" :
  1. Détermination du mode (Présentiel vs Télétravail) via une demande de
     télétravail APPROUVÉE et active à la date du jour.
  2. Analyse biométrique : capturerVisage + comparerVisage (DeepFace/FaceNet).
  3. Décision selon les seuils de la classe Configuration :
       score < seuilMin            -> REJETE
       seuilMin <= score < seuilMax -> EN_ATTENTE (validation RH requise)
       score >= seuilMax            -> VALIDE
"""
from datetime import datetime, date, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt

from extensions import db
from models import Utilisateur, Pointage, ReconnaissanceFaciale, Configuration, Teletravail
from routes._auth_utils import principal_courant, role_requis
from services import reconnaissance_service as rs
from services.reconnaissance_service import VisageNonDetecteError, ServiceReconnaissanceIndisponibleError
from services.presence_service import aujourd_hui_casablanca, bornes_jour_casablanca

bp = Blueprint("pointage", __name__, url_prefix="/api/pointage")


def _bornes_jour(jour: date):
    """Retourne les bornes UTC naïves d'une journée au Maroc."""
    return bornes_jour_casablanca(jour)


def _mode_est_teletravail(utilisateur_id: int, aujourd_hui: date) -> bool:
    """Détermination du mode de travail AUJOURD'HUI.

    Mode Télétravail =
      - teletravail_autorise == 1
        OU
      - il existe une demande Teletravail APPROUVÉE couvrant aujourd'hui.

    (Le mode est recalculé à chaque scan via la date d'aujourd'hui.)
    """
    utilisateur = db.session.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        return False

    if getattr(utilisateur, "teletravail_autorise", False):
        return True

    demande = (
        Teletravail.query.filter(
            Teletravail.utilisateur_id == utilisateur_id,
            Teletravail.statut == "APPROUVE",
            Teletravail.date_debut <= aujourd_hui,
            Teletravail.date_fin >= aujourd_hui,
        ).first()
    )
    return demande is not None




@bp.route("/scan", methods=["POST"])
@jwt_required()
def scan():
    """
    +pointerParCamera(image) : Pointage

    Body attendu : { "photo": "data:image/jpeg;base64,..." }
    Le type (ENTREE / SORTIE) est déterminé automatiquement :
      - Si aucun pointage ENTRÉE aujourd'hui → ENTRÉE
      - Si ENTRÉE existe déjà et ≥ 1h écoulée → SORTIE
      - Si ENTRÉE existe mais < 1h écoulée → erreur 400 avec compte à rebours
    """
    DUREE_MINIMUM_HEURES = 1

    principal = principal_courant()
    if not isinstance(principal, Utilisateur):
        return jsonify(erreur="Seul un compte employé/manager/RH peut pointer."), 403

    payload = request.get_json(silent=True) or {}
    photo = payload.get("photo")
    if not photo:
        return jsonify(erreur="Champ 'photo' manquant (capture caméra requise)."), 400

    # 1) Mode Présentiel vs Télétravail
    aujourd_hui = aujourd_hui_casablanca()
    mode_teletravail = _mode_est_teletravail(principal.id, aujourd_hui)

    # 2) Empreinte de référence enregistrée ?
    if principal.empreinte is None:
        return jsonify(
            erreur="Aucune empreinte faciale de référence enregistrée pour cet employé. "
                   "Contactez les RH pour l'enrôlement initial."
        ), 409

    # 3) Détermination du type (ENTRÉE / SORTIE) avec logique de tentatives
    MAX_TENTATIVES = 3
    debut_jour, fin_jour = _bornes_jour(aujourd_hui)

    # Tous les pointages du jour pour cet utilisateur
    pointages_aujourdhui = Pointage.query.filter(
        Pointage.utilisateur_id == principal.id,
        Pointage.date_heure >= debut_jour,
        Pointage.date_heure < fin_jour,
    ).order_by(Pointage.date_heure.desc()).all()

    total_tentatives = len(pointages_aujourdhui)
    dernier_pointage = pointages_aujourdhui[0] if pointages_aujourdhui else None
    maintenant = datetime.utcnow()

    # Vérifier la limite de tentatives
    if total_tentatives >= MAX_TENTATIVES:
        return jsonify(
            erreur=f"Vous avez atteint la limite de {MAX_TENTATIVES} tentatives aujourd'hui. Contactez les RH.",
            code="TENTATIVES_EPUISEES",
        ), 400

    # Chercher une entrée VALIDE ou EN_ATTENTE aujourd'hui
    entree_valide = Pointage.query.filter(
        Pointage.utilisateur_id == principal.id,
        Pointage.date_heure >= debut_jour,
        Pointage.date_heure < fin_jour,
        Pointage.type == "ENTREE",
        Pointage.statut.in_(["VALIDE", "EN_ATTENTE"]),
    ).order_by(Pointage.date_heure.asc()).first()

    # Si le dernier pointage a été REJETÉ → réessai immédiat (même type, pas d'attente)
    if (dernier_pointage is not None
            and dernier_pointage.statut == "REJETE"
            and total_tentatives < MAX_TENTATIVES):
        type_pointage = dernier_pointage.type

    elif entree_valide is None:
        # Pas d'entrée validée → c'est une nouvelle tentative d'ENTRÉE
        type_pointage = "ENTREE"

    else:
        # Une entrée validée existe → c'est une tentative de SORTIE (règle 1h)
        duree_secondes = (maintenant - entree_valide.date_heure).total_seconds()
        duree_minimum_secondes = DUREE_MINIMUM_HEURES * 3600

        if duree_secondes < duree_minimum_secondes:
            temps_restant_secondes = int(duree_minimum_secondes - duree_secondes)
            heures_restantes = temps_restant_secondes // 3600
            minutes_restantes = (temps_restant_secondes % 3600) // 60
            secondes_restantes = temps_restant_secondes % 60
            heure_entree_utc = entree_valide.date_heure.replace(tzinfo=timezone.utc)
            heure_autorisee = (heure_entree_utc.timestamp() + duree_minimum_secondes) * 1000  # en ms pour JS

            return jsonify(
                erreur=(
                    f"Vous ne pouvez pas pointer votre sortie avant {DUREE_MINIMUM_HEURES}h "
                    f"après votre entrée ({entree_valide.date_heure.strftime('%H:%M')}). "
                    f"Temps restant : {heures_restantes}h {minutes_restantes}m {secondes_restantes}s."
                ),
                code="SORTIE_BLOQUEE",
                temps_restant_secondes=temps_restant_secondes,
                heure_autorisee=int(heure_autorisee),
                heure_entree=entree_valide.date_heure.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                duree_minimum_heures=DUREE_MINIMUM_HEURES,
            ), 400

        type_pointage = "SORTIE"

    # 4) Analyse biométrique (DeepFace / FaceNet)
    config = Configuration.instance()
    try:
        resultat = rs.generer_embedding(
            photo, model_name=config.modele_reconnaissance, detector_backend="opencv"
        )
        score = rs.comparer(principal.empreinte.get_embedding(), resultat.embedding)
    except VisageNonDetecteError as exc:
        return jsonify(erreur=str(exc), code="VISAGE_NON_RECONNU"), 422
    except ServiceReconnaissanceIndisponibleError as exc:
        return jsonify(erreur=str(exc), code="SERVICE_INDISPONIBLE"), 503

    # 5) Décision selon les seuils configurés (classe Configuration)
    # Calcul distance euclidienne (embedding candidat vs empreinte référence)
    import numpy as np
    a = np.asarray(principal.empreinte.get_embedding(), dtype=np.float64)
    b = np.asarray(resultat.embedding, dtype=np.float64)
    if a.shape == b.shape and np.linalg.norm(a) > 0 and np.linalg.norm(b) > 0:
        a_norm = a / np.linalg.norm(a)
        b_norm = b / np.linalg.norm(b)
        distance_euclidienne = float(np.linalg.norm(a_norm - b_norm))
    else:
        distance_euclidienne = None

    statut = config.decider_statut(score, distance_euclidienne=distance_euclidienne)

    methode_validation = "AUTOMATIQUE" if statut == "VALIDE" else (
        "MANUELLE_RH" if statut == "EN_ATTENTE" else "REJETE_AUTO"
    )

    pointage = Pointage(
        utilisateur_id=principal.id,
        date_heure=maintenant,
        type=type_pointage,
        mode=mode_teletravail,
        methode_validation=methode_validation,
        statut=statut,
        score_confiance=score,
    )
    db.session.add(pointage)
    db.session.commit()

    messages = {
        "REJETE": "Échec de l'authentification faciale — visage non reconnu.",
        "EN_ATTENTE": "Pointage enregistré. En attente de validation RH.",
        "VALIDE": "Pointage enregistré avec succès !",
    }
    return jsonify(
        type=type_pointage,
        statut=statut,
        mode="Télétravail" if mode_teletravail else "Présentiel",
        score=round(score, 4),
        distance_euclidienne=round(distance_euclidienne, 6) if distance_euclidienne is not None else None,
        message=messages[statut],
        pointage=pointage.to_dict(include_utilisateur=False),
    ), 201 if statut != "REJETE" else 200


@bp.route("", methods=["GET"])
@jwt_required()
def lister():
    """
    UC-03 (un employé consulte SES pointages) / UC-08 (manager/RH consultent
    ceux de leur périmètre). Filtres optionnels : ?utilisateur_id=&methode=&statut=
    """
    principal = principal_courant()
    claims = get_jwt()
    role = claims.get("role")

    query = Pointage.query
    utilisateur_id_filtre = request.args.get("utilisateur_id", type=int)

    if role == "employe":
        # un employé ne voit que ses propres pointages, quel que soit le filtre demandé
        query = query.filter(Pointage.utilisateur_id == principal.id)
    elif utilisateur_id_filtre:
        query = query.filter(Pointage.utilisateur_id == utilisateur_id_filtre)
    elif role == "manager":
        # Un manager voit uniquement les pointages des employés de son département.
        dept_id = getattr(principal, "departement_id", None)
        if dept_id is not None:
            query = query.join(Utilisateur).filter(
                Utilisateur.departement_id == dept_id
            )
        else:
            # Aucun département assigné → liste vide
            query = query.filter(False)



    methode = request.args.get("methode")
    # SQL Server BIT : utiliser == 0 / == 1 plutôt que IS TRUE/FALSE
    if methode == "Présentiel":
        query = query.filter(Pointage.mode == False)
    elif methode == "Télétravail":
        query = query.filter(Pointage.mode == True)


    statut = request.args.get("statut")
    if statut:
        query = query.filter(Pointage.statut == statut.upper())

    limite = min(request.args.get("limite", default=100, type=int), 500)
    pointages = query.order_by(Pointage.date_heure.desc()).limit(limite).all()
    return jsonify([p.to_dict() for p in pointages]), 200


@bp.route("/<int:pointage_id>/revalider", methods=["PATCH"])
@role_requis("valider_pointage")
def revalider(pointage_id):
    """
    Validation manuelle RH d'un pointage EN_ATTENTE (score entre les 2 seuils).
    Body : { "decision": "VALIDE" | "REJETE" }
    """
    pointage = db.session.get(Pointage, pointage_id)
    if pointage is None:
        return jsonify(erreur="Pointage introuvable."), 404
    if pointage.statut != "EN_ATTENTE":
        return jsonify(erreur="Ce pointage n'est pas en attente de validation."), 409

    decision = (request.get_json(silent=True) or {}).get("decision")
    if decision not in ("VALIDE", "REJETE"):
        return jsonify(erreur="decision doit valoir 'VALIDE' ou 'REJETE'."), 400

    pointage.statut = decision
    pointage.methode_validation = "MANUELLE_RH"
    db.session.commit()
    return jsonify(pointage.to_dict()), 200
