import * as echarts from "echarts";
import type { components } from "../api-types";
import type { FiltrosGrafico } from "./filtros";
import { setLegendaExclusao } from "./legend";
import { formatarMoedaBRL } from "./format";
import { tituloResponsivo } from "./theme";

type EscaladaCusto = components["schemas"]["EscaladaCusto"];

interface AnoAgregado {
  ano: number;
  totalVariacao: number;
}

function agregarPorAno(dados: EscaladaCusto[]): AnoAgregado[] {
  const porAno = new Map<number, number>();

  for (const contrato of dados) {
    if (contrato.ano_assinatura == null) continue;
    const variacao = contrato.vl_variacao == null ? 0 : Number(contrato.vl_variacao);
    porAno.set(contrato.ano_assinatura, (porAno.get(contrato.ano_assinatura) ?? 0) + variacao);
  }

  return Array.from(porAno.entries())
    .map(([ano, totalVariacao]) => ({ ano, totalVariacao }))
    .sort((a, b) => a.ano - b.ano);
}

export async function renderEscaladaCusto(
  containerId: string,
  legendaId: string,
  filtros: FiltrosGrafico = {},
): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  const params = new URLSearchParams();
  if (filtros.cod_unidade_gestora) params.set("cod_unidade_gestora", filtros.cod_unidade_gestora);
  if (filtros.nm_modalidade) params.set("nm_modalidade", filtros.nm_modalidade);
  if (filtros.ano) params.set("ano", filtros.ano);
  const query = params.toString();

  const resposta = await fetch(`/api/v1/escalada-custo${query ? `?${query}` : ""}`);
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const dados = (await resposta.json()) as EscaladaCusto[];

  // Decisão (adendo spec 012, 2026-08-20): contratos com fl_aditivo_inconsistente
  // === true são excluídos por padrão de agregações de valor — vl_aditado
  // diverge de vl_variacao acima de arredondamento, sinal de qualidade de
  // dado da fonte (spec 013/014). null/false permanecem incluídos.
  // Decisão (spec 021): contratos com fl_valor_suspeito === true também são
  // excluídos — vl_original/vl_atual implausível (3 padrões de corrupção de
  // valor confirmados, ver spec). Os dois critérios são independentes; um
  // contrato pode cair em qualquer um dos dois (ou nenhum).
  const excluidosAditivo = dados.filter((contrato) => contrato.fl_aditivo_inconsistente === true);
  const excluidosValor = dados.filter((contrato) => contrato.fl_valor_suspeito === true);
  const incluidos = dados.filter(
    (contrato) => contrato.fl_aditivo_inconsistente !== true && contrato.fl_valor_suspeito !== true,
  );
  const totalExcluidos = dados.length - incluidos.length;

  const agregado = agregarPorAno(incluidos);

  // notMerge: true evita que categorias/série de uma chamada anterior (outro filtro)
  // sobrevivam misturadas ao trocar o filtro e re-renderizar na mesma instância.
  const instanciaExistente = echarts.getInstanceByDom(container);
  const chart = instanciaExistente ?? echarts.init(container);
  chart.setOption(
    {
      title: tituloResponsivo("Escalada de custo por ano de assinatura"),
      tooltip: {
        trigger: "axis",
        valueFormatter: (value: number | string) => formatarMoedaBRL(Number(value)),
      },
      xAxis: {
        type: "category",
        data: agregado.map((item) => String(item.ano)),
        name: "Ano de assinatura",
      },
      yAxis: {
        type: "value",
        name: "Variação de valor (R$)",
        axisLabel: { formatter: (value: number) => formatarMoedaBRL(value) },
      },
      series: [
        {
          name: "Variação de valor (vl_atual - vl_original)",
          type: "bar",
          data: agregado.map((item) => item.totalVariacao),
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

  setLegendaExclusao(
    legendaId,
    `${totalExcluidos} de ${dados.length} contratos excluídos desta agregação por ` +
      `inconsistência de dado (${excluidosAditivo.length} por aditivo, ${excluidosValor.length} ` +
      `por valor implausível; ver <a href="/metodologia">metodologia</a>).`,
  );
}
