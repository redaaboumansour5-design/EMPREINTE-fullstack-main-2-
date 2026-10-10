"""
models/administrateur.py
--------------------------
Correspond à la classe `Administrateur` du diagramme de classes :
  -id, -identifiantAdmin, -motDePasse
  +gererRolesEtPermissions() : void
  +configurerSysteme(param) : void
  +sauvegarderDonnees() : void

Distinct de `Utilisateur` : compte système à privilèges élevés
(gestion des rôles/permissions, configuration des seuils, sauvegardes),
et non un rôle métier (employé/manager/RH).
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class Administrateur(db.Model):
    __tablename__ = "administrateurs"

    id = db.Column(db.Integer, primary_key=True)
    identifiant_admin = db.Column(db.String(50), nullable=False, unique=True)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    nom_complet = db.Column(db.String(150))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, mot_de_passe: str) -> None:
        self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

    def s_authentifier(self, mot_de_passe: str) -> bool:
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

    def to_dict(self):
        return {
            "id": self.id,
            "identifiant_admin": self.identifiant_admin,
            "nom_complet": self.nom_complet,
            "role": "administrateur",
        }

    def __repr__(self):
        return f"<Administrateur {self.identifiant_admin}>"
