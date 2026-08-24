import * as echarts from "echarts";
import type { components } from "../api-types";
import type { FiltroAnoIntervalo } from "./filtros";
import { criarPaginador } from "./pagination";
import { isMobileViewport } from "./theme";
import { truncarTexto } from "./format";

type VariacaoPrazoModalidade = components["schemas"]["VariacaoPrazoModalidade"];

export async function renderVariacaoPrazoModalidade(
  containerId: string,
  tableId: string,
  botaoId: string,
  filtros: FiltroAnoIntervalo = {},
): Promise<void> {
  const container = document.getElementById(containerId);
  const table = document.getElementById(tableId);
  const tbody = table?.querySelector("tbody");
  const botao = document.getElementById(botaoId) as HTMLButtonElement | null;
  if (container === null || table === null || tbody == null) return;

  const params = new URLSearchParams();
  if (filtros.ano_inicio) params.set("ano_inicio", filtros.ano_inicio);
  if (filtros.ano_fim) params.set("ano_fim", filtros.ano_fim);
  const query = params.toString();

  const resposta = await fetch(`/api/v1/variacao-prazo-modalidade${query ? `?${query}` : ""}`);
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const linhas = (await resposta.json()) as VariacaoPrazoModalidade[];
  const ordenadas = [...linhas].sort((a, b) => Number(b.dias_variacao_media) - Number(a.dias_variacao_media));

  const mobile = isMobileViewport();

  // notMerge: true evita que categorias/série de uma chamada anterior (outro filtro)
  // sobrevivam misturadas ao trocar o filtro e re-renderizar na mesma instância.
  const instanciaExistente = echarts.getInstanceByDom(container);
  const chart = instanciaExistente ?? echarts.init(container);
  chart.setOption(
    {
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
    },
    true,
  );

  // Fix especulativo (spec pendente) para gráfico encolhido observado em iPhone real —
  // causa não confirmada em código (container já tem altura px explícita, listener de
  // resize já existia); força um resize após o primeiro layout do Safari por precaução.
  requestAnimationFrame(() => chart.resize());
  // Listener de resize só é anexado na primeira renderização — reaproveitar a instância
  // ao trocar filtro não deve empilhar um novo listener a cada troca.
  if (instanciaExistente === undefined) {
    window.addEventListener("resize", () => chart.resize());
  }

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
