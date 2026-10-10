"""
routes/auth.py
------------------
UC-01 — Authentification Simplifiée (cf. diagramme de séquence).

POST /api/auth/login   { email, password }  (l'identifiant admin passe aussi
                                              par le champ "email")
    -> 200 { access_token, role, utilisateur }
    -> 401 { erreur: "Email ou mot de passe incorrect" }

POST /api/auth/logout  -> 200 (le token est stateless ; le "logout" réel se
                                fait côté client en supprimant le token — voir
                                README pour la note sur la révocation de token)

GET  /api/auth/moi     -> profil du principal actuellement authentifié
"""
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required

from extensions import db
from models import Administrateur, Utilisateur
from routes._auth_utils import identite_jwt, role_jwt, principal_courant

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def valider_espace_connexion(
    principal: Utilisateur,
    espace_connexion: str,
    teletravail_approuve_active: bool,
) -> None:
    """Valide strictement l'espace de connexion demandé.

    Règle hybride :
      - Aujourd’hui, l’employé est considéré en "Télétravail" si :
          teletravail_autorise == 1  OU  (il existe une demande Teletravail APPROUVÉE
          couvrant aujourd’hui)
      - Sinon, il est considéré en "Présentiel".

    Ensuite :
      - Si en Télétravail aujourd’hui => espace attendu = "teletravail"
      - Si en Présentiel aujourd’hui => espace attendu = "presentiel"
    """
    espace = (espace_connexion or "").strip().lower()

    # IMPORTANT : la fonction est volontairement "duck-typed" pour faciliter les tests.
    teletravail_autorise = bool(getattr(principal, "teletravail_autorise", False))
    teletravail_aujourdhui = teletravail_autorise or bool(teletravail_approuve_active)

    # NOTE: ici on valide le mode attendu AUJOURD’HUI selon la règle hybride.
    if teletravail_aujourdhui:
        if espace == "teletravail":
            return
        raise PermissionError(
            "Connexion refusée : vous êtes en Télétravail aujourd’hui. Sélectionnez 'Télétravail'."
        )

    # Présentiel aujourd’hui
    if espace == "presentiel":
        return
    raise PermissionError(
        "Connexion refusée : vous êtes en Présentiel aujourd’hui (aucune autorisation télétravail active). "
        "Sélectionnez 'Présentiel'."
    )




@bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    mot_de_passe = payload.get("password") or ""
    espace = (payload.get("espace") or "").strip().lower()  # admin | employe
    mode_demande = (payload.get("mode_demande") or "").strip().lower()  # teletravail | presentiel

    if not email or not mot_de_passe:
        return jsonify(erreur="Email et mot de passe requis."), 400


    principal = None

    # Cas 1 : compte utilisateur métier (employé / manager / rh)
    if espace != "admin":
        utilisateur = Utilisateur.query.filter(db.func.lower(Utilisateur.email) == email).first()
        if utilisateur and utilisateur.s_authentifier(mot_de_passe):
            principal = utilisateur

    # Cas 2 : compte administrateur (identifiant_admin transmis dans "email")
    if principal is None and espace == "admin":
        admin = Administrateur.query.filter(
            db.func.lower(Administrateur.identifiant_admin) == email
        ).first()
        if admin and admin.s_authentifier(mot_de_passe):
            principal = admin

    if principal is None and espace == "admin":
        return jsonify(erreur="Compte admin introuvable ou mot de passe incorrect."), 401

    if principal is None and espace != "admin":
        return jsonify(erreur="Email ou mot de passe incorrect."), 401


    if principal is None:
        # message volontairement générique (ne pas indiquer si l'email existe)
        return jsonify(erreur="Email ou mot de passe incorrect."), 401

    # Vérification stricte de l'espace de connexion (uniquement pour les comptes employé)
    if isinstance(principal, Utilisateur):
        mode_demande_norm = (mode_demande or "presentiel").lower()  # télétravail | presentiel

        # Pour télétravail, on garde la contrainte "demande APPROUVÉE active aujourd’hui"
        teletravail_approuve_active = False
        if mode_demande_norm == "teletravail":
            from models import Teletravail
            from datetime import date

            aujourd_hui = date.today()
            active = (
                Teletravail.query.filter(
                    Teletravail.utilisateur_id == principal.id,
                    Teletravail.statut == "APPROUVE",
                    Teletravail.date_debut <= aujourd_hui,
                    Teletravail.date_fin >= aujourd_hui,
                ).first()
            )
            teletravail_approuve_active = active is not None

        try:
            valider_espace_connexion(
                principal=principal,
                espace_connexion=mode_demande_norm,
                teletravail_approuve_active=teletravail_approuve_active,
            )
        except PermissionError as exc:
            return jsonify(erreur=str(exc)), 403



    token = create_access_token(
        identity=identite_jwt(principal),
        additional_claims={"role": role_jwt(principal)},
    )


    reponse = {
        "access_token": token,
        "role": role_jwt(principal),
        "utilisateur": principal.to_dict(),
    }
    return jsonify(reponse), 200


@bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    # Authentification "simplifiée" par JWT stateless : rien à faire côté
    # serveur ici (le client supprime son token). Pour une vraie révocation,
    # ajoutez une blocklist (voir flask-jwt-extended docs "token revoking").
    return jsonify(message="Déconnecté."), 200




@bp.route("/moi", methods=["GET"])
@jwt_required()
def moi():
    principal = principal_courant()
    if principal is None:
        return jsonify(erreur="Principal introuvable."), 404
    return jsonify(principal.to_dict()), 200

