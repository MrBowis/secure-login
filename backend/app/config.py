"""
Configuración de la aplicación
Principio: Single Responsibility - Solo maneja configuración
"""
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Configuración de la aplicación"""
    
    # Database
    database_url: str = Field(
        default="postgresql://admin:admin@localhost:5432/db_login",
        alias="DATABASE_URL"
    )
    
    # JWT
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Application
    app_name: str = "Secure Login API"
    debug: bool = False
    
    # TOTP
    totp_issuer: str = "SecureLoginApp"
    totp_interval: int = 30  # Segundos de validez del código
    totp_digits: int = 6
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instancia global de configuración (Singleton pattern)
settings = Settings()
