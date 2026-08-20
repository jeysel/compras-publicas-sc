from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class DiversidadeVencedores(BaseModel):
    cod_unidade_gestora: str = Field(..., description="Código da unidade gestora")
    nm_unidade_gestora: str | None = Field(None, description="Nome da unidade gestora")
    nu_processo: str = Field(..., description="Número do processo licitatório")
    qt_contratos: int = Field(..., description="Quantidade de contratos vinculados a este processo")
    qt_fornecedores_distintos: int = Field(
        ..., description="Quantidade de fornecedores distintos que venceram contratos deste processo"
    )
    qt_modalidades_distintas: int | None = Field(
        None, description="Quantidade de modalidades distintas usadas nos contratos deste processo"
    )
    vl_total_original: Decimal | None = Field(None, description="Soma de vl_original dos contratos deste processo")
    vl_total_atual: Decimal | None = Field(None, description="Soma de vl_atual dos contratos deste processo")
    vl_total_variacao: Decimal | None = Field(None, description="Soma de vl_variacao dos contratos deste processo")
    dt_primeiro_contrato: date | None = Field(None, description="Data de assinatura do contrato mais antigo")
    dt_ultimo_contrato: date | None = Field(None, description="Data de assinatura do contrato mais recente")
    ds_diversidade: str | None = Field(
        None, description="Classificação: 'Fornecedor único' ou 'Múltiplos fornecedores'"
    )
    rank_por_diversidade: int | None = Field(
        None, description="Ranking do processo por quantidade de fornecedores distintos (1 = mais diverso)"
    )
