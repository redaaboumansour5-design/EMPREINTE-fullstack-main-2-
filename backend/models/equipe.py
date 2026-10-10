"""models/equipe.py
------------------
Table `equipes` pour modéliser la notion d'équipe gérée par un manager.

Règles:
- Une équipe correspond à 1 manager (1 équipe -> 1 responsable/manager)
- Les employés (role='employe') sont affectés via Utilisateur.equipe_id
- On conserve aussi departement_id (non cassant pour le reste du système)
"""

from datetime import datetime

from extensions import db


class Equipe(db.Model):
    __tablename__ = "equipes"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)

    # 1 manager par équipe
    manager_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    manager = db.relationship("Utilisateur", foreign_keys=[manager_id], post_update=True)

    def to_dict(self, with_manager=False):
        data = {
            "id": self.id,
            "nom": self.nom,
        }
        if with_manager and self.manager:
            data["manager"] = {
                "id": self.manager.id,
                "nom_complet": f"{self.manager.prenom} {self.manager.nom}",
            }
        return data

    def __repr__(self):
        return f"<Equipe {self.nom}>"

