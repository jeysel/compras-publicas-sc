const formatadorMoedaBRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export function formatarMoedaBRL(valor: number): string {
  return formatadorMoedaBRL.format(valor);
}

const formatadorPercentual = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatarPercentual(valor: number): string {
  return `${formatadorPercentual.format(valor)}%`;
}

// Notação compacta ("R$ 500 mi") para rótulo de eixo em mobile — o formato completo
// (formatarMoedaBRL) sobrepõe em telas estreitas quando o eixo tem vários ticks.
const formatadorMoedaCompactaBRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
  minimumFractionDigits: 0,
});

export function formatarMoedaCompactaBRL(valor: number): string {
  return formatadorMoedaCompactaBRL.format(valor);
}

export function truncarTexto(texto: string, maxCaracteres: number): string {
  return texto.length > maxCaracteres ? `${texto.slice(0, maxCaracteres - 1)}…` : texto;
}

// data ISO ("aaaa-mm-dd") para "dd/mm/aaaa" sem passar por Date (evita conversão de
// fuso horário deslocando o dia) — null vira "—" (ex.: dt_inicio/dt_fim_atual nulos).
export function formatarData(dataISO: string | null | undefined): string {
  if (!dataISO) return "—";
  const [ano, mes, dia] = dataISO.split("-");
  return `${dia}/${mes}/${ano}`;
}

// Período "início – fim", cada lado em aberto ("—") se a data faltar (spec 031,
// achado: dt_inicio também pode ser nulo na fonte, não só dt_fim_atual).
export function formatarPeriodo(dtInicio: string | null | undefined, dtFimAtual: string | null | undefined): string {
  return `${formatarData(dtInicio)} – ${formatarData(dtFimAtual)}`;
}
