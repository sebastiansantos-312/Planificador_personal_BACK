"""
schemas.py — Esquemas Pydantic para validación y serialización de datos.
"""

from pydantic import BaseModel
from datetime import date, datetime
from uuid import UUID
from typing import Optional


# ─── USER ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    birth_date: Optional[date] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    birth_date: Optional[date] = None
    daily_limit_minutes: Optional[int] = None


class User(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    created_at: Optional[datetime] = None
    daily_limit_minutes: Optional[int] = 360

    class Config:
        from_attributes = True


# ─── SUBJECT ─────────────────────────────────────────────────────────────────

class SubjectCreate(BaseModel):
    name: str
    color: Optional[str] = None
    user_id: UUID


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class Subject(BaseModel):
    id: UUID
    name: str
    color: Optional[str] = None
    user_id: UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── TASK ────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    """
    Datos para crear una tarea con IDs directamente.
    task_type: Tipo de actividad requerido por US-01.
               Valores: 'examen' | 'quiz' | 'taller' | 'proyecto' | 'exposición' | 'otro'
    """
    title: str
    task_type: Optional[str] = None                               # ← NUEVO (US-01)
    subject_id: Optional[UUID] = None
    user_id: UUID
    due_date: Optional[date] = None
    duration_minutes: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = "pending"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    task_type: Optional[str] = None                               # ← NUEVO (US-01)
    subject_id: Optional[UUID] = None
    due_date: Optional[date] = None
    duration_minutes: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class Task(BaseModel):
    """Representación completa de una tarea en las respuestas de la API."""
    id: UUID
    title: str
    task_type: Optional[str] = None                               # ← NUEVO (US-01)
    subject_id: Optional[UUID] = None
    user_id: UUID
    due_date: Optional[date] = None
    duration_minutes: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── SUBTASK ─────────────────────────────────────────────────────────────────

class SubtaskCreate(BaseModel):
    task_id: UUID
    title: str
    description: Optional[str] = None
    target_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    status: Optional[str] = "pending"


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    status: Optional[str] = None
    postpone_note: Optional[str] = None


class Subtask(BaseModel):
    id: UUID
    task_id: UUID
    title: str
    description: Optional[str] = None
    target_date: Optional[date] = None
    estimated_minutes: Optional[int] = None
    status: Optional[str] = None
    postpone_note: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── VARIANTES POR EMAIL ─────────────────────────────────────────────────────

class SubjectCreateByEmail(BaseModel):
    name: str
    color: Optional[str] = None
    user_email: str


class TaskCreateByEmail(BaseModel):
    """
    Alternativa a TaskCreate que acepta email y nombre de materia.
    task_type agregado para consistencia con TaskCreate (US-01).
    """
    title: str
    task_type: Optional[str] = None                               # ← NUEVO (US-01)
    subject_name: str
    user_email: str
    due_date: Optional[date] = None
    duration_minutes: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = "pending"