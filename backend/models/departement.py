"""
models/departement.py
----------------------
Correspond à la classe `Departement` du diagramme de classes.
  -id : int
  -nom : string
  +listerEmployes() : List<Utilisateur>

Relations :
  - 1 Departement -> N Utilisateur ("appartient à")
  - 1 Departement -> 1 Utilisateur "responsable" (le manager du service)
"""
from datetime import datetime
from extensions import db


class Departement(db.Model):
    __tablename__ = "departements"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    responsable_id = db.Column(
        db.Integer, db.ForeignKey("utilisateurs.id", use_alter=True, name="fk_departement_responsable"),
        nullable=True,
    )
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # côté "N" de la relation appartient à (voir Utilisateur.departement_id)
    utilisateurs = db.relationship(
        "Utilisateur",
        back_populates="departement",
        foreign_keys="Utilisateur.departement_id",
    )
    # le responsable/manager désigné du département
    responsable = db.relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
        post_update=True,
    )

    def lister_employes(self):
        """+listerEmployes() : List<Utilisateur> — tous les utilisateurs rattachés."""
        return list(self.utilisateurs)

    def to_dict(self, with_responsable=True):
        data = {
            "id": self.id,
            "nom": self.nom,
            "effectif": len(self.utilisateurs),
        }
        if with_responsable and self.responsable:
            data["responsable"] = {
                "id": self.responsable.id,
                "nom_complet": f"{self.responsable.prenom} {self.responsable.nom}",
            }
        return data

    def __repr__(self):
        return f"<Departement {self.nom}>"
