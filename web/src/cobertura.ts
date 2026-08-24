import type { components } from "./api-types";

type AnosDisponiveis = components["schemas"]["AnosDisponiveis"];

// Substitui o "2016" fixo no footer/home/metodologia (herdado do protótipo, spec 025,
// nunca conferido contra o dado real) pelo ano_min real de anos-disponiveis — mesma
// fonte usada pelos dropdowns de ano (filtros.ts). Roda em toda página (o footer,
// via layout.html, aparece em todas).
export async function initCoberturaAno(): Promise<void> {
  const elementos = document.querySelectorAll<HTMLElement>(".ano-cobertura");
  if (elementos.length === 0) return;

  const resposta = await fetch("/api/v1/anos-disponiveis");
  if (!resposta.ok) return;
  const { ano_min } = (await resposta.json()) as AnosDisponiveis;
  elementos.forEach((el) => {
    el.textContent = String(ano_min);
  });
}
