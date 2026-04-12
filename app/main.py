"""
main.py — Punto de entrada de la API REST del Planificador de Estudio.

Este archivo inicializa la aplicación FastAPI, configura el middleware CORS
para permitir peticiones desde el frontend (Vercel), y registra todos los
routers de la aplicación.

Flujo de arranque:
  1. Se crean las tablas en la base de datos si no existen.
  2. Se instancia la aplicación FastAPI.
  3. Se configura CORS para aceptar peticiones de cualquier origen.
  4. Se registran los routers: auth, users, subjects, tasks, subtasks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routes import tasks, users, subjects, subtasks, auth

# 1. Crear tablas en la BD a partir de los modelos SQLAlchemy
Base.metadata.create_all(bind=engine)

# 2. Instanciar la aplicación
app = FastAPI(title="Study Planner API", version="1.0.0")

# 3. Configurar CORS
# IMPORTANTE: allow_origins=["*"] es incompatible con allow_credentials=True
# según la especificación CORS. Se deben listar los orígenes explícitamente.
origins = [
    "http://localhost:5173",                                  # Vite dev server
    "http://localhost:3000",                                  # React dev server alternativo
    "https://planificador-personal-front.vercel.app",        # Producción Vercel (actual)
    "https://planificador-estudio-app-frontend.vercel.app",  # Producción Vercel (anterior)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Registrar routers — cada uno agrupa los endpoints de su dominio
app.include_router(auth.router)       # POST /auth/login
app.include_router(users.router)      # CRUD /users/
app.include_router(subjects.router)   # CRUD /subjects/
app.include_router(tasks.router)      # CRUD /tasks/ + vista /hoy
app.include_router(subtasks.router)   # CRUD /subtasks/ + check-conflict


@app.get("/")
def root():
    """Endpoint raíz. Confirma que la API está activa."""
    return {"message": "Study Planner API running ✅"}


@app.get("/health")
def health():
    """Health check. Usado por Render para verificar que el servicio responde."""
    return {"status": "ok"}