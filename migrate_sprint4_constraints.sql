-- ============================================================
-- migrate_sprint4_constraints.sql
-- Sprint 4 — Agregar CHECK constraints de status a tablas
--            existentes y crear índices de rendimiento.
--
-- EJECUTAR UNA SOLA VEZ contra la base de datos PostgreSQL.
-- Los constraints en models.py solo aplican a tablas nuevas;
-- esta migración los agrega a las tablas ya existentes.
-- ============================================================

-- 1. Limpiar valores inválidos antes de agregar constraints
--    (seguridad: si hubiera algún status inconsistente)
UPDATE tasks
SET status = 'pending'
WHERE status IS NOT NULL
  AND status NOT IN ('pending', 'in_progress', 'done', 'postponed');

UPDATE subtasks
SET status = 'pending'
WHERE status IS NOT NULL
  AND status NOT IN ('pending', 'done', 'postponed');

-- 2. Agregar CHECK constraint a tasks
ALTER TABLE tasks
    ADD CONSTRAINT chk_task_status
    CHECK (status IN ('pending', 'in_progress', 'done', 'postponed'));

-- 3. Agregar CHECK constraint a subtasks
ALTER TABLE subtasks
    ADD CONSTRAINT chk_subtask_status
    CHECK (status IN ('pending', 'done', 'postponed'));

-- 4. Índices de rendimiento (idempotentes con IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_tasks_user_id
    ON tasks (user_id);

CREATE INDEX IF NOT EXISTS idx_subtasks_task_id
    ON subtasks (task_id);

CREATE INDEX IF NOT EXISTS idx_subtasks_status
    ON subtasks (status);

-- ============================================================
-- Verificación post-migración:
--   SELECT conname FROM pg_constraint WHERE conname LIKE 'chk_%';
-- Debería listar: chk_task_status, chk_subtask_status
-- ============================================================
