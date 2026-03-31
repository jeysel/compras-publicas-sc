-- ─────────────────────────────────────────────────────────────────────────────
-- Compras Públicas — Inicialização do banco
-- Executado automaticamente pelo PostgreSQL na primeira inicialização
-- ─────────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;

GRANT ALL PRIVILEGES ON SCHEMA raw          TO cp_user;
GRANT ALL PRIVILEGES ON SCHEMA staging      TO cp_user;
GRANT ALL PRIVILEGES ON SCHEMA intermediate TO cp_user;
GRANT ALL PRIVILEGES ON SCHEMA marts        TO cp_user;
