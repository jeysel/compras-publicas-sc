import type { components } from "../api-types";

type KpisResumo = components["schemas"]["KpisResumo"];

export async function renderKpisResumo(): Promise<void> {
  const totalContratosEl = document.getElementById("kpi-total-contratos");
  const fornecedoresEl = document.getElementById("kpi-fornecedores-distintos");
  const orgaosEl = document.getElementById("kpi-orgaos-distintos");
  const comAditivoEl = document.getElementById("kpi-contratos-com-aditivo");
  if (totalContratosEl == null || fornecedoresEl == null || orgaosEl == null || comAditivoEl == null) return;

  const resposta = await fetch("/api/v1/kpis-resumo");
  if (!resposta.ok) {
    for (const el of [totalContratosEl, fornecedoresEl, orgaosEl, comAditivoEl]) {
      el.textContent = "—";
    }
    return;
  }

  const kpis = (await resposta.json()) as KpisResumo;
  totalContratosEl.textContent = kpis.total_contratos.toLocaleString("pt-BR");
  fornecedoresEl.textContent = kpis.fornecedores_distintos.toLocaleString("pt-BR");
  orgaosEl.textContent = kpis.orgaos_distintos.toLocaleString("pt-BR");
  comAditivoEl.textContent = kpis.contratos_com_aditivo.toLocaleString("pt-BR");
}
