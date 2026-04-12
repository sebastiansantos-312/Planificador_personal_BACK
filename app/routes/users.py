"""
routes/users.py — Endpoints CRUD para usuarios y configuración de límite diario.

Gestiona el registro y administración de cuentas de usuario.

Endpoints:
  POST   /users/           — Registra un nuevo usuario.
  GET    /users/           — Lista todos los usuarios.
  GET    /users/{id}       — Obtiene un usuario por UUID.
  PATCH  /users/{id}       — Actualiza el perfil de un usuario.
  DELETE /users/{id}       — Elimina un usuario.
  GET    /users/{id}/config  — Obtiene el límite diario del usuario (US-12).
  PATCH  /users/{id}/config  — Actualiza el límite diario del usuario (US-12).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from ..database import get_db
from .. import crud, schemas

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema.

    Llamado desde AuthPage (formulario de registro) en el frontend.
    La contraseña se hashea con bcrypt antes de guardar (Sprint 2).

    Args:
        user (UserCreate): Datos del nuevo usuario (nombre, email, contraseña).
        db (Session): Sesión de BD inyectada.

    Returns:
        User: Usuario creado (sin contraseña).
    """
    return crud.create_user(db, user)


@router.get("/", response_model=list[schemas.User])
def get_users(db: Session = Depends(get_db)):
    """
    Lista todos los usuarios registrados.

    Args:
        db (Session): Sesión de BD inyectada.

    Returns:
        list[User]: Todos los usuarios (sin contraseñas).
    """
    return crud.get_users(db)


# ── Rutas con path param /{user_id} ──────────────────────────────────────────
# IMPORTANTE: Las rutas con sufijos fijos como /{user_id}/config
# deben registrarse ANTES de /{user_id} para evitar conflictos de routing.

@router.get("/{user_id}/config")
def get_config(user_id: UUID, db: Session = Depends(get_db)):
    """
    Obtiene la configuración del límite diario de trabajo del usuario (US-12).

    Retorna el límite actual en minutos. Si el usuario nunca lo configuró,
    devuelve el valor por defecto de 360 minutos (6 horas).

    Args:
        user_id (UUID): UUID del usuario en la ruta.
        db (Session): Sesión de BD inyectada.

    Returns:
        dict: { daily_limit_minutes: int }
    """
    user = crud.get_user(db, user_id)
    return {"daily_limit_minutes": user.daily_limit_minutes or 360}


@router.patch("/{user_id}/config")
def update_config(user_id: UUID, daily_limit_minutes: int, db: Session = Depends(get_db)):
    """
    Actualiza el límite diario de trabajo del usuario (US-12).

    El sistema usará este valor al verificar sobrecarga en check-conflict.
    Valor por defecto si no se configura: 360 min (6h).

    Args:
        user_id (UUID): UUID del usuario en la ruta.
        daily_limit_minutes (int): Nuevo límite en minutos (ej: 480 = 8h).
        db (Session): Sesión de BD inyectada.

    Returns:
        User: Usuario actualizado con el nuevo límite.
    """
    return crud.update_user(
        db, user_id,
        schemas.UserUpdate(daily_limit_minutes=daily_limit_minutes)
    )


@router.get("/{user_id}", response_model=schemas.User)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Obtiene un usuario por su UUID.

    Args:
        user_id (UUID): UUID del usuario en la ruta.
        db (Session): Sesión de BD inyectada.

    Returns:
        User: Usuario encontrado.
    """
    return crud.get_user(db, user_id)


@router.patch("/{user_id}", response_model=schemas.User)
def update_user(user_id: UUID, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    """
    Actualiza parcialmente el perfil de un usuario (PATCH).

    Solo modifica los campos enviados en el request (exclude_unset=True en crud).

    Args:
        user_id (UUID): UUID del usuario a actualizar.
        user (UserUpdate): Campos a modificar.
        db (Session): Sesión de BD inyectada.

    Returns:
        User: Usuario actualizado.
    """
    return crud.update_user(db, user_id, user)


@router.delete("/{user_id}")
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Elimina un usuario de la base de datos.

    Args:
        user_id (UUID): UUID del usuario a eliminar.
        db (Session): Sesión de BD inyectada.

    Returns:
        dict: Mensaje de confirmación.
    """
    return crud.delete_user(db, user_id)