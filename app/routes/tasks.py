"""
routes/tasks.py — Endpoints CRUD para tareas y vista diaria.

Gestiona las tareas académicas del usuario. Incluye variantes 'by-email'
para compatibilidad con el frontend, y el endpoint especial de vista diaria
priorizada (US-04).

Endpoints:
  POST  /tasks/              — Crea tarea con IDs.
  POST  /tasks/by-email      — Crea tarea con email + nombre de materia.
  GET   /tasks/              — Lista tareas por user_id.
  GET   /tasks/by-email      — Lista tareas por email.
  GET   /tasks/hoy/prioridades — Vista diaria priorizada (US-04).
  GET   /tasks/{id}          — Obtiene una tarea por UUID.
  PATCH /tasks/{id}          — Actualiza una tarea.
  DELETE /tasks/{id}         — Elimina una tarea.

Nota sobre orden de rutas:
  FastAPI evalúa las rutas en el orden en que se registran. Las rutas
  /by-email y /hoy/prioridades deben registrarse ANTES de /{task_id}
  para evitar que FastAPI intente interpretar 'by-email' o 'hoy' como un UUID.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from ..database import get_db
from .. import crud, schemas

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva tarea usando UUIDs directamente.

    Args:
        task (TaskCreate): Datos de la tarea incluyendo subject_id y user_id.
        db (Session): Sesión de BD inyectada.

    Returns:
        Task: Tarea creada.
    """
    return crud.create_task(db, task)


@router.post("/by-email", response_model=schemas.Task)
def create_task_by_email(task: schemas.TaskCreateByEmail, db: Session = Depends(get_db)):
    """
    Crea una tarea usando email del usuario y nombre de la materia.

    El backend resuelve internamente los UUIDs de usuario y materia.

    Args:
        task (TaskCreateByEmail): Datos con user_email y subject_name.
        db (Session): Sesión de BD inyectada.

    Returns:
        Task: Tarea creada.
    """
    return crud.create_task_by_email(db, task)


@router.get("/", response_model=list[schemas.Task])
def get_tasks(user_id: UUID, db: Session = Depends(get_db)):
    """
    Lista todas las tareas de un usuario por UUID.

    Args:
        user_id (UUID): Query param con el UUID del usuario.
        db (Session): Sesión de BD inyectada.

    Returns:
        list[Task]: Tareas del usuario.
    """
    return crud.get_tasks(db, user_id)


@router.get("/by-email", response_model=list[schemas.Task])
def get_tasks_by_email(user_email: str, db: Session = Depends(get_db)):
    """
    Lista todas las tareas de un usuario por email.

    Usado por el frontend para cargar tareas en Progreso y en Crear.

    Args:
        user_email (str): Query param con el email del usuario.
        db (Session): Sesión de BD inyectada.

    Returns:
        list[Task]: Tareas del usuario.
    """
    return crud.get_tasks_by_email(db, user_email)


@router.get("/hoy/prioridades")
def get_today(user_email: str = None, user_id: UUID = None, db: Session = Depends(get_db)):
    """
    Retorna la vista diaria priorizada del usuario (US-04, T2).

    Agrupa las subtareas pendientes en tres categorías ordenadas:
      - overdue:    Vencidas (target_date < hoy).
      - for_today:  Para hoy (target_date == hoy).
      - upcoming:   Próximas (target_date > hoy).

    Acepta user_email o user_id como query param (el frontend envía user_email).

    Args:
        user_email (str, optional): Email del usuario.
        user_id (UUID, optional): UUID del usuario.
        db (Session): Sesión de BD inyectada.

    Returns:
        dict: Vista diaria con subtareas agrupadas y fecha actual.

    Raises:
        HTTPException 400: Si no se provee ni email ni user_id.
    """
    if user_email:
        return crud.get_today_view_by_email(db, user_email)
    if user_id:
        return crud.get_today_view(db, user_id)
    from fastapi import HTTPException
    raise HTTPException(status_code=400, detail="Debes enviar user_email o user_id")


