# crear_admin.py
from app.auth import get_password_hash
from app.database import SessionLocal
from app import models

def crear_admin():
    db = SessionLocal()
    
    admin = models.Usuario(
        email="admin@localhost",
        nombre="Admin",
        apellido="Sistema",
        hashed_password=get_password_hash("admin123"),
        esta_activo=True,
        rol="admin"  # 👈 Importante
    )
    
    db.add(admin)
    db.commit()
    print("✅ Usuario admin creado: admin@localhost / admin123")
    db.close()

if __name__ == "__main__":
    crear_admin()