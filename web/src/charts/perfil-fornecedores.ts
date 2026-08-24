import * as echarts from "echarts";
import type { components } from "../api-types";
import { formatarMoedaCompactaBRL } from "./format";

type PerfilFornecedores = components["schemas"]["PerfilFornecedores"];

// Mesma ordem de porte em todas as visualizações, do menor pro maior — a API
// retorna ordenado por valor_total desc, que não é a ordem de leitura natural
// de uma escala de porte (Micro < Pequeno < Médio < Grande).
const ORDEM_PORTE = ["Micro", "Pequeno", "Médio", "Grande"];

export async function renderPerfilFornecedores(containerId: string): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  const resposta = await fetch("/api/v1/perfil-fornecedores");
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const linhas = (await resposta.json()) as PerfilFornecedores[];
  const porOrdem = [...linhas].sort(
    (a, b) => ORDEM_PORTE.indexOf(a.porte_fornecedor) - ORDEM_PORTE.indexOf(b.porte_fornecedor),
  );

  const chart = echarts.init(container);
  chart.setOption({
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number | string) => Number(value).toLocaleString("pt-BR"),
    },
    grid: { left: 8, right: 30, bottom: 30, containLabel: true },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: porOrdem.map((l) => l.porte_fornecedor) },
    series: [
      {
        type: "bar",
        data: porOrdem.map((l) => l.qt_fornecedores),
        label: {
          show: true,
          position: "right",
          formatter: (params: { dataIndex: number }) =>
            porOrdem[params.dataIndex].valor_total == null
              ? ""
              : formatarMoedaCompactaBRL(Number(porOrdem[params.dataIndex].valor_total)),
        },
      },
    ],
  });

  requestAnimationFrame(() => chart.resize());
  window.addEventListener("resize", () => chart.resize());
}
