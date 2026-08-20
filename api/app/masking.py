import re

CPF_MASCARADO_NA_FONTE = re.compile(r"^\*\*\*\.\d{3}\.\d{3}-\*\*$")
CNPJ_FORMATADO = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")


def classify_id_contratado(value: str) -> str:
    """Classifica o formato de id_contratado como ele chega da mart.

    Achado (spec 012, 2026-08-20): a fonte (portal de transparência) já
    entrega CPF pré-mascarado (`***.NNN.NNN-**`) e CNPJ formatado sem
    máscara (`NN.NNN.NNN/NNNN-NN`). Não existem dígitos crus para mascarar
    neste ponto.
    """
    if CPF_MASCARADO_NA_FONTE.match(value):
        return "cpf_mascarado_na_fonte"
    if CNPJ_FORMATADO.match(value):
        return "cnpj"
    return "nao_identificado"


def mask_id_contratado(value: str) -> str:
    """Ponto único reaproveitável (Requirement não-funcional 1, spec 012).

    Não reformata: CPF já chega mascarado da fonte, CNPJ já chega completo
    por decisão registrada na spec. Repassa o valor como veio da mart em
    qualquer um dos três casos (CPF, CNPJ, não identificado).
    """
    return value
