import os
from app.auth import get_password_hash
from app.database import SessionLocal
from app import models
from pathlib import Path
from dotenv import load_dotenv

# Obtiene la carpeta donde está este archivo (crear_admin.py)
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

#

# Leer variables de entorno (con valores por defecto si no existen)
USER_ADMIN = os.getenv("USER_ADMIN")
if not USER_ADMIN:
    raise ValueError("La variable de entorno USER_ADMIN no está definida")

AD_PASSWORD = os.getenv("AD_PASSWORD")
if not AD_PASSWORD:
    raise ValueError("La variable de entorno AD_PASSWORD no está definida")
def crear_empresa_y_admin():
    db = SessionLocal()
    
    try:
        
        nit_principal = "900000001"  # Cambia por el NIT real que quieras usar
        empresa = db.query(models.Empresa).filter(models.Empresa.nit == nit_principal).first()
        
        if not empresa:
            # Si no existe, la creamos con datos por defecto (puedes pedir inputs)
            empresa = models.Empresa(
                nombre="Empresa Principal ContaFlow",
                nit=nit_principal,
                direccion="Calle Principal #123",
                telefono="555-1234"
                # fecha_creacion se asigna automáticamente con default=datetime.utcnow
            )
            db.add(empresa)
            db.commit()
            db.refresh(empresa)
            print(f"✅ Empresa creada con ID: {empresa.id} - NIT: {empresa.nit}")
        else:
            print(f"📌 Usando empresa existente: {empresa.nombre} (ID: {empresa.id})")
        
        # 2. Crear usuario administrador asociado a esa empresa
        # Verificar si ya existe un admin con ese email para esa empresa
        admin = db.query(models.Usuario).filter(
            models.Usuario.email == "admin@contaflow.com",
            models.Usuario.empresa_id == empresa.id
        ).first()
        
        if not admin:
            admin = models.Usuario(
                email=USER_ADMIN,
                nombre="admin",
                apellido="Sistema",
                hashed_password=get_password_hash(AD_PASSWORD),
                esta_activo=True,
                rol="admin",
                empresa_id=empresa.id
            )
            db.add(admin)
            db.commit()
            print("✅ Usuario admin creado: admin@contaflow.com / Admin123!")
        else:
            print("⚠️ El usuario admin ya existe para esta empresa.")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    
    crear_empresa_y_admin()