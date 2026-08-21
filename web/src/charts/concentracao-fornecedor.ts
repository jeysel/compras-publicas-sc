import * as echarts from "echarts";
import type { components } from "../api-types";
import { setLegendaExclusao } from "./legend";
import { formatarMoedaBRL } from "./format";

type ConcentracaoFornecedor = components["schemas"]["ConcentracaoFornecedor"];

const TOP_N_EXIBIDO = 10;

function topFornecedoresDistintos(dados: ConcentracaoFornecedor[], limite: number): ConcentracaoFornecedor[] {
  // Grão da mart é (cod_unidade_gestora, id_contratado): um fornecedor que
  // contratou com vários órgãos aparece uma vez por órgão, todas as linhas
  // repetindo o mesmo rank_estado/vl_total_fornecedor_estado (achado spec
  // 012, router já documenta isso). "ORDER BY rank_estado LIMIT N" no
  // backend não garante N fornecedores distintos — dedup fica pro cliente.
  const porFornecedor = new Map<string, ConcentracaoFornecedor>();
  for (const linha of dados) {
    if (!porFornecedor.has(linha.id_contratado)) {
      porFornecedor.set(linha.id_contratado, linha);
    }
  }

  return Array.from(porFornecedor.values())
    .sort((a, b) => Number(b.vl_total_fornecedor_estado ?? 0) - Number(a.vl_total_fornecedor_estado ?? 0))
    .slice(0, limite);
}

export async function renderConcentracaoFornecedor(containerId: string, legendaId: string): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  // top_n precisa cobrir a mart inteira (27.849 linhas): a duplicação por
  // órgão não é uniforme — um único fornecedor pode ocupar 126+ linhas
  // (achado spec 012, confirmado via psql), então nenhum top_n pequeno
  // garante 10 fornecedores distintos após o dedup abaixo.
  const resposta = await fetch("/api/v1/concentracao-fornecedor?top_n=30000");
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const dados = (await resposta.json()) as ConcentracaoFornecedor[];
  const top = topFornecedoresDistintos(dados, TOP_N_EXIBIDO);

  const chart = echarts.init(container);
  chart.setOption({
    title: { text: `Top ${TOP_N_EXIBIDO} fornecedores por gasto no estado` },
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number | string) => formatarMoedaBRL(Number(value)),
    },
    grid: { left: 200, bottom: 70 },
    xAxis: {
      type: "value",
      name: "Valor total no estado (R$)",
      axisLabel: {
        formatter: (value: number) => formatarMoedaBRL(value),
        rotate: 30,
      },
    },
    yAxis: {
      type: "category",
      data: top.map((f) => f.nm_contratado ?? f.id_contratado).reverse(),
    },
    series: [
      {
        name: "vl_total_fornecedor_estado",
        type: "bar",
        data: top.map((f) => (f.vl_total_fornecedor_estado == null ? 0 : Number(f.vl_total_fornecedor_estado))).reverse(),
      },
    ],
  });

  window.addEventListener("resize", () => chart.resize());

  // int_concentracao_fornecedor_por_orgao/_estado (spec 021, REQ-11) somam
  // vl_atual por fornecedor sem filtrar fl_valor_suspeito=true por linha —
  // não dá pra excluir client-side, exclusão já ocorre na camada de dado.
  setLegendaExclusao(
    legendaId,
    "Este ranking já exclui contratos com valor implausível (vl_original " +
      "ou vl_atual, spec 021) antes da soma — filtro aplicado na camada de " +
      "dado, não no cliente (ver <a href=\"#metodologia\">metodologia</a>).",
  );
}
