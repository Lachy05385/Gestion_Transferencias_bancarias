from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas
from app.utils import parse_transaccion_texto
from datetime import datetime
import json
import re
from typing import List, Optional

def create_transaccion(db: Session, transaccion: schemas.TransaccionCreate, usuario_id: int):
    """
    Crear una transacción manualmente asociada al usuario
    Usando tu schema con todas las validaciones
    """
    # Verificar si ya existe para este usuario
    existente = db.query(models.Transaccion).filter(
        models.Transaccion.numero_transaccion == transaccion.numero_transaccion,
        models.Transaccion.usuario_id == usuario_id
    ).first()
    
    if existente:
        raise ValueError(f"La transacción {transaccion.numero_transaccion} ya existe")
    
    # Crear transacción con todos los campos validados
    db_transaccion = models.Transaccion(
        usuario_id=usuario_id,
        banco=transaccion.banco,
        fecha=transaccion.fecha,  # Ya viene validado DD/MM/YYYY
        beneficiario=transaccion.beneficiario,
        ordenante=transaccion.ordenante,
        monto=transaccion.monto,  # Ya viene validado y redondeado
        moneda=transaccion.moneda,  # Ya viene en mayúsculas
        numero_transaccion=transaccion.numero_transaccion,
        tipo=transaccion.tipo,
        estado=models.EstadoTransaccion.PENDIENTE,
        descripcion=transaccion.descripcion or "",
        etiquetas=json.dumps(transaccion.etiquetas) if transaccion.etiquetas else "[]"
    )
    
    try:
        db.add(db_transaccion)
        db.commit()
        db.refresh(db_transaccion)
        return db_transaccion
    except Exception as e:
        db.rollback()
        raise e

def parse_and_create_transaccion(db: Session, texto: str, tipo: schemas.TipoTransaccion, 
                                 usuario_id: int, descripcion: Optional[str] = None):
    """
    Crear transacción desde texto bancario
    Usa el parser existente pero valida con tu schema
    """
    # Parsear el texto usando tu función existente
    datos = parse_transaccion_texto(texto)
    
    # Extraer datos del parseo
    from app.utils import enmascarar_numero_cuenta
    
    # Validar que tenemos todos los datos necesarios
    required_fields = ['banco', 'fecha', 'beneficiario', 'ordenante', 'monto', 'moneda', 'numero_transaccion']
    for field in required_fields:
        if field not in datos:
            raise ValueError(f"No se pudo extraer el campo '{field}' del texto")
    
    # Validar fecha (debe venir en formato DD/MM/YYYY del parser)
    fecha_pattern = r"^\d{2}/\d{2}/\d{4}$"
    if not re.match(fecha_pattern, datos['fecha']):
        # Intentar convertir si viene en otro formato
        from datetime import datetime
        try:
            # Asumiendo que viene en formato YYYY-MM-DD del parser
            fecha_obj = datetime.strptime(datos['fecha'], '%Y-%m-%d')
            datos['fecha'] = fecha_obj.strftime('%d/%m/%Y')
        except:
            raise ValueError(f"Formato de fecha inválido: {datos['fecha']}")
    
    # Validar monto
    try:
        monto = float(datos['monto'])
        if monto <= 0 or monto > 10000000:
            raise ValueError(f"Monto inválido: {monto}")
        datos['monto'] = round(monto, 2)
    except:
        raise ValueError(f"Monto inválido: {datos['monto']}")
    
    # Validar moneda
    moneda = datos.get('moneda', 'EUR').upper()
    monedas_validas = ['CUP', 'USD', 'EUR', 'MLC']
    if moneda not in monedas_validas:
        moneda = 'EUR'  # Valor por defecto
    datos['moneda'] = moneda
    
    # Crear objeto TransaccionCreate con los datos parseados
    transaccion_data = {
        "banco": datos.get('banco', 'Desconocido'),
        "fecha": datos['fecha'],
        "beneficiario": datos['beneficiario'],
        "ordenante": datos['ordenante'],
        "monto": datos['monto'],
        "moneda": datos['moneda'],
        "numero_transaccion": datos['numero_transaccion'],
        "tipo": tipo,
        "descripcion": descripcion or datos.get('concepto', ''),
        "etiquetas": []
    }
    
    # Validar con el schema
    try:
        transaccion_validada = schemas.TransaccionCreate(**transaccion_data)
    except Exception as e:
        raise ValueError(f"Error validando datos parseados: {str(e)}")
    
    # Verificar si ya existe
    existente = db.query(models.Transaccion).filter(
        models.Transaccion.numero_transaccion == transaccion_validada.numero_transaccion,
        models.Transaccion.usuario_id == usuario_id
    ).first()
    
    if existente:
        raise ValueError(f"La transacción {transaccion_validada.numero_transaccion} ya existe")
    
    # Crear en BD
    db_transaccion = models.Transaccion(
        usuario_id=usuario_id,
        banco=transaccion_validada.banco,
        fecha=transaccion_validada.fecha,
        beneficiario=transaccion_validada.beneficiario,
        ordenante=transaccion_validada.ordenante,
        monto=transaccion_validada.monto,
        moneda=transaccion_validada.moneda,
        numero_transaccion=transaccion_validada.numero_transaccion,
        tipo=transaccion_validada.tipo,
        estado=models.EstadoTransaccion.PENDIENTE,
        descripcion=transaccion_validada.descripcion,
        etiquetas="[]"
    )
    
    try:
        db.add(db_transaccion)
        db.commit()
        db.refresh(db_transaccion)
        return db_transaccion
    except Exception as e:
        db.rollback()
        raise e

