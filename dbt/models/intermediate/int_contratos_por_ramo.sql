-- ─────────────────────────────────────────────────────────────────────────────
-- int_contratos_por_ramo.sql
-- Classificação de contratos por ramo de atividade
-- baseada em palavras-chave do campo ds_objeto (objeto do contrato), por falta de dados cadastrais dos fornecedores
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

classificado as (

    select
        *,
        case
            -- ── Tecnologia da Informação ─────────────────────────────────
            when lower(ds_objeto) like '%desenvolvimento de software%'
              or lower(ds_objeto) like '%desenvolvimento de sistema%'
                then 'TI - Desenvolvimento de Software'

            when lower(ds_objeto) like '%manutenção de software%'
              or lower(ds_objeto) like '%manutencao de software%'
              or (lower(ds_objeto) like '%sustentação%'
                  and lower(ds_objeto) like '%software%')
              or lower(ds_objeto) like '%suporte técnico%'
              or lower(ds_objeto) like '%suporte tecnico%'
                then 'TI - Manutenção e Suporte'

            when lower(ds_objeto) like '%licenciamento%'
              or lower(ds_objeto) like '%licença%'
              or lower(ds_objeto) like '%licenca%'
                then 'TI - Licenciamento de Software'

            when lower(ds_objeto) like '%software%'
              or lower(ds_objeto) like '%tecnologia%'
              or lower(ds_objeto) like '%informática%'
              or lower(ds_objeto) like '%informatica%'
              or lower(ds_objeto) like '%computador%'
              or lower(ds_objeto) like '%smartphone%'
              or lower(ds_objeto) like '%plataforma%'
              or lower(ds_objeto) like '%aplicativo%'
                then 'TI - Geral'

            -- ── Combustíveis e Energia ────────────────────────────────────
            when lower(ds_objeto) like '%combustível%'
              or lower(ds_objeto) like '%combustivel%'
              or lower(ds_objeto) like '%combust%'
              or lower(ds_objeto) like '%gasolina%'
              or lower(ds_objeto) like '%lubrificante%'
              or lower(ds_objeto) like '%diesel%'
              or lower(ds_objeto) like '%gás glp%'
              or lower(ds_objeto) like '%gas glp%'
              or lower(ds_objeto) like '%glp%'
              or lower(ds_objeto) like '%energia elétrica%'
              or lower(ds_objeto) like '%energia eletrica%'
                then 'Combustíveis e Energia'

            -- ── Alimentação ───────────────────────────────────────────────
            when lower(ds_objeto) like '%alimenta%'
              or lower(ds_objeto) like '%refeição%'
              or lower(ds_objeto) like '%refeicao%'
              or lower(ds_objeto) like '%gênero alimentício%'
              or lower(ds_objeto) like '%genero alimenticio%'
              or lower(ds_objeto) like '%gêneros alimentícios%'
              or lower(ds_objeto) like '%generos alimenticios%'
              or lower(ds_objeto) like '%merenda%'
              or lower(ds_objeto) like '%pnae%'
              or lower(ds_objeto) like '%agua mineral%'
              or lower(ds_objeto) like '%água mineral%'
              or lower(ds_objeto) like '%ração%'
              or lower(ds_objeto) like '%racao%'
                then 'Alimentação'

            -- ── Limpeza e Higiene ─────────────────────────────────────────
            when lower(ds_objeto) like '%limpeza%'
              or lower(ds_objeto) like '%higiene%'
              or lower(ds_objeto) like '%saneante%'
                then 'Limpeza e Higiene'

            -- ── Veículos e Manutenção ─────────────────────────────────────
            when lower(ds_objeto) like '%veículo%'
              or lower(ds_objeto) like '%veiculo%'
              or lower(ds_objeto) like '%viatura%'
              or lower(ds_objeto) like '%pneu%'
              or lower(ds_objeto) like '%peça%'
              or lower(ds_objeto) like '%revisão%'
              or lower(ds_objeto) like '%manutenção%'
              or lower(ds_objeto) like '%manutencao%'
              or lower(ds_objeto) like '%aferição%'
              or lower(ds_objeto) like '%afericao%'
              or lower(ds_objeto) like '%etilômetro%'
              or lower(ds_objeto) like '%etilometro%'
                then 'Veículos e Manutenção'

            -- ── Obras e Construção ────────────────────────────────────────
            when lower(ds_objeto) like '%obra%'
              or lower(ds_objeto) like '%construção%'
              or lower(ds_objeto) like '%construcao%'
              or lower(ds_objeto) like '%pavimentação%'
              or lower(ds_objeto) like '%pavimentacao%'
              or lower(ds_objeto) like '%reforma%'
              or lower(ds_objeto) like '%edificação%'
              or lower(ds_objeto) like '%hidráulico%'
              or lower(ds_objeto) like '%hidraulico%'
                then 'Obras e Construção'

            -- ── Água e Saneamento ─────────────────────────────────────────
            when lower(ds_objeto) like '%água%'
              or lower(ds_objeto) like '%agua%'
              or lower(ds_objeto) like '%esgoto%'
              or lower(ds_objeto) like '%saneamento%'
                then 'Água e Saneamento'

            -- ── Educação e Capacitação ────────────────────────────────────
            when lower(ds_objeto) like '%educação%'
              or lower(ds_objeto) like '%educacao%'
              or lower(ds_objeto) like '%ensino%'
              or lower(ds_objeto) like '%escola%'
              or lower(ds_objeto) like '%capacitação%'
              or lower(ds_objeto) like '%capacitacao%'
              or lower(ds_objeto) like '%treinamento%'
              or lower(ds_objeto) like '%acervo bibliográfico%'
              or lower(ds_objeto) like '%acervo bibliografico%'
                then 'Educação e Capacitação'

            -- ── Saúde e Medicamentos ──────────────────────────────────────
            when lower(ds_objeto) like '%saúde%'
              or lower(ds_objeto) like '%saude%'
              or lower(ds_objeto) like '%medicamento%'
              or lower(ds_objeto) like '%hospitalar%'
              or lower(ds_objeto) like '%médico%'
              or lower(ds_objeto) like '%medico%'
              or lower(ds_objeto) like '%farmac%'
              or lower(ds_objeto) like '%laboratorial%'
              or lower(ds_objeto) like '%exame%'
              or lower(ds_objeto) like '%psicologia%'
              or lower(ds_objeto) like '%odontolog%'
              or lower(ds_objeto) like '%enfermagem%'
                then 'Saúde e Medicamentos'

            -- ── Segurança Pública ─────────────────────────────────────────
            when lower(ds_objeto) like '%segurança%'
              or lower(ds_objeto) like '%seguranca%'
              or lower(ds_objeto) like '%armamento%'
              or lower(ds_objeto) like '%vigilância%'
              or lower(ds_objeto) like '%vigilancia%'
              or lower(ds_objeto) like '%fardamento%'
              or lower(ds_objeto) like '%espingarda%'
              or lower(ds_objeto) like '%epi%'
              or lower(ds_objeto) like '%equipamento de proteção%'
                then 'Segurança Pública'

            -- ── Locação de Imóveis ────────────────────────────────────────
            when lower(ds_objeto) like '%locação%'
              or lower(ds_objeto) like '%locacao%'
              or lower(ds_objeto) like '%aluguel%'
              or lower(ds_objeto) like '%imóvel%'
              or lower(ds_objeto) like '%imovel%'
                then 'Locação de Imóveis'

            -- ── Transporte e Logística ────────────────────────────────────
            when lower(ds_objeto) like '%transporte%'
              or lower(ds_objeto) like '%frete%'
              or lower(ds_objeto) like '%logística%'
              or lower(ds_objeto) like '%logistica%'
                then 'Transporte e Logística'

            -- ── Material de Escritório e Equipamentos ─────────────────────
            when lower(ds_objeto) like '%escritório%'
              or lower(ds_objeto) like '%escritorio%'
              or lower(ds_objeto) like '%expediente%'
              or lower(ds_objeto) like '%material gráfico%'
              or lower(ds_objeto) like '%lâmpada%'
              or lower(ds_objeto) like '%lampada%'
              or lower(ds_objeto) like '%papel a4%'
              or lower(ds_objeto) like '%mobiliário%'
              or lower(ds_objeto) like '%mobiliario%'
              or lower(ds_objeto) like '%cadeira%'
              or lower(ds_objeto) like '%ferramenta%'
              or lower(ds_objeto) like '%material elétrico%'
              or lower(ds_objeto) like '%material eletrico%'
                then 'Material de Escritório e Equipamentos'

            -- ── Agropecuária ──────────────────────────────────────────────
            when lower(ds_objeto) like '%agrícola%'
              or lower(ds_objeto) like '%agricola%'
              or lower(ds_objeto) like '%agropec%'
              or lower(ds_objeto) like '%insumo agrícola%'
              or lower(ds_objeto) like '%insumo agricola%'
              or lower(ds_objeto) like '%epagri%'
              or lower(ds_objeto) like '%agricultura familiar%'
                then 'Agropecuária'

            -- ── Meio Ambiente e Recursos Hídricos ─────────────────────────
            when lower(ds_objeto) like '%meio ambiente%'
              or lower(ds_objeto) like '%hidrológico%'
              or lower(ds_objeto) like '%hidrologico%'
              or lower(ds_objeto) like '%hidrometeorológico%'
              or lower(ds_objeto) like '%hidrometeorologico%'
              or lower(ds_objeto) like '%ambiental%'
                then 'Meio Ambiente e Recursos Hídricos'

            else 'Outros'
        end as ramo_atividade

    from contratos

),

agregado as (

    select
        ramo_atividade,

        count(*)                                        as qt_contratos,
        count(distinct id_contratado)                   as qt_fornecedores,
        count(distinct cod_unidade_gestora)             as qt_orgaos,

        coalesce(sum(vl_original), 0)                   as vl_total_original,
        coalesce(sum(vl_atual), 0)                      as vl_total_atual,
        coalesce(sum(vl_aditado), 0)                    as vl_total_aditado,

        coalesce(avg(vl_original), 0)                   as vl_medio_contrato,
        coalesce(max(vl_atual), 0)                      as vl_maior_contrato

    from classificado
    group by 1

),

com_ranking as (

    select
        *,
        rank() over (order by qt_contratos desc)        as rank_por_quantidade,
        rank() over (order by vl_total_atual desc)      as rank_por_valor,
        round(
            qt_contratos * 100.0 / nullif(sum(qt_contratos) over (), 0),
            2
        )                                               as perc_sobre_total_qt,
        round(
            vl_total_atual * 100.0 / nullif(sum(vl_total_atual) over (), 0),
            2
        )                                               as perc_sobre_total_valor

    from agregado

)

select * from com_ranking