from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base

class TipoTransaccion(str, enum.Enum):
    ENVIADA = "enviada"
    RECIBIDA = "recibida"

class EstadoTransaccion(str, enum.Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    RECHAZADA = "rechazada"
    
# creando entidad     
class Entidad(Base):
    __tablename__ = "entidad"
    id = Column(Integer, primary_key=True,index=True)
    name = Column(String, nullable=False,unique=True)
    
    
    pass
#usuario
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    esta_activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relación con transacciones
    transacciones = relationship("Transaccion", back_populates="usuario")

class Transaccion(Base):
    __tablename__ = "transacciones"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Datos del usuario
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Datos de la transacción
    banco = Column(String, nullable=False)
    fecha = Column(String, nullable=False)
    beneficiario = Column(String, nullable=False)
    ordenante = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    moneda = Column(String, nullable=False)
    numero_transaccion = Column(String, unique=True, nullable=False, index=True)
    
    # Clasificación del usuario
    tipo = Column(Enum(TipoTransaccion), nullable=False)
    estado = Column(Enum(EstadoTransaccion), default=EstadoTransaccion.PENDIENTE)
    
    # Metadatos
    descripcion = Column(String, default="")
    etiquetas = Column(String, default="")  # JSON string de etiquetas
    fecha_procesamiento = Column(DateTime(timezone=True), server_default=func.now())
    fecha_confirmacion = Column(DateTime(timezone=True), nullable=True)
    
    # Relación
    usuario = relationship("Usuario", back_populates="transacciones")

class Etiqueta(Base):
    __tablename__ = "etiquetas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    color = Column(String, default="#007bff")
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Relación muchos a muchos con transacciones
    transacciones = relationship("Transaccion", secondary="transaccion_etiquetas", backref="etiquetas_rel")

class TransaccionEtiqueta(Base):
    __tablename__ = "transaccion_etiquetas"
    
    transaccion_id = Column(Integer, ForeignKey("transacciones.id"), primary_key=True)
    etiqueta_id = Column(Integer, ForeignKey("etiquetas.id"), primary_key=True)

# Crear las tablas
def create_tables():
    Base.metadata.create_all(bind=engine)