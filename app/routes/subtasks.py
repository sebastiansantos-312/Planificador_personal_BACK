"""
routes/subtasks.py — Endpoints CRUD para subtareas y verificación de sobrecarga.

Gestiona los pasos/subtareas dentro de una tarea. Incluye el endpoint especial
de verificación de conflicto de sobrecarga diaria (US-07, T3).

Endpoints:
  POST   /subtasks/                    — Crea una subtarea.
  GET    /subtasks/task/{task_id}      — Lista subtareas de una tarea.
  PATCH  /subtasks/{id}                — Actualiza una subtarea (fechas, estado).
  PATCH  /subtasks/{id}/status         — Actualiza solo el estado.
  DELETE /subtasks/{id}                — Elimina una subtarea.
  POST   /subtasks/{id}/check-conflict — Verifica sobrecarga diaria (US-07).

Nota sobre orden de rutas:
  Las rutas con sufijos fijos como /{id}/check-conflict y /{id}/status
  deben registrarse ANTES de /{id} para que FastAPI no intente
  interpretar 'check-conflict' o 'status' como un UUID.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from ..database import get_db
from .. import crud, schemas

router = APIRouter(prefix="/subtasks", tags=["Subtasks"])


@router.post("/", response_model=schemas.Subtask)
def create_subtask(subtask: schemas.SubtaskCreate, db: Session = Depends(get_db)):
    """
    Crea una nueva subtarea asociada a una tarea (T1).

    El frontend la llama al crear una actividad con pasos desde CrearPage.

    Args:
        subtask (SubtaskCreate): Datos del paso (task_id, título, fecha, minutos).
        db (Session): Sesión de BD inyectada.

    Returns:
        Subtask: Subtarea creada.
    """
    return crud.create_subtask(db, subtask)


@router.get("/task/{task_id}", response_model=list[schemas.Subtask])
def get_subtasks(task_id: UUID, db: Session = Depends(get_db)):
    """
    Lista todas las subtareas de una tarea específica.

    Usado por ActividadPage al cargar el detalle de una tarea.

    Args:
        task_id (UUID): UUID de la tarea padre en la ruta.
        db (Session): Sesión de BD inyectada.

    Returns:
        list[Subtask]: Subtareas de la tarea.
    """
    return crud.get_subtasks_by_task(db, task_id)


@router.get("/daily-overload")
def get_daily_overload(user_id: UUID, limit_minutes: int, db: Session = Depends(get_db)):
    """
    Retorna los días que exceden el límite dado (US-12).

    Llamado desde HoyPage cuando el usuario guarda un nuevo límite diario,
    para informarle qué días ya tienen más horas planificadas que el nuevo valor.

    Args:
        user_id (UUID): UUID del usuario.
        limit_minutes (int): Límite a comparar (el nuevo que quiere guardar).
        db (Session): Sesión de BD inyectada.

    Returns:
        list[dict]: Días con sobrecarga [{ date, total_hours, overflow_hours, ... }]
    """
    return crud.get_overloaded_days(db, user_id, limit_minutes)


@router.get("/week-summary")
def get_week_summary(
    user_id: UUID,
    from_date: str,
    to_date: str,
    db: Session = Depends(get_db),
):
    """
    Retorna el resumen de minutos planificados por día para un rango de fechas.

    Usado en CrearPage y ActividadPage para mostrar la disponibilidad de
    cada día (horas usadas, horas libres) al elegir la fecha de una actividad.

    Args:
        user_id (UUID): UUID del usuario.
        from_date (str): Fecha inicio del rango (YYYY-MM-DD, inclusivo).
        to_date (str): Fecha fin del rango (YYYY-MM-DD, inclusivo).
        db (Session): Sesión de BD inyectada.

    Returns:
        list[dict]: [{ date, used_minutes, limit_minutes, free_minutes, over_limit }]
    """
    from datetime import date as date_type, timedelta
    start = date_type.fromisoformat(from_date)
    end   = date_type.fromisoformat(to_date)
    return crud.get_week_summary(db, user_id, start, end)



# ── Rutas con sufijos fijos — deben ir ANTES de /{subtask_id} ────────────────

@router.post("/{subtask_id}/check-conflict")
def check_conflict(
    subtask_id: UUID,
    target_date: str,
    estimated_minutes: int,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Verifica si reprogramar una subtarea genera sobrecarga diaria (US-07, T3).

    Suma los minutos estimados de todas las subtareas pendientes del usuario
    para el día indicado y evalúa si supera el límite diario configurado por
    el usuario (US-12). Excluye la subtarea actual del conteo.

    El frontend lo llama desde ActividadPage al cambiar la fecha de una subtarea.

    Args:
        subtask_id (UUID): UUID de la subtarea evaluada (se excluye del conteo).
        target_date (str): Fecha objetivo en formato ISO (YYYY-MM-DD).
        estimated_minutes (int): Minutos estimados de la subtarea.
        user_id (UUID): UUID del usuario propietario.
        db (Session): Sesión de BD inyectada.

    Returns:
        dict: {
            has_conflict, current_minutes, new_total_minutes,
            limit_minutes, current_hours, new_total_hours,
            limit_hours, message
        }
    """
    parsed_date = date.fromisoformat(target_date)
    return crud.check_overload_conflict(
        db=db,
        user_id=user_id,
        target_date=parsed_date,
        new_estimated_minutes=estimated_minutes,
        exclude_subtask_id=subtask_id,
    )


