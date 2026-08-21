export function setLegendaExclusao(legendaId: string, texto: string): void {
  const legenda = document.getElementById(legendaId);
  if (legenda === null) return;
  legenda.innerHTML = texto;
}
