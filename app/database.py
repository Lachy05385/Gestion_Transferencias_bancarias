# app/database.py
import os
import sys
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.pool as pool

# Configuración de Turso
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "libsql://bancaria-lachy05385.aws-us-west-2.turso.io")
TURSO_TOKEN = os.getenv("TURSO_TOKEN", "eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDIyMkFBQSIsImtpZCI6Imluc18yYzA4R3ZNeEhYMlNCc3l0d2padm95cEdJeDUiLCJ0eXAiOiJKV1QifQ.eyJleHAiOjE3ODY3ODA0MTQsImlhdCI6MTc4NjE3NTYxNCwiaXNzIjoiaHR0cHM6Ly9jbGVyay50dXJzby50ZWNoIiwianRpIjoiZmE4ZWIxMWU0ZjI2NDA3N2I1NWUiLCJuYmYiOjE3ODYxNzU2MDksInN1YiI6InVzZXJfM0V4THRzSUk0WjcwcERFSU5mUW1SRW12QmdBIn0.poZA9J4CADZvIUAfpUzNpVb7pqjCQ_CLupDaxL3p2wUWAu7_NUAjerAcF7AjBNJIu1LmQs-7y30mv8JbxUCz0gxKqSFUdW3JtpuT-bvzJndtxPt10iWwucVfb_9m9_Z5S6umeY_yIwnPUYiuuXvN8XcJGFAGvByL876tdkNFeyWpsPC7By3FEagfCBQ52dEbIKvJb28WDQbgoP_oVBqPaI1f4MTPvPf4gBsFvTEtNQZmLz8hc1c0AFk2X9dL4pN-kBaj3kacu-g_M_8aINIvpvm-4IG7yah9h5BNvpSdZxiho5jRtvIWL_aW8ASZBo0wvuOONV7FcEFi0O56ekCXhg")

# Convertir libsql:// a https:// para la API HTTP
TURSO_HTTP_URL = TURSO_DATABASE_URL.replace("libsql://", "https://")

# Función para ejecutar consultas en Turso vía HTTP
def execute_turso_query(sql, params=None):
    """Ejecuta una consulta SQL en Turso usando la API HTTP."""
    headers = {
        "Authorization": f"Bearer {TURSO_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Preparar la consulta
    payload = {
        "requests": [{
            "type": "execute",
            "stmt": {"sql": sql}
        }]
    }
    
    # Si hay parámetros, añadirlos
    if params:
        payload["requests"][0]["stmt"]["args"] = params
    
    # Ejecutar la consulta
    response = requests.post(f"{TURSO_HTTP_URL}/v2/pipeline", headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Error en Turso: {response.status_code} - {response.text}")
    
    return response.json()

# Crear un engine de SQLAlchemy que use Turso
class TursoConnection:
    """Wrapper para conectar Turso con SQLAlchemy."""
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {TURSO_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def execute(self, sql, parameters=None):
        """Ejecuta una consulta SQL."""
        payload = {
            "requests": [{
                "type": "execute",
                "stmt": {"sql": sql}
            }]
        }
        
        if parameters:
            payload["requests"][0]["stmt"]["args"] = parameters
        
        response = requests.post(f"{TURSO_HTTP_URL}/v2/pipeline", 
                                headers=self.headers, 
                                json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Error en Turso: {response.status_code}")
        
        return response.json()
    
    def close(self):
        """Cierra la conexión (no necesario para HTTP)."""
        pass

# Función para crear el engine de SQLAlchemy
def create_turso_engine():
    """Crea un engine de SQLAlchemy para Turso."""
    def get_connection():
        return TursoConnection()
    
    # Usar un pool simple para mantener la compatibilidad con SQLAlchemy
    from sqlalchemy.pool import StaticPool
    return create_engine(
        "sqlite://",
        creator=get_connection,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )

# Crear el engine (usar Turso en producción, SQLite local en desarrollo)
import sys
IS_PRODUCTION = os.getenv("RENDER", "false").lower() == "true"

if IS_PRODUCTION:
    # En Render: Usar Turso
    try:
        engine = create_turso_engine()
        print("✅ Conectado a Turso en la nube")
        
        # Probar la conexión con SELECT 1
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            print(f"✅ Prueba de conexión exitosa: {result.fetchone()}")
    except Exception as e:
        print(f"⚠️ Error conectando a Turso: {e}")
        print("Usando SQLite local como fallback")
        engine = create_engine("sqlite:///./data/bancaria.db", connect_args={"check_same_thread": False})
else:
    # En local: Usar SQLite
    engine = create_engine("sqlite:///./data/bancaria.db", connect_args={"check_same_thread": False})
    print("✅ Usando SQLite local para desarrollo")

# Crear sesión - ELIMINAR auto_close
SessionLocal = sessionmaker(autocommit=False, bind=engine)  # <--- auto_close eliminado

# Base para modelos
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Crea todas las tablas en la base de datos."""
    from app import models
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas correctamente")