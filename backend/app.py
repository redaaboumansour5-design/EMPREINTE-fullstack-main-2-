"""
app.py
--------
Point d'entrée de l'API Flask (Application Factory pattern).

Démarrage local :
    flask --app app run --debug --port 5000
ou :
    python app.py
"""
import os

from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()  # charge .env AVANT d'importer config (qui lit os.environ)

from config import Config, build_sqlserver_uri, ConfigurationError
from extensions import db, jwt, cors


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    try:
        app.config["SQLALCHEMY_DATABASE_URI"] = build_sqlserver_uri()
    except ConfigurationError as exc:
        # On ne bloque pas complètement l'import (utile pour `flask --help`
        # ou les tests unitaires purs), mais toute requête touchant la DB
        # échouera clairement tant que .env n'est pas configuré.
        app.logger.warning(str(exc))
        app.config["SQLALCHEMY_DATABASE_URI"] = "mssql+pyodbc://__non_configure__"

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}}, supports_credentials=True)

    # --- Blueprints (un module par cas d'utilisation) -----------------------
    from routes.auth import bp as auth_bp
    from routes.employes import bp as employes_bp
    from routes.pointage import bp as pointage_bp
    from routes.teletravail import bp as teletravail_bp
    from routes.configuration import bp as configuration_bp
    from routes.dashboard import bp as dashboard_bp
    from routes.dashboard_mois import bp as dashboard_mois_bp
    from routes.conges import bp as conges_bp
    from routes.demandes import bp as demandes_bp
    from routes.rapports import bp as rapports_bp

    for bp in (auth_bp, employes_bp, pointage_bp, teletravail_bp, conges_bp, demandes_bp, configuration_bp, dashboard_bp, dashboard_mois_bp, rapports_bp):
        app.register_blueprint(bp)


    @app.route("/api/sante", methods=["GET"])
    def sante():
        """Endpoint de vérification (uptime, monitoring)."""
        return jsonify(statut="ok", service="EMPREINTE API"), 200

    @app.errorhandler(404)
    def non_trouve(_):
        return jsonify(erreur="Route introuvable."), 404

    @app.errorhandler(500)
    def erreur_serveur(exc):
        app.logger.exception(exc)
        return jsonify(erreur="Erreur interne du serveur."), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
