"""
database.py — Configuración de la conexión a la base de datos PostgreSQL.

Utiliza SQLAlchemy como ORM y carga la URL de conexión desde el archivo .env.
La base de datos está alojada en Supabase (PostgreSQL en AWS us-east-2).

Componentes:
  - engine: Motor de conexión a la BD. Es el objeto central de SQLAlchemy.
  - SessionLocal: Fábrica de sesiones. Cada petición HTTP obtiene su propia sesión.
  - Base: Clase base de la que heredan todos los modelos ORM.
  - get_db(): Función generadora usada como dependencia en los endpoints de FastAPI.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar variables de entorno desde el archivo .env
# En producción (Render), DATABASE_URL se configura como variable de entorno del servicio.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el motor de conexión a PostgreSQL
engine = create_engine(DATABASE_URL)

# Configurar la fábrica de sesiones
# autocommit=False: los cambios no se guardan automáticamente, se requiere db.commit()
# autoflush=False: no se sincronizan los cambios antes de cada consulta
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base declarativa: todos los modelos ORM heredan de esta clase
Base = declarative_base()


def get_db():
    """
    Dependencia de FastAPI que provee una sesión de base de datos por petición.

    Se usa con Depends(get_db) en los endpoints. Garantiza que la sesión
    siempre se cierre al finalizar la petición, aunque ocurra un error.

    Yields:
        Session: Sesión activa de SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()