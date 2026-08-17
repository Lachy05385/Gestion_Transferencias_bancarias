# app/auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import models, schemas
from .database import get_db
import os
import bcrypt  # ✅ Usar bcrypt directamente, sin passlib

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta_super_segura_aqui_cambiar_en_produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ✅ Función para generar hash con bcrypt directo
def get_password_hash(password: str) -> str:
    """
    Genera un hash de la contraseña usando bcrypt directamente.
    Trunca la contraseña a 72 bytes si es necesario (límite de bcrypt).
    """
    try:
        # Truncar a 72 bytes (límite de bcrypt)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Generar salt y hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"❌ Error generando hash: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar hash: {str(e)}"
        )

# ✅ Función para verificar contraseña con bcrypt directo
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña contra su hash usando bcrypt directamente.
    Trunca la contraseña a 72 bytes si es necesario.
    """
    try:
        # Truncar a 72 bytes (límite de bcrypt)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Verificar
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"❌ Error verificando: {e}")
        return False

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        print(f"❌ Usuario no encontrado: {email}")
        return False
    print(f"✅ Usuario encontrado: {user.email}")
    if not verify_password(password, user.hashed_password):
        print(f"❌ Contraseña incorrecta para: {email}")
        return False
    print(f"✅ Autenticación exitosa para: {email}")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar token: {str(e)}"
        )

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"🔍 Decodificando token: {token[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            print("❌ Token no contiene email")
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
        print(f"✅ Token válido para: {email}")
    except JWTError as e:
        print(f"❌ Error decodificando token: {e}")
        raise credentials_exception
    
    user = db.query(models.Usuario).filter(models.Usuario.email == token_data.email).first()
    if user is None:
        print(f"❌ Usuario no encontrado en BD: {token_data.email}")
        raise credentials_exception
    
    print(f"✅ Usuario encontrado: {user.email} (ID: {user.id})")
    return user

async def get_current_user_from_token(token: str, db: Session):
    """
    Obtiene el usuario actual a partir de un token JWT (para uso manual).
    """
    from jose import JWTError, jwt
    from fastapi import HTTPException, status
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"🔍 Verificando token manual: {token[:30]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        print(f"📧 Email del token: {email}")
        
        if email is None:
            print("❌ Token no contiene email")
            raise credentials_exception
            
    except jwt.ExpiredSignatureError:
        print("❌ Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except JWTError as e:
        print(f"❌ Error decodificando token: {str(e)}")
        raise credentials_exception
    
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if user is None:
        print(f"❌ Usuario no encontrado: {email}")
        raise credentials_exception
    
    print(f"✅ Usuario encontrado: {user.email} (ID: {user.id})")
    return user

async def get_current_active_user(current_user: models.Usuario = Depends(get_current_user)):
    if not current_user.esta_activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user