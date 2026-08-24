import * as echarts from "echarts";
import type { components } from "../api-types";
import type { FiltroAnoIntervalo } from "./filtros";
import { formatarMoedaCompactaBRL } from "./format";

type PerfilFornecedores = components["schemas"]["PerfilFornecedores"];

// Mesma ordem de porte em todas as visualizações, do menor pro maior — a API
// retorna ordenado por valor_total desc, que não é a ordem de leitura natural
// de uma escala de porte (Micro < Pequeno < Médio < Grande).
const ORDEM_PORTE = ["Micro", "Pequeno", "Médio", "Grande"];

export async function renderPerfilFornecedores(containerId: string, filtros: FiltroAnoIntervalo = {}): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  const params = new URLSearchParams();
  if (filtros.ano_inicio) params.set("ano_inicio", filtros.ano_inicio);
  if (filtros.ano_fim) params.set("ano_fim", filtros.ano_fim);
  const query = params.toString();

  const resposta = await fetch(`/api/v1/perfil-fornecedores${query ? `?${query}` : ""}`);
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const linhas = (await resposta.json()) as PerfilFornecedores[];
  const porOrdem = [...linhas].sort(
    (a, b) => ORDEM_PORTE.indexOf(a.porte_fornecedor) - ORDEM_PORTE.indexOf(b.porte_fornecedor),
  );

  const instanciaExistente = echarts.getInstanceByDom(container);
  const chart = instanciaExistente ?? echarts.init(container);
  chart.setOption(
    {
      tooltip: {
        trigger: "axis",
        valueFormatter: (value: number | string) => Number(value).toLocaleString("pt-BR"),
      },
      grid: { left: 8, right: 30, bottom: 30, containLabel: true },
      xAxis: { type: "value" },
      yAxis: { type: "category", data: porOrdem.map((l) => l.porte_fornecedor) },
      series: [
        {
          type: "bar",
          data: porOrdem.map((l) => l.qt_fornecedores),
          label: {
            show: true,
            position: "right",
            formatter: (params: { dataIndex: number }) =>
              porOrdem[params.dataIndex].valor_total == null
                ? ""
                : formatarMoedaCompactaBRL(Number(porOrdem[params.dataIndex].valor_total)),
          },
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
