-- ─────────────────────────────────────────────────────────────────────────────
-- int_processos.sql
-- Agrupamento de contratos por processo licitatório (spec 007 — entidade
-- "Processo", NOVA). Grão: (cod_unidade_gestora, nu_processo).
--
-- nu_processo sozinho não é chave estável (mesma numeração é reaberta por
-- UG a cada ano — achado spec 007, Bloco 1); (cod_unidade_gestora,
-- nu_processo) resolve, mesma lógica já usada para nu_contrato (spec 003).
--
-- Exclui nu_processo placeholder: vazio, sem nenhum dígito (ex.: '-', '.',
-- 'SED', 'S/N', 'CT', 'xxx') ou com dígitos mas todos zero (ex.: '00',
-- '000', '0000/0000') — reconfirmado nesta sessão direto em
-- staging.stg_contratos (76.041 linhas): 4.482 linhas placeholder, 71.559
-- elegíveis, 43.953 processos únicos. Não confundir com contrato sem
-- processo formal (dispensa/inexigibilidade) — aqui o contrato só fica de
-- fora do agrupamento por Processo, continua existindo em stg_contratos/
-- fct_contratos normalmente.
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

elegiveis as (

    select *
    from contratos
    where not (
        nu_processo is null
        or trim(nu_processo) = ''
        or regexp_replace(nu_processo, '[^0-9]', '', 'g') = ''
        or regexp_replace(nu_processo, '[^0-9]', '', 'g') ~ '^0+$'
    )

),

agregado as (

    select
        cod_unidade_gestora,
        nu_processo,
        mode() within group (order by nm_unidade_gestora) as nm_unidade_gestora,

        count(*)                                        as qt_contratos,
        count(distinct id_contratado)                   as qt_fornecedores_distintos,
        count(distinct nm_modalidade)                   as qt_modalidades_distintas,

        coalesce(sum(vl_original), 0)                   as vl_total_original,
        coalesce(sum(vl_atual), 0)                      as vl_total_atual,
        coalesce(sum(vl_variacao), 0)                   as vl_total_variacao,

        min(dt_assinatura)                              as dt_primeiro_contrato,
        max(dt_assinatura)                              as dt_ultimo_contrato

    from elegiveis
    group by 1, 2

)

select * from agregado
