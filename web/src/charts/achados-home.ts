import type { components } from "../api-types";
import { formatarMoedaBRL, formatarPercentual } from "./format";

type ConcentracaoFornecedor = components["schemas"]["ConcentracaoFornecedor"];

const TOP_N = 10;

export async function renderAchadosHome(): Promise<void> {
  const valorFornecedorEl = document.getElementById("achado-maior-fornecedor-valor");
  const descFornecedorEl = document.getElementById("achado-maior-fornecedor-desc");
  const valorConcentracaoEl = document.getElementById("achado-concentracao-valor");
  const descConcentracaoEl = document.getElementById("achado-concentracao-desc");
  if (valorFornecedorEl == null || descFornecedorEl == null || valorConcentracaoEl == null || descConcentracaoEl == null) {
    return;
  }

  const resposta = await fetch(`/api/v1/concentracao-fornecedor?top_n=${TOP_N}`);
  if (!resposta.ok) {
    descFornecedorEl.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    descConcentracaoEl.textContent = `Erro ao carregar dados (HTTP ${resposta.status})`;
    return;
  }

  const top = (await resposta.json()) as ConcentracaoFornecedor[];
  if (top.length === 0) return;

  const maior = top[0];
  valorFornecedorEl.textContent =
    maior.vl_total_fornecedor_estado == null ? "—" : formatarMoedaBRL(Number(maior.vl_total_fornecedor_estado));
  descFornecedorEl.textContent =
    `Maior fornecedor do estado no período: ${maior.nm_contratado ?? maior.id_contratado}` +
    (maior.perc_sobre_total_estado == null
      ? "."
      : `, equivalente a ${formatarPercentual(Number(maior.perc_sobre_total_estado))} de todo o valor contratado em Santa Catarina.`);

  const somaPercentual = top.reduce(
    (soma, f) => soma + (f.perc_sobre_total_estado == null ? 0 : Number(f.perc_sobre_total_estado)),
    0,
  );
  valorConcentracaoEl.textContent = `${formatarPercentual(somaPercentual)} em ${top.length} fornecedores`;
  descConcentracaoEl.textContent =
    `Os ${top.length} maiores fornecedores do estado concentram ${formatarPercentual(somaPercentual)} de todo o valor ` +
    "contratado no período.";
}
