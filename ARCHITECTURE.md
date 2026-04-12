# 🏗️ Arquitectura del Backend — Study Planner API

> **Stack:** FastAPI · SQLAlchemy · PostgreSQL (Supabase) · bcrypt · JWT (python-jose)  
> **Entorno:** 100% local · Uvicorn en `http://localhost:8000`

---

## 📁 Estructura de archivos

```
planificador_estudio_personal/BACK/
├── app/
│   ├── main.py          → Punto de entrada: instancia FastAPI, registra routers, CORS
│   ├── database.py      → Conexión a PostgreSQL (engine, sesión, get_db)
│   ├── models.py        → Modelos ORM (tablas de la BD)
│   ├── schemas.py       → Esquemas Pydantic (validación entrada/salida)
│   ├── crud.py          → Toda la lógica de negocio y consultas a la BD
│   ├── security.py      → bcrypt (contraseñas) + JWT (tokens)
│   └── routes/
│       ├── auth.py      → POST /auth/login · GET /auth/me
│       ├── users.py     → CRUD /users/ + configuración límite diario /users/{id}/config
│       ├── subjects.py  → CRUD /subjects/ + creación por email
│       ├── tasks.py     → CRUD /tasks/ + vista /hoy/prioridades + check-conflict por tarea
│       └── subtasks.py  → CRUD /subtasks/ + check-conflict + daily-overload + week-summary
├── requirements.txt     → Dependencias Python
├── render.yaml          → Configuración de deploy en Render (no usado en local)
└── .env                 → Variables de entorno (DATABASE_URL, SECRET_KEY) — NO subir a git
```

---

## 🔄 Flujo general de una petición HTTP

```
Cliente (Frontend React)
        │
        │  HTTP Request (con o sin JWT en el header)
        ▼
┌──────────────────┐
│    main.py       │  FastAPI recibe la petición
│  (CORS Middleware)│  Verifica el origen — orígenes permitidos:
│                  │    localhost:5173, localhost:3000
└────────┬─────────┘
         │  Redirige al router correspondiente
         ▼
┌──────────────────┐
│  routes/*.py     │  El router llama a la función del endpoint
│                  │  Si tiene Depends(get_current_user_email) → valida JWT
└────────┬─────────┘
         │  Inyecta db=Depends(get_db) + validación Pydantic automática
         ▼
┌──────────────────┐
│   crud.py        │  Lógica de negocio — consultas a la BD con SQLAlchemy
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  database.py     │  Sesión SQLAlchemy → PostgreSQL (Supabase)
└──────────────────┘
         │
         ▼
   Respuesta JSON serializada por Pydantic (schemas.py)
```

---

## 🔐 Seguridad: Contraseñas y Tokens JWT

> **Archivo:** `app/security.py`

### 1. Hash de contraseñas con bcrypt

```
Contraseña ingresada ("mi_clave_123")
        │
        ▼  hash_password()
  bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        │
        ▼
  "$2b$12$xxxxx..."  ← Hash guardado en la BD (columna users.password)
```

### 2. Generación del Token JWT

```python
# routes/auth.py → POST /auth/login
token = create_access_token({"sub": user.email})
```

| Parámetro | Valor |
|-----------|-------|
| Algoritmo | `HS256` |
| Expiración | 7 días (10,080 minutos) |
| Clave secreta | Variable de entorno `SECRET_KEY` |
| Payload principal | `sub` = email del usuario |

### 3. Validación del Token en endpoints protegidos

```
Authorization: Bearer <token>
        │
        ▼  get_current_user_email(credentials)
  jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        │
   Token válido?   │   Token inválido/expirado?
   → email (str)   │   → HTTP 401 "Token inválido"
```

---

## 🗄️ Base de Datos

> **Archivo:** `app/database.py` · `app/models.py`

### Modelos ORM (tablas)

| Modelo | Tabla | Campos clave |
|--------|-------|-------------|
| `User` | `users` | `id` (UUID PK), `email` (único), `password` (bcrypt), `first_name`, `last_name`, `birth_date`, `daily_limit_minutes` (default 360) |
| `Subject` | `subjects` | `id` (UUID PK), `name`, `color`, `user_id` → users (CASCADE DELETE) |
| `Task` | `tasks` | `id` (UUID PK), `title`, `task_type`, `subject_id` (nullable), `user_id`, `due_date`, `duration_minutes`, `priority`, `status` |
| `Subtask` | `subtasks` | `id` (UUID PK), `task_id` → tasks (CASCADE DELETE), `title`, `description`, `target_date`, `estimated_minutes`, `status`, `postpone_note` |

