import * as echarts from "echarts";
import type { components } from "../api-types";
import { formatarPercentual, truncarTexto } from "./format";
import { criarPaginador } from "./pagination";
import { isMobileViewport } from "./theme";

type VariacaoCustoModalidade = components["schemas"]["VariacaoCustoModalidade"];

// Materialidade mínima para comparar taxa de variação entre modalidades — evita destacar
// uma modalidade com poucos contratos só porque a média saiu alta por acaso de amostra.
const LIMIAR_VOLUME_INSIGHT = 500;

// "Não informado"/"Não Aplicável" são rótulos residuais da fonte, não modalidades de
// licitação reais — excluídos da comparação de taxa para não produzir um insight sem
// sentido jurídico (ex.: comparar contra um "Não Aplicável" com variação média alta).
function ehModalidadeReal(nm_modalidade: string): boolean {
  return !nm_modalidade.startsWith("Não ");
}

function montarInsight(linhas: VariacaoCustoModalidade[]): string {
  const totalContratos = linhas.reduce((soma, l) => soma + l.qt_contratos_com_aditivo, 0);
  const maisFrequente = linhas
    .filter((l) => ehModalidadeReal(l.nm_modalidade))
    .reduce((max, l) => (l.qt_contratos_com_aditivo > max.qt_contratos_com_aditivo ? l : max));
  const percFrequente = formatarPercentual((maisFrequente.qt_contratos_com_aditivo / totalContratos) * 100);

  let texto =
    `${maisFrequente.nm_modalidade} concentra a maior parte dos contratos com aditivo de valor: ` +
    `${maisFrequente.qt_contratos_com_aditivo.toLocaleString("pt-BR")} contratos (${percFrequente} do total), ` +
    `com variação média de custo de ${formatarPercentual(Number(maisFrequente.perc_variacao_media))}.`;

  const comVolumeRelevante = linhas.filter(
    (l) => ehModalidadeReal(l.nm_modalidade) && l.qt_contratos_com_aditivo >= LIMIAR_VOLUME_INSIGHT,
  );
  const maiorVariacao = comVolumeRelevante.reduce((max, l) =>
    Number(l.perc_variacao_media) > Number(max.perc_variacao_media) ? l : max,
  );
  if (maiorVariacao.nm_modalidade !== maisFrequente.nm_modalidade) {
    texto +=
      ` Entre modalidades com pelo menos ${LIMIAR_VOLUME_INSIGHT} contratos com aditivo, ${maiorVariacao.nm_modalidade} ` +
      `tem a maior variação média de custo, ${formatarPercentual(Number(maiorVariacao.perc_variacao_media))} — ` +
      `bem acima do ${formatarPercentual(Number(maisFrequente.perc_variacao_media))} de ${maisFrequente.nm_modalidade}, ` +
      `apesar de ter só ${maiorVariacao.qt_contratos_com_aditivo.toLocaleString("pt-BR")} contratos com aditivo.`;
  }
  return texto;
}

export async function renderVariacaoCustoModalidade(
  containerId: string,
  tableId: string,
  botaoId: string,
  insightId: string,
): Promise<void> {
  const container = document.getElementById(containerId);
  const table = document.getElementById(tableId);
  const tbody = table?.querySelector("tbody");
  const botao = document.getElementById(botaoId) as HTMLButtonElement | null;
  const insight = document.getElementById(insightId);
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

  if (insight !== null) insight.textContent = montarInsight(linhas);

  const mobile = isMobileViewport();

  const chart = echarts.init(container);
  chart.setOption({
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number | string) => formatarPercentual(Number(value)),
    },
    // containLabel: true evita que o nome da modalidade seja cortado pela borda do
    // grid (left fixo de 260px não cabe em tela mobile estreita).
    grid: { left: mobile ? 8 : 260, right: 30, bottom: 30, containLabel: true },
    xAxis: { type: "value", axisLabel: { formatter: (value: number) => formatarPercentual(value) } },
    yAxis: {
      type: "category",
      data: porVariacao.map((l) => (mobile ? truncarTexto(l.nm_modalidade, 18) : l.nm_modalidade)).reverse(),
    },
    series: [
      {
        type: "bar",
        data: porVariacao.map((l) => Number(l.perc_variacao_media)).reverse(),
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