@router.patch("/{subtask_id}/status")
def update_status(subtask_id: UUID, status: str, db: Session = Depends(get_db)):
    """
    Actualiza únicamente el estado de una subtarea (T4 — registrar avance).

    Shortcut para marcar como hecha/pendiente sin enviar todos los campos.

    Args:
        subtask_id (UUID): UUID de la subtarea.
        status (str): Nuevo estado — 'pending' | 'done'.
        db (Session): Sesión de BD inyectada.

    Returns:
        Subtask: Subtarea actualizada.
    """
    return crud.update_subtask(db, subtask_id, schemas.SubtaskUpdate(status=status))


# ── Rutas genéricas /{subtask_id} — deben ir AL FINAL ────────────────────────

@router.get("/{subtask_id}", response_model=schemas.Subtask)
def get_subtask(subtask_id: UUID, db: Session = Depends(get_db)):
    """
    Obtiene una subtarea por su UUID.

    Usado por el frontend cuando necesita recargar una subtarea individual.

    Args:
        subtask_id (UUID): UUID de la subtarea.
        db (Session): Sesión de BD inyectada.

    Returns:
        Subtask: Subtarea encontrada.
    """
    return crud.get_subtask(db, subtask_id)


@router.patch("/{subtask_id}", response_model=schemas.Subtask)
def update_subtask(subtask_id: UUID, subtask: schemas.SubtaskUpdate, db: Session = Depends(get_db)):
    """
    Actualiza una subtarea parcialmente — T3 (reprogramar) y T4 (marcar avance).

    Permite modificar: título, descripción, fecha objetivo, minutos estimados
    o estado. Solo se actualizan los campos enviados en el request.

    Args:
        subtask_id (UUID): UUID de la subtarea a actualizar.
        subtask (SubtaskUpdate): Campos a modificar.
        db (Session): Sesión de BD inyectada.

    Returns:
        Subtask: Subtarea actualizada.
    """
    return crud.update_subtask(db, subtask_id, subtask)


@router.delete("/{subtask_id}")
def delete_subtask(subtask_id: UUID, db: Session = Depends(get_db)):
    """
    Elimina una subtarea por su UUID.

    Args:
        subtask_id (UUID): UUID de la subtarea a eliminar.
        db (Session): Sesión de BD inyectada.

    Returns:
        dict: Mensaje de confirmación.
    """
    return crud.delete_subtask(db, subtask_id)