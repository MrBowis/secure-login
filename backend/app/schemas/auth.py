"""
Schemas de autenticación
Principio: Single Responsibility - Solo maneja validación de datos
Principio: Interface Segregation - Schemas específicos para cada operación
"""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, computed_field


# ============= Request Schemas =============

class UserRegisterRequest(BaseModel):
    """Schema para registro de usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=8, description="Contraseña (mínimo 8 caracteres)")
    name: str = Field(..., min_length=1, description="Nombre completo del usuario")
    phone_number: Optional[str] = Field(None, description="Número de teléfono (opcional)")
    role: Literal["ADMIN", "CLIENT"] = Field(default="CLIENT", description="Rol del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "name": "Juan Pérez",
                "phone_number": "+34600123456",
                "role": "CLIENT"
            }
        }


class UserLoginRequest(BaseModel):
    """Schema para inicio de sesión"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña")
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6, description="Código TOTP de 6 dígitos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "totp_code": "123456"
            }
        }


class TOTPVerifyRequest(BaseModel):
    """Schema para verificar código TOTP"""
    totp_code: str = Field(..., min_length=6, max_length=6, description="Código TOTP de 6 dígitos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "totp_code": "123456"
            }
        }


# ============= Response Schemas =============

class UserResponse(BaseModel):
    """Schema de respuesta con información del usuario"""
    id: UUID
    email: str
    name: str
    phone_number: Optional[str]
    role: str
    totp_verified: bool
    created_at: datetime
    
    @computed_field
    @property
    def uuid(self) -> UUID:
        """Campo computado que retorna el mismo valor que id para compatibilidad"""
        return self.id
    
    class Config:
        from_attributes = True


class TOTPSetupResponse(BaseModel):
    """Schema de respuesta para setup de 2FA"""
    secret: str = Field(..., description="Secret TOTP en formato base32")
    qr_uri: str = Field(..., description="URI para generar código QR")
    manual_entry_key: str = Field(..., description="Clave para entrada manual")
    
    class Config:
        json_schema_extra = {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qr_uri": "otpauth://totp/SecureLoginApp:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=SecureLoginApp",
                "manual_entry_key": "JBSW Y3DP EHPK 3PXP"
            }
        }


class TokenResponse(BaseModel):
    """Schema de respuesta con token JWT"""
    access_token: str
    token_type: str = "bearer"
    role: str
    uuid: UUID
    user: UserResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "role": "CLIENT",
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "name": "Juan Pérez",
                    "phone_number": "+34600123456",
                    "role": "CLIENT",
                    "totp_verified": True,
                    "created_at": "2026-02-05T10:00:00"
                }
            }
        }


class MessageResponse(BaseModel):
    """Schema genérico para mensajes"""
    message: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operación exitosa",
                "detail": "Detalles adicionales"
            }
        }


class ErrorResponse(BaseModel):
    """Schema para respuestas de error"""
    error: str
    detail: Optional[str] = None
    status_code: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Unauthorized",
                "detail": "Credenciales inválidas",
                "status_code": 401
            }
        }


# ============= Admin Schemas =============

class UserUpdateRequest(BaseModel):
    """Schema para actualizar información del usuario (Admin)"""
    name: Optional[str] = Field(None, min_length=1, description="Nombre completo del usuario")
    phone_number: Optional[str] = Field(None, description="Número de teléfono")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Juan Pérez González",
                "phone_number": "+34600654321"
            }
        }


class UserListResponse(BaseModel):
    """Schema para lista de usuarios"""
    users: list[UserResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "name": "Juan Pérez",
                        "phone_number": "+34600123456",
                        "role": "CLIENT",
                        "totp_verified": True,
                        "created_at": "2026-02-05T10:00:00"
                    }
                ],
                "total": 1
            }
        }
