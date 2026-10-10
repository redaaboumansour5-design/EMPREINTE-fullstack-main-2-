"""
routes/_auth_utils.py
------------------------
Utilitaires communs à toutes les routes protégées :
  - résolution de l'identité JWT (Administrateur OU Utilisateur)
  - décorateur @role_requis(...) qui s'appuie sur Permission.verifier_droit()
    (classe Permission : +verifierDroit(action) : bool)
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

from extensions import db
from models import Administrateur, Utilisateur, Permission


def identite_jwt(principal) -> str:
    """Construit l'identité JWT : 'admin:<id>' ou 'user:<id>'."""
    if isinstance(principal, Administrateur):
        return f"admin:{principal.id}"
    return f"user:{principal.id}"


def role_jwt(principal) -> str:
    return "administrateur" if isinstance(principal, Administrateur) else principal.role


def principal_courant():
    """Résout le principal (Administrateur ou Utilisateur) à partir du JWT courant."""
    identity = get_jwt_identity()
    kind, _, raw_id = identity.partition(":")
    principal_id = int(raw_id)
    if kind == "admin":
        return db.session.get(Administrateur, principal_id)
    return db.session.get(Utilisateur, principal_id)


def role_requis(*actions_autorisees):
    """
    Décorateur d'autorisation basé sur la classe Permission du diagramme de
    classes (+verifierDroit(action): bool). Exemple :

        @bp.route("/api/teletravail/demandes/<int:id>/decider", methods=["PATCH"])
        @role_requis("valider_teletravail")
        def decider(id): ...

    Un administrateur passe toujours (accès système complet). Pour les autres
    rôles, on vérifie qu'AU MOINS une des actions listées est autorisée pour
    leur rôle dans la table `permissions`.
    """
    def decorateur(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")
            if role == "administrateur":
                return fn(*args, **kwargs)
            if any(Permission.verifier_droit(role, action) for action in actions_autorisees):
                return fn(*args, **kwargs)
            return jsonify(erreur="Accès refusé : permission manquante pour ce rôle."), 403
        return wrapper
    return decorateur