@router.get("/progreso-global")
def get_global_progress(user_email: str, db: Session = Depends(get_db)):
    """
    C2 (US-10): Progreso global del usuario — actividades y subtareas.

    Devuelve métricas de dos niveles:
      - Actividades (tasks): métricas principales para ProgresoPage.
      - Subtareas: desglose interno de los pasos dentro de cada actividad.

    El porcentaje y contadores de actividades (tasks_percent, tasks_done, etc.)
    son consistentes con los estados reales en BD.

    Args:
        user_email (str): Email del usuario (query param).

    Returns:
        dict: {
            tasks_total, tasks_done, tasks_postponed, tasks_pending,
            tasks_percent,
            total_subtasks, done, postponed, pending, percent
        }

    Example response:
        {
            "tasks_total": 4,
            "tasks_done": 1,
            "tasks_postponed": 1,
            "tasks_pending": 2,
            "tasks_percent": 25,
            "total_subtasks": 12,
            "done": 5,
            "postponed": 2,
            "pending": 5,
            "percent": 42
        }

    Raises:
        HTTPException 404: Si no existe usuario con ese email.
    """
    return crud.get_global_progress_by_email(db, user_email)


@router.post("/{task_id}/check-conflict")
def check_task_conflict(
    task_id: UUID,
    due_date: str,
    duration_minutes: int,
    user_id: UUID,
    priority: str = None,
    db: Session = Depends(get_db),
):
    """
    Verifica si la duración de una tarea en una fecha supera el límite diario.

    Suma los minutos de las demás tareas con ese due_date y subtareas con ese
    target_date, y evalúa si agregar esta tarea genera sobrecarga.
    La tarea con task_id se excluye del conteo (para soportar edición).
    Si hay conflicto, retorna también recomendaciones inteligentes.

    Args:
        task_id (UUID): UUID de la tarea evaluada (se excluye del conteo al editar).
                        Usar un UUID nulo/dummy al crear una tarea nueva.
        due_date (str): Fecha límite en formato ISO (YYYY-MM-DD).
        duration_minutes (int): Duración de la tarea en minutos.
        user_id (UUID): UUID del usuario propietario.
        priority (str, optional): Prioridad de la tarea ('alta' | 'media' | 'baja').
                                   Requerido para calcular tareas desplazables.
        db (Session): Sesión de BD inyectada.

    Returns:
        dict: { has_conflict, current_minutes, new_total_minutes,
                limit_minutes, current_hours, new_total_hours,
                limit_hours, message, recommendations }
    """
    from datetime import date as date_type
    parsed_date = date_type.fromisoformat(due_date)
    return crud.check_task_overload_conflict(
        db=db,
        user_id=user_id,
        target_date=parsed_date,
        new_duration_minutes=duration_minutes,
        exclude_task_id=task_id,
        new_task_priority=priority,
    )


@router.get("/{task_id}", response_model=schemas.Task)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    """
    Obtiene una tarea por su UUID.

    Usado por el frontend al navegar a /actividad/{id}.

    Args:
        task_id (UUID): UUID de la tarea en la ruta.
        db (Session): Sesión de BD inyectada.

    Returns:
        Task: Tarea encontrada.
    """
    return crud.get_task(db, task_id)


@router.patch("/{task_id}", response_model=schemas.Task)
def update_task(task_id: UUID, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """
    Actualiza una tarea parcialmente (PATCH).

    Usado principalmente para cambiar el estado de la tarea
    (pending → in_progress → done) desde la página de detalle.

    Args:
        task_id (UUID): UUID de la tarea a actualizar.
        task (TaskUpdate): Campos a modificar.
        db (Session): Sesión de BD inyectada.

    Returns:
        Task: Tarea actualizada.
    """
    return crud.update_task(db, task_id, task)


@router.delete("/{task_id}")
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    """
    Elimina una tarea y retorna confirmación.

    Args:
        task_id (UUID): UUID de la tarea a eliminar.
        db (Session): Sesión de BD inyectada.

    Returns:
        dict: Mensaje de confirmación.
    """
    return crud.delete_task(db, task_id)