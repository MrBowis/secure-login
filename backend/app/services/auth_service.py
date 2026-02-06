"""
Servicio de Autenticación
Principio: Single Responsibility - Solo maneja lógica de autenticación
Principio: Dependency Inversion - Depende de abstracciones (Repository, TOTP)
Principio: Open/Closed - Extensible sin modificar código existente
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID
import jwt
from pwdlib import PasswordHash

from app.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.totp_service import TOTPService


class AuthService:
    """
    Servicio de autenticación con soporte para 2FA obligatorio
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        totp_service: TOTPService
    ):
        """
        Constructor con inyección de dependencias
        
        Args:
            user_repository: Repositorio de usuarios
            totp_service: Servicio TOTP
        """
        self.user_repository = user_repository
        self.totp_service = totp_service
        self.password_hash = PasswordHash.recommended()
    
    def hash_password(self, password: str) -> str:
        """
        Hashea una contraseña usando pwdlib
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Contraseña hasheada
        """
        return self.password_hash.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica una contraseña contra su hash
        
        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Contraseña hasheada
            
        Returns:
            True si la contraseña es correcta
        """
        return self.password_hash.verify(plain_password, hashed_password)
    
    def create_access_token(self, user: User) -> str:
        """
        Crea un token JWT de acceso
        
        Args:
            user: Usuario para el que se crea el token
            
        Returns:
            Token JWT
        """
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
        
        payload = {
            "sub": str(user.id),
            "uuid": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "totp_verified": user.totp_verified
        }
        
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        return token
    
    def decode_access_token(self, token: str) -> Optional[dict]:
        """
        Decodifica y valida un token JWT
        
        Args:
            token: Token JWT
            
        Returns:
            Payload del token o None si es inválido
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.PyJWTError:
            return None
    
    def register_user(self, email: str, password: str, name: str, phone_number: Optional[str] = None, role: str = "CLIENT") -> User:
        """
        Registra un nuevo usuario
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            name: Nombre completo del usuario
            phone_number: Número de teléfono (opcional)
            role: Rol del usuario (ADMIN o CLIENT)
            
        Returns:
            Usuario creado
            
        Raises:
            ValueError: Si el email ya está registrado
        """
        # Verificar si el email ya existe
        if self.user_repository.exists_by_email(email):
            raise ValueError("El email ya está registrado")
        
        # Hashear contraseña
        hashed_password = self.hash_password(password)
        
        # Crear usuario
        user = self.user_repository.create(email, hashed_password, name, phone_number, role)
        
        return user
    
    def setup_totp(self, user_id: UUID) -> Tuple[str, str]:
        """
        Configura 2FA para un usuario (genera secret y URI)
        
        Args:
            user_id: UUID del usuario
            
        Returns:
            Tupla (secret, provisioning_uri)
            
        Raises:
            ValueError: Si el usuario no existe
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        # Generar nuevo secret
        secret = self.totp_service.generate_secret()
        
        # Guardar secret en la base de datos
        self.user_repository.update_totp_secret(user_id, secret)
        
        # Generar URI para código QR
        provisioning_uri = self.totp_service.get_provisioning_uri(user.email, secret)
        
        return secret, provisioning_uri
    
    def verify_totp_code(self, user_id: UUID, totp_code: str) -> bool:
        """
        Verifica un código TOTP y marca el 2FA como verificado si es correcto
        
        Args:
            user_id: UUID del usuario
            totp_code: Código TOTP a verificar
            
        Returns:
            True si el código es válido
            
        Raises:
            ValueError: Si el usuario no existe o no tiene secret configurado
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        if not user.totp_secret:
            raise ValueError("2FA no configurado para este usuario")
        
        # Verificar código
        is_valid = self.totp_service.verify_totp(user.totp_secret, totp_code)
        
        # Si es válido y no estaba verificado, marcar como verificado
        if is_valid and not user.totp_verified:
            self.user_repository.verify_totp(user_id)
        
        return is_valid
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Autentica un usuario por email y contraseña
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Usuario si las credenciales son correctas, None en caso contrario
        """
        user = self.user_repository.get_by_email(email)
        
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def login(self, email: str, password: str, totp_code: Optional[str] = None) -> Tuple[Optional[str], Optional[User], str]:
        """
        Maneja el flujo completo de login con 2FA obligatorio y control de intentos fallidos
        
        Regla de negocio crítica: 
        - Verificar si la cuenta está bloqueada ANTES de validar credenciales
        - Si el usuario NO tiene 2FA verificado, NO se retorna token de acceso
        - Incrementar intentos fallidos en caso de error de contraseña o 2FA
        - Bloquear cuenta después de 3 intentos fallidos (15 minutos)
        - Resetear intentos en login exitoso
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            totp_code: Código TOTP (opcional en primera fase)
            
        Returns:
            Tupla (token, user, message):
            - token: Token JWT solo si 2FA está verificado y código es válido
            - user: Usuario autenticado (o None si no existe)
            - message: Mensaje indicando el siguiente paso
            
        Raises:
            ValueError: Si las credenciales son incorrectas o cuenta bloqueada
        """
        # Obtener usuario por email
        user = self.user_repository.get_by_email(email)
        
        if not user:
            raise ValueError("Credenciales inválidas")
        
        # PASO 1: Verificar si la cuenta está bloqueada (ANTES de validar credenciales)
        if self.user_repository.is_account_locked(user):
            remaining_seconds = self.user_repository.get_lock_remaining_time(user)
            remaining_minutes = remaining_seconds // 60 if remaining_seconds else 0
            raise ValueError(f"Cuenta bloqueada por intentos fallidos. Tiempo restante: {remaining_minutes} minutos")
        
        # PASO 2: Verificar contraseña
        if not self.verify_password(password, user.hashed_password):
            # Incrementar intentos fallidos
            self.user_repository.increment_failed_attempts(user.id)
            
            # Verificar si debe bloquear la cuenta
            user = self.user_repository.get_by_id(user.id)  # Refrescar datos
            if user.failed_login_attempts >= 3:
                self.user_repository.lock_account(user.id, minutes=15)
                raise ValueError("Cuenta bloqueada por múltiples intentos fallidos. Intente nuevamente en 15 minutos")
            
            raise ValueError("Credenciales inválidas")
        
        # PASO 3: Verificar si tiene 2FA configurado y verificado
        if not user.totp_verified:
            return None, user, "2FA_REQUIRED"
        
        # PASO 4: Debe proporcionar código TOTP
        if not totp_code:
            return None, user, "TOTP_CODE_REQUIRED"
        
        # PASO 5: Verificar código TOTP
        if not self.totp_service.verify_totp(user.totp_secret, totp_code):
            # Incrementar intentos fallidos por 2FA inválido
            self.user_repository.increment_failed_attempts(user.id)
            
            # Verificar si debe bloquear la cuenta
            user = self.user_repository.get_by_id(user.id)  # Refrescar datos
            if user.failed_login_attempts >= 3:
                self.user_repository.lock_account(user.id, minutes=15)
                raise ValueError("Cuenta bloqueada por múltiples intentos fallidos. Intente nuevamente en 15 minutos")
            
            raise ValueError("Código TOTP inválido")
        
        # PASO 6: Login exitoso - resetear intentos fallidos
        self.user_repository.reset_failed_attempts(user.id)
        
        # PASO 7: Generar token de acceso
        token = self.create_access_token(user)
        
        return token, user, "LOGIN_SUCCESS"


def get_auth_service(user_repository: UserRepository) -> AuthService:
    """
    Factory function para obtener instancia de AuthService
    Implementa inyección de dependencias para FastAPI
    
    Args:
        user_repository: Repositorio de usuarios
        
    Returns:
        Instancia de AuthService
    """
    totp_service = TOTPService()
    return AuthService(user_repository, totp_service)
