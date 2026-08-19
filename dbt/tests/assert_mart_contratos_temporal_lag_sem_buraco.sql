-- Falha se a variação ano a ano (vl_variacao_ano_anterior) estiver
-- preenchida sem que o ano-1 realmente exista no mesmo recorte, ou nula
-- quando o ano-1 existe e deveria ter gerado valor. Testa exatamente o
-- guard contra buraco de ano usado em mart_contratos_temporal — sem essa
-- checagem, LAG() pularia silenciosamente pro ano disponível mais próximo
-- em recortes com cobertura esparsa (achado real nesta sessão: órgão
-- 150001, mês 1, anos 2020 e 2022 ausentes).

with base as (

    select * from {{ ref('mart_contratos_temporal') }}

),

com_ano_anterior_real as (

    select
        b.tp_recorte,
        b.cod_unidade_gestora,
        b.nm_modalidade,
        b.mes_assinatura,
        b.ano_assinatura,
        b.vl_total_atual,
        b.vl_variacao_ano_anterior,
        p.vl_total_atual as vl_ano_anterior_real

    from base b
    left join base p
      on  b.tp_recorte                            = p.tp_recorte
      and coalesce(b.cod_unidade_gestora, '')      = coalesce(p.cod_unidade_gestora, '')
      and coalesce(b.nm_modalidade, '')            = coalesce(p.nm_modalidade, '')
      and b.mes_assinatura                         = p.mes_assinatura
      and p.ano_assinatura                         = b.ano_assinatura - 1

)

select *
from com_ano_anterior_real
where (vl_ano_anterior_real is not null and vl_variacao_ano_anterior is null)
   or (vl_ano_anterior_real is null and vl_variacao_ano_anterior is not null)
   or (
        vl_ano_anterior_real is not null
        and vl_variacao_ano_anterior is not null
        and round(vl_variacao_ano_anterior, 2)
            <> round(vl_total_atual - vl_ano_anterior_real, 2)
      )
