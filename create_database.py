import os
import sys
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Leer configuración
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Validar que existan las variables necesarias
if not all([DB_NAME, DB_USER, DB_PASSWORD]):
    logger.error("Faltan variables de entorno: DB_NAME, DB_USER, DB_PASSWORD")
    sys.exit(1)

def create_database():
    """Crea la base de datos si no existe."""
    # Conectar a la base de datos por defecto 'postgres'
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Verificar si la base de datos ya existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()

        if not exists:
            # Crear la base de datos
            cursor.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(DB_NAME),
                sql.Identifier(DB_USER)
            ))
            logger.info(f"✅ Base de datos '{DB_NAME}' creada exitosamente.")
        else:
            logger.info(f"📌 La base de datos '{DB_NAME}' ya existe.")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"❌ Error al crear la base de datos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_database()