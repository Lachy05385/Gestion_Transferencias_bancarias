# app/schemas.py (versión temporal para debugging)
from pydantic import BaseModel, field_validator, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re

class TipoTransaccion(str, Enum):
    ENVIADA = "enviada"
    RECIBIDA = "recibida"

class EstadoTransaccion(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    RECHAZADA = "rechazada"

# Esquemas para autenticación - VERSIÓN SIMPLIFICADA TEMPORAL
class UserCreate(BaseModel):
    email: str  # Cambiado temporalmente de EmailStr a str
    nombre: str
    apellido: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validar_email(cls, v: str) -> str:
        """Validación simple de email"""
        v = v.strip().lower()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Email inválido')
        return v
    
    @field_validator('nombre', 'apellido')
    @classmethod
    def validar_nombre_apellido(cls, v: str) -> str:
        """Validación simplificada"""
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Debe tener al menos 2 caracteres')
        return v.title()
    
    @field_validator('password')
    @classmethod
    def validar_password(cls, v: str) -> str:
        """Validación simplificada"""
        v = v.strip()
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v

class UserLogin(BaseModel):
    email: str  # Cambiado temporalmente
    password: str
    
    @field_validator('email')
    @classmethod
    def validar_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Email inválido')
        return v

# ... (mantén el resto del código igual o simplifica temporalmente) ...