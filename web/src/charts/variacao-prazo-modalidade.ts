import * as echarts from "echarts";
import type { components } from "../api-types";

type VariacaoPrazoModalidade = components["schemas"]["VariacaoPrazoModalidade"];

export async function renderVariacaoPrazoModalidade(containerId: string, tableId: string): Promise<void> {
  const container = document.getElementById(containerId);
  const table = document.getElementById(tableId);
  const tbody = table?.querySelector("tbody");
  if (container === null || table === null || tbody == null) return;

  const resposta = await fetch("/api/v1/variacao-prazo-modalidade");
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const linhas = (await resposta.json()) as VariacaoPrazoModalidade[];
  const ordenadas = [...linhas].sort((a, b) => Number(b.dias_variacao_media) - Number(a.dias_variacao_media));

  const chart = echarts.init(container);
  chart.setOption({
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number | string) => `${value} dias`,
    },
    grid: { left: 260, right: 30, bottom: 30 },
    xAxis: { type: "value", axisLabel: { formatter: "{value}d" } },
    yAxis: { type: "category", data: ordenadas.map((l) => l.nm_modalidade).reverse() },
    series: [
      {
        type: "bar",
        data: ordenadas.map((l) => Number(l.dias_variacao_media)).reverse(),
      },
    ],
  });

  window.addEventListener("resize", () => chart.resize());

  tbody.textContent = "";
  for (const linha of ordenadas) {
    const row = tbody.insertRow();
    row.insertCell().textContent = linha.nm_modalidade;
    row.insertCell().textContent = String(linha.qt_contratos_com_aditivo_prazo);
    row.insertCell().textContent = `${linha.dias_variacao_media} dias`;
    for (const cell of Array.from(row.cells).slice(1)) cell.classList.add("num");
  }
}
