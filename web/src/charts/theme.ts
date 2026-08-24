import type { TitleComponentOption } from "echarts";

// Mesmo breakpoint usado em style.css (@media max-width: 720px).
const MOBILE_BREAKPOINT = 720;

// main (16px) + chart-card (8px) de padding horizontal de cada lado em mobile (style.css).
const MOBILE_HORIZONTAL_PADDING = (16 + 8) * 2;

export function isMobileViewport(): boolean {
  return window.innerWidth <= MOBILE_BREAKPOINT;
}

// ECharts desenha o título em canvas, não herda cor de CSS — lê a variável de
// heading do tema (light/dark via prefers-color-scheme) para manter contraste.
function corTitulo(): string {
  const cor = getComputedStyle(document.documentElement).getPropertyValue("--text-h").trim();
  return cor || "#333";
}

// Título mobile quebrado em linha em vez de cortado (fix para título longo cortado
// na borda ao ficar mais largo que a viewport, ver spec de correção de gráficos mobile).
export function tituloResponsivo(text: string): TitleComponentOption {
  const mobile = isMobileViewport();
  return {
    text,
    textStyle: {
      color: corTitulo(),
      fontSize: mobile ? 14 : 18,
      lineHeight: mobile ? 18 : undefined,
      width: mobile ? window.innerWidth - MOBILE_HORIZONTAL_PADDING : undefined,
      overflow: mobile ? "break" : undefined,
    },
  };
}
