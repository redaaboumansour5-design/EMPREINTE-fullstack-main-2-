"""
models/configuration.py
--------------------------
Classe `Configuration` (introduite dans votre révision du diagramme de
classes) : réglages système globaux consultés à chaque pointage.

  -id, -seuilMin : float, -seuilMax : float, -seuilDistance : float,
  -modeleReconnaissance : string
  -dateMaj : DateTime, -majParId : int (FK Administrateur)

Logique à 3 zones (diagramme de séquence UC-02 « Pointage avec Seuils
Configuration Dynamiques ») :
  distance_euclidienne > seuil_distance  -> REJETE   (dissimilarité trop élevée)
  score < seuilMin                       -> REJETE   (échec reconnaissance)
  seuilMin <= score < seuilMax           -> EN_ATTENTE (validation manuelle RH)
  score >= seuilMax                      -> VALIDE   (validation automatique)

Table à une seule ligne (singleton) : on utilise toujours l'id=1.
"""
from datetime import datetime
from extensions import db


class Configuration(db.Model):
    __tablename__ = "configuration"

    id = db.Column(db.Integer, primary_key=True)
    seuil_min = db.Column(db.Float, nullable=False, default=0.45)
    seuil_max = db.Column(db.Float, nullable=False, default=0.75)
    seuil_distance = db.Column(db.Float, nullable=False, default=1.0)
    modele_reconnaissance = db.Column(db.String(50), default="Facenet")
    date_maj = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    maj_par_id = db.Column(db.Integer, db.ForeignKey("administrateurs.id"), nullable=True)

    __table_args__ = (
        db.CheckConstraint("seuil_min >= 0 AND seuil_min <= 1", name="ck_config_seuil_min_range"),
        db.CheckConstraint("seuil_max >= 0 AND seuil_max <= 1", name="ck_config_seuil_max_range"),
        db.CheckConstraint("seuil_min < seuil_max", name="ck_config_seuil_min_lt_max"),
        db.CheckConstraint("seuil_distance > 0", name="ck_config_seuil_distance_positif"),
    )

    @staticmethod
    def instance(app_defaults=None) -> "Configuration":
        """Retourne la ligne unique de configuration, la crée si absente (1er démarrage)."""
        config = db.session.get(Configuration, 1)
        if config is None:
            config = Configuration(
                id=1,
                seuil_min=(app_defaults or {}).get("SEUIL_MIN_DEFAUT", 0.45),
                seuil_max=(app_defaults or {}).get("SEUIL_MAX_DEFAUT", 0.75),
                seuil_distance=(app_defaults or {}).get("SEUIL_DISTANCE_DEFAUT", 1.0),
                modele_reconnaissance=(app_defaults or {}).get("MODELE_RECONNAISSANCE", "Facenet"),
            )
            db.session.add(config)
            db.session.commit()
        return config

    def decider_statut(self, score: float, distance_euclidienne: float = None) -> str:
        # Priorité 1 : score ≥ seuil_max → validation automatique immédiate
        # (un score de similarité élevé prime toujours sur la distance)
        if score >= self.seuil_max:
            return "VALIDE"

        # Priorité 2 : distance euclidienne trop élevée → dissimilarité → rejet
        # (calculée uniquement si le score n'est pas déjà validé automatiquement)
        if distance_euclidienne is not None and distance_euclidienne > self.seuil_distance:
            return "REJETE"

        # Priorité 3 : score basé sur la similarité cosinus
        if score < self.seuil_min:
            return "REJETE"

        # Cas restant : seuil_min <= score < seuil_max → validation manuelle RH
        return "EN_ATTENTE"

    def to_dict(self):
        return {
            "seuil_min": self.seuil_min,
            "seuil_max": self.seuil_max,
            "seuil_distance": self.seuil_distance,
            "modele_reconnaissance": self.modele_reconnaissance,
            "date_maj": self.date_maj.isoformat() if self.date_maj else None,
        }
