"""
Router de Autenticación
Principio: Single Responsibility - Solo maneja endpoints de autenticación
Principio: Dependency Injection - Usa Depends de FastAPI
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_current_active_user, require_admin
from app.models.user import User
from app.repositories.user_repository import get_user_repository, UserRepository
from app.services.auth_service import get_auth_service, AuthService
from app.services.totp_service import TOTPService
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TOTPVerifyRequest,
    UserResponse,
    TOTPSetupResponse,
    TokenResponse,
    MessageResponse,
    ErrorResponse,
    UserUpdateRequest,
    UserListResponse
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Registra un nuevo usuario con nombre y teléfono. Después del registro, el usuario DEBE configurar 2FA antes de poder hacer login."
)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint de registro de usuario
    
    Flujo:
    1. Registrar usuario con nombre y teléfono
    2. Usuario debe llamar a /auth/setup-2fa para configurar 2FA
    3. Usuario debe llamar a /auth/verify-2fa para verificar 2FA
    4. Solo entonces puede hacer login exitoso
    """
    user_repository = get_user_repository(db)
    auth_service = get_auth_service(user_repository)
    
    try:
        user = auth_service.register_user(
            request.email, 
            request.password, 
            request.name,
            request.phone_number,
            request.role
        )
        
        return MessageResponse(
            message="Usuario registrado exitosamente",
            detail=f"Usuario UUID: {user.id}, Nombre: {user.name}, Rol: {user.role}. Debe configurar 2FA antes de poder iniciar sesión. Use /auth/setup-2fa"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post(
    "/setup-2fa",
    response_model=TOTPSetupResponse,
    summary="Configurar autenticación de dos factores",
    description="Genera un secret TOTP y URI para configurar Microsoft Authenticator. El usuario debe escanear el código QR o ingresar el secret manualmente."
)
async def setup_2fa(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint para configurar 2FA
    
    El usuario debe proporcionar email y contraseña.
    Retorna el secret y URI para configurar en Microsoft Authenticator.
    Después debe llamar a /auth/verify-2fa para verificar la configuración.
    """
    user_repository = get_user_repository(db)
    auth_service = get_auth_service(user_repository)
    totp_service = TOTPService()
    
    try:
        # Autenticar usuario
        user = auth_service.authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Generar secret y URI
        secret, provisioning_uri = auth_service.setup_totp(user.id)
        
        return TOTPSetupResponse(
            secret=secret,
            qr_uri=provisioning_uri,
            manual_entry_key=totp_service.format_secret_for_manual_entry(secret)
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post(
    "/verify-2fa",
    response_model=MessageResponse,
    summary="Verificar configuración de 2FA",
    description="Verifica el código TOTP generado por Microsoft Authenticator. Marca el 2FA como verificado si el código es correcto."
)
async def verify_2fa(
    request: UserLoginRequest,
    totp_request: TOTPVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint para verificar la configuración de 2FA
    
    El usuario proporciona email, contraseña y el código de 6 dígitos
    generado por Microsoft Authenticator.
    Si es correcto, marca el 2FA como verificado y el usuario puede hacer login.
    """
    user_repository = get_user_repository(db)
    auth_service = get_auth_service(user_repository)
    
    try:
        # Autenticar usuario
        user = auth_service.authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Verificar código TOTP
        is_valid = auth_service.verify_totp_code(user.id, totp_request.totp_code)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código TOTP inválido"
            )
        
        return MessageResponse(
            message="2FA verificado exitosamente",
            detail="Ahora puede iniciar sesión con su email, contraseña y código TOTP"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Inicia sesión con email, contraseña y código TOTP. CRÍTICO: Solo permite login si el usuario ha verificado su 2FA. Implementa bloqueo de cuenta después de 3 intentos fallidos."
)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint de login con 2FA obligatorio y control de seguridad
    
    REGLAS CRÍTICAS DE NEGOCIO:
    - Verifica si la cuenta está bloqueada ANTES de validar credenciales
    - El usuario DEBE tener 2FA verificado para obtener token de acceso
    - Si no tiene 2FA configurado, retorna error indicando que debe configurarlo
    - Si tiene 2FA pero no proporciona código, retorna error solicitando código
    - Incrementa contador de intentos fallidos en cada error de contraseña o 2FA
    - Bloquea cuenta por 15 minutos después de 3 intentos fallidos
    - Resetea contador en login exitoso
    
    Flujo exitoso:
    1. Usuario proporciona email, password y totp_code
    2. Sistema verifica que cuenta no esté bloqueada
    3. Sistema verifica credenciales
    4. Sistema verifica que 2FA esté configurado
    5. Sistema valida código TOTP
    6. Sistema resetea intentos fallidos
    7. Sistema retorna token de acceso JWT con role y uuid
    """
    user_repository = get_user_repository(db)
    auth_service = get_auth_service(user_repository)
    
    try:
        token, user, message = auth_service.login(
            request.email,
            request.password,
            request.totp_code
        )
        
        # Verificar resultado del login
        if message == "2FA_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debe configurar y verificar 2FA antes de iniciar sesión. Use /auth/setup-2fa"
            )
        
        if message == "TOTP_CODE_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar el código TOTP generado por Microsoft Authenticator"
            )
        
        if message == "LOGIN_SUCCESS" and token:
            user_response = UserResponse.model_validate(user)
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                role=user.role,
                uuid=user.id,
                user=user_response
            )
        
        # Caso no esperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el proceso de login"
        )
    
    except ValueError as e:
        error_message = str(e)
        
        # Si el error es de cuenta bloqueada, retornar 403
        if "bloqueada" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message
            )
        
        # Otros errores de credenciales retornan 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# ============= User Profile Endpoints =============

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener mi información de perfil",
    description="Obtiene la información del usuario autenticado actual."
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint para obtener la información del usuario actual
    
    Requiere:
    - Token JWT válido
    - 2FA verificado
    
    Retorna:
    - Información completa del usuario autenticado
    """
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Actualizar mi información de perfil",
    description="Permite a cualquier usuario autenticado actualizar su propio nombre y/o teléfono."
)
async def update_my_profile(
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint para que el usuario actualice su propia información
    
    Requiere:
    - Token JWT válido
    - 2FA verificado
    
    Permite actualizar:
    - Nombre del usuario
    - Número de teléfono
    
    No permite cambiar:
    - Email
    - Contraseña
    - Rol
    - Configuración 2FA
    """
    user_repository = get_user_repository(db)
    
    try:
        # Validar que al menos un campo esté presente
        if request.name is None and request.phone_number is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar al menos un campo para actualizar"
            )
        
        # Actualizar usuario
        updated_user = user_repository.update_user_info(
            current_user.id,
            name=request.name,
            phone_number=request.phone_number
        )
        
        return UserResponse.model_validate(updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el perfil"
        )


# ============= Admin Endpoints =============

@router.get(
    "/admin/users",
    response_model=UserListResponse,
    summary="Obtener todos los usuarios (Admin)",
    description="Obtiene la lista de todos los usuarios registrados. Requiere rol ADMIN."
)
async def get_all_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Endpoint administrativo para obtener todos los usuarios
    
    Requiere:
    - Token JWT válido
    - Rol ADMIN
    
    Retorna:
    - Lista completa de usuarios con su información
    """
    user_repository = get_user_repository(db)
    
    try:
        users = user_repository.get_all()
        users_response = [UserResponse.model_validate(user) for user in users]
        
        return UserListResponse(
            users=users_response,
            total=len(users_response)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la lista de usuarios"
        )


@router.patch(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    summary="Actualizar información de usuario (Admin)",
    description="Permite a un administrador actualizar el nombre y/o teléfono de cualquier usuario. Requiere rol ADMIN."
)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Endpoint administrativo para actualizar información de usuario
    
    Requiere:
    - Token JWT válido
    - Rol ADMIN
    
    Permite actualizar:
    - Nombre del usuario
    - Número de teléfono
    
    No permite cambiar:
    - Email
    - Contraseña
    - Rol
    - Configuración 2FA
    """
    from uuid import UUID
    
    user_repository = get_user_repository(db)
    
    try:
        # Convertir string a UUID
        try:
            uuid_obj = UUID(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de usuario inválido"
            )
        
        # Verificar que el usuario existe
        user = user_repository.get_by_id(uuid_obj)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Validar que al menos un campo esté presente
        if request.name is None and request.phone_number is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar al menos un campo para actualizar"
            )
        
        # Actualizar usuario
        updated_user = user_repository.update_user_info(
            uuid_obj,
            name=request.name,
            phone_number=request.phone_number
        )
        
        return UserResponse.model_validate(updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el usuario"
        )


@router.delete(
    "/admin/users/{user_id}",
    response_model=MessageResponse,
    summary="Eliminar usuario (Admin)",
    description="Permite a un administrador eliminar cualquier usuario. Requiere rol ADMIN."
)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Endpoint administrativo para eliminar un usuario
    
    Requiere:
    - Token JWT válido
    - Rol ADMIN
    
    Precauciones:
    - El administrador no puede eliminarse a sí mismo
    - La eliminación es permanente
    """
    from uuid import UUID
    
    user_repository = get_user_repository(db)
    
    try:
        # Convertir string a UUID
        try:
            uuid_obj = UUID(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de usuario inválido"
            )
        
        # Verificar que el usuario existe
        user = user_repository.get_by_id(uuid_obj)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Prevenir que el admin se elimine a sí mismo
        if user.id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puede eliminar su propia cuenta de administrador"
            )
        
        # Eliminar usuario
        deleted = user_repository.delete(uuid_obj)
        
        if deleted:
            return MessageResponse(
                message="Usuario eliminado exitosamente",
                detail=f"El usuario {user.email} ha sido eliminado"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el usuario"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el usuario"
        )
