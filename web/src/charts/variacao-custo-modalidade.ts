import * as echarts from "echarts";
import type { components } from "../api-types";
import { formatarPercentual } from "./format";
import { criarPaginador } from "./pagination";

type VariacaoCustoModalidade = components["schemas"]["VariacaoCustoModalidade"];

export async function renderVariacaoCustoModalidade(
  containerId: string,
  tableId: string,
  botaoId: string,
): Promise<void> {
  const container = document.getElementById(containerId);
  const table = document.getElementById(tableId);
  const tbody = table?.querySelector("tbody");
  const botao = document.getElementById(botaoId) as HTMLButtonElement | null;
  if (container === null || table === null || tbody == null) return;

  const resposta = await fetch("/api/v1/variacao-custo-modalidade");
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  // A API já retorna as linhas ordenadas por qt_contratos_com_aditivo (tabela); o gráfico
  // precisa de uma ordem própria por perc_variacao_media para as barras saírem maior-primeiro.
  const linhas = (await resposta.json()) as VariacaoCustoModalidade[];
  const porVariacao = [...linhas].sort((a, b) => Number(b.perc_variacao_media) - Number(a.perc_variacao_media));

  const chart = echarts.init(container);
  chart.setOption({
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number | string) => formatarPercentual(Number(value)),
    },
    grid: { left: 260, right: 30, bottom: 30 },
    xAxis: { type: "value", axisLabel: { formatter: (value: number) => formatarPercentual(value) } },
    yAxis: { type: "category", data: porVariacao.map((l) => l.nm_modalidade).reverse() },
    series: [
      {
        type: "bar",
        data: porVariacao.map((l) => Number(l.perc_variacao_media)).reverse(),
      },
    ],
  });

  window.addEventListener("resize", () => chart.resize());

  tbody.textContent = "";
  criarPaginador(
    linhas,
    tbody,
    (linha, row) => {
      row.insertCell().textContent = linha.nm_modalidade;
      row.insertCell().textContent = String(linha.qt_contratos_com_aditivo);
      row.insertCell().textContent = formatarPercentual(Number(linha.perc_variacao_media));
      for (const cell of Array.from(row.cells).slice(1)) cell.classList.add("num");
    },
    botao,
  );
}
