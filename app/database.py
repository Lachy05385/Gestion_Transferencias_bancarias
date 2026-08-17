# app/database.py
import os
import sys
import requests
import json
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.pool as pool
from sqlalchemy.engine import Engine

# Detectar entorno
IS_PRODUCTION = os.getenv("RENDER", "false").lower() == "true"

if IS_PRODUCTION:
    TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
    TURSO_TOKEN = os.getenv("TURSO_TOKEN")
    
    if not TURSO_DATABASE_URL or not TURSO_TOKEN:
        raise ValueError("❌ Variables TURSO_DATABASE_URL y TURSO_TOKEN son obligatorias en Render")
    
    class TursoConnection:
        """Wrapper completo para Turso compatible con SQLAlchemy."""
        def __init__(self):
            self.headers = {
                "Authorization": f"Bearer {TURSO_TOKEN}",
                "Content-Type": "application/json"
            }
            self.url = TURSO_DATABASE_URL.replace("libsql://", "https://")
            self.closed = False
            self.transaction_active = False
        
        def cursor(self):
            """Devuelve un cursor compatible con SQLAlchemy."""
            return TursoCursor(self)
        
        def execute(self, sql, parameters=None):
            """Ejecuta una consulta SQL y devuelve un cursor."""
            cursor = self.cursor()
            cursor.execute(sql, parameters)
            return cursor
        
        def commit(self):
            """No es necesario para Turso (autocommit), pero se mantiene por compatibilidad."""
            self.transaction_active = False
            return self
        
        def rollback(self):
            """No es necesario para Turso (autocommit), pero se mantiene por compatibilidad."""
            self.transaction_active = False
            return self
        
        def close(self):
            """Cierra la conexión."""
            self.closed = True
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()
    
    class TursoCursor:
        """Cursor compatible con SQLAlchemy para Turso."""
        def __init__(self, connection):
            self.connection = connection
            self.arraysize = 1
            self._results = []
            self._rowcount = -1
            self._lastrowid = None
            self._description = None
            self.closed = False
        
        def execute(self, sql, parameters=None):
            """Ejecuta una consulta SQL."""
            if self.closed:
                raise Exception("Cursor already closed")
            
            # Preparar payload para Turso
            payload = {"requests": [{"type": "execute", "stmt": {"sql": sql}}]}
            
            # Manejar parámetros
            if parameters:
                args = []
                if isinstance(parameters, dict):
                    # Si es dict, ordenar por posición
                    for key, value in parameters.items():
                        args.append(self._convert_param(value))
                elif isinstance(parameters, (list, tuple)):
                    for value in parameters:
                        args.append(self._convert_param(value))
                else:
                    args.append(self._convert_param(parameters))
                
                if args:
                    payload["requests"][0]["stmt"]["args"] = args
            
            try:
                response = requests.post(
                    f"{self.connection.url}/v2/pipeline",
                    headers=self.connection.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code != 200:
                    raise Exception(f"Error en Turso: {response.status_code} - {response.text}")
                
                data = response.json()
                self._results = []
                self._rowcount = 0
                self._description = None
                
                # Procesar resultados
                if "results" in data and data["results"]:
                    result = data["results"][0]
                    if "response" in result and "result" in result["response"]:
                        result_data = result["response"]["result"]
                        
                        # Obtener columnas (description)
                        if "cols" in result_data:
                            self._description = [
                                (col.get("name"), None, None, None, None, None, None)
                                for col in result_data["cols"]
                            ]
                        
                        # Obtener filas
                        rows = result_data.get("rows", [])
                        for row in rows:
                            row_values = []
                            for col in row:
                                row_values.append(col.get("value"))
                            self._results.append(tuple(row_values))
                        
                        self._rowcount = len(self._results)
                        
                        # Obtener last_insert_rowid
                        if "last_insert_rowid" in result_data:
                            self._lastrowid = result_data["last_insert_rowid"]
                
                return self
                
            except requests.exceptions.Timeout:
                raise Exception("Timeout conectando a Turso")
            except Exception as e:
                raise Exception(f"Error en ejecución: {str(e)}")
        
        def _convert_param(self, value):
            """Convierte un valor de Python al formato de Turso."""
            if value is None:
                return {"type": "null", "value": None}
            elif isinstance(value, bool):
                return {"type": "integer", "value": "1" if value else "0"}
            elif isinstance(value, int):
                return {"type": "integer", "value": str(value)}
            elif isinstance(value, float):
                return {"type": "text", "value": str(value)}
            else:
                return {"type": "text", "value": str(value)}
        
        def fetchone(self):
            """Obtiene una fila del resultado."""
            if self._results:
                return self._results.pop(0)
            return None
        
        def fetchall(self):
            """Obtiene todas las filas del resultado."""
            return self._results
        
        def fetchmany(self, size=None):
            """Obtiene varias filas del resultado."""
            if size is None:
                size = self.arraysize
            if self._results:
                result = self._results[:size]
                self._results = self._results[size:]
                return result
            return []
        
        @property
        def rowcount(self):
            """Número de filas afectadas."""
            return self._rowcount
        
        @property
        def lastrowid(self):
            """Último ID insertado."""
            return self._lastrowid
        
        @property
        def description(self):
            """Descripción de columnas."""
            return self._description
        
        def close(self):
            """Cierra el cursor."""
            self.closed = True
    
    # Función para crear la conexión Turso
    def create_turso_connection():
        return TursoConnection()
    
    # Crear el engine con SQLAlchemy
    engine = create_engine(
        "sqlite://",
        creator=create_turso_connection,
        poolclass=pool.StaticPool,
        connect_args={"check_same_thread": False}
    )
    print("✅ Conectado a Turso en la nube")
    
else:
    # En local: Usar SQLite
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
    """Crea todas las tablas en la base de datos."""
    from app import models
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas correctamente")

# Evento para deshabilitar funciones no soportadas por Turso
@event.listens_for(engine, "connect")
def on_connect(dbapi_connection, connection_record):
    """Deshabilita funciones SQLite que Turso no soporta."""
    # Turso no soporta regexp, así que lo deshabilitamos
    if hasattr(dbapi_connection, "create_function"):
        try:
            dbapi_connection.create_function("regexp", 2, lambda x, y: 0)
        except:
            pass