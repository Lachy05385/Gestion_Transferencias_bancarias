import os
from app.auth import get_password_hash
from app.database import SessionLocal
from app import models
from pathlib import Path

# Usar credenciales fijas para SQLite (sin .env)
USER_ADMIN = "admin@contaflow.com"
AD_PASSWORD = "Admin123!"

#print("="*50)
#print("Usuario Admin:", USER_ADMIN)
#print("Contraseña:", AD_PASSWORD)
#print("="*50)

def crear_empresa_y_admin():
    db = SessionLocal()
    
    try:
        # 1. Crear empresa principal
        nit_principal = "900000001"
        empresa = db.query(models.Empresa).filter(models.Empresa.nit == nit_principal).first()
        
        if not empresa:
            empresa = models.Empresa(
                nombre="Empresa Principal ContaFlow",
                nit=nit_principal,
                direccion="Calle Principal #123",
                telefono="555-1234"
            )
            db.add(empresa)
            db.commit()
            db.refresh(empresa)
            print(f"✅ Empresa creada con ID: {empresa.id} - NIT: {empresa.nit}")
        else:
            print(f"📌 Usando empresa existente: {empresa.nombre} (ID: {empresa.id})")
        
        # 2. Crear usuario administrador
        admin = db.query(models.Usuario).filter(
            models.Usuario.email == USER_ADMIN,
            models.Usuario.empresa_id == empresa.id
        ).first()
        
        if not admin:
            admin = models.Usuario(
                email=USER_ADMIN,
                nombre="Admin",
                apellido="Sistema",
                hashed_password=get_password_hash(AD_PASSWORD),
                esta_activo=True,
                rol="admin",
                empresa_id=empresa.id
            )
            db.add(admin)
            db.commit()
            print("✅ Usuario admin creado exitosamente")
        else:
            print("⚠️ El usuario admin ya existe para esta empresa.")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_empresa_y_admin()