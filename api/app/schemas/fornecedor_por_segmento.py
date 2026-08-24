from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.masking import mask_id_contratado


class FornecedorPorSegmentoGrafico(BaseModel):
    ramo_atividade: str = Field(..., description="Ramo de atividade classificado por palavras-chave do objeto")
    id_contratado: str = Field(..., description="Identificador do fornecedor (CNPJ ou CPF pré-mascarado pela fonte)")
    nm_contratado: str | None = Field(None, description="Nome/razão social do fornecedor")
    vl_total: Decimal = Field(..., description="Soma de vl_atual dos contratos deste fornecedor neste ramo")

    @field_validator("id_contratado")
    @classmethod
    def _mask(cls, value: str) -> str:
        return mask_id_contratado(value)


class FornecedorPorSegmentoContrato(BaseModel):
    nu_contrato: str = Field(..., description="Número do contrato")
    nm_contratado: str | None = Field(None, description="Nome/razão social do fornecedor")
    vl_atual: Decimal | None = Field(None, description="Valor atual do contrato")
    dt_inicio: date | None = Field(None, description="Data de início de vigência — pode ser nula na fonte")
    dt_fim_atual: date | None = Field(
        None, description="Data de fim de vigência atualizada — pode ser nula na fonte"
    )
    ramo_atividade: str = Field(..., description="Ramo de atividade classificado por palavras-chave do objeto")
