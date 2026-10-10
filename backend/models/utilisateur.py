"""
models/utilisateur.py
-----------------------
Correspond à la classe `Utilisateur` du diagramme de classes mis à jour :
  -id, -matricule, -nom, -prenom, -email, -motDePasse, -telephone,
  -role «employe, rh, manager», -poste, -dateEmbauche, -dateCreation
  +sAuthentifier(email, mdp) : bool
  +seDeconnecter() : void
  +pointerParCamera(image) : Pointage
  +consulterSesPointages(periode) : List<Pointage>

NB : les anciennes sous-classes Employe/Manager/RH sont désormais fusionnées
dans une seule table `utilisateurs`, distinguées par la colonne `role`
(cf. le diagramme de classes révisé). `Administrateur` reste une classe/table
séparée (voir models/administrateur.py) car son périmètre est différent
(config système, rôles & permissions) et non un rôle métier ordinaire.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

ROLES_VALIDES = ("employe", "manager", "rh")


class Utilisateur(db.Model):
    __tablename__ = "utilisateurs"

    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(20), nullable=False, unique=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    telephone = db.Column(db.String(30))
    role = db.Column(db.String(20), nullable=False, default="employe")  # employe | manager | rh
    poste = db.Column(db.String(100))
    teletravail_autorise = db.Column(db.Boolean, nullable=False, default=False)
    date_embauche = db.Column(db.Date)

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    departement_id = db.Column(db.Integer, db.ForeignKey("departements.id"), nullable=True)
    departement = db.relationship(
        "Departement",
        back_populates="utilisateurs",
        foreign_keys=[departement_id],
    )

    pointages = db.relationship(
        "Pointage", back_populates="utilisateur", cascade="all, delete-orphan",
        order_by="Pointage.date_heure.desc()",
    )
    empreinte = db.relationship(
        "ReconnaissanceFaciale", back_populates="utilisateur", uselist=False,
        cascade="all, delete-orphan",
    )
    demandes_teletravail = db.relationship(
        "Teletravail", back_populates="employe", foreign_keys="Teletravail.utilisateur_id",
        cascade="all, delete-orphan",
    )
    demandes_conge = db.relationship(
        "Conge", back_populates="employe", foreign_keys="Conge.utilisateur_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.CheckConstraint(f"role IN {ROLES_VALIDES}", name="ck_utilisateur_role"),
    )

    # ---- Authentification (UC-01) ----------------------------------------
    def set_password(self, mot_de_passe: str) -> None:
        self.mot_de_passe_hash = generate_password_hash(mot_de_passe)

    def s_authentifier(self, mot_de_passe: str) -> bool:
        """+sAuthentifier(email, mdp) : bool — email déjà résolu en amont (login route)."""
        return check_password_hash(self.mot_de_passe_hash, mot_de_passe)

    # ---- Sérialisation -----------------------------------------------------
    def to_dict(self, include_departement=True):
        data = {
            "id": self.id,
            "matricule": self.matricule,
            "nom": self.nom,
            "prenom": self.prenom,
            "email": self.email,
            "telephone": self.telephone,
            "role": self.role,
            "poste": self.poste,
            "teletravail_autorise": bool(self.teletravail_autorise),
            "date_embauche": self.date_embauche.isoformat() if self.date_embauche else None,

            "a_empreinte_enregistree": self.empreinte is not None,
        }
        if include_departement and self.departement:
            data["departement"] = {"id": self.departement.id, "nom": self.departement.nom}
        return data

    def __repr__(self):
        return f"<Utilisateur {self.matricule} {self.prenom} {self.nom} ({self.role})>"
