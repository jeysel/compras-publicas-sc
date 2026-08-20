from decimal import Decimal

from pydantic import BaseModel, Field


class Modalidade(BaseModel):
    nm_modalidade: str = Field(..., description="Nome da modalidade de licitação")
    qt_contratos: int = Field(..., description="Total de contratos na modalidade")
    qt_orgaos_distintos: int | None = Field(None, description="Quantidade de órgãos distintos que usaram a modalidade")
    qt_fornecedores_distintos: int | None = Field(None, description="Quantidade de fornecedores distintos na modalidade")
    vl_total_original: Decimal | None = Field(None, description="Soma dos valores originais")
    vl_total_atual: Decimal | None = Field(None, description="Soma dos valores atuais")
    vl_total_aditado: Decimal | None = Field(None, description="Soma dos valores de aditivo")
    vl_total_variacao: Decimal | None = Field(None, description="Soma da variação total")
    vl_medio_contrato: Decimal | None = Field(None, description="Valor médio dos contratos")
    vl_maior_contrato: Decimal | None = Field(None, description="Valor do maior contrato")
    vl_menor_contrato: Decimal | None = Field(None, description="Valor do menor contrato")
    perc_contratos_com_aditivo: Decimal | None = Field(None, description="Percentual de contratos que tiveram aditivo")
    rank_por_quantidade: int | None = Field(None, description="Ranking por quantidade de contratos")
    rank_por_valor: int | None = Field(None, description="Ranking por valor total")
    perc_sobre_total_qt: Decimal | None = Field(None, description="Percentual da modalidade sobre o total de contratos")
    perc_sobre_total_valor: Decimal | None = Field(None, description="Percentual da modalidade sobre o valor total")
