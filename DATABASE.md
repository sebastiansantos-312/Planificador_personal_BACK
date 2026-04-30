# 🗄️ Base de Datos — Study Planner

> **Proveedor:** Supabase (PostgreSQL 15)  
> **ORM local:** SQLAlchemy (ver `app/models.py`)  
> **Validación:** Pydantic con `Literal` (ver `app/schemas.py`)

---

## Diagrama de relaciones

```
users
 │
 ├──< subjects   (user_id → users.id  ON DELETE CASCADE)
 │
 └──< tasks      (user_id → users.id  ON DELETE CASCADE)
       │
       └──< subtasks  (task_id → tasks.id  ON DELETE CASCADE)
```

- Borrar un **usuario** elimina todas sus materias y tareas.
- Borrar una **tarea** elimina todas sus subtareas.
- Borrar una **materia** pone `subject_id = NULL` en las tareas (SET NULL).

---

## Tablas

### `users`

| Columna | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Identificador único |
| `first_name` | `TEXT` | NOT NULL | Nombre |
| `last_name` | `TEXT` | NOT NULL | Apellido |
| `email` | `TEXT` | NOT NULL, UNIQUE | Email (login) |
| `password` | `TEXT` | NOT NULL | Hash bcrypt |
| `birth_date` | `DATE` | NULL | Fecha de nacimiento |
| `daily_limit_minutes` | `INTEGER` | default `360` | Límite diario de estudio (6h) |
| `created_at` | `TIMESTAMP` | default `now()` | Fecha de registro |

**Constraints:**
- `users_pkey` → PK en `id`
- `users_email_key` → UNIQUE en `email`

---

### `subjects`

| Columna | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Identificador único |
| `name` | `TEXT` | NOT NULL | Nombre de la materia |
| `color` | `TEXT` | NULL | Color hex (ej: `#6366f1`) |
| `user_id` | `UUID` | FK → `users.id` | Propietario |
| `created_at` | `TIMESTAMP` | default `now()` | Fecha de creación |

**Constraints:**
- `subjects_pkey` → PK en `id`
- `subjects_user_id_fkey` → FK a `users.id` ON DELETE CASCADE

---

### `tasks`

| Columna | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Identificador único |
| `title` | `TEXT` | NOT NULL | Título de la actividad |
| `task_type` | `VARCHAR` | NULL | Tipo: `examen`, `quiz`, `taller`, `proyecto`, `exposición`, `otro` |
| `subject_id` | `UUID` | FK → `subjects.id`, NULL | Materia asociada |
| `user_id` | `UUID` | FK → `users.id` | Propietario |
| `due_date` | `DATE` | NULL | Fecha límite de entrega |
| `duration_minutes` | `INTEGER` | NULL | Duración estimada total |
| `priority` | `TEXT` | NULL | `alta` / `media` / `baja` |
| `status` | `TEXT` | default `'pending'`, CHECK | Estado actual |
| `postpone_note` | `TEXT` | NULL | Nota al posponer (Sprint 4) |
| `created_at` | `TIMESTAMP` | default `now()` | Fecha de creación |

**Constraints:**
- `tasks_pkey` → PK en `id`
- `tasks_user_id_fkey` → FK a `users.id` ON DELETE CASCADE
- `tasks_subject_id_fkey` → FK a `subjects.id` ON DELETE SET NULL
- `tasks_status_check` → CHECK:
  ```sql
  status IN ('pending', 'in_progress', 'done', 'postponed')
  ```

---

### `subtasks`

| Columna | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Identificador único |
| `task_id` | `UUID` | FK → `tasks.id` | Tarea padre |
| `title` | `TEXT` | NOT NULL | Título del paso |
| `description` | `TEXT` | NULL | Descripción opcional |
| `target_date` | `DATE` | NULL | Fecha objetivo del paso |
| `estimated_minutes` | `INTEGER` | NULL | Minutos estimados |
| `status` | `TEXT` | default `'pending'`, CHECK | Estado actual |
| `postpone_note` | `TEXT` | NULL | Nota al posponer (Sprint 4) |
| `created_at` | `TIMESTAMP` | default `now()` | Fecha de creación |

**Constraints:**
- `subtasks_pkey` → PK en `id`
- `subtasks_task_id_fkey` → FK a `tasks.id` ON DELETE CASCADE
- `subtasks_status_check` → CHECK:
  ```sql
  status IN ('pending', 'done', 'postponed')
  ```

---

## Estados válidos

### `tasks.status`

