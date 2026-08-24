from decimal import Decimal

from pydantic import BaseModel, Field


class PerfilFornecedores(BaseModel):
    porte_fornecedor: str = Field(..., description="Classificação por porte: Micro, Pequeno, Médio, Grande")
    qt_fornecedores: int = Field(..., description="Quantidade de fornecedores na faixa")
    valor_total: Decimal | None = Field(None, description="Soma de vl_total_atual dos fornecedores na faixa")
