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
