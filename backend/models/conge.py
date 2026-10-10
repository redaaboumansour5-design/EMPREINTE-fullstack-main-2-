"""
models/conge.py
---------------
Demande de congé employé avec validation admin/manager.

Statuts :
  SOUMISE  → en attente, aucun impact sur la présence
  APPROUVE → l'employé est « en congé » pour chaque jour couvert
  REJETE   → la logique d'absence standard s'applique
"""
from extensions import db

STATUTS_VALIDES = ("SOUMISE", "APPROUVE", "REJETE")


class Conge(db.Model):
    __tablename__ = "conges"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    motif = db.Column(db.String(255))
    statut = db.Column(db.String(20), nullable=False, default="SOUMISE")

    validateur_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"), nullable=True)
    date_decision = db.Column(db.DateTime, nullable=True)
    commentaire = db.Column(db.String(255), nullable=True)

    employe = db.relationship(
        "Utilisateur", foreign_keys=[utilisateur_id], back_populates="demandes_conge"
    )
    validateur = db.relationship("Utilisateur", foreign_keys=[validateur_id])

    __table_args__ = (
        db.CheckConstraint(f"statut IN {STATUTS_VALIDES}", name="ck_conge_statut"),
        db.CheckConstraint("date_fin >= date_debut", name="ck_conge_periode"),
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
        return f"<Conge {self.id} statut={self.statut}>"
