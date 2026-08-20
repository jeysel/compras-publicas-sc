from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.masking import mask_id_contratado


class ConcentracaoFornecedor(BaseModel):
    cod_unidade_gestora: str = Field(..., description="Código da unidade gestora")
    nm_unidade_gestora: str | None = Field(None, description="Nome da unidade gestora")
    id_contratado: str = Field(
        ...,
        description=(
            "Identificador do fornecedor. CNPJ exibido por completo; CPF já chega "
            "mascarado pela fonte (ex.: '***.006.069-**') — spec 012, achado 2026-08-20."
        ),
    )
    nm_contratado: str | None = Field(None, description="Nome/razão social do fornecedor")
    vl_total_fornecedor_orgao: Decimal | None = Field(
        None, description="Soma de vl_atual dos contratos deste fornecedor com este órgão"
    )
    vl_total_orgao: Decimal | None = Field(None, description="Soma de vl_atual de todos os fornecedores deste órgão")
    rank_no_orgao: int | None = Field(None, description="Ranking do fornecedor por gasto dentro do órgão (1 = maior)")
    perc_sobre_total_orgao: Decimal | None = Field(
        None, description="Percentual do gasto do órgão concentrado neste fornecedor"
    )
    vl_total_fornecedor_estado: Decimal | None = Field(
        None, description="Soma de vl_atual de todos os contratos deste fornecedor, todos os órgãos"
    )
    vl_total_estado: Decimal | None = Field(None, description="Soma de vl_atual de todos os contratos do estado")
    rank_estado: int | None = Field(None, description="Ranking do fornecedor por gasto no estado inteiro")
    perc_sobre_total_estado: Decimal | None = Field(
        None, description="Percentual do gasto total do estado concentrado neste fornecedor"
    )

    @field_validator("id_contratado")
    @classmethod
    def _mask(cls, value: str) -> str:
        return mask_id_contratado(value)
