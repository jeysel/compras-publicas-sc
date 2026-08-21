from decimal import Decimal

from pydantic import BaseModel, Field


class VariacaoPrazoModalidade(BaseModel):
    nm_modalidade: str = Field(..., description="Modalidade de licitação normalizada (nm_modalidade_norm, spec 025)")
    qt_contratos_com_aditivo_prazo: int = Field(
        ..., description="Quantidade de contratos com dias_variacao <> 0, excluindo fl_aditivo_inconsistente/fl_valor_suspeito"
    )
    dias_variacao_media: Decimal = Field(
        ..., description="Média de dias_variacao entre os contratos com aditivo de prazo"
    )
