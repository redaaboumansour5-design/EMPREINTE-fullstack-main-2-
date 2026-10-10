"""
models/reconnaissance_faciale.py
-----------------------------------
Correspond à la classe `ReconnaissanceFaciale` :
  -id, -empreinteFaciale : byte[], -dateEnregistrement : Date
  +capturerVisage(img) : void
  +comparerVisage(img) : float

L'attribut `seuilConfiance` du diagramme d'origine a été déplacé vers la
classe `Configuration` (réglage global, cf. models/configuration.py) car vos
diagrammes de séquence interrogent un SeuilMin/SeuilMax communs à tous les
pointages (`SELECT SeuilMin, SeuilMax FROM Configuration`), et non un seuil
par employé.

L'empreinte (vecteur d'embedding FaceNet, 128 ou 512 dimensions selon le
modèle) est stockée sérialisée en JSON dans un champ texte — plus portable
et plus sûr à désérialiser qu'un pickle binaire.
"""
import json
from datetime import datetime
from extensions import db


class ReconnaissanceFaciale(db.Model):
    __tablename__ = "reconnaissances_faciales"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False, unique=True
    )
    empreinte_faciale = db.Column(db.Text, nullable=False)  # JSON list[float] (embedding)
    modele = db.Column(db.String(50), default="Facenet")
    date_enregistrement = db.Column(db.DateTime, default=datetime.utcnow)

    utilisateur = db.relationship("Utilisateur", back_populates="empreinte")

    def set_embedding(self, vecteur: list[float]) -> None:
        self.empreinte_faciale = json.dumps(vecteur)

    def get_embedding(self) -> list[float]:
        return json.loads(self.empreinte_faciale)

    def to_dict(self):
        return {
            "id": self.id,
            "utilisateur_id": self.utilisateur_id,
            "modele": self.modele,
            "dimensions": len(self.get_embedding()) if self.empreinte_faciale else 0,
            "date_enregistrement": self.date_enregistrement.isoformat() if self.date_enregistrement else None,
        }

    def __repr__(self):
        return f"<ReconnaissanceFaciale utilisateur_id={self.utilisateur_id}>"
