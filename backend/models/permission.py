"""
models/permission.py
----------------------
Correspond à la classe `Permission` :
  -id, -nomRole, -actionAutorisee
  +verifierDroit(action) : bool

Table plate (nomRole, actionAutorisee) consultée par le décorateur
`role_requis` (voir routes/_auth_utils.py) pour l'autorisation.
"""
from extensions import db


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    nom_role = db.Column(db.String(20), nullable=False)          # employe | manager | rh | administrateur
    action_autorisee = db.Column(db.String(100), nullable=False)  # ex: "consulter_dashboard", "valider_teletravail"

    __table_args__ = (
        db.UniqueConstraint("nom_role", "action_autorisee", name="uq_permission_role_action"),
    )

    @staticmethod
    def verifier_droit(nom_role: str, action: str) -> bool:
        """+verifierDroit(action) : bool"""
        return (
            db.session.query(Permission)
            .filter_by(nom_role=nom_role, action_autorisee=action)
            .first()
            is not None
        )

    def to_dict(self):
        return {"id": self.id, "nom_role": self.nom_role, "action_autorisee": self.action_autorisee}

    def __repr__(self):
        return f"<Permission {self.nom_role}:{self.action_autorisee}>"
