from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

from extensions import db
from models.rapport import Rapport


def test_to_dict_uses_admin_label_when_user_relation_is_missing():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)

    with app.app_context():
        rapport = Rapport(id=1, type="pointages", genere_par_id=42)
        rapport.genere_par = None

        admin = SimpleNamespace(nom_complet="Admin Test", identifiant_admin="admin")
        with patch.object(db.session, "get", return_value=admin):
            payload = rapport.to_dict()

        assert payload["genere_par"] == "Admin"
