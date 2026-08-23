import * as echarts from "echarts";
import type { components } from "../api-types";

type DiversidadeVencedores = components["schemas"]["DiversidadeVencedores"];

function contarPorClassificacao(dados: DiversidadeVencedores[]): Map<string, number> {
  const contagem = new Map<string, number>();

  for (const processo of dados) {
    const classificacao = processo.ds_diversidade ?? "Não classificado";
    contagem.set(classificacao, (contagem.get(classificacao) ?? 0) + 1);
  }

  return contagem;
}

export async function renderDiversidadeVencedores(containerId: string): Promise<void> {
  const container = document.getElementById(containerId);
  if (container === null) return;

  const resposta = await fetch("/api/v1/diversidade-vencedores");
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const dados = (await resposta.json()) as DiversidadeVencedores[];
  const contagem = contarPorClassificacao(dados);

  const chart = echarts.init(container);
  chart.setOption({
    title: { text: "Diversidade de vencedores por processo licitatório" },
    tooltip: { trigger: "item" },
    series: [
      {
        name: "Processos",
        type: "pie",
        radius: "60%",
        data: Array.from(contagem.entries()).map(([name, value]) => ({ name, value })),
      },
    ],
  });

  // Fix especulativo (spec pendente) para gráfico encolhido observado em iPhone real —
  // causa não confirmada em código (container já tem altura px explícita, listener de
  // resize já existia); força um resize após o primeiro layout do Safari por precaução.
  requestAnimationFrame(() => chart.resize());
  window.addEventListener("resize", () => chart.resize());
}
