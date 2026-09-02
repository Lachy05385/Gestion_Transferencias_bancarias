# fix_empresa_id_null.py
from database import SessionLocal
from models import models

def fix_empresa_id_null():
    db = SessionLocal()
    
    # Buscar transacciones con empresa_id NULL
    transacciones = db.query(models.Transaccion).filter(
        models.Transaccion.empresa_id.is_(None)
    ).all()
    
    print(f"🔍 Transacciones con empresa_id NULL: {len(transacciones)}")
    
    for t in transacciones:
        # Buscar el usuario de la transacción para obtener su empresa_id
        usuario = db.query(models.Usuario).filter(models.Usuario.id == t.usuario_id).first()
        if usuario and usuario.empresa_id:
            t.empresa_id = usuario.empresa_id
            print(f"✅ Corregida transacción {t.id}: empresa_id = {t.empresa_id}")
        else:
            # Si no se puede determinar, usar empresa por defecto (id=1)
            t.empresa_id = 1
            print(f"⚠️ Transacción {t.id}: usando empresa_id=1 (por defecto)")
    
    db.commit()
    print("✅ Corrección completada")
    db.close()

if __name__ == "__main__":
    fix_empresa_id_null()