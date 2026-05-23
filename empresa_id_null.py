# fix_empresa_id_null.py
from app.database import SessionLocal
from app import models

def fix_empresa_id_null():
    db = SessionLocal()
    
    # Actualiza todas las transacciones con empresa_id = NULL
    transacciones_null = db.query(models.Transaccion).filter(
        models.Transaccion.empresa_id.is_(None)
    ).all()

    for t in transacciones_null:
        # Intenta obtener la empresa del usuario relacionado
        if t.usuario and t.usuario.empresa_id:
            t.empresa_id = t.usuario.empresa_id
        else:
            # Si no se puede, asigna un ID de empresa por defecto (por ejemplo, 1)
            t.empresa_id = 1
        print(f"✅ Corregida transacción {t.id}: empresa_id = {t.empresa_id}")

    db.commit()
    db.close()

if __name__ == "__main__":
    fix_empresa_id_null()