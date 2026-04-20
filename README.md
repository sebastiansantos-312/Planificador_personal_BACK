# 📚 Planificador de Estudio — Backend

> API REST para gestionar tareas académicas, materias y planificación diaria de estudio.

**Stack:** FastAPI · SQLAlchemy · PostgreSQL (Supabase) · bcrypt · JWT (python-jose) · Uvicorn  
**Deploy:** [planificador-personal-back.onrender.com](https://planificador-personal-back.onrender.com)  
**Documentación interactiva:** [/docs (Swagger UI)](https://planificador-personal-back.onrender.com/docs)  
**Frontend:** [planificador-personal-front.vercel.app](https://planificador-personal-front.vercel.app)

---

## 🚀 Funcionalidades

- 🔐 **Autenticación con JWT** — Login con bcrypt + tokens HS256 de 7 días
- 👤 **Usuarios** — Registro, perfil y configuración de límite diario de horas
- 🎨 **Materias** — CRUD con nombre y color personalizable
- 📝 **Tareas** — CRUD completo con tipo, prioridad, estado y materia opcional
- 📋 **Pasos (subtareas)** — CRUD con fechas objetivo, tiempo estimado y notas de posposición
- 📅 **Vista diaria priorizada** — Subtareas clasificadas: vencidas / para hoy / próximas
- ⚡ **Detección de conflictos** — Verifica si crear/editar una tarea o paso supera el límite diario
- 📊 **Resumen semanal** — Disponibilidad de horas por día en un rango de fechas

---

## 🗂️ Estructura del proyecto

```
app/
├── main.py          → Punto de entrada: FastAPI + CORS + routers
├── database.py      → Conexión a PostgreSQL (engine, sesión, get_db)
├── models.py        → Modelos ORM: User, Subject, Task, Subtask
├── schemas.py       → Esquemas Pydantic (validación entrada/salida)
├── crud.py          → Lógica de negocio y consultas a la BD
├── security.py      → bcrypt + JWT (creación y validación)
└── routes/
    ├── auth.py      → POST /auth/login · GET /auth/me
    ├── users.py     → CRUD /users/ + /users/{id}/config
    ├── subjects.py  → CRUD /subjects/
    ├── tasks.py     → CRUD /tasks/ + /hoy/prioridades + check-conflict
    └── subtasks.py  → CRUD /subtasks/ + check-conflict + daily-overload + week-summary
```

---

## 📡 Endpoints principales

### Auth
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/login` | Login → retorna JWT + datos del usuario |
| `GET` | `/auth/me` | Datos del usuario autenticado |

### Users
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/users/` | Registrar nuevo usuario |
| `GET` | `/users/{id}` | Obtener usuario por ID |
| `PATCH` | `/users/{id}` | Actualizar perfil |
| `DELETE` | `/users/{id}` | Eliminar usuario |
| `GET` | `/users/{id}/config` | Obtener límite diario de horas |
| `PATCH` | `/users/{id}/config` | Actualizar límite diario |

### Tasks
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/tasks/` | Crear tarea |
| `GET` | `/tasks/by-email` | Listar tareas por email de usuario |
| `GET` | `/tasks/hoy/prioridades` | Vista diaria: vencidas / hoy / próximas |
| `POST` | `/tasks/{id}/check-conflict` | Verificar conflicto de horas al crear/editar |
| `GET` | `/tasks/{id}` | Obtener tarea |
| `PATCH` | `/tasks/{id}` | Actualizar tarea |
| `DELETE` | `/tasks/{id}` | Eliminar tarea (cascade: elimina sus pasos) |

### Subtasks (Pasos)
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/subtasks/` | Crear paso |
| `GET` | `/subtasks/task/{task_id}` | Listar pasos de una tarea |
| `GET` | `/subtasks/daily-overload` | Detectar días con exceso al cambiar límite |
| `GET` | `/subtasks/week-summary` | Disponibilidad por día en un rango |
| `POST` | `/subtasks/{id}/check-conflict` | Verificar conflicto al reprogramar un paso |
| `GET` | `/subtasks/{id}` | Obtener paso |
| `PATCH` | `/subtasks/{id}` | Actualizar paso |
| `DELETE` | `/subtasks/{id}` | Eliminar paso |

### Subjects (Materias)
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/subjects/by-email` | Crear materia |
| `GET` | `/subjects/by-email` | Listar materias del usuario |
| `PATCH` | `/subjects/{id}` | Actualizar materia |
| `DELETE` | `/subjects/{id}` | Eliminar materia |

---

## ⚙️ Setup local

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear archivo .env con las variables necesarias
# (ver sección Variables de entorno)

# 4. Arrancar el servidor con hot-reload
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

---


| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `DATABASE_URL` | URL de conexión a PostgreSQL (Supabase) | ✅ Sí |
| `SECRET_KEY` | Clave para firmar los tokens JWT | ✅ Sí |

> ⚠️ El archivo `.env` **nunca se sube al repositorio**. En Render, configurar estas variables en **Settings → Environment Variables**.

---

## 🌐 Deploy en Render

1. Conectar este repositorio a Render (Runtime: **Python**)
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
4. En **Settings → Environment Variables**, agregar `DATABASE_URL` y `SECRET_KEY`

---

## 📦 Dependencias principales

| Paquete | Uso |
|---------|-----|
| `fastapi` | Framework web |
| `uvicorn` | Servidor ASGI |
| `sqlalchemy` | ORM para PostgreSQL |
| `psycopg2-binary` | Driver PostgreSQL |
| `pydantic` | Validación de datos |
| `python-dotenv` | Variables de entorno |
| `bcrypt==4.2.1` | Hash de contraseñas |
| `python-jose[cryptography]` | Tokens JWT |

---

## 📖 Documentación adicional

Ver [`ARCHITECTURE.md`](./ARCHITECTURE.md) para la arquitectura detallada, flujos de datos, lógica de negocio y esquema de base de datos.
