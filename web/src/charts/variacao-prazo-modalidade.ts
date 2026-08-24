import * as echarts from "echarts";
import type { components } from "../api-types";
import { criarPaginador } from "./pagination";
import { isMobileViewport } from "./theme";
import { truncarTexto } from "./format";

type VariacaoPrazoModalidade = components["schemas"]["VariacaoPrazoModalidade"];

export async function renderVariacaoPrazoModalidade(
  containerId: string,
  tableId: string,
  botaoId: string,
): Promise<void> {
  const container = document.getElementById(containerId);
  const table = document.getElementById(tableId);
  const tbody = table?.querySelector("tbody");
  const botao = document.getElementById(botaoId) as HTMLButtonElement | null;
  if (container === null || table === null || tbody == null) return;

  const resposta = await fetch("/api/v1/variacao-prazo-modalidade");
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const linhas = (await resposta.json()) as VariacaoPrazoModalidade[];
  const ordenadas = [...linhas].sort((a, b) => Number(b.dias_variacao_media) - Number(a.dias_variacao_media));

  const mobile = isMobileViewport();

  const chart = echarts.init(container);
  chart.setOption({
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number | string) => `${value} dias`,
    },
    // containLabel: true evita que o nome da modalidade seja cortado pela borda do
    // grid (left fixo de 260px não cabe em tela mobile estreita).
    grid: { left: mobile ? 8 : 260, right: 30, bottom: 30, containLabel: true },
    xAxis: { type: "value", axisLabel: { formatter: "{value}d" } },
    yAxis: {
      type: "category",
      data: ordenadas.map((l) => (mobile ? truncarTexto(l.nm_modalidade, 18) : l.nm_modalidade)).reverse(),
    },
    series: [
      {
        type: "bar",
        data: ordenadas.map((l) => Number(l.dias_variacao_media)).reverse(),
      },
    ],
  });

  // Fix especulativo (spec pendente) para gráfico encolhido observado em iPhone real —
  // causa não confirmada em código (container já tem altura px explícita, listener de
  // resize já existia); força um resize após o primeiro layout do Safari por precaução.
  requestAnimationFrame(() => chart.resize());
  window.addEventListener("resize", () => chart.resize());

  tbody.textContent = "";
  criarPaginador(
    ordenadas,
    tbody,
    (linha, row) => {
      row.insertCell().textContent = linha.nm_modalidade;
      row.insertCell().textContent = String(linha.qt_contratos_com_aditivo_prazo);
      row.insertCell().textContent = `${linha.dias_variacao_media} dias`;
      for (const cell of Array.from(row.cells).slice(1)) cell.classList.add("num");
    },
    botao,
  );
}
