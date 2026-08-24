export function criarPaginador<T>(
  linhas: T[],
  tbody: HTMLTableSectionElement,
  renderLinha: (linha: T, row: HTMLTableRowElement) => void,
  botao: HTMLButtonElement | null,
  tamanhoPagina = 15,
): void {
  let exibidas = 0;

  function renderPagina(): void {
    for (const linha of linhas.slice(exibidas, exibidas + tamanhoPagina)) {
      renderLinha(linha, tbody.insertRow());
    }
    exibidas = Math.min(exibidas + tamanhoPagina, linhas.length);
    if (botao) botao.hidden = exibidas >= linhas.length;
  }

  renderPagina();
  botao?.addEventListener("click", renderPagina);
}
