"""
Configuración de base de datos
Principio: Single Responsibility - Solo maneja conexión a BD
Principio: Dependency Inversion - Provee abstracción para acceso a BD
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

# Crear engine de SQLAlchemy
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.debug
)

# Crear session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos
    Implementa el patrón de inyección de dependencias
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas
    """
    Base.metadata.create_all(bind=engine)
