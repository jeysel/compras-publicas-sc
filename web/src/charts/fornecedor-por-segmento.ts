import * as echarts from "echarts";
import type { components } from "../api-types";
import { setLegendaExclusao } from "./legend";
import { formatarMoedaBRL, formatarMoedaCompactaBRL, formatarPeriodo, truncarTexto } from "./format";
import { isMobileViewport, tituloResponsivo } from "./theme";
import { criarPaginador } from "./pagination";

type FornecedorPorSegmentoGrafico = components["schemas"]["FornecedorPorSegmentoGrafico"];
type FornecedorPorSegmentoContrato = components["schemas"]["FornecedorPorSegmentoContrato"];

const TOP_N_EXIBIDO = 10;

// Nota de população (spec 031, REQ-6) + exclusão de valor implausível (spec 021/031,
// REQ-16) — mesmo padrão de nota já usado em concentracao-fornecedor.ts. Fixa porque
// não depende do resultado da consulta, só da definição da mart/filtro.
const NOTA_POPULACAO =
  "Esta base (marts.fct_contratos_ramo) exclui contratos de teste e com valor original " +
  "até R$ 1.000 — a classificação por ramo é heurística, por palavras-chave do objeto do " +
  "contrato, e 28,47% dos contratos caem em \"Outros\" por não casar com nenhuma palavra-chave. " +
  "Também já exclui contratos com valor implausível (vl_original ou vl_atual, spec 021) antes " +
  "da agregação — filtro aplicado na camada de dado, não no cliente " +
  "(ver <a href=\"/metodologia\">metodologia</a>).";

export interface FiltroSegmento {
  ramo_atividade?: string;
  dt_inicio_de?: string;
  dt_inicio_ate?: string;
}

export async function renderFornecedorPorSegmentoGrafico(
  containerId: string,
  legendaId: string,
  filtros: FiltroSegmento = {},
): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  const params = new URLSearchParams({ top_n: String(TOP_N_EXIBIDO) });
  if (filtros.ramo_atividade) params.set("ramo_atividade", filtros.ramo_atividade);
  if (filtros.dt_inicio_de) params.set("dt_inicio_de", filtros.dt_inicio_de);
  if (filtros.dt_inicio_ate) params.set("dt_inicio_ate", filtros.dt_inicio_ate);

  const resposta = await fetch(`/api/v1/fornecedor-por-segmento?${params.toString()}`);
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const top = (await resposta.json()) as FornecedorPorSegmentoGrafico[];
  const mobile = isMobileViewport();
  // Sem filtro de segmento, o ranking mistura ramos — o nome do fornecedor sozinho
  // não deixa isso claro, então o ramo entra entre parênteses no rótulo do eixo.
  const nomes = top.map((f) =>
    filtros.ramo_atividade ? String(f.nm_contratado ?? f.id_contratado) : `${f.nm_contratado ?? f.id_contratado} (${f.ramo_atividade})`,
  );
  const valores = top.map((f) => (f.vl_total == null ? 0 : Number(f.vl_total)));
  const titulo = filtros.ramo_atividade
    ? `Top ${TOP_N_EXIBIDO} fornecedores — ${filtros.ramo_atividade}`
    : `Top ${TOP_N_EXIBIDO} fornecedores por segmento`;

  const instanciaExistente = echarts.getInstanceByDom(container);
  const chart = instanciaExistente ?? echarts.init(container);
  chart.setOption(
    {
      title: tituloResponsivo(titulo),
      tooltip: {
        trigger: "axis",
        valueFormatter: (value: number | string) => formatarMoedaBRL(Number(value)),
      },
      grid: { left: mobile ? 8 : 200, bottom: mobile ? 40 : 70, containLabel: true },
      xAxis: {
        type: "value",
        name: mobile ? undefined : "Valor total (R$)",
        splitNumber: mobile ? 3 : undefined,
        axisLabel: {
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
          name: "vl_total",
          type: "bar",
          data: [...valores].reverse(),
        },
      ],
    },
    true,
  );

  requestAnimationFrame(() => chart.resize());
  if (instanciaExistente === undefined) {
    window.addEventListener("resize", () => chart.resize());
  }

  setLegendaExclusao(legendaId, NOTA_POPULACAO);
}

export interface FiltroSegmentoBusca extends FiltroSegmento {
  nm_contratado?: string;
}

export async function renderFornecedorPorSegmentoRelatorio(
  tableId: string,
  botaoId: string,
  legendaId: string,
  filtros: FiltroSegmentoBusca = {},
): Promise<void> {
  const table = document.getElementById(tableId);
  const tbody = table?.querySelector("tbody");
  const botao = document.getElementById(botaoId) as HTMLButtonElement | null;
  if (table === null || tbody == null) return;

  const params = new URLSearchParams();
  if (filtros.ramo_atividade) params.set("ramo_atividade", filtros.ramo_atividade);
  if (filtros.nm_contratado) params.set("nm_contratado", filtros.nm_contratado);
  if (filtros.dt_inicio_de) params.set("dt_inicio_de", filtros.dt_inicio_de);
  if (filtros.dt_inicio_ate) params.set("dt_inicio_ate", filtros.dt_inicio_ate);
  const query = params.toString();

  const resposta = await fetch(`/api/v1/fornecedor-por-segmento/contratos${query ? `?${query}` : ""}`);
  if (!resposta.ok) {
    tbody.textContent = "";
    const row = tbody.insertRow();
    const cell = row.insertCell();
    cell.colSpan = 5;
    cell.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const linhas = (await resposta.json()) as FornecedorPorSegmentoContrato[];

  tbody.textContent = "";
  criarPaginador(
    linhas,
    tbody,
    (linha, row) => {
      row.insertCell().textContent = linha.nm_contratado ?? "—";
      row.insertCell().textContent = linha.nu_contrato;
      row.insertCell().textContent = linha.ramo_atividade;
      row.insertCell().textContent = linha.vl_atual == null ? "—" : formatarMoedaBRL(Number(linha.vl_atual));
      row.insertCell().textContent = formatarPeriodo(linha.dt_inicio, linha.dt_fim_atual);
      row.cells[3]?.classList.add("num");
    },
    botao,
  );

  setLegendaExclusao(legendaId, NOTA_POPULACAO);
}
