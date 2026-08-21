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
