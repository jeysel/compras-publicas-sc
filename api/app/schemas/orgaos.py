from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class Orgao(BaseModel):
    cod_unidade_gestora: str = Field(..., description="Código da unidade gestora")
    nm_unidade_gestora: str = Field(..., description="Nome da unidade gestora")
    cod_gestao: str | None = Field(None, description="Código da gestão")
    nm_gestao: str | None = Field(None, description="Nome da gestão")
    qt_contratos: int = Field(..., description="Total de contratos do órgão")
    qt_fornecedores_distintos: int | None = Field(None, description="Quantidade de fornecedores distintos contratados")
    vl_total_original: Decimal | None = Field(None, description="Soma dos valores originais")
    vl_total_atual: Decimal | None = Field(None, description="Soma dos valores atuais")
    vl_total_aditado: Decimal | None = Field(None, description="Soma dos valores de aditivo")
    vl_total_variacao: Decimal | None = Field(None, description="Soma da variação total")
    vl_medio_contrato: Decimal | None = Field(None, description="Valor médio dos contratos")
    vl_maior_contrato: Decimal | None = Field(None, description="Valor do maior contrato")
    vl_menor_contrato: Decimal | None = Field(None, description="Valor do menor contrato")
    dt_primeiro_contrato: date | None = Field(None, description="Data do primeiro contrato")
    dt_ultimo_contrato: date | None = Field(None, description="Data do último contrato")
    rank_por_valor: int | None = Field(None, description="Ranking do órgão por valor total contratado")
    rank_por_quantidade: int | None = Field(None, description="Ranking do órgão por quantidade de contratos")
    ds_situacao_aditivo: str | None = Field(None, description="Classificação textual da situação de aditivo do órgão")
    ds_perfil_contratacao: str | None = Field(None, description="Classificação textual do perfil de contratação do órgão")
