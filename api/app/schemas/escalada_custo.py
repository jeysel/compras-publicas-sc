from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class EscaladaCusto(BaseModel):
    cod_unidade_gestora: str = Field(..., description="Código da unidade gestora")
    nu_contrato: str = Field(..., description="Número do contrato")
    nm_unidade_gestora: str | None = Field(None, description="Nome da unidade gestora")
    nm_modalidade: str | None = Field(None, description="Modalidade de licitação (valor bruto da fonte)")
    ano_assinatura: int | None = Field(None, description="Ano de assinatura do contrato")
    mes_assinatura: int | None = Field(None, description="Mês de assinatura do contrato")
    dt_assinatura: date | None = Field(None, description="Data de assinatura do contrato")
    id_contratado: str = Field(..., description="Identificador do fornecedor (CNPJ ou CPF pré-mascarado pela fonte)")
    nm_contratado: str | None = Field(None, description="Nome/razão social do fornecedor")
    vl_original: Decimal | None = Field(None, description="Valor original do contrato")
    vl_atual: Decimal | None = Field(None, description="Valor atual do contrato")
    vl_variacao: Decimal | None = Field(
        None, description="Escalada de custo — métrica oficial (vl_atual - vl_original), spec 013/014"
    )
    perc_variacao: Decimal | None = Field(None, description="Percentual de variação sobre vl_original")
    dias_originais: int | None = Field(None, description="Prazo original em dias")
    dias_atuais: int | None = Field(None, description="Prazo atual em dias")
    dias_variacao: int | None = Field(None, description="Variação de prazo em dias")
    tp_variacao: str | None = Field(None, description="Classificação da variação de valor")
    fl_aditivo_inconsistente: bool | None = Field(
        None,
        description="Sinal de qualidade de dado (spec 013/014): true quando vl_aditado diverge de vl_variacao",
    )
