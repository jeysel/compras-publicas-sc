"""Dataset determinístico de contratos para a suíte de integração (spec 033).

Fonte única de verdade: as mesmas linhas usadas aqui para gerar o CSV que
substitui `dbt/seeds/contratos.csv` antes de `dbt seed`/`dbt build` (via
`write_seed_csv()`, chamável também como script — `python contratos.py
<destino>`) são as linhas contra as quais os testes de KPI validam
resultado esperado — qualquer ajuste nos valores abaixo deve ser refletido
nos dois lados (CSV de seed e asserções dos testes), por isso os dois vivem
no mesmo arquivo.

Cobre deliberadamente:
- 2 órgãos (ORG_A, ORG_B), 3 fornecedores (F1/F2/F3), 2 modalidades
  normalizáveis (Pregão Eletrônico / Dispensa).
- 1 contrato com fl_aditivo_inconsistente=true (row 3: vl_aditado não bate
  com vl_variacao).
- 1 contrato com fl_valor_suspeito=true (row 4: vl_atual explode pra 600
  milhões com razão original/atual bem distante de 1 — Padrão C do CASE em
  stg_contratos.sql).
- 1 processo (2023PROC001) com 2 fornecedores distintos (rows 1 e 8), pra
  diversidade_vencedores ter ao menos um "Múltiplos fornecedores".
- 1 contrato assinado antes de 2016 (row 9: 2014) — deve ser cortado em
  stg_contratos pela fronteira de cobertura oficial (spec 034) e não
  aparecer em nenhuma mart. Valida-se em test_cobertura_oficial.py. Usa
  órgão/fornecedor/modalidade já existentes de propósito: como a linha some
  em stg, nenhum agregado das outras rotas muda por causa dela.
"""

from __future__ import annotations

import csv
from pathlib import Path

CSV_HEADER = [
    "cdunidadegestora", "nmunidadegestora", "cdgestao", "nmgestao", "nucontrato",
    "idcontratado", "contratado", "resumo", "objeto", "dtinicio", "dtfim",
    "dtfimatual", "dtassinatura", "situacao", "nuprocesso", "vloriginal",
    "vlatual", "nmfiscal", "nuedital", "nmbempublico", "nmregimeexecucao",
    "detipocontrato", "detipodocumentolegal", "nudocumentolegal", "demulta",
    "nuautorizacaoorgao", "nuprazo", "nminterveniente", "nmlocalexecucao",
    "nmmodalidade", "nmrepcredor", "nmrepinterveniente", "nmrepug",
    "dtautorizacao", "dtinclusao", "dtlimiteproposta", "vlgarantia",
    "vlpercgarantia", "vlpercmulta", "nutitulo", "vladitado",
    "cdugfiscalizador", "ugfiscalizador", "cdgestaofiscalizador",
    "gestaofiscalizador", "bempublico", "deesptitulo", "dataproposta",
    "diasoriginais", "diasaditados", "diasatuais",
]

ORG_A = {"cdunidadegestora": "900001", "nmunidadegestora": "Secretaria de Teste A", "cdgestao": "9001", "nmgestao": "Gestão Teste A"}
ORG_B = {"cdunidadegestora": "900002", "nmunidadegestora": "Secretaria de Teste B", "cdgestao": "9002", "nmgestao": "Gestão Teste B"}

F1 = {"idcontratado": "11.111.111/0001-11", "contratado": "Fornecedor Alpha Teste Ltda"}
F2 = {"idcontratado": "22.222.222/0001-22", "contratado": "Fornecedor Beta Teste Ltda"}
F3 = {"idcontratado": "33.333.333/0001-33", "contratado": "Fornecedor Gamma Teste Ltda"}

MOD_PE = "Pregão Eletrônico Lei 14.133"  # sem traço antes de "Lei" — grafia exata normalizada em stg_contratos.sql
MOD_PE_NORM = "Pregão Eletrônico - Leis 10.520/2002 e 14.133/2021"
MOD_DISP = "Dispensa de Licitação - Lei 14.133"
MOD_DISP_NORM = "Dispensa de Licitação - Leis 8.666/1993 e 14.133/2021"

