from decimal import Decimal

from pydantic import BaseModel, Field


class QualidadeDadoOrgao(BaseModel):
    cod_unidade_gestora: str = Field(..., description="Código da unidade gestora")
    nm_unidade_gestora: str | None = Field(None, description="Nome da unidade gestora")
    qt_contratos: int = Field(..., description="Total de contratos do órgão em mart_escalada_custo")
    qt_aditivo_inconsistente: int = Field(
        ..., description="Quantidade de contratos com fl_aditivo_inconsistente = true"
    )
    perc_aditivo_inconsistente: Decimal = Field(
        ..., description="Percentual de contratos com fl_aditivo_inconsistente = true"
    )
    qt_valor_suspeito: int = Field(..., description="Quantidade de contratos com fl_valor_suspeito = true")
    perc_valor_suspeito: Decimal = Field(..., description="Percentual de contratos com fl_valor_suspeito = true")
