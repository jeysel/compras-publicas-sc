import * as echarts from "echarts";
import type { components } from "../api-types";
import type { FiltrosGrafico } from "./filtros";
import { setLegendaExclusao } from "./legend";
import { formatarMoedaBRL } from "./format";
import { tituloResponsivo } from "./theme";

type ContratosTemporal = components["schemas"]["ContratosTemporal"];

function periodoLabel(item: ContratosTemporal): string {
  return `${item.ano_assinatura}-${String(item.mes_assinatura).padStart(2, "0")}`;
}

const NOMES_MES = [
  "Jan",
  "Fev",
  "Mar",
  "Abr",
  "Mai",
  "Jun",
  "Jul",
  "Ago",
  "Set",
  "Out",
  "Nov",
  "Dez",
];

function renderSazonalidadeMensal(containerId: string, serie: ContratosTemporal[]): void {
  const container = document.getElementById(containerId);
  if (container === null) return;

  const porMes = new Array<number>(12).fill(0);
  for (const item of serie) {
    porMes[item.mes_assinatura - 1] += item.qt_contratos;
  }

  const instanciaExistente = echarts.getInstanceByDom(container);
  const chart = instanciaExistente ?? echarts.init(container);
  chart.setOption(
    {
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category",
        data: NOMES_MES,
        name: "Mês de assinatura",
      },
      yAxis: {
        type: "value",
        name: "Qtd. de contratos (soma de todos os anos)",
      },
      series: [
        {
          name: "qt_contratos",
          type: "bar",
          data: porMes,
        },
      ],
    },
    true,
  );

  requestAnimationFrame(() => chart.resize());
  if (instanciaExistente === undefined) {
    window.addEventListener("resize", () => chart.resize());
  }
}

export async function renderContratosTemporal(
  containerId: string,
  legendaId: string,
  sazonalidadeId: string,
  filtros: FiltrosGrafico = {},
): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  const params = new URLSearchParams();
  if (filtros.cod_unidade_gestora) params.set("cod_unidade_gestora", filtros.cod_unidade_gestora);
  if (filtros.nm_modalidade) params.set("nm_modalidade", filtros.nm_modalidade);
  const query = params.toString();

  const resposta = await fetch(`/api/v1/contratos-temporal${query ? `?${query}` : ""}`);
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  // mart_contratos_temporal só tem recorte pré-agregado de uma dimensão por vez —
  // 'Geral' tem cod_unidade_gestora/nm_modalidade nulos, 'Órgão' só preenche
  // cod_unidade_gestora, 'Modalidade' só preenche nm_modalidade (grão descrito em
  // mart_contratos_temporal.sql). O filtro aplicado do lado do servidor já restringe
  // a resposta ao recorte correspondente; aqui só selecionamos qual recorte ler.
  const recorteAlvo = filtros.cod_unidade_gestora ? "Órgão" : filtros.nm_modalidade ? "Modalidade" : "Geral";

  const dados = (await resposta.json()) as ContratosTemporal[];
  const serie = dados
    .filter((item) => item.tp_recorte === recorteAlvo)
    .sort((a, b) => a.ano_assinatura - b.ano_assinatura || a.mes_assinatura - b.mes_assinatura);

  renderSazonalidadeMensal(sazonalidadeId, serie);

  const instanciaExistente = echarts.getInstanceByDom(container);
  const chart = instanciaExistente ?? echarts.init(container);
  chart.setOption(
    {
      title: tituloResponsivo("Valor contratado por mês de assinatura"),
      tooltip: {
        trigger: "axis",
        valueFormatter: (value: number | string) => formatarMoedaBRL(Number(value)),
      },
      xAxis: {
        type: "category",
        data: serie.map(periodoLabel),
        name: "Ano-mês de assinatura",
      },
      yAxis: {
        type: "value",
        name: "Valor atual (R$)",
        axisLabel: { formatter: (value: number) => formatarMoedaBRL(value) },
      },
      series: [
        {
          name: "vl_total_atual",
          type: "line",
          data: serie.map((item) => (item.vl_total_atual == null ? null : Number(item.vl_total_atual))),
        },
      ],
    },
    true,
  );

  // Fix especulativo (spec pendente) para gráfico encolhido observado em iPhone real —
  // causa não confirmada em código (container já tem altura px explícita, listener de
  // resize já existia); força um resize após o primeiro layout do Safari por precaução.
  requestAnimationFrame(() => chart.resize());
  if (instanciaExistente === undefined) {
    window.addEventListener("resize", () => chart.resize());
  }

  // mart_contratos_temporal já chega pré-agregada (grão ano/mês, spec 007).
  // fl_aditivo_inconsistente: os modelos intermediários (int_contratos_evolucao_*)
  // somam vl_atual/vl_variacao sem filtrar o flag, e não o expõem por linha —
  // não dá pra excluir client-side (informação já perdida na agregação);
  // achado registrado no adendo da spec 012, correção ainda pendente.
  // fl_valor_suspeito (spec 021): tratamento diferente — os mesmos
  // int_contratos_evolucao_* já excluem essas 146 linhas do SUM antes desta
  // mart existir (não é filtro client-side, é exclusão na camada dbt).
  // A contagem "146" é do dataset completo (recorte 'Geral') — com filtro de
  // órgão/modalidade aplicado, o texto fica genérico porque a contagem exata
  // excluída dentro do subconjunto filtrado não é exposta por esta API.
  setLegendaExclusao(
    legendaId,
    recorteAlvo === "Geral"
      ? "Este agregado já exclui 146 contratos com valor implausível (vl_original " +
          "ou vl_atual, spec 021) antes da soma — filtro aplicado na camada de dado, " +
          "não no cliente. Ainda não exclui contratos com inconsistência de aditivo " +
          "detectada na fonte — a granularidade desta mart não permite esse filtro " +
          'no cliente; correção pendente na camada dbt (ver <a href="/metodologia">metodologia</a>).'
      : "Este agregado já exclui contratos com valor implausível (spec 021) antes da " +
          "soma, na camada de dado. Ainda não exclui contratos com inconsistência de " +
          'aditivo detectada na fonte (ver <a href="/metodologia">metodologia</a>).',
  );
}
