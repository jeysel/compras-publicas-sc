import type { components } from "../api-types";
import { formatarPercentual } from "./format";

type QualidadeDadoOrgao = components["schemas"]["QualidadeDadoOrgao"];

export async function renderQualidadeDadoOrgao(tableId: string): Promise<void> {
  const table = document.getElementById(tableId);
  const tbody = table?.querySelector("tbody");
  if (table === null || tbody == null) return;

  const resposta = await fetch("/api/v1/qualidade-dado-orgao");
  if (!resposta.ok) {
    tbody.textContent = "";
    const row = tbody.insertRow();
    const cell = row.insertCell();
    cell.colSpan = 4;
    cell.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const linhas = (await resposta.json()) as QualidadeDadoOrgao[];

  tbody.textContent = "";
  for (const linha of linhas) {
    const row = tbody.insertRow();
    row.insertCell().textContent = linha.nm_unidade_gestora ?? linha.cod_unidade_gestora;
    row.insertCell().textContent = String(linha.qt_contratos);
    row.insertCell().textContent = formatarPercentual(Number(linha.perc_aditivo_inconsistente));
    row.insertCell().textContent = formatarPercentual(Number(linha.perc_valor_suspeito));
    for (const cell of Array.from(row.cells).slice(1)) cell.classList.add("num");
  }
}
