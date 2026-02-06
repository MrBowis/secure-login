"""
Dependencies para autenticación
Principio: Single Responsibility - Solo maneja verificación de tokens JWT
"""
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import get_user_repository
from app.services.auth_service import get_auth_service


# Security scheme para JWT
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obtener el usuario actual desde el token JWT
    
    Args:
        credentials: Credenciales HTTP Bearer (token JWT)
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    # Extraer token
    token = credentials.credentials
    
    # Crear servicios
    user_repository = get_user_repository(db)
    auth_service = get_auth_service(user_repository)
    
    # Decodificar token
    payload = auth_service.decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Obtener user_id del payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta información del usuario",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Buscar usuario en base de datos (convertir string a UUID)
    try:
        user_uuid = UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: formato de ID incorrecto",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = user_repository.get_by_id(user_uuid)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency para obtener usuario activo (con 2FA verificado)
    
    Args:
        current_user: Usuario actual
        
    Returns:
        Usuario activo
        
    Raises:
        HTTPException: Si el usuario no tiene 2FA verificado
    """
    if not current_user.totp_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="2FA no verificado. Complete la verificación de 2FA."
        )
    
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency para requerir rol ADMIN
    
    Args:
        current_user: Usuario actual
        
    Returns:
        Usuario con rol ADMIN
        
    Raises:
        HTTPException: Si el usuario no es ADMIN
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol de administrador"
        )
    
    return current_user
