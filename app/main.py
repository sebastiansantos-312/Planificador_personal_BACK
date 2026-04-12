"""
main.py — Punto de entrada de la API REST del Planificador de Estudio.

Este archivo inicializa la aplicación FastAPI, configura el middleware CORS
para permitir peticiones desde el frontend (Vercel), y registra todos los
routers de la aplicación.

Flujo de arranque:
  1. Se instancia la aplicación FastAPI con CORS configurado.
  2. Se crean las tablas en la base de datos si no existen.
  3. Se registran los routers: auth, users, subjects, tasks, subtasks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routes import tasks, users, subjects, subtasks, auth

# 1. Instanciar la aplicación PRIMERO para que CORS esté activo desde el inicio
app = FastAPI(title="Study Planner API", version="1.0.0")

# 2. Configurar CORS — debe registrarse ANTES que los routers
# Lista de orígenes permitidos (include_credentials=True requiere lista explícita, no "*")
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 3. Crear tablas en la BD a partir de los modelos SQLAlchemy
Base.metadata.create_all(bind=engine)

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