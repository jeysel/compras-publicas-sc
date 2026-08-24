import * as echarts from "echarts";
import type { components } from "../api-types";
import type { FiltrosGrafico } from "./filtros";
import { tituloResponsivo } from "./theme";

type DiversidadeVencedores = components["schemas"]["DiversidadeVencedores"];

function contarPorClassificacao(dados: DiversidadeVencedores[]): Map<string, number> {
  const contagem = new Map<string, number>();

  for (const processo of dados) {
    const classificacao = processo.ds_diversidade ?? "Não classificado";
    contagem.set(classificacao, (contagem.get(classificacao) ?? 0) + 1);
  }

  return contagem;
}

export async function renderDiversidadeVencedores(
  containerId: string,
  filtros: FiltrosGrafico = {},
): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  const params = new URLSearchParams();
  if (filtros.cod_unidade_gestora) params.set("cod_unidade_gestora", filtros.cod_unidade_gestora);
  const query = params.toString();

  const resposta = await fetch(`/api/v1/diversidade-vencedores${query ? `?${query}` : ""}`);
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const dados = (await resposta.json()) as DiversidadeVencedores[];
  const contagem = contarPorClassificacao(dados);

  const instanciaExistente = echarts.getInstanceByDom(container);
  const chart = instanciaExistente ?? echarts.init(container);
  chart.setOption(
    {
      title: tituloResponsivo("Diversidade de vencedores por processo licitatório"),
      tooltip: { trigger: "item" },
      series: [
        {
          name: "Processos",
          type: "pie",
          radius: "60%",
          data: Array.from(contagem.entries()).map(([name, value]) => ({ name, value })),
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
}
