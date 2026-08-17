# app/database.py
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Detectar entorno
IS_PRODUCTION = os.getenv("RENDER", "false").lower() == "true"

if IS_PRODUCTION:
    # ✅ En Render: Usar Turso (persistente)
    import libsql_experimental as libsql
    TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
    TURSO_TOKEN = os.getenv("TURSO_TOKEN")
    
    if not TURSO_DATABASE_URL or not TURSO_TOKEN:
        raise ValueError("❌ Variables de entorno TURSO_DATABASE_URL y TURSO_TOKEN son obligatorias en Render")
    
    engine = create_engine(
        "sqlite://",
        creator=lambda: libsql.connect(TURSO_DATABASE_URL, auth_token=TURSO_TOKEN),
        connect_args={"check_same_thread": False}
    )
    print("✅ Conectado a Turso en la nube")
else:
    # ✅ En local: Usar SQLite (para desarrollo)
    import os
    from pathlib import Path
    
    # Asegurar que el directorio data/ existe
    DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    DATA_DIR.mkdir(exist_ok=True)
    
    SQLITE_DATABASE_URL = f"sqlite:///{DATA_DIR}/bancaria.db"
    engine = create_engine(
        SQLITE_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    print("✅ Usando SQLite local para desarrollo")

# Sesión y Base (común para ambos casos)
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