# Cada linha só declara os campos que importam para os testes — o resto
# (campos descritivos não consultados por nenhuma rota) fica em branco,
# uniformemente, via DEFAULTS em _row().
FIXTURE_ROWS = [
    {
        **ORG_A, **F1, "nucontrato": "CT-TESTE-001", "dtassinatura": "2023-03-10 00:00:00",
        "nuprocesso": "2023PROC001", "nmmodalidade": MOD_PE,
        "objeto": "Prestação de serviços de manutenção preventiva de veículos oficiais da frota",
        "vloriginal": "50000", "vlatual": "50000", "vladitado": "0",
        "diasoriginais": "30", "diasaditados": "0", "diasatuais": "30",
    },
    {
        **ORG_A, **F1, "nucontrato": "CT-TESTE-002", "dtassinatura": "2024-05-20 00:00:00",
        "nuprocesso": "2024PROC002", "nmmodalidade": MOD_PE,
        "objeto": "Prestação de serviços gerais de apoio administrativo ao órgão",
        "vloriginal": "40000", "vlatual": "45000", "vladitado": "5000",
        "diasoriginais": "30", "diasaditados": "15", "diasatuais": "45",
    },
    {
        **ORG_A, **F2, "nucontrato": "CT-TESTE-003", "dtassinatura": "2024-07-02 00:00:00",
        "nuprocesso": "2024PROC003", "nmmodalidade": MOD_DISP,
        "objeto": "Fornecimento de materiais diversos para o almoxarifado central",
        "vloriginal": "10000", "vlatual": "12000", "vladitado": "500",
        "diasoriginais": "60", "diasaditados": "30", "diasatuais": "90",
    },
    {
        **ORG_B, **F2, "nucontrato": "CT-TESTE-004", "dtassinatura": "2023-01-15 00:00:00",
        "nuprocesso": "2023PROC005", "nmmodalidade": MOD_PE,
        "objeto": "Aquisição de combustível para abastecimento da frota de veículos",
        "vloriginal": "500000", "vlatual": "600000000", "vladitado": "0",
        "diasoriginais": "30", "diasaditados": "5", "diasatuais": "35",
    },
    {
        **ORG_B, **F3, "nucontrato": "CT-TESTE-005", "dtassinatura": "2025-02-10 00:00:00",
        "nuprocesso": "2025PROC006", "nmmodalidade": MOD_DISP,
        "objeto": "Prestação de serviços de apoio administrativo diversos",
        "vloriginal": "20000", "vlatual": "20000", "vladitado": "0",
        "diasoriginais": "20", "diasaditados": "0", "diasatuais": "20",
    },
    {
        **ORG_A, **F3, "nucontrato": "CT-TESTE-006", "dtassinatura": "2025-04-18 00:00:00",
        "nuprocesso": "2025PROC004", "nmmodalidade": MOD_PE,
        "objeto": "Aquisição de combustível para veículos oficiais do órgão",
        "vloriginal": "15000", "vlatual": "15000", "vladitado": "0",
        "diasoriginais": "25", "diasaditados": "0", "diasatuais": "25",
    },
    {
        **ORG_B, **F1, "nucontrato": "CT-TESTE-007", "dtassinatura": "2023-09-05 00:00:00",
        "nuprocesso": "2023PROC007", "nmmodalidade": MOD_DISP,
        "objeto": "Execução de obras de pavimentação da rodovia estadual SC-301",
        "vloriginal": "30000", "vlatual": "30000", "vladitado": "0",
        "diasoriginais": "40", "diasaditados": "0", "diasatuais": "40",
    },
    {
        **ORG_A, **F2, "nucontrato": "CT-TESTE-008", "dtassinatura": "2023-06-15 00:00:00",
        "nuprocesso": "2023PROC001", "nmmodalidade": MOD_PE,
        "objeto": "Aquisição de materiais de expediente para o escritório central",
        "vloriginal": "25000", "vlatual": "25000", "vladitado": "0",
        "diasoriginais": "15", "diasaditados": "0", "diasatuais": "15",
    },
    {
        # Assinado em 2014 — antes da fronteira de cobertura oficial (2016,
        # spec 034). Deve ser cortado em stg_contratos e não aparecer em
        # nenhuma mart nem no intervalo de /api/v1/anos-disponiveis.
        **ORG_A, **F1, "nucontrato": "CT-TESTE-PRE2016", "dtassinatura": "2014-08-11 00:00:00",
        "nuprocesso": "2014PROC009", "nmmodalidade": MOD_PE,
        "objeto": "Contrato histórico anterior ao início da cobertura do painel",
        "vloriginal": "99000", "vlatual": "99000", "vladitado": "0",
        "diasoriginais": "30", "diasaditados": "0", "diasatuais": "30",
    },
]


_DATE_COLUMNS = ("dtinicio", "dtfim", "dtfimatual", "dtautorizacao", "dtinclusao", "dtlimiteproposta", "dataproposta")


def _row(data: dict) -> dict:
    defaults = {col: "" for col in CSV_HEADER}
    defaults["situacao"] = "Concluído"
    # Todas as colunas de data precisam de um valor consistente em TODAS as
    # linhas — se uma coluna de data ficasse vazia em toda a seed, o agate
    # (leitor de CSV do dbt) infere o tipo da coluna como integer (coluna
    # 100% vazia não tem nenhum valor pra inferir "data" a partir dele), e
    # o cast(... as date) em stg_contratos.sql falha em runtime
    # ("cannot cast type integer to date") — achado rodando dbt build de
    # verdade contra este fixture, não presumido.
    for col in _DATE_COLUMNS:
        defaults[col] = data["dtassinatura"]
    return {**defaults, **data}


def write_seed_csv(path: Path | str) -> None:
    """Escreve o CSV de seed de teste no mesmo formato de dbt/seeds/contratos.csv
    (delimitador ';', mesmo header/ordem de colunas)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER, delimiter=";")
        writer.writeheader()
        for data in FIXTURE_ROWS:
            writer.writerow(_row(data))


if __name__ == "__main__":
    import sys

    write_seed_csv(sys.argv[1])
