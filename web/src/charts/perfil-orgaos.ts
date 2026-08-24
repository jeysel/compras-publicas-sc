import * as echarts from "echarts";
import type { components } from "../api-types";
import { formatarMoedaBRL } from "./format";
import { isMobileViewport } from "./theme";

type Orgao = components["schemas"]["Orgao"];

// Mesma ordem de leitura do menor pro maior volume, igual ao critério do
// CASE em dim_orgaos.sql (>=1000 / >=100 / >=10 / resto).
const ORDEM_PERFIL = ["Esporádico", "Baixo volume", "Médio volume", "Alto volume"];

function renderRanking(tbody: HTMLTableSectionElement, linhas: Orgao[], valorCol: (o: Orgao) => string): void {
  tbody.textContent = "";
  for (const orgao of linhas) {
    const row = tbody.insertRow();
    row.insertCell().textContent = orgao.nm_unidade_gestora;
    const valorCell = row.insertCell();
    valorCell.textContent = valorCol(orgao);
    valorCell.classList.add("num");
  }
}

export async function renderPerfilOrgaos(
  containerId: string,
  tabelaQuantidadeId: string,
  tabelaValorId: string,
): Promise<void> {
  const container = document.getElementById(containerId);
  const tabelaQuantidade = document.getElementById(tabelaQuantidadeId)?.querySelector("tbody");
  const tabelaValor = document.getElementById(tabelaValorId)?.querySelector("tbody");
  if (container === null || tabelaQuantidade == null || tabelaValor == null) return;

  const resposta = await fetch("/api/v1/orgaos");
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  // Resposta já é o agregado por órgão (187 linhas, marts.dim_orgaos) — contar
  // por categoria e ordenar top-10 aqui é O(187), não repete o antipadrão de
  // buscar o grão de contrato pra agregar no cliente (spec 026).
  const orgaos = (await resposta.json()) as Orgao[];

  const contagemPorPerfil = new Map<string, number>();
  for (const orgao of orgaos) {
    if (orgao.ds_perfil_contratacao == null) continue;
    contagemPorPerfil.set(orgao.ds_perfil_contratacao, (contagemPorPerfil.get(orgao.ds_perfil_contratacao) ?? 0) + 1);
  }
  const perfis = ORDEM_PERFIL.filter((p) => contagemPorPerfil.has(p));

  const mobile = isMobileViewport();
  const chart = echarts.init(container);
  chart.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: mobile ? 8 : 120, right: 30, bottom: 30, containLabel: true },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: perfis },
    series: [{ type: "bar", data: perfis.map((p) => contagemPorPerfil.get(p) ?? 0) }],
  });
  requestAnimationFrame(() => chart.resize());
  window.addEventListener("resize", () => chart.resize());

  const porQuantidade = [...orgaos]
    .filter((o) => o.rank_por_quantidade != null)
    .sort((a, b) => (a.rank_por_quantidade ?? 0) - (b.rank_por_quantidade ?? 0))
    .slice(0, 10);
  renderRanking(tabelaQuantidade as HTMLTableSectionElement, porQuantidade, (o) =>
    o.qt_contratos.toLocaleString("pt-BR"),
  );

  const porValor = [...orgaos]
    .filter((o) => o.rank_por_valor != null)
    .sort((a, b) => (a.rank_por_valor ?? 0) - (b.rank_por_valor ?? 0))
    .slice(0, 10);
  renderRanking(tabelaValor as HTMLTableSectionElement, porValor, (o) =>
    o.vl_total_atual == null ? "—" : formatarMoedaBRL(Number(o.vl_total_atual)),
  );
}
