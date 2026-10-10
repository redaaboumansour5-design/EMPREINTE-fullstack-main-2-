import sys
import os
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
import models # Make sure models are loaded so db.create_all() knows about them

app = create_app()

def reset_database():
    with app.app_context():
        print("Connecting to the database...")
        # 1. Drop all foreign key constraints
        print("Dropping foreign key constraints...")
        drop_fks_sql = """
        DECLARE @sql NVARCHAR(MAX) = N'';
        SELECT @sql += N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id))
            + N'.' + QUOTENAME(OBJECT_NAME(parent_object_id)) 
            + N' DROP CONSTRAINT ' + QUOTENAME(name) + N';'
        FROM sys.foreign_keys;
        EXEC sp_executesql @sql;
        """
        db.session.execute(text(drop_fks_sql))
        db.session.commit()

        # 2. Drop all tables
        print("Dropping all tables...")
        drop_tables_sql = """
        DECLARE @sql NVARCHAR(MAX) = N'';
        SELECT @sql += N'DROP TABLE ' + QUOTENAME(SCHEMA_NAME(schema_id)) + N'.' + QUOTENAME(name) + N';'
        FROM sys.tables;
        EXEC sp_executesql @sql;
        """
        db.session.execute(text(drop_tables_sql))
        db.session.commit()

        print("Creating all tables via SQLAlchemy...")
        db.create_all()
        db.session.commit()
        print("Database tables created successfully!")

if __name__ == "__main__":
    reset_database()
