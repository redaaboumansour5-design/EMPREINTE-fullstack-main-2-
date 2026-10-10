"""
extensions.py
--------------
Instances partagées (pattern factory Flask) pour éviter les imports circulaires
entre app.py, models/ et routes/.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
        