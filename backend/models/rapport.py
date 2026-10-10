"""
models/rapport.py
---------------------
Correspond à la classe `Rapport` :
  -id, -type, -dateDebut, -dateFin, -dateGeneration, -format
  «Contrainte» : uniquement si role == 'rh' (imposé côté route, pas ici)
"""
from datetime import datetime

from extensions import db
from models.administrateur import Administrateur


class Rapport(db.Model):
    __tablename__ = "rapports"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)   # pointages | employes | teletravail | absenteisme
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    date_generation = db.Column(db.DateTime, default=datetime.utcnow)
    format = db.Column(db.String(10), default="CSV")
    genere_par_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)

    genere_par = db.relationship("Utilisateur")

    def to_dict(self):
        auteur = None
        if self.genere_par_id is not None:
            admin = db.session.get(Administrateur, self.genere_par_id)
            if admin is not None:
                auteur = "Admin"

        if auteur is None and self.genere_par is not None:
            auteur = f"{self.genere_par.prenom} {self.genere_par.nom}"

        return {
            "id": self.id,
            "type": self.type,
            "date_debut": self.date_debut.isoformat() if self.date_debut else None,
            "date_fin": self.date_fin.isoformat() if self.date_fin else None,
            "date_generation": self.date_generation.isoformat() if self.date_generation else None,
            "format": self.format,
            "genere_par": auteur,
        }
