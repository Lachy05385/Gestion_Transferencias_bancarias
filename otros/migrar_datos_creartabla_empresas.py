

import sqlite3
from datetime import datetime

def crear_tablas():
    """Crear tablas si no existen"""
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    
    # Crear tabla empresas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            nit TEXT UNIQUE NOT NULL,
            direccion TEXT,
            telefono TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear empresa por defecto
    cursor.execute('''
        INSERT OR IGNORE INTO empresas (nombre, nit, fecha_creacion)
        VALUES ('Empresa Principal', 'NIT-DEFAULT-001', ?)
    ''', (datetime.now(),))
    
    conn.commit()
    conn.close()
    print("✅ Tablas creadas")

def agregar_columnas():
    """Agregar columnas necesarias"""
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    
    # Obtener empresa por defecto
    cursor.execute("SELECT id FROM empresas WHERE nit = 'NIT-DEFAULT-001'")
    empresa_id = cursor.fetchone()[0]
    
    # Agregar columna empresa_id a usuarios
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN empresa_id INTEGER DEFAULT 1")
        print("✅ Columna empresa_id agregada a usuarios")
    except sqlite3.OperationalError:
        print("⚠️ Columna empresa_id ya existe en usuarios")
    
    # Agregar columna empresa_id a transacciones
    try:
        cursor.execute("ALTER TABLE transacciones ADD COLUMN empresa_id INTEGER DEFAULT 1")
        print("✅ Columna empresa_id agregada a transacciones")
    except sqlite3.OperationalError:
        print("⚠️ Columna empresa_id ya existe en transacciones")
    
    # Actualizar registros existentes
    cursor.execute("UPDATE usuarios SET empresa_id = ? WHERE empresa_id IS NULL", (empresa_id,))
    cursor.execute("UPDATE transacciones SET empresa_id = ? WHERE empresa_id IS NULL", (empresa_id,))
    
    conn.commit()
    conn.close()
    print("✅ Columnas actualizadas")

def verificar_estructura():
    """Verificar que todo esté correcto"""
    conn = sqlite3.connect('bancaria.db')
    cursor = conn.cursor()
    
    # Verificar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [t[0] for t in cursor.fetchall()]
    print(f"\n📋 Tablas en la base de datos: {tablas}")
    
    # Verificar columnas de usuarios
    cursor.execute("PRAGMA table_info(usuarios)")
    columnas_usuarios = [c[1] for c in cursor.fetchall()]
    print(f"\n📋 Columnas en usuarios: {columnas_usuarios}")
    
    # Verificar columnas de transacciones
    cursor.execute("PRAGMA table_info(transacciones)")
    columnas_transacciones = [c[1] for c in cursor.fetchall()]
    print(f"\n📋 Columnas en transacciones: {columnas_transacciones}")
    
    # Contar registros
    cursor.execute("SELECT COUNT(*) FROM empresas")
    count_empresas = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count_usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM transacciones")
    count_transacciones = cursor.fetchone()[0]
    
    print(f"\n📊 Registros:")
    print(f"   Empresas: {count_empresas}")
    print(f"   Usuarios: {count_usuarios}")
    print(f"   Transacciones: {count_transacciones}")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migración a estructura con Empresa")
    print("="*50)
    
    crear_tablas()
    agregar_columnas()
    verificar_estructura()
    
    print("\n✅ Migración completada")
    print("   Reinicia tu servidor FastAPI")