**Relaciones:**
```
User (1) ──< Subject (N)
User (1) ──< Task    (N)
Task (1) ──< Subtask (N)
```

**Cascadas:** al eliminar un `User` se eliminan sus `Subject` y `Task`. Al eliminar una `Task` se eliminan sus `Subtask`.

---

## 📡 Endpoints de la API

### Auth — `/auth`
| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| `POST` | `/auth/login` | Login → retorna JWT + datos del usuario | ❌ |
| `GET` | `/auth/me` | Datos del usuario autenticado (valida sesión) | ✅ JWT |

### Users — `/users`
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/users/` | Registrar nuevo usuario |
| `GET` | `/users/` | Listar todos los usuarios |
| `GET` | `/users/{id}` | Obtener usuario por UUID |
| `PATCH` | `/users/{id}` | Actualizar perfil del usuario |
| `DELETE` | `/users/{id}` | Eliminar usuario |
| `GET` | `/users/{id}/config` | Obtener límite diario `{ daily_limit_minutes }` (default: 360 min = 6h) |
| `PATCH` | `/users/{id}/config` | Actualizar límite diario `?daily_limit_minutes=480` |

### Subjects — `/subjects`
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/subjects/` | Crear materia (por user_id) |
| `POST` | `/subjects/by-email` | Crear materia (por user_email — usado desde el frontend) |
| `GET` | `/subjects/` | Listar materias del usuario |
| `GET` | `/subjects/by-email` | Listar materias por email |
| `GET` | `/subjects/{id}` | Obtener materia por UUID |
| `PATCH` | `/subjects/{id}` | Actualizar materia |
| `DELETE` | `/subjects/{id}` | Eliminar materia |

### Tasks — `/tasks`
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/tasks/` | Crear tarea (por user_id) |
| `POST` | `/tasks/by-email` | Crear tarea (por user_email + nombre de materia) |
| `GET` | `/tasks/` | Listar tareas del usuario |
| `GET` | `/tasks/by-email` | Listar tareas por email |
| `GET` | `/tasks/hoy/prioridades` | Vista diaria priorizada: `{ date, overdue, for_today, upcoming }` |
| `POST` | `/tasks/{id}/check-conflict` | **[Sprint 3]** Verificar si la duración de una tarea supera el límite diario |
| `GET` | `/tasks/{id}` | Obtener tarea por UUID |
| `PATCH` | `/tasks/{id}` | Actualizar tarea (título, fecha, duración, tipo, prioridad, estado, materia) |
| `DELETE` | `/tasks/{id}` | Eliminar tarea y sus pasos (CASCADE) |

**Vista diaria `/hoy/prioridades`** — reglas de priorización:
1. 🔴 Vencidas → más antiguas primero → menor esfuerzo en empate
2. 🟣 Para hoy → menor `estimated_minutes` primero
3. ⚪ Próximas → por `target_date` ascendente

> **Nota de orden de rutas:** Las rutas con sufijos fijos (`/by-email`, `/hoy/prioridades`, `/{id}/check-conflict`) se registran **antes** de `/{task_id}` para que FastAPI no intente interpretarlos como un UUID.

### Subtasks — `/subtasks`
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/subtasks/` | Crear paso |
| `GET` | `/subtasks/task/{task_id}` | Listar pasos de una tarea |
| `GET` | `/subtasks/daily-overload` | Detectar días con exceso al cambiar el límite global |
| `GET` | `/subtasks/week-summary` | **[Sprint 3]** Resumen de disponibilidad por día en un rango de fechas |
| `POST` | `/subtasks/{id}/check-conflict` | **[Sprint 3]** Verificar sobrecarga diaria al reprogramar un paso |
| `PATCH` | `/subtasks/{id}/status` | Actualizar solo el estado del paso |
| `GET` | `/subtasks/{id}` | Obtener paso por UUID |
| `PATCH` | `/subtasks/{id}` | Actualizar paso (título, desc, fecha, minutos, estado, nota) |
| `DELETE` | `/subtasks/{id}` | Eliminar paso |

---

## 🧠 Lógica de negocio clave (`crud.py`)

### `check_overload_conflict` — Conflicto al reprogramar un PASO

```
Parámetros: subtask_id, target_date, estimated_minutes, user_id

1. Obtiene daily_limit_minutes del usuario (default 360)
2. Suma estimated_minutes de todos los pasos pendientes del usuario
   para target_date, excluyendo el paso actual si está siendo editado
3. new_total = suma_existente + estimated_minutes

Retorna ConflictResult:
  has_conflict = new_total > daily_limit_minutes
  current_minutes, new_total_minutes, limit_minutes
  current_hours,   new_total_hours,   limit_hours
  message (descripción en lenguaje natural)
```

