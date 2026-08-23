import * as echarts from "echarts";
import type { components } from "../api-types";
import { setLegendaExclusao } from "./legend";
import { formatarMoedaBRL } from "./format";

type ConcentracaoFornecedor = components["schemas"]["ConcentracaoFornecedor"];

const TOP_N_EXIBIDO = 10;

export async function renderConcentracaoFornecedor(containerId: string, legendaId: string): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  // Dedup por id_contratado + top-N já acontece no SQL (spec 024) — a API
  // devolve só as linhas necessárias, não a mart inteira.
  const resposta = await fetch(`/api/v1/concentracao-fornecedor?top_n=${TOP_N_EXIBIDO}`);
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const top = (await resposta.json()) as ConcentracaoFornecedor[];

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

  // Fix especulativo (spec pendente) para gráfico encolhido observado em iPhone real —
  // causa não confirmada em código (container já tem altura px explícita, listener de
  // resize já existia); força um resize após o primeiro layout do Safari por precaução.
  requestAnimationFrame(() => chart.resize());
  window.addEventListener("resize", () => chart.resize());

  // int_concentracao_fornecedor_por_orgao/_estado (spec 021, REQ-11) somam
  // vl_atual por fornecedor sem filtrar fl_valor_suspeito=true por linha —
  // não dá pra excluir client-side, exclusão já ocorre na camada de dado.
  setLegendaExclusao(
    legendaId,
    "Este ranking já exclui contratos com valor implausível (vl_original " +
      "ou vl_atual, spec 021) antes da soma — filtro aplicado na camada de " +
      "dado, não no cliente (ver <a href=\"/metodologia\">metodologia</a>).",
  );
}
