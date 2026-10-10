"""
models/teletravail.py
-------------------------
Correspond à la classe `Teletravail` :
  -id, -dateDebut : Date, -dateFin : Date, -motif : string, -statut : string

Statuts alignés sur le diagramme de séquence UC-04/UC-06 :
  SOUMISE -> APPROUVE | REJETE  (décision prise par le manager)
"""
from extensions import db

STATUTS_VALIDES = ("SOUMISE", "APPROUVE", "REJETE")


class Teletravail(db.Model):
    __tablename__ = "teletravail"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)  # "soumet"
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    motif = db.Column(db.String(255))
    statut = db.Column(db.String(20), nullable=False, default="SOUMISE")

    validateur_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)  # "valide"
    date_decision = db.Column(db.DateTime, nullable=True)
    commentaire = db.Column(db.String(255), nullable=True)

    employe = db.relationship(
        "Utilisateur", foreign_keys=[utilisateur_id], back_populates="demandes_teletravail"
    )
    validateur = db.relationship("Utilisateur", foreign_keys=[validateur_id])

    __table_args__ = (
        db.CheckConstraint(f"statut IN {STATUTS_VALIDES}", name="ck_teletravail_statut"),
        db.CheckConstraint("date_fin >= date_debut", name="ck_teletravail_periode"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "employe": {
                "id": self.employe.id,
                "nom_complet": f"{self.employe.prenom} {self.employe.nom}",
                "matricule": self.employe.matricule,
                "departement": self.employe.departement.nom if self.employe.departement else None,
            },
            "date_debut": self.date_debut.isoformat(),
            "date_fin": self.date_fin.isoformat(),
            "motif": self.motif,
            "statut": self.statut,
            "validateur": (
                f"{self.validateur.prenom} {self.validateur.nom}" if self.validateur else None
            ),
            "date_decision": self.date_decision.isoformat() if self.date_decision else None,
            "commentaire": self.commentaire,
        }

    def __repr__(self):
        return f"<Teletravail {self.id} statut={self.statut}>"
