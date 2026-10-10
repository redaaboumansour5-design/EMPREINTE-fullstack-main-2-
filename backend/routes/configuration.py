"""
routes/configuration.py
---------------------------
UC-13 — Configurer système (Administrateur uniquement).
Classe Configuration : seuils de reconnaissance dynamiques (SeuilMin/SeuilMax)
utilisés par le pointage (routes/pointage.py) — cf. diagramme de séquence
"Pointage avec Seuils Configuration Dynamiques".
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from extensions import db
from models import Configuration, Administrateur
from routes._auth_utils import principal_courant

bp = Blueprint("configuration", __name__, url_prefix="/api/configuration")


@bp.route("", methods=["GET"])
@jwt_required()
def obtenir():
    # Lecture ouverte à tout principal authentifié (utile pour afficher les
    # seuils courants côté React), mais la MODIFICATION est réservée à l'admin.
    return jsonify(Configuration.instance().to_dict()), 200


@bp.route("", methods=["PATCH"])
@jwt_required()
def modifier():
    """+configurerSysteme(param) : void — réservé à l'Administrateur."""
    claims = get_jwt()
    if claims.get("role") != "administrateur":
        return jsonify(erreur="Seul un administrateur peut modifier la configuration."), 403

    payload = request.get_json(silent=True) or {}
    config = Configuration.instance()

    seuil_min = payload.get("seuil_min", config.seuil_min)
    seuil_max = payload.get("seuil_max", config.seuil_max)
    seuil_distance = payload.get("seuil_distance", config.seuil_distance)

    if not (0 <= seuil_min <= 1) or not (0 <= seuil_max <= 1):
        return jsonify(erreur="Les seuils doivent être compris entre 0 et 1."), 400
    if seuil_min >= seuil_max:
        return jsonify(erreur="seuil_min doit être strictement inférieur à seuil_max."), 400
    if seuil_distance <= 0:
        return jsonify(erreur="seuil_distance doit être strictement supérieur à 0."), 400

    config.seuil_min = seuil_min
    config.seuil_max = seuil_max
    config.seuil_distance = seuil_distance
    if "modele_reconnaissance" in payload:
        config.modele_reconnaissance = payload["modele_reconnaissance"]

    principal = principal_courant()
    if isinstance(principal, Administrateur):
        config.maj_par_id = principal.id

    db.session.commit()
    return jsonify(config.to_dict()), 200
