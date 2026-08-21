const formatadorMoedaBRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export function formatarMoedaBRL(valor: number): string {
  return formatadorMoedaBRL.format(valor);
}
