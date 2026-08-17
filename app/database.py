# app/database.py
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.pool as pool

# Detectar entorno
IS_PRODUCTION = os.getenv("RENDER", "false").lower() == "true"

if IS_PRODUCTION:
    # En Render: Usar Turso
    try:
        from turso_python.connection import TursoConnection
        
        TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
        TURSO_TOKEN = os.getenv("TURSO_TOKEN")
        
        if not TURSO_DATABASE_URL or not TURSO_TOKEN:
            raise ValueError("❌ Variables de entorno TURSO_DATABASE_URL y TURSO_TOKEN son obligatorias en Render")
        
        # Crear el engine con turso-python
        def create_turso_connection():
            return TursoConnection(
                database_url=TURSO_DATABASE_URL,
                auth_token=TURSO_TOKEN
            )
        
        engine = create_engine(
            "sqlite://",
            creator=create_turso_connection,
            poolclass=pool.StaticPool,
            connect_args={"check_same_thread": False}
        )
        print("✅ Conectado a Turso en la nube")
    except Exception as e:
        print(f"⚠️ Error conectando a Turso: {e}")
        # Fallback a SQLite local si falla
        engine = create_engine("sqlite:///./data/bancaria.db", connect_args={"check_same_thread": False})
        print("⚠️ Usando SQLite local como fallback")
else:
    # En local: Usar SQLite
    engine = create_engine("sqlite:///./data/bancaria.db", connect_args={"check_same_thread": False})
    print("✅ Usando SQLite local para desarrollo")

# Sesión y Base
SessionLocal = sessionmaker(autocommit=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    from app import models
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas correctamente")