### `check_task_overload_conflict` — Conflicto al crear/editar una TAREA *(nuevo — Sprint 3)*

```
Parámetros: task_id, due_date, duration_minutes, user_id

1. Obtiene daily_limit_minutes del usuario (default 360)
2. Suma task.duration_minutes de otras tareas con ese due_date
3. Suma subtask.estimated_minutes de pasos pendientes con ese target_date
4. current_total = task_minutes + sub_minutes
   (excluye la tarea actual por task_id — soporta edición)
5. new_total = current_total + duration_minutes

Retorna ConflictResult (mismo formato que check_overload_conflict)
```

> **Diferencia clave:** `check_overload_conflict` solo cuenta pasos (`estimated_minutes`).  
> `check_task_overload_conflict` cuenta **también** la duración de otras tareas (`duration_minutes`), dando un total de carga diaria más preciso.

### `get_week_summary` — Disponibilidad diaria en un rango *(nuevo — Sprint 3)*

```
Parámetros: user_id, from_date, to_date

1. Suma subtask.estimated_minutes por día en el rango
2. Para cada día (inclusivo) genera:
   { date, used_minutes, limit_minutes, free_minutes, over_limit }

Usado por el frontend para mostrar disponibilidad al elegir fecha de una actividad.
```

### `get_daily_overload` — Días con exceso al cambiar límite

```
Parámetros: user_id, new_limit_minutes

1. Agrupa todos los pasos del usuario por target_date
2. Suma estimated_minutes por día
3. Filtra días donde la suma > new_limit_minutes

Retorna: lista de { date, total_minutes, excess_minutes }
```

### `get_today_view` — Vista diaria `/hoy/prioridades`

```
Parámetros: user_id (o user_email)

1. Obtiene subtareas pendientes del usuario con target_date definido
2. Clasifica según target_date vs hoy:
   - overdue:   target_date < hoy
   - for_today: target_date == hoy
   - upcoming:  target_date > hoy
3. Ordena según reglas de priorización
4. Retorna { date, overdue, for_today, upcoming }
```

---

## 🧩 Capas de la arquitectura

```
┌─────────────────────────────────────────────────────┐
│              CAPA DE PRESENTACIÓN                   │
│         routes/*.py  (FastAPI routers)              │
│  • Valida entrada con Pydantic (schemas.py)         │
│  • Inyecta dependencias (db, usuario actual)        │
│  • Serializa respuesta (schemas.py)                 │
├─────────────────────────────────────────────────────┤
│              CAPA DE NEGOCIO                        │
│         crud.py  (funciones puras)                  │
│  • check_overload_conflict  (conflicto por paso)    │
│  • check_task_overload_conflict (conflicto x tarea) │
│  • get_week_summary (disponibilidad semanal)        │
│  • get_daily_overload (exceso al cambiar límite)    │
│  • get_today_view (vista diaria priorizada)         │
├─────────────────────────────────────────────────────┤
│              CAPA DE DATOS                          │
│  models.py (ORM) + database.py (sesión)             │
│  • SQLAlchemy maneja el SQL generado                │
│  • PostgreSQL en Supabase (cloud)                   │
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ Variables de entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `DATABASE_URL` | URL de conexión PostgreSQL (Supabase) | ✅ Sí |
| `SECRET_KEY` | Clave para firmar los JWT | ✅ Sí (si no está en `.env`, usa un default inseguro) |

---

## 🚀 Cómo correr el proyecto localmente

```bash
# 1. Activar entorno virtual
.\venv\Scripts\activate

# 2. Arrancar el servidor con hot-reload
.\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# 3. Ver documentación interactiva
# http://localhost:8000/docs   → Swagger UI
# http://localhost:8000/redoc  → ReDoc
```

> **Nota:** Si `uvicorn` no está en el PATH, usa directamente el ejecutable del venv: `.\venv\Scripts\uvicorn.exe`

---

## 📦 Dependencias principales

| Paquete | Uso |
|---------|-----|
| `fastapi` | Framework web principal |
| `uvicorn` | Servidor ASGI |
| `sqlalchemy` | ORM para PostgreSQL |
| `psycopg2-binary` | Driver PostgreSQL |
| `pydantic` | Validación de datos de entrada/salida |
| `python-dotenv` | Carga de variables de entorno desde `.env` |
| `bcrypt==4.2.1` | Hash seguro de contraseñas |
| `python-jose[cryptography]==3.3.0` | Generación y validación de tokens JWT |
