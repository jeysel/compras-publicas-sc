-- ─────────────────────────────────────────────────────────────────────────────
-- fct_contratos_ramo.sql
-- Contratos individuais com classificação por ramo de atividade
-- Exclui contratos de teste (objeto 'teste') e valores abaixo de R$ 1.000
-- ─────────────────────────────────────────────────────────────────────────────

with contratos as (

    select * from {{ ref('stg_contratos') }}

),

classificado as (

    select
        nu_contrato,
        id_contratado,
        nm_contratado,
        cod_unidade_gestora,
        nm_unidade_gestora,
        nm_modalidade,
        ds_objeto,
        dt_assinatura,
        ano_assinatura,
        vl_original,
        vl_atual,
        coalesce(vl_aditado, 0)     as vl_aditado,
        ds_situacao,

        case
            when lower(ds_objeto) like '%desenvolvimento de software%'
              or lower(ds_objeto) like '%desenvolvimento de sistema%'
                then 'TI - Desenvolvimento de Software'
            when lower(ds_objeto) like '%manutenção de software%'
              or lower(ds_objeto) like '%manutencao de software%'
              or (lower(ds_objeto) like '%sustentação%'
                  and lower(ds_objeto) like '%software%')
              or lower(ds_objeto) like '%suporte técnico%'
              or lower(ds_objeto) like '%suporte tecnico%'
              or lower(ds_objeto) like '%sigrh%'
              or lower(ds_objeto) like '%sigef%'
              or lower(ds_objeto) like '%sistema integrado%'
              or lower(ds_objeto) like '%manutenção corretiva%'
              or lower(ds_objeto) like '%manutencao corretiva%'
              or lower(ds_objeto) like '%manutenção evolutiva%'
              or lower(ds_objeto) like '%manutenção adaptativa%'
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
            when lower(ds_objeto) like '%alimenta%'
              or lower(ds_objeto) like '%refeição%'
              or lower(ds_objeto) like '%refeicao%'
              or lower(ds_objeto) like '%gêneros alimentícios%'
              or lower(ds_objeto) like '%generos alimenticios%'
              or lower(ds_objeto) like '%merenda%'
              or lower(ds_objeto) like '%pnae%'
              or lower(ds_objeto) like '%agua mineral%'
              or lower(ds_objeto) like '%água mineral%'
              or lower(ds_objeto) like '%ração%'
              or lower(ds_objeto) like '%racao%'
                then 'Alimentação'
            when lower(ds_objeto) like '%limpeza%'
              or lower(ds_objeto) like '%higiene%'
              or lower(ds_objeto) like '%saneante%'
                then 'Limpeza e Higiene'
            when lower(ds_objeto) like '%veículo%'
              or lower(ds_objeto) like '%veiculo%'
              or lower(ds_objeto) like '%viatura%'
              or lower(ds_objeto) like '%pneu%'
              or lower(ds_objeto) like '%peça%'
              or lower(ds_objeto) like '%revisão%'
              or lower(ds_objeto) like '%aferição%'
              or lower(ds_objeto) like '%etilômetro%'
                then 'Veículos e Manutenção'
            when lower(ds_objeto) like '%obra%'
              or lower(ds_objeto) like '%construção%'
              or lower(ds_objeto) like '%construcao%'
              or lower(ds_objeto) like '%pavimentação%'
              or lower(ds_objeto) like '%reforma%'
              or lower(ds_objeto) like '%hidráulico%'
                then 'Obras e Construção'
            when lower(ds_objeto) like '%água%'
              or lower(ds_objeto) like '%agua%'
              or lower(ds_objeto) like '%esgoto%'
              or lower(ds_objeto) like '%saneamento%'
                then 'Água e Saneamento'
            when lower(ds_objeto) like '%educação%'
              or lower(ds_objeto) like '%educacao%'
              or lower(ds_objeto) like '%ensino%'
              or lower(ds_objeto) like '%escola%'
              or lower(ds_objeto) like '%capacitação%'
              or lower(ds_objeto) like '%treinamento%'
              or lower(ds_objeto) like '%acervo bibliográfico%'
                then 'Educação e Capacitação'
            when lower(ds_objeto) like '%saúde%'
              or lower(ds_objeto) like '%saude%'
              or lower(ds_objeto) like '%medicamento%'
              or lower(ds_objeto) like '%hospitalar%'
              or lower(ds_objeto) like '%médico%'
              or lower(ds_objeto) like '%farmac%'
              or lower(ds_objeto) like '%laboratorial%'
              or lower(ds_objeto) like '%exame%'
              or lower(ds_objeto) like '%psicologia%'
              or lower(ds_objeto) like '%odontolog%'
              or lower(ds_objeto) like '%enfermagem%'
                then 'Saúde e Medicamentos'
            when lower(ds_objeto) like '%segurança%'
              or lower(ds_objeto) like '%seguranca%'
              or lower(ds_objeto) like '%armamento%'
              or lower(ds_objeto) like '%vigilância%'
              or lower(ds_objeto) like '%fardamento%'
              or lower(ds_objeto) like '%espingarda%'
              or lower(ds_objeto) like '%epi%'
                then 'Segurança Pública'
            when lower(ds_objeto) like '%locação%'
              or lower(ds_objeto) like '%locacao%'
              or lower(ds_objeto) like '%aluguel%'
              or lower(ds_objeto) like '%imóvel%'
                then 'Locação de Imóveis'
            when lower(ds_objeto) like '%transporte%'
              or lower(ds_objeto) like '%frete%'
              or lower(ds_objeto) like '%logística%'
                then 'Transporte e Logística'
            when lower(ds_objeto) like '%escritório%'
              or lower(ds_objeto) like '%expediente%'
              or lower(ds_objeto) like '%material gráfico%'
              or lower(ds_objeto) like '%lâmpada%'
              or lower(ds_objeto) like '%papel a4%'
              or lower(ds_objeto) like '%mobiliário%'
              or lower(ds_objeto) like '%cadeira%'
              or lower(ds_objeto) like '%ferramenta%'
              or lower(ds_objeto) like '%material elétrico%'
                then 'Material de Escritório e Equipamentos'
            when lower(ds_objeto) like '%agrícola%'
              or lower(ds_objeto) like '%agricola%'
              or lower(ds_objeto) like '%agropec%'
              or lower(ds_objeto) like '%epagri%'
              or lower(ds_objeto) like '%agricultura familiar%'
                then 'Agropecuária'
            when lower(ds_objeto) like '%meio ambiente%'
              or lower(ds_objeto) like '%hidrológico%'
              or lower(ds_objeto) like '%hidrometeorológico%'
              or lower(ds_objeto) like '%ambiental%'
                then 'Meio Ambiente e Recursos Hídricos'
            else 'Outros'
        end                         as ramo_atividade

    from contratos
    -- Exclui contratos de teste e valores abaixo de R$ 1.000
    where lower(ds_objeto) not in ('teste', 'teste.')
      and lower(trim(ds_objeto)) != 'teste'
      and vl_original > 1000

)

select * from classificado