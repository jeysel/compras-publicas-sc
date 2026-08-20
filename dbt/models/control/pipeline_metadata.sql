-- ─────────────────────────────────────────────────────────────────────────────
-- pipeline_metadata.sql
-- Tabela de controle da rotina de ingestão (spec 009) — não é dado de negócio.
-- Guarda estado entre execuções (ex.: último ETag processado do CSV do portal).
--
-- Materializada como table, mas sempre criada vazia: dbt build faz DROP+CREATE
-- a cada execução, então esta tabela não pode depender do próprio model dbt
-- para reter linhas. Quem escreve/atualiza linhas aqui é o script de ingestão
-- (via psql), sempre depois do dbt build terminar.
--
-- A constraint unique(chave), necessária pro upsert do script, NÃO é criada
-- aqui via post_hook: achado real de implementação — o materializer de
-- table do adapter postgres faz um swap (tabela antiga vira backup, nova
-- tabela assume o nome final) e só derruba o backup DEPOIS do post_hook
-- rodar. Um post_hook tentando recriar a constraint colide com a constraint
-- de mesmo nome que ainda existe no backup, cai em exceção e não recria
-- nada de verdade — resultado observado: tabela final sem constraint
-- nenhuma. Por isso a constraint é responsabilidade do script de ingestão
-- (CREATE UNIQUE INDEX IF NOT EXISTS, depois do dbt build já ter retornado
-- e o swap estar 100% concluído) — ver dbt/scripts/ingest.sh.
-- ─────────────────────────────────────────────────────────────────────────────

{{ config(materialized='table') }}

select
    cast(null as varchar)   as chave,
    cast(null as varchar)   as valor,
    cast(null as timestamp) as atualizado_em

where false
