"""
crud.py — Operaciones de base de datos (Create, Read, Update, Delete).

Este módulo contiene toda la lógica de acceso a datos. Los routers de FastAPI
llaman a estas funciones pasándoles la sesión de BD como primer argumento.

Organización:
  - Sección USERS:    Registro, consulta y actualización de usuarios.
  - Sección SUBJECTS: Gestión de materias del usuario.
  - Sección TASKS:    Gestión de tareas académicas.
  - Sección SUBTASKS: Gestión de subtareas/pasos dentro de una tarea.
  - Vista HOY:        Algoritmo de priorización diaria (US-04).
  - Conflicto:        Detección de sobrecarga diaria (US-07).
  - Por EMAIL:        Variantes que resuelven IDs a partir del email del usuario.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from datetime import date
from uuid import UUID
from typing import Optional
from fastapi import HTTPException


# ─── USERS ───────────────────────────────────────────────────────────────────

def create_user(db: Session, user: schemas.UserCreate):
    from .security import hash_password  # import local para evitar ciclos
    hashed = hash_password(user.password)
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=hashed,
        birth_date=user.birth_date,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session):
    """
    Retorna todos los usuarios registrados.

    Args:
        db (Session): Sesión activa de SQLAlchemy.

    Returns:
        list[models.User]: Lista con todos los usuarios.
    """
    return db.query(models.User).all()


def get_user_by_email(db: Session, email: str):
    """
    Busca un usuario por su correo electrónico.

    Usado principalmente en el login y en las operaciones 'by-email'.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        email (str): Correo electrónico a buscar.

    Returns:
        models.User | None: Usuario encontrado o None si no existe.
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_user(db: Session, user_id: UUID):
    """
    Busca un usuario por su UUID.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): Identificador único del usuario.

    Returns:
        models.User: Usuario encontrado.

    Raises:
        HTTPException 404: Si no existe usuario con ese UUID.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


def update_user(db: Session, user_id: UUID, user: schemas.UserUpdate):
    """
    Actualiza parcialmente el perfil de un usuario (PATCH).

    Solo modifica los campos que vienen en el request (exclude_unset=True).

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario a actualizar.
        user (UserUpdate): Campos a modificar.

    Returns:
        models.User: Usuario actualizado.
    """
    db_user = get_user(db, user_id)
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: UUID):
    """
    Elimina un usuario de la base de datos.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario a eliminar.

    Returns:
        dict: Mensaje de confirmación.
    """
    db_user = get_user(db, user_id)
    db.delete(db_user)
    db.commit()
    return {"message": "user deleted"}


# ─── SUBJECTS ────────────────────────────────────────────────────────────────

def create_subject(db: Session, subject: schemas.SubjectCreate):
    """
    Crea una nueva materia usando el UUID del usuario.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        subject (SubjectCreate): Datos de la materia (nombre, color, user_id).

    Returns:
        models.Subject: Materia creada.
    """
    db_subject = models.Subject(**subject.dict())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


def get_subjects(db: Session, user_id: UUID):
    """
    Retorna todas las materias de un usuario por su UUID.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario propietario.

    Returns:
        list[models.Subject]: Lista de materias del usuario.
    """
    return db.query(models.Subject).filter(models.Subject.user_id == user_id).all()


def get_subject(db: Session, subject_id: UUID):
    """
    Busca una materia por su UUID.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        subject_id (UUID): UUID de la materia.

    Returns:
        models.Subject: Materia encontrada.

    Raises:
        HTTPException 404: Si no existe la materia.
    """
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return db_subject


def update_subject(db: Session, subject_id: UUID, subject: schemas.SubjectUpdate):
    """
    Actualiza parcialmente una materia (PATCH).

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        subject_id (UUID): UUID de la materia a actualizar.
        subject (SubjectUpdate): Campos a modificar (nombre y/o color).

    Returns:
        models.Subject: Materia actualizada.
    """
    db_subject = get_subject(db, subject_id)
    for key, value in subject.dict(exclude_unset=True).items():
        setattr(db_subject, key, value)
    db.commit()
    db.refresh(db_subject)
    return db_subject


def delete_subject(db: Session, subject_id: UUID):
    """
    Elimina una materia de la base de datos.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        subject_id (UUID): UUID de la materia a eliminar.

    Returns:
        dict: Mensaje de confirmación.

    Raises:
        HTTPException 404: Si no existe la materia.
    """
    db_subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(db_subject)
    db.commit()
    return {"message": "subject deleted"}


# ─── TASKS ───────────────────────────────────────────────────────────────────

def create_task(db: Session, task: schemas.TaskCreate):
    """
    Crea una nueva tarea usando IDs directamente.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        task (TaskCreate): Datos de la tarea.

    Returns:
        models.Task: Tarea creada con su UUID asignado.
    """
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(db: Session, user_id: UUID):
    """
    Retorna todas las tareas de un usuario por su UUID.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario propietario.

    Returns:
        list[models.Task]: Lista de tareas del usuario.
    """
    return db.query(models.Task).filter(models.Task.user_id == user_id).all()


def get_task(db: Session, task_id: UUID):
    """
    Busca una tarea por su UUID.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        task_id (UUID): UUID de la tarea.

    Returns:
        models.Task: Tarea encontrada.

    Raises:
        HTTPException 404: Si no existe la tarea.
    """
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


def update_task(db: Session, task_id: UUID, task: schemas.TaskUpdate):
    """
    Actualiza parcialmente una tarea (PATCH).

    Solo modifica los campos enviados en el request (exclude_unset=True),
    lo que permite actualizar únicamente el estado sin tocar los demás campos.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        task_id (UUID): UUID de la tarea a actualizar.
        task (TaskUpdate): Campos a modificar.

    Returns:
        models.Task: Tarea actualizada.
    """
    db_task = get_task(db, task_id)
    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: UUID):
    """
    Elimina una tarea de la base de datos.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        task_id (UUID): UUID de la tarea a eliminar.

    Returns:
        dict: Mensaje de confirmación.
    """
    db_task = get_task(db, task_id)
    db.delete(db_task)
    db.commit()
    return {"message": "task deleted"}


# ─── SUBTASKS ────────────────────────────────────────────────────────────────

def create_subtask(db: Session, subtask: schemas.SubtaskCreate):
    """
    Crea una nueva subtarea asociada a una tarea existente.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        subtask (SubtaskCreate): Datos del paso/subtarea.

    Returns:
        models.Subtask: Subtarea creada.
    """
    db_subtask = models.Subtask(**subtask.dict())
    db.add(db_subtask)
    db.commit()
    db.refresh(db_subtask)
    return db_subtask


def get_subtasks_by_task(db: Session, task_id: UUID):
    """
    Retorna todas las subtareas de una tarea específica.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        task_id (UUID): UUID de la tarea padre.

    Returns:
        list[models.Subtask]: Lista de subtareas de la tarea.
    """
    return db.query(models.Subtask).filter(models.Subtask.task_id == task_id).all()


def get_subtask(db: Session, subtask_id: UUID):
    """
    Busca una subtarea por su UUID.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        subtask_id (UUID): UUID de la subtarea.

    Returns:
        models.Subtask: Subtarea encontrada.

    Raises:
        HTTPException 404: Si no existe la subtarea.
    """
    db_subtask = db.query(models.Subtask).filter(models.Subtask.id == subtask_id).first()
    if not db_subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return db_subtask


def update_subtask(db: Session, subtask_id: UUID, subtask: schemas.SubtaskUpdate):
    """
    Actualiza parcialmente una subtarea (PATCH).

    Usado tanto para reprogramar fechas (T3) como para marcar como hecha (T4).

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        subtask_id (UUID): UUID de la subtarea a actualizar.
        subtask (SubtaskUpdate): Campos a modificar.

    Returns:
        models.Subtask: Subtarea actualizada.
    """
    db_subtask = get_subtask(db, subtask_id)
    for key, value in subtask.dict(exclude_unset=True).items():
        setattr(db_subtask, key, value)
    db.commit()
    db.refresh(db_subtask)
    return db_subtask


def delete_subtask(db: Session, subtask_id: UUID):
    """
    Elimina una subtarea de la base de datos.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        subtask_id (UUID): UUID de la subtarea a eliminar.

    Returns:
        dict: Mensaje de confirmación.
    """
    db_subtask = get_subtask(db, subtask_id)
    db.delete(db_subtask)
    db.commit()
    return {"message": "subtask deleted"}


# ─── VISTA "HOY" — US-04 ─────────────────────────────────────────────────────

def get_today_view(db: Session, user_id: UUID):
    """
    Genera la vista diaria priorizada del usuario (US-04, T2).

    Consulta todas las subtareas pendientes del usuario que tienen
    fecha objetivo definida, y las agrupa en tres categorías:

      - overdue:    Subtareas con target_date anterior a hoy (vencidas).
      - for_today:  Subtareas con target_date igual a hoy.
      - upcoming:   Subtareas con target_date posterior a hoy (próximas).

    Criterio de ordenamiento dentro de cada grupo:
      - Primero las más antiguas (fecha ascendente).
      - En caso de empate, primero las de menor esfuerzo estimado.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario.

    Returns:
        dict: {
            "date": str (ISO),
            "overdue": list[dict],
            "for_today": list[dict],
            "upcoming": list[dict]
        }
    """
    today = date.today()

    # Obtener subtareas pendientes con fecha objetivo, del usuario
    subtasks = (
        db.query(models.Subtask)
        .join(models.Task, models.Subtask.task_id == models.Task.id)
        .filter(models.Task.user_id == user_id)
        .filter(models.Subtask.status != "done")
        .filter(models.Subtask.target_date != None)
        .all()
    )

    overdue = []
    for_today = []
    upcoming = []

    for s in subtasks:
        if s.target_date < today:
            overdue.append(s)
        elif s.target_date == today:
            for_today.append(s)
        else:
            upcoming.append(s)

    # Ordenar cada grupo por fecha y luego por esfuerzo estimado
    overdue.sort(key=lambda s: (s.target_date, s.estimated_minutes or 9999))
    for_today.sort(key=lambda s: (s.estimated_minutes or 9999,))
    upcoming.sort(key=lambda s: (s.target_date, s.estimated_minutes or 9999))

    def to_dict(s):
        """Convierte un objeto Subtask ORM a dict serializable por Pydantic."""
        return {
            "id": str(s.id),
            "task_id": str(s.task_id),
            "title": s.title,
            "description": s.description,
            "target_date": s.target_date.isoformat() if s.target_date else None,
            "estimated_minutes": s.estimated_minutes,
            "status": s.status,
            "postpone_note": s.postpone_note,   # ← Fix C1: incluir nota de posposición (US-09)
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }

    return {
        "date": today.isoformat(),
        "overdue": [to_dict(s) for s in overdue],
        "for_today": [to_dict(s) for s in for_today],
        "upcoming": [to_dict(s) for s in upcoming],
    }


# ─── CONFLICTO DE SOBRECARGA — US-07 ─────────────────────────────────────────

def check_overload_conflict(
    db: Session,
    user_id: UUID,
    target_date: date,
    new_estimated_minutes: int,
    exclude_subtask_id: Optional[UUID] = None,
):
    """
    Verifica si agregar una subtarea generaría sobrecarga en un día (US-07, T3).

    Suma los minutos estimados de todas las subtareas pendientes del usuario
    para el día indicado y evalúa si supera el límite diario configurado
    por el usuario (US-12). El límite se lee directamente de la BD.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario.
        target_date (date): Día para el que se verifica la carga.
        new_estimated_minutes (int): Minutos de la nueva subtarea a agregar.
        exclude_subtask_id (UUID, optional): UUID de subtarea a excluir del
            conteo — usado al reprogramar para no contarla dos veces.

    Returns:
        dict: {
            "has_conflict": bool,
            "current_minutes": int,
            "new_total_minutes": int,
            "limit_minutes": int,
            "current_hours": float,
            "new_total_hours": float,
            "limit_hours": float,
            "message": str
        }
    """
    # Leer el límite real del usuario desde la BD (US-12)
    user = get_user(db, user_id)
    daily_limit_minutes = user.daily_limit_minutes or 360

    query = (
        db.query(func.sum(models.Subtask.estimated_minutes))
        .join(models.Task, models.Subtask.task_id == models.Task.id)
        .filter(models.Task.user_id == user_id)
        .filter(models.Subtask.target_date == target_date)
        .filter(models.Subtask.status != "done")
    )

    if exclude_subtask_id:
        query = query.filter(models.Subtask.id != exclude_subtask_id)

    current_total = query.scalar() or 0
    new_total = current_total + new_estimated_minutes
    has_conflict = new_total > daily_limit_minutes

    return {
        "has_conflict": has_conflict,
        "current_minutes": current_total,
        "new_total_minutes": new_total,
        "limit_minutes": daily_limit_minutes,
        "current_hours": round(current_total / 60, 1),
        "new_total_hours": round(new_total / 60, 1),
        "limit_hours": round(daily_limit_minutes / 60, 1),
        "message": (
            f"Quedarías con {round(new_total/60, 1)}h planificadas "
            f"(límite {round(daily_limit_minutes/60, 1)}h)"
            if has_conflict else "Sin conflicto"
        ),
    }


# ─── DÍAS CON SOBRECARGA — US-12 ─────────────────────────────────────────────

def get_overloaded_days(db: Session, user_id: UUID, limit_minutes: int):
    """
    Retorna los días que ya tienen más minutos planificados que el límite dado.

    Usado cuando el usuario cambia su límite diario para informarle qué días
    existentes ya superan el nuevo valor configurado.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario.
        limit_minutes (int): Nuevo límite en minutos a comparar.

    Returns:
        list[dict]: Lista de días con sobrecarga, cada uno con:
            {
                "date": str (ISO),
                "total_minutes": int,
                "total_hours": float,
                "overflow_minutes": int,
                "overflow_hours": float
            }
    """
    results = (
        db.query(
            models.Subtask.target_date,
            func.sum(models.Subtask.estimated_minutes).label("total_minutes"),
        )
        .join(models.Task, models.Subtask.task_id == models.Task.id)
        .filter(models.Task.user_id == user_id)
        .filter(models.Subtask.status != "done")
        .filter(models.Subtask.target_date != None)
        .group_by(models.Subtask.target_date)
        .having(func.sum(models.Subtask.estimated_minutes) > limit_minutes)
        .all()
    )

    return [
        {
            "date": r.target_date.isoformat(),
            "total_minutes": r.total_minutes,
            "total_hours": round(r.total_minutes / 60, 1),
            "overflow_minutes": r.total_minutes - limit_minutes,
            "overflow_hours": round((r.total_minutes - limit_minutes) / 60, 1),
        }
        for r in results
    ]


# ─── RESUMEN SEMANAL DE DISPONIBILIDAD ───────────────────────────────────────

def get_week_summary(db: Session, user_id: UUID, from_date: date, to_date: date):
    """
    Retorna el resumen de minutos usados/libres por día en un rango de fechas.

    Para cada día del rango (inclusivo) devuelve cuántos minutos tiene
    planificados el usuario y cuántos le quedan disponibles según su límite.
    Los días sin ninguna subtarea retornan used_minutes = 0.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario.
        from_date (date): Fecha inicio del rango (inclusivo).
        to_date (date): Fecha fin del rango (inclusivo).

    Returns:
        list[dict]: Lista con un elemento por día: {
            date, used_minutes, limit_minutes, free_minutes, over_limit
        }
    """
    from datetime import timedelta

    user = get_user(db, user_id)
    limit = user.daily_limit_minutes or 360

    # Sumar minutos por día en el rango
    rows = (
        db.query(
            models.Subtask.target_date,
            func.sum(models.Subtask.estimated_minutes).label("total"),
        )
        .join(models.Task, models.Subtask.task_id == models.Task.id)
        .filter(models.Task.user_id == user_id)
        .filter(models.Subtask.status != "done")
        .filter(models.Subtask.target_date >= from_date)
        .filter(models.Subtask.target_date <= to_date)
        .group_by(models.Subtask.target_date)
        .all()
    )

    # Mapa fecha → minutos usados
    used_map = {r.target_date: r.total for r in rows}

    # Generar un registro por cada día del rango
    result = []
    current = from_date
    while current <= to_date:
        used = used_map.get(current, 0)
        free = max(0, limit - used)
        result.append({
            "date": current.isoformat(),
            "used_minutes": used,
            "limit_minutes": limit,
            "free_minutes": free,
            "over_limit": used > limit,
        })
        current += timedelta(days=1)

    return result



# ─── CRUD POR EMAIL ──────────────────────────────────────────────────────────
# El frontend almacena el email del usuario en localStorage (no el UUID).
# Estas funciones resuelven el UUID internamente a partir del email,
# simplificando las peticiones desde el cliente.

def create_subject_by_email(db: Session, data: schemas.SubjectCreateByEmail):
    """
    Crea una materia resolviendo el usuario a partir de su email.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        data (SubjectCreateByEmail): Datos de la materia + email del usuario.

    Returns:
        models.Subject: Materia creada.

    Raises:
        HTTPException 404: Si no existe usuario con ese email.
    """
    user = get_user_by_email(db, data.user_email)
    if not user:
        raise HTTPException(status_code=404, detail=f"No existe usuario con email: {data.user_email}")

    db_subject = models.Subject(name=data.name, color=data.color, user_id=user.id)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


def get_subjects_by_email(db: Session, user_email: str):
    """
    Retorna las materias de un usuario identificado por email.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_email (str): Email del usuario.

    Returns:
        list[models.Subject]: Materias del usuario.

    Raises:
        HTTPException 404: Si no existe usuario con ese email.
    """
    user = get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(status_code=404, detail=f"No existe usuario con email: {user_email}")
    return db.query(models.Subject).filter(models.Subject.user_id == user.id).all()


def create_task_by_email(db: Session, data: schemas.TaskCreateByEmail):
    """
    Crea una tarea resolviendo usuario y materia a partir de email y nombre.
    task_type agregado para cumplir US-01.
    """
    user = get_user_by_email(db, data.user_email)
    if not user:
        raise HTTPException(status_code=404, detail=f"No existe usuario con email: {data.user_email}")

    subject = (
        db.query(models.Subject)
        .filter(models.Subject.name == data.subject_name)
        .filter(models.Subject.user_id == user.id)
        .first()
    )
    if not subject:
        raise HTTPException(status_code=404, detail=f"No existe materia '{data.subject_name}' para ese usuario")

    db_task = models.Task(
        title=data.title,
        task_type=data.task_type,                                 # ← NUEVO (US-01)
        subject_id=subject.id,
        user_id=user.id,
        due_date=data.due_date,
        duration_minutes=data.duration_minutes,
        priority=data.priority,
        status=data.status,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks_by_email(db: Session, user_email: str):
    """
    Retorna todas las tareas de un usuario identificado por email.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_email (str): Email del usuario.

    Returns:
        list[models.Task]: Tareas del usuario.

    Raises:
        HTTPException 404: Si no existe usuario con ese email.
    """
    user = get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(status_code=404, detail=f"No existe usuario con email: {user_email}")
    return db.query(models.Task).filter(models.Task.user_id == user.id).all()


def get_today_view_by_email(db: Session, user_email: str):
    """
    Genera la vista diaria priorizada para un usuario identificado por email.

    Resuelve el UUID del usuario a partir del email y delega en get_today_view().

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_email (str): Email del usuario.

    Returns:
        dict: Vista diaria con subtareas agrupadas (ver get_today_view).

    Raises:
        HTTPException 404: Si no existe usuario con ese email.
    """
    user = get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(status_code=404, detail=f"No existe usuario con email: {user_email}")
    return get_today_view(db, user.id)


# ─── CONFLICTO DE SOBRECARGA PARA TAREAS — US-07 ─────────────────────────────

def check_task_overload_conflict(
    db: Session,
    user_id: UUID,
    target_date: date,
    new_duration_minutes: int,
    exclude_task_id: Optional[UUID] = None,
):
    """
    Verifica si agregar/mover una tarea a un día genera sobrecarga (US-07).

    Suma los minutos de todas las tareas (duration_minutes, por due_date)
    y de todas las subtareas (estimated_minutes, por target_date) del usuario
    para el día dado, y evalúa si supera el límite diario configurado.

    Args:
        db (Session): Sesión activa de SQLAlchemy.
        user_id (UUID): UUID del usuario.
        target_date (date): Día para el que se verifica la carga.
        new_duration_minutes (int): Minutos de la nueva tarea / cambio a agregar.
        exclude_task_id (UUID, optional): UUID de la tarea a excluir del conteo
            (para no contarse a sí misma al editar).

    Returns:
        dict: { has_conflict, current_minutes, new_total_minutes,
                limit_minutes, current_hours, new_total_hours,
                limit_hours, message }
    """
    user = get_user(db, user_id)
    daily_limit_minutes = user.daily_limit_minutes or 360

    # Suma de duration_minutes de otras tareas con ese due_date
    task_query = (
        db.query(func.sum(models.Task.duration_minutes))
        .filter(models.Task.user_id == user_id)
        .filter(models.Task.due_date == target_date)
        .filter(models.Task.duration_minutes != None)
    )
    if exclude_task_id:
        task_query = task_query.filter(models.Task.id != exclude_task_id)
    task_minutes = task_query.scalar() or 0

    # Suma de estimated_minutes de subtareas con ese target_date
    sub_query = (
        db.query(func.sum(models.Subtask.estimated_minutes))
        .join(models.Task, models.Subtask.task_id == models.Task.id)
        .filter(models.Task.user_id == user_id)
        .filter(models.Subtask.target_date == target_date)
        .filter(models.Subtask.status != "done")
    )
    sub_minutes = sub_query.scalar() or 0

    current_total = task_minutes + sub_minutes
    new_total = current_total + new_duration_minutes
    has_conflict = new_total > daily_limit_minutes

    return {
        "has_conflict": has_conflict,
        "current_minutes": current_total,
        "new_total_minutes": new_total,
        "limit_minutes": daily_limit_minutes,
        "current_hours": round(current_total / 60, 1),
        "new_total_hours": round(new_total / 60, 1),
        "limit_hours": round(daily_limit_minutes / 60, 1),
        "message": (
            f"Quedarías con {round(new_total/60, 1)}h planificadas "
            f"(límite {round(daily_limit_minutes/60, 1)}h)"
            if has_conflict else "Sin conflicto"
        ),
    }