"""
models.py — Modelos ORM que representan las tablas de la base de datos.
"""

from sqlalchemy import Column, String, Integer, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
import uuid

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)                   # ← Fix M2
    last_name = Column(String, nullable=False)                    # ← Fix M2
    email = Column(String, nullable=False, unique=True)           # ← Fix M2
    password = Column(String, nullable=False)                     # ← Fix M2
    birth_date = Column(Date)
    created_at = Column(TIMESTAMP, server_default=func.now())
    daily_limit_minutes = Column(Integer, default=360)            # ← Sprint 3


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)                         # ← Fix M2
    color = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))  # ← Fix M1
    created_at = Column(TIMESTAMP, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)                        # ← Fix M2
    task_type = Column(String)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"))  # ← Fix M1
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))         # ← Fix M1
    due_date = Column(Date)
    duration_minutes = Column(Integer)
    priority = Column(String)
    status = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))  # ← Fix M1
    title = Column(String, nullable=False)                        # ← Fix M2
    description = Column(Text)
    target_date = Column(Date)
    estimated_minutes = Column(Integer)
    status = Column(String)
    postpone_note = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())