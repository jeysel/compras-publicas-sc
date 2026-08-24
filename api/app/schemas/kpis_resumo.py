from pydantic import BaseModel, Field


class KpisResumo(BaseModel):
    total_contratos: int = Field(..., description="Total de contratos")
    fornecedores_distintos: int = Field(..., description="Quantidade de fornecedores distintos")
    orgaos_distintos: int = Field(..., description="Quantidade de órgãos distintos")
    contratos_com_aditivo: int = Field(..., description="Quantidade de contratos com vl_variacao <> 0")
