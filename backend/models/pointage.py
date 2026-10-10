"""
models/pointage.py
---------------------
Correspond à la classe `Pointage` :
  -id, -dateHeure : DateTime, -type : string, -mode : bool «true=Télétravail, false=Présentiel»,
  -methodeValidation : string, -statut : string, -photoCapture : string

(score_confiance ajouté : nécessaire pour tracer le résultat de la comparaison
biométrique — implicite dans le diagramme de séquence via la variable @score,
mais absent du diagramme de classes d'origine.)
"""
from datetime import datetime, timezone
from extensions import db

STATUTS_VALIDES = ("VALIDE", "EN_ATTENTE", "REJETE")


class Pointage(db.Model):
    __tablename__ = "pointages"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)
    date_heure = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    type = db.Column(db.String(20), default="ENTREE")           # ENTREE | SORTIE
    mode = db.Column(db.Boolean, nullable=False, default=False)  # True = Télétravail, False = Présentiel
    methode_validation = db.Column(db.String(30))                 # AUTOMATIQUE | MANUELLE_RH
    statut = db.Column(db.String(20), nullable=False)             # VALIDE | EN_ATTENTE | REJETE
    score_confiance = db.Column(db.Float, nullable=True)
    photo_capture = db.Column(db.String(255), nullable=True)  # chemin/réf. de la frame capturée

    utilisateur = db.relationship("Utilisateur", back_populates="pointages")

    __table_args__ = (
        db.CheckConstraint(f"statut IN {STATUTS_VALIDES}", name="ck_pointage_statut"),
    )

    def to_dict(self, include_utilisateur=True):
        data = {
            "id": self.id,
            # Les dates stockées sans timezone sont UTC; le suffixe Z évite
            # qu'un navigateur les interprète dans le fuseau de sa machine.
            "date_heure": self.date_heure.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "type": self.type,
            "mode": "Télétravail" if self.mode else "Présentiel",
            "methode_validation": self.methode_validation,
            "statut": self.statut,
            "score_confiance": round(self.score_confiance, 4) if self.score_confiance is not None else None,
        }
        if include_utilisateur and self.utilisateur:
            data["utilisateur"] = {
                "id": self.utilisateur.id,
                "matricule": self.utilisateur.matricule,
                "nom_complet": f"{self.utilisateur.prenom} {self.utilisateur.nom}",
                "departement": self.utilisateur.departement.nom if self.utilisateur.departement else None,
            }
        return data

    def __repr__(self):
        return f"<Pointage {self.id} user={self.utilisateur_id} statut={self.statut}>"
