"""
Repositorio de Usuarios
Principio: Single Responsibility - Solo maneja operaciones CRUD de usuarios
Principio: Dependency Inversion - Trabaja con abstracciones (Session)
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User


class UserRepository:
    """
    Repositorio para operaciones de base de datos con usuarios
    Implementa el patrón Repository
    """
    
    def __init__(self, db: Session):
        """
        Constructor con inyección de dependencias
        
        Args:
            db: Sesión de SQLAlchemy
        """
        self.db = db
    
    def create(self, email: str, hashed_password: str, name: str, phone_number: Optional[str] = None, role: str = "CLIENT") -> User:
        """
        Crea un nuevo usuario
        
        Args:
            email: Email del usuario
            hashed_password: Contraseña hasheada
            name: Nombre completo del usuario
            phone_number: Número de teléfono (opcional)
            role: Rol del usuario (ADMIN o CLIENT)
            
        Returns:
            Usuario creado
            
        Raises:
            IntegrityError: Si el email ya existe
        """
        user = User(
            email=email,
            hashed_password=hashed_password,
            name=name,
            phone_number=phone_number,
            role=role,
            totp_verified=False,
            failed_login_attempts=0,
            locked_until=None
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Obtiene un usuario por ID (UUID)
        
        Args:
            user_id: UUID del usuario
            
        Returns:
            Usuario o None si no existe
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por email
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario o None si no existe
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def update_totp_secret(self, user_id: UUID, totp_secret: str) -> Optional[User]:
        """
        Actualiza el secret TOTP del usuario
        
        Args:
            user_id: UUID del usuario
            totp_secret: Nuevo secret TOTP
            
        Returns:
            Usuario actualizado o None si no existe
        """
        user = self.get_by_id(user_id)
        if user:
            user.totp_secret = totp_secret
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def verify_totp(self, user_id: UUID) -> Optional[User]:
        """
        Marca el TOTP del usuario como verificado
        
        Args:
            user_id: UUID del usuario
            
        Returns:
            Usuario actualizado o None si no existe
        """
        user = self.get_by_id(user_id)
        if user:
            user.totp_verified = True
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def increment_failed_attempts(self, user_id: UUID) -> Optional[User]:
        """
        Incrementa el contador de intentos fallidos de login
        
        Args:
            user_id: UUID del usuario
            
        Returns:
            Usuario actualizado o None si no existe
        """
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts += 1
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def reset_failed_attempts(self, user_id: UUID) -> Optional[User]:
        """
        Resetea el contador de intentos fallidos y desbloquea la cuenta
        
        Args:
            user_id: UUID del usuario
            
        Returns:
            Usuario actualizado o None si no existe
        """
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def lock_account(self, user_id: UUID, minutes: int = 15) -> Optional[User]:
        """
        Bloquea la cuenta del usuario por un tiempo determinado
        
        Args:
            user_id: UUID del usuario
            minutes: Minutos de bloqueo (default 15)
            
        Returns:
            Usuario actualizado o None si no existe
        """
        user = self.get_by_id(user_id)
        if user:
            user.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def is_account_locked(self, user: User) -> bool:
        """
        Verifica si la cuenta del usuario está bloqueada
        
        Args:
            user: Usuario a verificar
            
        Returns:
            True si la cuenta está bloqueada, False en caso contrario
        """
        if user.locked_until is None:
            return False
        
        # Si el tiempo de bloqueo ya pasó, desbloquear automáticamente
        if datetime.utcnow() >= user.locked_until:
            self.reset_failed_attempts(user.id)
            return False
        
        return True
    
    def get_lock_remaining_time(self, user: User) -> Optional[int]:
        """
        Obtiene el tiempo restante de bloqueo en segundos
        
        Args:
            user: Usuario a verificar
            
        Returns:
            Segundos restantes o None si no está bloqueado
        """
        if user.locked_until is None:
            return None
        
        remaining = (user.locked_until - datetime.utcnow()).total_seconds()
        return int(remaining) if remaining > 0 else None
    
    def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado
        
        Args:
            email: Email a verificar
            
        Returns:
            True si existe, False en caso contrario
        """
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def get_all(self) -> list[User]:
        """
        Obtiene todos los usuarios
        
        Returns:
            Lista de todos los usuarios
        """
        return self.db.query(User).all()
    
    def update_user_info(self, user_id: UUID, name: Optional[str] = None, phone_number: Optional[str] = None) -> Optional[User]:
        """
        Actualiza la información del usuario (nombre y/o teléfono)
        
        Args:
            user_id: UUID del usuario
            name: Nuevo nombre (opcional)
            phone_number: Nuevo teléfono (opcional)
            
        Returns:
            Usuario actualizado o None si no existe
        """
        user = self.get_by_id(user_id)
        if user:
            if name is not None:
                user.name = name
            if phone_number is not None:
                user.phone_number = phone_number
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def delete(self, user_id: UUID) -> bool:
        """
        Elimina un usuario
        
        Args:
            user_id: UUID del usuario
            
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False


def get_user_repository(db: Session) -> UserRepository:
    """
    Factory function para obtener instancia de UserRepository
    Implementa inyección de dependencias para FastAPI
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Instancia de UserRepository
    """
    return UserRepository(db)
