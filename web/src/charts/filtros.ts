import type { components } from "../api-types";

type Orgao = components["schemas"]["Orgao"];
type Modalidade = components["schemas"]["Modalidade"];

export interface FiltrosGrafico {
  cod_unidade_gestora?: string;
  nm_modalidade?: string;
}

async function popularOrgaos(select: HTMLSelectElement): Promise<void> {
  const resposta = await fetch("/api/v1/orgaos");
  if (!resposta.ok) return;
  const orgaos = (await resposta.json()) as Orgao[];
  for (const orgao of orgaos) {
    const option = document.createElement("option");
    option.value = orgao.cod_unidade_gestora;
    option.textContent = orgao.nm_unidade_gestora;
    select.append(option);
  }
}

async function popularModalidades(select: HTMLSelectElement): Promise<void> {
  const resposta = await fetch("/api/v1/modalidades");
  if (!resposta.ok) return;
  const modalidades = (await resposta.json()) as Modalidade[];
  for (const modalidade of modalidades) {
    const option = document.createElement("option");
    option.value = modalidade.nm_modalidade;
    option.textContent = modalidade.nm_modalidade;
    select.append(option);
  }
}

interface OpcoesFiltrosGrafico {
  // mart_contratos_temporal só tem recorte pré-agregado de uma dimensão por vez
  // (Geral | Órgão | Modalidade, ver mart_contratos_temporal.sql) — não existe
  // recorte "Órgão + Modalidade" combinado. Nessa mart, escolher um filtro
  // precisa limpar o outro; nas demais (grão de contrato), os dois combinam.
  mutuamenteExclusivo?: boolean;
}

// Popula os <select> de órgão/modalidade (options além do "Todos" inicial, já no HTML)
// e dispara onChange com os filtros atuais a cada troca de seleção. Estado do filtro
// não persiste entre navegações — cada carga de página volta para "Todos".
export function initFiltrosGrafico(
  orgaoSelectId: string,
  modalidadeSelectId: string | null,
  onChange: (filtros: FiltrosGrafico) => void,
  opcoes: OpcoesFiltrosGrafico = {},
): void {
  const orgaoSelect = document.getElementById(orgaoSelectId) as HTMLSelectElement | null;
  if (orgaoSelect === null) return;
  const modalidadeSelect =
    modalidadeSelectId === null ? null : (document.getElementById(modalidadeSelectId) as HTMLSelectElement | null);

  void popularOrgaos(orgaoSelect);
  if (modalidadeSelect !== null) void popularModalidades(modalidadeSelect);

  const disparar = (): void => {
    onChange({
      cod_unidade_gestora: orgaoSelect.value || undefined,
      nm_modalidade: modalidadeSelect?.value || undefined,
    });
  };

  orgaoSelect.addEventListener("change", () => {
    if (opcoes.mutuamenteExclusivo && orgaoSelect.value && modalidadeSelect) modalidadeSelect.value = "";
    disparar();
  });
  modalidadeSelect?.addEventListener("change", () => {
    if (opcoes.mutuamenteExclusivo && modalidadeSelect.value) orgaoSelect.value = "";
    disparar();
  });
}
