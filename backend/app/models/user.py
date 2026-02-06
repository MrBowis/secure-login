"""
Modelo de Usuario
Principio: Single Responsibility - Solo representa entidad User en BD
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from app.database import Base


class UserRole(str, enum.Enum):
    """Enum para roles de usuario"""
    ADMIN = "ADMIN"
    CLIENT = "CLIENT"


class User(Base):
    """
    Modelo de usuario con soporte para 2FA y control de seguridad
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.CLIENT.value, nullable=False)
    
    # Campos de información personal
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    
    # Campos para 2FA
    totp_secret = Column(String, nullable=True)  # Secret para generar códigos TOTP
    totp_verified = Column(Boolean, default=False)  # Si el usuario ha verificado su 2FA
    
    # Campos para control de seguridad (intentos fallidos)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, totp_verified={self.totp_verified})>"
