import * as echarts from "echarts";
import type { components } from "../api-types";
import type { FiltrosGrafico } from "./filtros";
import { isMobileViewport, tituloResponsivo } from "./theme";

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
  if (filtros.ano_inicio) params.set("ano_inicio", filtros.ano_inicio);
  if (filtros.ano_fim) params.set("ano_fim", filtros.ano_fim);
  const query = params.toString();

  const resposta = await fetch(`/api/v1/diversidade-vencedores${query ? `?${query}` : ""}`);
  if (!resposta.ok) {
    container.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const dados = (await resposta.json()) as DiversidadeVencedores[];
  const contagem = contarPorClassificacao(dados);

  const mobile = isMobileViewport();

  const instanciaExistente = echarts.getInstanceByDom(container);
  const chart = instanciaExistente ?? echarts.init(container);
  chart.setOption(
    {
      title: tituloResponsivo("Diversidade de vencedores por processo licitatório"),
      tooltip: { trigger: "item" },
      // Rótulo com linha de chamada (padrão desktop) trunca em "…" num grid estreito
      // (observado real em 375px) — em mobile o nome completo da categoria vai pra
      // legenda embaixo do pie em vez de rótulo externo cortado.
      legend: mobile ? { bottom: 0, left: "center" } : undefined,
      series: [
        {
          name: "Processos",
          type: "pie",
          radius: mobile ? "50%" : "60%",
          center: mobile ? ["50%", "48%"] : undefined,
          label: mobile ? { show: false } : undefined,
          data: Array.from(contagem.entries()).map(([name, value]) => ({ name, value })),
        },
      ],
    },
    true,
  );

  // Fix especulativo para gráfico encolhido observado em iPhone real — causa não
  // confirmada em código (container já tem altura px explícita, listener de resize já
  // existia); força um resize após o primeiro layout do Safari por precaução. Investigação
  // em iOS real segue pendente (spec 036, "Não validado") — isto NÃO foi confirmado como
  // correção, só mantido por precaução.
  requestAnimationFrame(() => chart.resize());
  if (instanciaExistente === undefined) {
    window.addEventListener("resize", () => chart.resize());
  }
}
