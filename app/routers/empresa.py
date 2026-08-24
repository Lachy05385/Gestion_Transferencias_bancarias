# routers/empresa.py
# routers/empresa.py
from typing import List
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Empresa as EmpresaModel
from app.models import Usuario as UsuarioModel
from app.schemas import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResponse
)
from app.auth import get_current_user

router = APIRouter(prefix="/empresas", tags=["empresas"])

# ========== VERIFICAR PERMISOS (SOLO ADMIN) ==========
def get_admin_user(current_user: UsuarioModel = Depends(get_current_user)):
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can access this resource")
    return current_user

# ========== CRUD BÁSICO ==========
@router.post("/", response_model=EmpresaResponse)
def create_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_admin_user)
):
    # Verificar NIT único
    existing = db.query(EmpresaModel).filter(EmpresaModel.nit == empresa.nit).first()
    if existing:
        raise HTTPException(status_code=400, detail="NIT already exists")
    
    db_empresa = EmpresaModel(**empresa.model_dump())
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

@router.get("/", response_model=List[EmpresaResponse])
def list_empresas(
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, description="Buscar por nombre o NIT"),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    query = db.query(EmpresaModel)
    if search:
        query = query.filter(
            (EmpresaModel.nombre.ilike(f"%{search}%")) |
            (EmpresaModel.nit.ilike(f"%{search}%"))
        )
    empresas = query.offset(skip).limit(limit).all()
    return empresas

@router.get("/{empresa_id}", response_model=EmpresaResponse)
def get_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa not found")
    return empresa

@router.put("/{empresa_id}", response_model=EmpresaResponse)
def update_empresa(
    empresa_id: int,
    empresa_update: EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_admin_user)
):
    empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa not found")
    
    # Si se actualiza NIT, verificar que no exista otro
    if empresa_update.nit and empresa_update.nit != empresa.nit:
        existing = db.query(EmpresaModel).filter(EmpresaModel.nit == empresa_update.nit).first()
        if existing:
            raise HTTPException(status_code=400, detail="NIT already exists")
    
    update_data = empresa_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(empresa, field, value)
    
    db.commit()
    db.refresh(empresa)
    return empresa

@router.delete("/{empresa_id}")
def delete_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_admin_user)
):
    empresa = db.query(EmpresaModel).filter(EmpresaModel.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa not found")
    
    # Verificar si tiene relaciones (usuarios o transacciones)
    if empresa.usuarios:
        raise HTTPException(status_code=400, detail="Cannot delete empresa with associated usuarios")
    if empresa.transacciones:
        raise HTTPException(status_code=400, detail="Cannot delete empresa with associated transacciones")
    
    db.delete(empresa)
    db.commit()
    return {"message": "Empresa deleted successfully"}

# ========== EXPORTAR EMPRESAS A CSV ==========
@router.get("/export/csv")
def export_empresas_csv(
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_admin_user)
):
    """
    Exporta todas las empresas a un archivo CSV.
    """
    empresas = db.query(EmpresaModel).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Cabeceras
    writer.writerow([
        "id", "nombre", "nit", "direccion", "telefono", "fecha_creacion"
    ])
    
    # Datos
    for e in empresas:
        writer.writerow([
            e.id,
            e.nombre,
            e.nit,
            e.direccion or "",
            e.telefono or "",
            e.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S") if e.fecha_creacion else ""
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=empresas_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

# ========== IMPORTAR EMPRESAS DESDE CSV ==========
@router.post("/import/csv")
def import_empresas_csv(
    file: UploadFile = File(...),
    update_existing: bool = Query(True, description="Si True, actualiza empresas existentes. Si False, omite duplicados."),
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_admin_user)
):
    """
    Importa empresas desde un archivo CSV.
    
    - Si NIT existe y update_existing=True: actualiza la empresa.
    - Si NIT existe y update_existing=False: omite la empresa.
    - Si NIT no existe: crea una nueva empresa.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser CSV")
    
    try:
        contents = file.file.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
    
    stats = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": []
    }
    
    for row_num, row in enumerate(csv_reader, start=2):
        try:
            nit = row.get("nit", "").strip()
            nombre = row.get("nombre", "").strip()
            
            if not nit or not nombre:
                stats["errors"].append(f"Fila {row_num}: NIT y nombre son obligatorios")
                continue
            
            # Buscar empresa existente por NIT
            existing = db.query(EmpresaModel).filter(EmpresaModel.nit == nit).first()
            
            if existing:
                if update_existing:
                    # Actualizar empresa existente
                    existing.nombre = nombre
                    existing.direccion = row.get("direccion", "").strip() or None
                    existing.telefono = row.get("telefono", "").strip() or None
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            else:
                # Crear nueva empresa
                new_empresa = EmpresaModel(
                    nombre=nombre,
                    nit=nit,
                    direccion=row.get("direccion", "").strip() or None,
                    telefono=row.get("telefono", "").strip() or None
                )
                db.add(new_empresa)
                stats["created"] += 1
        
        except Exception as e:
            stats["errors"].append(f"Fila {row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "message": "Importación completada",
        "stats": stats,
        "total_rows": row_num - 1 if stats["errors"] else row_num - 1
    }

# ========== OBTENER EMPRESA POR NIT ==========
@router.get("/nit/{nit}", response_model=EmpresaResponse)
def get_empresa_by_nit(
    nit: str,
    db: Session = Depends(get_db),
    current_user: UsuarioModel = Depends(get_current_user)
):
    empresa = db.query(EmpresaModel).filter(EmpresaModel.nit == nit).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa not found")
    return empresa