def get_transacciones_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 100,
                              tipo: Optional[schemas.TipoTransaccion] = None,
                              estado: Optional[schemas.EstadoTransaccion] = None,
                              banco: Optional[str] = None,
                              moneda: Optional[str] = None,
                              fecha_desde: Optional[str] = None,
                              fecha_hasta: Optional[str] = None):
    """
    Obtener transacciones del usuario con filtros avanzados
    """
    query = db.query(models.Transaccion).filter(
        models.Transaccion.usuario_id == usuario_id
    )
    
    # Aplicar filtros
    if tipo:
        query = query.filter(models.Transaccion.tipo == tipo)
    if estado:
        query = query.filter(models.Transaccion.estado == estado)
    if banco:
        query = query.filter(models.Transaccion.banco.ilike(f"%{banco}%"))
    if moneda:
        query = query.filter(models.Transaccion.moneda == moneda.upper())
    
    # Filtros de fecha (formato DD/MM/YYYY en BD)
    if fecha_desde:
        query = query.filter(models.Transaccion.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(models.Transaccion.fecha <= fecha_hasta)
    
    # Ordenar por fecha de transacción (no procesamiento)
    query = query.order_by(models.Transaccion.fecha.desc())
    
    return query.offset(skip).limit(limit).all()

def get_transaccion(db: Session, transaccion_id: int, usuario_id: int):
    """
    Obtener una transacción verificando propiedad
    """
    return db.query(models.Transaccion).filter(
        models.Transaccion.id == transaccion_id,
        models.Transaccion.usuario_id == usuario_id
    ).first()

def update_transaccion(db: Session, transaccion_id: int, usuario_id: int, 
                       transaccion_update: schemas.TransaccionUpdate):
    """
    Actualizar transacción (solo campos permitidos)
    """
    db_transaccion = get_transaccion(db, transaccion_id, usuario_id)
    if not db_transaccion:
        return None
    
    update_data = transaccion_update.dict(exclude_unset=True)
    
    # Manejar etiquetas como JSON
    if 'etiquetas' in update_data and update_data['etiquetas'] is not None:
        update_data['etiquetas'] = json.dumps(update_data['etiquetas'])
    
    # Actualizar solo campos permitidos
    for key, value in update_data.items():
        if value is not None and hasattr(db_transaccion, key):
            setattr(db_transaccion, key, value)
    
    try:
        db.commit()
        db.refresh(db_transaccion)
        return db_transaccion
    except Exception as e:
        db.rollback()
        raise e

def confirmar_transaccion(db: Session, transaccion_id: int, usuario_id: int):
    """
    Confirmar transacción recibida
    """
    db_transaccion = get_transaccion(db, transaccion_id, usuario_id)
    if not db_transaccion:
        return None
    
    if db_transaccion.tipo == schemas.TipoTransaccion.RECIBIDA:
        db_transaccion.estado = schemas.EstadoTransaccion.CONFIRMADA
        db_transaccion.fecha_confirmacion = datetime.now()
        
        try:
            db.commit()
            db.refresh(db_transaccion)
        except Exception as e:
            db.rollback()
            raise e
    
    return db_transaccion

def get_estadisticas_usuario(db: Session, usuario_id: int):
    """
    Obtener estadísticas detalladas del usuario
    """
    transacciones = db.query(models.Transaccion).filter(
        models.Transaccion.usuario_id == usuario_id
    ).all()
    
    if not transacciones:
        return {
            "total_transacciones": 0,
            "total_enviadas": 0,
            "total_recibidas": 0,
            "balance": 0,
            "por_moneda": {},
            "por_banco": {},
            "pendientes": 0,
            "confirmadas": 0
        }
    
    # Estadísticas por moneda
    por_moneda = {}
    for t in transacciones:
        if t.moneda not in por_moneda:
            por_moneda[t.moneda] = {
                "enviado": 0,
                "recibido": 0,
                "balance": 0
            }
        
        if t.tipo == schemas.TipoTransaccion.ENVIADA:
            por_moneda[t.moneda]["enviado"] += t.monto
        else:
            por_moneda[t.moneda]["recibido"] += t.monto
        
        por_moneda[t.moneda]["balance"] = (
            por_moneda[t.moneda]["recibido"] - por_moneda[t.moneda]["enviado"]
        )
    
    # Estadísticas por banco
    por_banco = {}
    for t in transacciones:
        if t.banco not in por_banco:
            por_banco[t.banco] = {
                "cantidad": 0,
                "monto_total": 0,
                "promedio": 0
            }
        por_banco[t.banco]["cantidad"] += 1
        por_banco[t.banco]["monto_total"] += t.monto
    
    for banco in por_banco:
        por_banco[banco]["promedio"] = (
            por_banco[banco]["monto_total"] / por_banco[banco]["cantidad"]
        )
    
    return {
        "total_transacciones": len(transacciones),
        "total_enviadas": sum(t.monto for t in transacciones if t.tipo == schemas.TipoTransaccion.ENVIADA),
        "total_recibidas": sum(t.monto for t in transacciones if t.tipo == schemas.TipoTransaccion.RECIBIDA),
        "balance": sum(t.monto for t in transacciones if t.tipo == schemas.TipoTransaccion.RECIBIDA) - 
                  sum(t.monto for t in transacciones if t.tipo == schemas.TipoTransaccion.ENVIADA),
        "por_moneda": por_moneda,
        "por_banco": por_banco,
        "pendientes": len([t for t in transacciones if t.estado == schemas.EstadoTransaccion.PENDIENTE]),
        "confirmadas": len([t for t in transacciones if t.estado == schemas.EstadoTransaccion.CONFIRMADA])
    }

def buscar_transacciones(db: Session, usuario_id: int, query: str):
    """
    Búsqueda avanzada de transacciones
    """
    return db.query(models.Transaccion).filter(
        models.Transaccion.usuario_id == usuario_id,
        (
            models.Transaccion.beneficiario.ilike(f"%{query}%") |
            models.Transaccion.ordenante.ilike(f"%{query}%") |
            models.Transaccion.descripcion.ilike(f"%{query}%") |
            models.Transaccion.numero_transaccion.ilike(f"%{query}%") |
            models.Transaccion.banco.ilike(f"%{query}%")
        )
    ).order_by(models.Transaccion.fecha.desc()).all()

def get_transacciones_por_mes(db: Session, usuario_id: int, año: int, mes: int):
    """
    Obtener transacciones de un mes específico
    """
    mes_str = f"{mes:02d}"
    return db.query(models.Transaccion).filter(
        models.Transaccion.usuario_id == usuario_id,
        models.Transaccion.fecha.like(f"%/{mes_str}/{año}")
    ).order_by(models.Transaccion.fecha.desc()).all()
    
    
# app/crud.py

def get_transacciones_enviadas_por_fecha(
    db: Session, 
    usuario_id: int, 
    fecha_inicio: str, 
    fecha_fin: str
):
    """
    Obtiene las transacciones ENVIADAS de un usuario en un rango de fechas
    Las fechas deben estar en formato DD/MM/YYYY
    """
    print(f"🔍 Buscando transacciones ENVIADAS del usuario {usuario_id}")
    print(f"📅 Rango: {fecha_inicio} - {fecha_fin}")
    
    # Validar formato de fechas (opcional pero recomendado)
    try:
        # Verificar que tengan formato DD/MM/YYYY
        dia_i, mes_i, año_i = map(int, fecha_inicio.split('/'))
        dia_f, mes_f, año_f = map(int, fecha_fin.split('/'))
        
        # Crear objetos datetime para comparar (opcional)
        from datetime import datetime
        fecha_inicio_dt = datetime(año_i, mes_i, dia_i)
        fecha_fin_dt = datetime(año_f, mes_f, dia_f)
        
        if fecha_inicio_dt > fecha_fin_dt:
            raise ValueError("La fecha de inicio no puede ser mayor que la fecha fin")
            
    except ValueError as e:
        raise ValueError(f"Formato de fecha inválido. Use DD/MM/YYYY. Error: {str(e)}")
    
    # Consulta a la base de datos
    transacciones = db.query(models.Transaccion).filter(
        models.Transaccion.usuario_id == usuario_id,
        models.Transaccion.tipo == "enviada",  # Solo enviadas
        models.Transaccion.fecha >= fecha_inicio,
        models.Transaccion.fecha <= fecha_fin
    ).order_by(models.Transaccion.fecha.desc()).all()
    
    print(f"✅ Encontradas {len(transacciones)} transacciones")
    return transacciones

def get_transacciones_recibidas_por_fecha(
    db: Session, 
    usuario_id: int, 
    fecha_inicio: str, 
    fecha_fin: str
):
    """
    Obtiene las transacciones RECIBIDAS de un usuario en un rango de fechas
    Las fechas deben estar en formato DD/MM/YYYY
    """
    transacciones = db.query(models.Transaccion).filter(
        models.Transaccion.usuario_id == usuario_id,
        models.Transaccion.tipo == "recibida",  # Solo recibidas
        models.Transaccion.fecha >= fecha_inicio,
        models.Transaccion.fecha <= fecha_fin
    ).order_by(models.Transaccion.fecha.desc()).all()
    
    return transacciones