| Valor | Descripción | Transiciones válidas |
|---|---|---|
| `pending` | Sin comenzar | → `in_progress`, `done`, `postponed` |
| `in_progress` | En curso | → `pending`, `done`, `postponed` |
| `done` | Completada | → `pending`, `in_progress` |
| `postponed` | Pospuesta (con nota opcional) | → `pending`, `in_progress` |

### `subtasks.status`

| Valor | Descripción | Transiciones válidas |
|---|---|---|
| `pending` | Sin hacer | → `done`, `postponed` |
| `done` | Completada | → `pending` |
| `postponed` | Pospuesta (con nota opcional) | → `pending` |

> **Nota:** Al cambiar de `postponed` a `pending`, el frontend limpia `postpone_note = ""` automáticamente.

---

## Decisiones de diseño

### ¿Por qué `status` es `TEXT` con CHECK y no `ENUM`?

PostgreSQL permite ENUMs nativos pero tienen una limitación: **agregar un valor nuevo requiere un `ALTER TYPE`** que bloquea la tabla. Con `TEXT + CHECK` solo se ejecuta `ALTER TABLE ... DROP CONSTRAINT ... ADD CONSTRAINT ...`, más liviano y compatible con Supabase sin migraciones complejas.

### ¿Por qué `postpone_note` está en ambas tablas?

- **`tasks.postpone_note`:** el estado global de la actividad puede posponer con contexto (ej: "examen se corrió una semana").
- **`subtasks.postpone_note`:** cada paso puede tener su propia razón de posposición independiente.

### ¿Por qué no hay columna `progress` en `tasks`?

El progreso se calcula **dinámicamente** a partir del conteo de subtareas:
```
percent = round((done_count / total_count) * 100)
```
Guardar un porcentaje precalculado introduciría inconsistencias si las subtareas cambian directamente.

---

## Correspondencia con el código

| BD | ORM (`models.py`) | Schema (`schemas.py`) |
|---|---|---|
| `users` | `class User(Base)` | `User`, `UserCreate`, `UserUpdate` |
| `subjects` | `class Subject(Base)` | `Subject`, `SubjectCreate`, `SubjectUpdate` |
| `tasks` | `class Task(Base)` | `Task`, `TaskCreate`, `TaskUpdate` |
| `subtasks` | `class Subtask(Base)` | `Subtask`, `SubtaskCreate`, `SubtaskUpdate` |

> Los schemas usan `Literal["pending", "done", ...]` para validar `status` **antes** de que llegue a la BD, dando error 422 si el valor no es válido.

---

## SQL completo del schema (referencia)

```sql
-- USERS
create table public.users (
  id uuid not null default gen_random_uuid(),
  first_name text not null,
  last_name text not null,
  email text not null,
  password text not null,
  birth_date date null,
  created_at timestamp without time zone null default now(),
  daily_limit_minutes integer null default 360,
  constraint users_pkey primary key (id),
  constraint users_email_key unique (email)
);

-- SUBJECTS
create table public.subjects (
  id uuid not null default gen_random_uuid(),
  name text not null,
  color text null,
  user_id uuid null,
  created_at timestamp without time zone null default now(),
  constraint subjects_pkey primary key (id),
  constraint subjects_user_id_fkey foreign key (user_id)
    references users (id) on delete cascade
);

-- TASKS
create table public.tasks (
  id uuid not null default gen_random_uuid(),
  title text not null,
  subject_id uuid null,
  user_id uuid null,
  due_date date null,
  duration_minutes integer null,
  priority text null,
  status text null default 'pending'::text,
  created_at timestamp without time zone null default now(),
  task_type character varying null,
  postpone_note text null,
  constraint tasks_pkey primary key (id),
  constraint tasks_subject_id_fkey foreign key (subject_id)
    references subjects (id) on delete set null,
  constraint tasks_user_id_fkey foreign key (user_id)
    references users (id) on delete cascade,
  constraint tasks_status_check check (
    status = any (array['pending'::text, 'in_progress'::text, 'done'::text, 'postponed'::text])
  )
);

-- SUBTASKS
create table public.subtasks (
  id uuid not null default gen_random_uuid(),
  task_id uuid null,
  title text not null,
  description text null,
  target_date date null,
  estimated_minutes integer null,
  status text null default 'pending'::text,
  created_at timestamp without time zone null default now(),
  postpone_note text null,
  constraint subtasks_pkey primary key (id),
  constraint subtasks_task_id_fkey foreign key (task_id)
    references tasks (id) on delete cascade,
  constraint subtasks_status_check check (
    status = any (array['pending'::text, 'done'::text, 'postponed'::text])
  )
);
```
