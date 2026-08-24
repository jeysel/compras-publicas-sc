import type { components } from "../api-types";

type Orgao = components["schemas"]["Orgao"];
type Modalidade = components["schemas"]["Modalidade"];

export interface FiltrosGrafico {
  cod_unidade_gestora?: string;
  nm_modalidade?: string;
  ano?: string;
  ano_inicio?: string;
  ano_fim?: string;
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

// Intervalo fixo (footer do layout: "a partir de 2016") — não há endpoint que liste os
// anos com dado real, e o volume por ano já é pequeno o bastante pra não valer a pena
// buscar do dataset carregado (spec pendente, ver nota de filtro de ano).
const ANO_MIN = 2016;

function popularAnos(select: HTMLSelectElement): void {
  const anoAtual = new Date().getFullYear();
  for (let ano = anoAtual; ano >= ANO_MIN; ano--) {
    const option = document.createElement("option");
    option.value = String(ano);
    option.textContent = String(ano);
    select.append(option);
  }
}

// Dropdown de ano único (EscaladaCusto — parâmetro `ano` do endpoint).
export function initFiltroAnoUnico(selectId: string, onChange: (ano: string | undefined) => void): void {
  const select = document.getElementById(selectId) as HTMLSelectElement | null;
  if (select === null) return;
  popularAnos(select);
  select.addEventListener("change", () => onChange(select.value || undefined));
}

export interface FiltroAnoIntervalo {
  ano_inicio?: string;
  ano_fim?: string;
}

// Par "Ano Inicial"/"Ano Final" (ano_inicio/ano_fim) — reutilizado pelos 4 endpoints
// que suportam intervalo. Estado inicial sem filtro = mostra tudo, como os demais filtros.
export function initFiltroAnoIntervalo(
  inicioSelectId: string,
  fimSelectId: string,
  onChange: (filtro: FiltroAnoIntervalo) => void,
): void {
  const inicioSelect = document.getElementById(inicioSelectId) as HTMLSelectElement | null;
  const fimSelect = document.getElementById(fimSelectId) as HTMLSelectElement | null;
  if (inicioSelect === null || fimSelect === null) return;
  popularAnos(inicioSelect);
  popularAnos(fimSelect);

  const disparar = (): void => {
    onChange({
      ano_inicio: inicioSelect.value || undefined,
      ano_fim: fimSelect.value || undefined,
    });
  };
  inicioSelect.addEventListener("change", disparar);
  fimSelect.addEventListener("change", disparar);
}
