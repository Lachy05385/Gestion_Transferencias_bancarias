

# Configurar CryptContext con Argon2 - VERSIÓN CORREGIDA
# Quitamos el parámetro 'encoding' que no es soportado
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import models, schemas
from .database import get_db
import os

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta_super_segura_aqui_cambiar_en_produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CAMBIO IMPORTANTE: Usar bcrypt en lugar de Argon2
pwd_context = CryptContext(
    schemes=["bcrypt"],  # <--- Cambio: bcrypt en lugar de argon2
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str:
    """Genera un hash de la contraseña usando bcrypt."""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar hash de contraseña: {str(e)}"
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash usando bcrypt."""
    try:
        print(f"🔐 Verificando password...")
        plain_password = str(plain_password).strip()
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"  Resultado: {result}")
        return result
    except Exception as e:
        print(f"❌ Error verifying: {str(e)}")
        return False

# El resto del código (authenticate_user, create_access_token, etc.) 
# permanece EXACTAMENTE IGUAL

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
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

# Dependencia para obtener usuario actual
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.Usuario).filter(models.Usuario.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    print(user)
    return user

async def get_current_active_user(current_user: models.Usuario = Depends(get_current_user)):
    if not current_user.esta_activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

async def get_current_user_from_token(token: str, db: Session):
    """
    Obtiene el usuario actual a partir de un token JWT (para uso manual)
    Esta función es para cuando recibes el token como parámetro, no del header
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
        
        # Usar las mismas variables de configuración
        from .auth import SECRET_KEY, ALGORITHM
        
        # Decodificar token
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
    
    # Buscar usuario en BD
    from . import models
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    
    if user is None:
        print(f"❌ Usuario no encontrado: {email}")
        raise credentials_exception
    
    print(f"✅ Usuario encontrado: {user.email} (ID: {user.id})")
    return user