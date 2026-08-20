from decimal import Decimal

from pydantic import BaseModel, Field


class ContratosTemporal(BaseModel):
    tp_recorte: str = Field(..., description="Nível de recorte: 'Geral', 'Órgão' ou 'Modalidade'")
    ano_assinatura: int = Field(..., description="Ano de assinatura do contrato")
    mes_assinatura: int = Field(..., description="Mês de assinatura do contrato")
    cod_unidade_gestora: str | None = Field(
        None, description="Código da unidade gestora — preenchido só quando tp_recorte = 'Órgão'"
    )
    nm_unidade_gestora: str | None = Field(
        None, description="Nome da unidade gestora — preenchido só quando tp_recorte = 'Órgão'"
    )
    nm_modalidade: str | None = Field(
        None, description="Modalidade de licitação — preenchida só quando tp_recorte = 'Modalidade'"
    )
    qt_contratos: int = Field(..., description="Quantidade de contratos no período/recorte")
    vl_total_original: Decimal | None = Field(None, description="Soma dos valores originais no período/recorte")
    vl_total_atual: Decimal | None = Field(None, description="Soma dos valores atuais no período/recorte")
    vl_total_variacao: Decimal | None = Field(None, description="Soma da variação no período/recorte")
    qt_contratos_acumulado_ano: int | None = Field(
        None, description="Quantidade acumulada de contratos no ano até o mês — só em tp_recorte = 'Geral'"
    )
    vl_acumulado_ano: Decimal | None = Field(
        None, description="Valor acumulado no ano até o mês — só em tp_recorte = 'Geral'"
    )
    vl_mesmo_mes_ano_anterior: Decimal | None = Field(
        None, description="vl_total_atual do mesmo mês, ano-1, no mesmo recorte — null se não houver ano-1"
    )
    vl_variacao_ano_anterior: Decimal | None = Field(
        None, description="vl_total_atual - vl_mesmo_mes_ano_anterior — null se não houver ano-1"
    )
    perc_variacao_ano_anterior: Decimal | None = Field(
        None, description="Percentual de variação sobre o mesmo mês do ano anterior"
    )
    vl_media_movel_3anos: Decimal | None = Field(
        None, description="Média de vl_total_atual dos últimos 3 anos-calendário para o mesmo mês/recorte"
    )
