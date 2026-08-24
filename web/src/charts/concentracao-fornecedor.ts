import * as echarts from "echarts";
import type { components } from "../api-types";
import { setLegendaExclusao } from "./legend";
import { formatarMoedaBRL, formatarMoedaCompactaBRL, truncarTexto } from "./format";
import { isMobileViewport, tituloResponsivo } from "./theme";

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
  const mobile = isMobileViewport();
  const nomes = top.map((f) => String(f.nm_contratado ?? f.id_contratado));

  const chart = echarts.init(container);
  chart.setOption({
    title: tituloResponsivo(`Top ${TOP_N_EXIBIDO} fornecedores por gasto no estado`),
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number | string) => formatarMoedaBRL(Number(value)),
    },
    // containLabel: true evita que rótulo de eixo (nome de fornecedor, valor) seja
    // cortado pela borda do grid — left/bottom viram folga extra além do rótulo.
    grid: { left: mobile ? 8 : 200, bottom: mobile ? 40 : 70, containLabel: true },
    xAxis: {
      type: "value",
      // Nome do eixo estoura a largura da tela em mobile (não cabe ao lado do
      // último tick) — some no valor completo já disponível no tooltip/título.
      name: mobile ? undefined : "Valor total no estado (R$)",
      // Menos ticks em mobile: rótulo compacto ainda se sobrepõe se o eixo tentar
      // caber os ~5 ticks padrão num grid estreito.
      splitNumber: mobile ? 3 : undefined,
      axisLabel: {
        // Notação completa gira 30° e sobrepõe em telas estreitas; compacta cabe
        // na horizontal (rotate 0) mesmo em mobile.
        formatter: (value: number) => (mobile ? formatarMoedaCompactaBRL(value) : formatarMoedaBRL(value)),
        rotate: mobile ? 0 : 30,
      },
    },
    yAxis: {
      type: "category",
      data: nomes.map((nome) => (mobile ? truncarTexto(nome, 18) : nome)).reverse(),
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
