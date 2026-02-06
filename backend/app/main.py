"""
Aplicación Principal FastAPI
Sistema de autenticación con 2FA obligatorio

Principios SOLID aplicados:
- Single Responsibility: Cada módulo tiene una responsabilidad única
- Open/Closed: Extensible mediante servicios y repositorios
- Liskov Substitution: Uso de abstracciones e interfaces
- Interface Segregation: Schemas específicos para cada operación
- Dependency Injection: FastAPI Depends para inyección de dependencias
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import init_db
from app.routers import auth

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API de autenticación segura con 2FA obligatorio usando Microsoft Authenticator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============= Middleware =============

# CORS - Configurar según necesidades de producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= Exception Handlers =============

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Manejo global de errores de validación de Pydantic
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Los datos proporcionados no son válidos",
            "errors": errors,
            "status_code": 422
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """
    Manejo global de errores de integridad de base de datos
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Integrity Error",
            "detail": "El recurso ya existe o viola una restricción de integridad",
            "status_code": 409
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Manejo global de excepciones no controladas
    """
    # En producción, registrar el error en logs
    print(f"Error no controlado: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "Ha ocurrido un error interno en el servidor",
            "status_code": 500
        }
    )


# ============= Events =============

@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio de la aplicación
    Inicializa la base de datos
    """
    print("🚀 Iniciando aplicación...")
    print(f"📋 Configuración: {settings.app_name}")
    print(f"🔒 JWT Algorithm: {settings.jwt_algorithm}")
    print(f"⏱️  TOTP Interval: {settings.totp_interval}s")
    
    # Inicializar base de datos
    try:
        init_db()
        print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento de cierre de la aplicación
    """
    print("🛑 Cerrando aplicación...")


# ============= Routers =============

app.include_router(auth.router)


# ============= Health Check =============

@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Verifica que el servidor esté funcionando"
)
async def root():
    """
    Endpoint de health check
    """
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "1.0.0",
        "message": "Secure Login API with mandatory 2FA"
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check detallado",
    description="Verifica el estado del servidor y sus componentes"
)
async def health_check():
    """
    Endpoint de health check detallado
    """
    return {
        "status": "healthy",
        "components": {
            "api": "ok",
            "database": "ok",  # En producción, verificar conexión real
            "2fa": "ok"
        },
        "settings": {
            "totp_interval": settings.totp_interval,
            "totp_digits": settings.totp_digits,
            "jwt_expire_minutes": settings.jwt_access_token_expire_minutes
        }
    }


# ============= Documentación adicional =============

@app.get(
    "/flow",
    tags=["Documentation"],
    summary="Flujo de autenticación",
    description="Describe el flujo completo de registro y autenticación con 2FA"
)
async def authentication_flow():
    """
    Documentación del flujo de autenticación
    """
    return {
        "flow": {
            "1_register": {
                "endpoint": "POST /auth/register",
                "description": "Registrar nuevo usuario con email y contraseña",
                "required": ["email", "password"],
                "next_step": "setup_2fa"
            },
            "2_setup_2fa": {
                "endpoint": "POST /auth/setup-2fa",
                "description": "Configurar 2FA en Microsoft Authenticator",
                "required": ["email", "password"],
                "action": "Escanear código QR o ingresar secret manualmente en Microsoft Authenticator",
                "next_step": "verify_2fa"
            },
            "3_verify_2fa": {
                "endpoint": "POST /auth/verify-2fa",
                "description": "Verificar configuración de 2FA con código de 6 dígitos",
                "required": ["email", "password", "totp_code"],
                "next_step": "login"
            },
            "4_login": {
                "endpoint": "POST /auth/login",
                "description": "Iniciar sesión con email, contraseña y código TOTP",
                "required": ["email", "password", "totp_code"],
                "response": "Token JWT de acceso",
                "critical_rule": "Solo permite login si el usuario ha verificado su 2FA"
            }
        },
        "critical_rules": [
            "El usuario NO puede iniciar sesión sin haber verificado su 2FA",
            "El código TOTP debe ser generado por Microsoft Authenticator",
            "Los códigos TOTP tienen una validez de 30 segundos",
            "El token JWT expira después de 30 minutos (configurable)"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
