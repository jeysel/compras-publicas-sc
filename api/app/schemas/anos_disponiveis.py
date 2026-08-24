from pydantic import BaseModel, Field


class AnosDisponiveis(BaseModel):
    ano_min: int = Field(..., description="Menor ano_assinatura com contrato real")
    ano_max: int = Field(..., description="Maior ano_assinatura com contrato real")
