-- ─────────────────────────────────────────────────────────────────────────────
-- Compras Públicas — Inicialização do banco
-- Executado automaticamente pelo PostgreSQL na primeira inicialização
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Schemas ───────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;

-- ── Permissões ────────────────────────────────────────────────────────────────
GRANT ALL PRIVILEGES ON SCHEMA raw          TO cp_user;
GRANT ALL PRIVILEGES ON SCHEMA staging      TO cp_user;
GRANT ALL PRIVILEGES ON SCHEMA intermediate TO cp_user;
GRANT ALL PRIVILEGES ON SCHEMA marts        TO cp_user;

-- ── Tabela dim_datas no schema raw ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw.dim_datas (
    dt_data             DATE        PRIMARY KEY,
    ano                 INTEGER     NOT NULL,
    mes                 INTEGER     NOT NULL,
    dia                 INTEGER     NOT NULL,
    trimestre           INTEGER     NOT NULL,
    semana_ano          INTEGER     NOT NULL,
    dia_semana_num      INTEGER     NOT NULL,
    nm_mes              VARCHAR(20) NOT NULL,
    nm_mes_abrev        VARCHAR(5)  NOT NULL,
    nm_dia_semana       VARCHAR(20) NOT NULL,
    ano_mes             VARCHAR(7)  NOT NULL,
    nm_trimestre        VARCHAR(10) NOT NULL,
    sigla_trimestre     VARCHAR(2)  NOT NULL,
    fl_fim_de_semana    BOOLEAN     NOT NULL,
    primeiro_dia_mes    DATE        NOT NULL,
    ultimo_dia_mes      DATE        NOT NULL
);

-- ── Procedure para popular dim_datas ─────────────────────────────────────────
CREATE OR REPLACE PROCEDURE raw.sp_popula_dim_datas(
    p_data_inicio DATE DEFAULT '2015-01-01',
    p_data_fim    DATE DEFAULT '2030-12-31'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_data DATE := p_data_inicio;
BEGIN
    WHILE v_data <= p_data_fim LOOP

        INSERT INTO raw.dim_datas (
            dt_data,
            ano,
            mes,
            dia,
            trimestre,
            semana_ano,
            dia_semana_num,
            nm_mes,
            nm_mes_abrev,
            nm_dia_semana,
            ano_mes,
            nm_trimestre,
            sigla_trimestre,
            fl_fim_de_semana,
            primeiro_dia_mes,
            ultimo_dia_mes
        )
        VALUES (
            v_data,
            EXTRACT(YEAR    FROM v_data)::INTEGER,
            EXTRACT(MONTH   FROM v_data)::INTEGER,
            EXTRACT(DAY     FROM v_data)::INTEGER,
            EXTRACT(QUARTER FROM v_data)::INTEGER,
            EXTRACT(WEEK    FROM v_data)::INTEGER,
            EXTRACT(DOW     FROM v_data)::INTEGER,
            TO_CHAR(v_data, 'TMMonth'),
            TO_CHAR(v_data, 'TMMon'),
            TO_CHAR(v_data, 'TMDay'),
            TO_CHAR(v_data, 'YYYY-MM'),
            TO_CHAR(v_data, 'Q"º Tri"'),
            CASE EXTRACT(QUARTER FROM v_data)::INTEGER
                WHEN 1 THEN 'Q1'
                WHEN 2 THEN 'Q2'
                WHEN 3 THEN 'Q3'
                WHEN 4 THEN 'Q4'
            END,
            EXTRACT(DOW FROM v_data) IN (0, 6),
            DATE_TRUNC('month', v_data)::DATE,
            (DATE_TRUNC('month', v_data) + INTERVAL '1 month - 1 day')::DATE
        )
        ON CONFLICT (dt_data) DO NOTHING;

        v_data := v_data + INTERVAL '1 day';

    END LOOP;
END;
$$;

-- ── Executa a procedure ───────────────────────────────────────────────────────
CALL raw.sp_popula_dim_datas('2015-01-01', '2030-12-31');

-- ── Permissão na tabela ───────────────────────────────────────────────────────
GRANT ALL PRIVILEGES ON TABLE raw.dim_datas TO cp_user;