"""
routes/subjects.py — Endpoints CRUD para materias (subjects).

Permite crear, consultar, actualizar y eliminar las materias del usuario.
Incluye variantes 'by-email' que usan el email del usuario en lugar de su UUID,
ya que el frontend almacena el email en localStorage.

Endpoints:
  POST   /subjects/           — Crea materia con user_id.
  POST   /subjects/by-email   — Crea materia con email del usuario.
  GET    /subjects/            — Lista materias por user_id.
  GET    /subjects/by-email   — Lista materias por email del usuario.
  GET    /subjects/{id}       — Obtiene una materia por UUID.
  PATCH  /subjects/{id}       — Actualiza nombre o color de una materia.
  DELETE /subjects/{id}       — Elimina una materia.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from ..database import get_db
from .. import crud, schemas

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("/", response_model=schemas.Subject)
def create_subject(subject: schemas.SubjectCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva materia usando el UUID del usuario.

    Args:
        subject (SubjectCreate): Nombre, color y user_id de la materia.
        db (Session): Sesión de BD inyectada.

    Returns:
        Subject: Materia creada.
    """
    return crud.create_subject(db, subject)


@router.post("/by-email", response_model=schemas.Subject)
def create_subject_by_email(subject: schemas.SubjectCreateByEmail, db: Session = Depends(get_db)):
    """
    Crea una nueva materia usando el email del usuario en lugar de su UUID.

    El backend resuelve internamente el UUID del usuario a partir del email.

    Args:
        subject (SubjectCreateByEmail): Nombre, color y email del usuario.
        db (Session): Sesión de BD inyectada.

    Returns:
        Subject: Materia creada.
    """
    return crud.create_subject_by_email(db, subject)


@router.get("/", response_model=list[schemas.Subject])
def get_subjects(user_id: UUID, db: Session = Depends(get_db)):
    """
    Lista todas las materias de un usuario por su UUID.

    Args:
        user_id (UUID): Query param con el UUID del usuario.
        db (Session): Sesión de BD inyectada.

    Returns:
        list[Subject]: Materias del usuario.
    """
    return crud.get_subjects(db, user_id)


@router.get("/by-email", response_model=list[schemas.Subject])
def get_subjects_by_email(user_email: str, db: Session = Depends(get_db)):
    """
    Lista todas las materias de un usuario por su email.

    Usado por el frontend para cargar las materias al iniciar sesión.

    Args:
        user_email (str): Query param con el email del usuario.
        db (Session): Sesión de BD inyectada.

    Returns:
        list[Subject]: Materias del usuario.
    """
    return crud.get_subjects_by_email(db, user_email)


@router.get("/{subject_id}", response_model=schemas.Subject)
def get_subject(subject_id: UUID, db: Session = Depends(get_db)):
    """
    Obtiene una materia por su UUID.

    Args:
        subject_id (UUID): UUID de la materia en la ruta.
        db (Session): Sesión de BD inyectada.

    Returns:
        Subject: Materia encontrada.
    """
    return crud.get_subject(db, subject_id)


@router.patch("/{subject_id}", response_model=schemas.Subject)
def update_subject(subject_id: UUID, subject: schemas.SubjectUpdate, db: Session = Depends(get_db)):
    """
    Actualiza el nombre o color de una materia.

    Args:
        subject_id (UUID): UUID de la materia a actualizar.
        subject (SubjectUpdate): Campos a modificar.
        db (Session): Sesión de BD inyectada.

    Returns:
        Subject: Materia actualizada.
    """
    return crud.update_subject(db, subject_id, subject)


@router.delete("/{subject_id}")
def delete_subject(subject_id: UUID, db: Session = Depends(get_db)):
    """
    Elimina una materia por su UUID.

    Args:
        subject_id (UUID): UUID de la materia a eliminar.
        db (Session): Sesión de BD inyectada.

    Returns:
        dict: Mensaje de confirmación.
    """
    return crud.delete_subject(db, subject_id)