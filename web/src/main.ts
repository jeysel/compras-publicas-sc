import { renderEscaladaCusto } from "./charts/escalada-custo";
import { renderDiversidadeVencedores } from "./charts/diversidade-vencedores";
import { renderContratosTemporal } from "./charts/contratos-temporal";
import { renderConcentracaoFornecedor } from "./charts/concentracao-fornecedor";
import {
  renderFornecedorPorSegmentoGrafico,
  renderFornecedorPorSegmentoRelatorio,
  type FiltroSegmento,
  type FiltroSegmentoBusca,
} from "./charts/fornecedor-por-segmento";
import { renderQualidadeDadoOrgao } from "./charts/qualidade-dado-orgao";
import { renderVariacaoCustoModalidade } from "./charts/variacao-custo-modalidade";
import { renderVariacaoPrazoModalidade } from "./charts/variacao-prazo-modalidade";
import { renderAchadosHome } from "./charts/achados-home";
import { renderKpisResumo } from "./charts/kpis-resumo";
import { renderPerfilFornecedores } from "./charts/perfil-fornecedores";
import { renderPerfilOrgaos } from "./charts/perfil-orgaos";
import {
  initFiltrosGrafico,
  initFiltroAnoIntervalo,
  initFiltroSegmento,
  initFiltroBuscaTexto,
  initFiltroPeriodo,
  type FiltrosGrafico,
  type FiltroAnoIntervalo,
} from "./charts/filtros";
import { initNavbarToggle } from "./nav";
import { initCoberturaAno } from "./cobertura";
import "./style.css";

initNavbarToggle();
void initCoberturaAno();

const page = document.body.dataset.page;

if (page === "home") {
  void renderKpisResumo();
  void renderAchadosHome();
} else if (page === "relatorio-perfil-fornecedores") {
  const rerenderPerfilFornecedores = (filtros: FiltroAnoIntervalo): void =>
    void renderPerfilFornecedores("chart-perfil-fornecedores", filtros);
  rerenderPerfilFornecedores({});
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", rerenderPerfilFornecedores);
} else if (page === "relatorio-perfil-orgaos") {
  const rerenderPerfilOrgaos = (filtros: FiltroAnoIntervalo): void =>
    void renderPerfilOrgaos("chart-perfil-orgaos", "tabela-ranking-quantidade", "tabela-ranking-valor", filtros);
  rerenderPerfilOrgaos({});
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", rerenderPerfilOrgaos);
} else if (page === "grafico-escalada-custo") {
  let filtrosAtuais: FiltrosGrafico = {};
  const rerenderEscaladaCusto = (): void =>
    void renderEscaladaCusto("chart-escalada-custo", "legenda-escalada-custo", filtrosAtuais);
  rerenderEscaladaCusto();
  initFiltrosGrafico("filtro-orgao", "filtro-modalidade", (filtros) => {
    filtrosAtuais = { ...filtrosAtuais, ...filtros };
    rerenderEscaladaCusto();
  });
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", (anoFiltro) => {
    filtrosAtuais = { ...filtrosAtuais, ...anoFiltro };
    rerenderEscaladaCusto();
  });
} else if (page === "grafico-diversidade-vencedores") {
  let filtrosAtuais: FiltrosGrafico = {};
  const rerenderDiversidadeVencedores = (): void =>
    void renderDiversidadeVencedores("chart-diversidade-vencedores", filtrosAtuais);
  rerenderDiversidadeVencedores();
  initFiltrosGrafico("filtro-orgao", null, (filtros) => {
    filtrosAtuais = { ...filtrosAtuais, ...filtros };
    rerenderDiversidadeVencedores();
  });
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", (anoFiltro) => {
    filtrosAtuais = { ...filtrosAtuais, ...anoFiltro };
    rerenderDiversidadeVencedores();
  });
} else if (page === "grafico-serie-temporal") {
  let filtrosAtuais: FiltrosGrafico = {};
  const rerenderContratosTemporal = (): void =>
    void renderContratosTemporal(
      "chart-contratos-temporal",
      "legenda-contratos-temporal",
      "chart-sazonalidade-mensal",
      filtrosAtuais,
    );
  rerenderContratosTemporal();
  initFiltrosGrafico(
    "filtro-orgao",
    "filtro-modalidade",
    (filtros) => {
      filtrosAtuais = { ...filtrosAtuais, ...filtros };
      rerenderContratosTemporal();
    },
    { mutuamenteExclusivo: true },
  );
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", (anoFiltro) => {
    filtrosAtuais = { ...filtrosAtuais, ...anoFiltro };
    rerenderContratosTemporal();
  });
} else if (page === "grafico-concentracao-fornecedor") {
  let filtrosAtuais: FiltrosGrafico = {};
  const rerenderConcentracaoFornecedor = (): void =>
    void renderConcentracaoFornecedor("chart-concentracao-fornecedor", "legenda-concentracao-fornecedor", filtrosAtuais);
  rerenderConcentracaoFornecedor();
  initFiltrosGrafico("filtro-orgao", null, (filtros) => {
    filtrosAtuais = { ...filtrosAtuais, ...filtros };
    rerenderConcentracaoFornecedor();
  });
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", (anoFiltro) => {
    filtrosAtuais = { ...filtrosAtuais, ...anoFiltro };
    rerenderConcentracaoFornecedor();
  });
} else if (page === "grafico-fornecedor-por-segmento") {
  let filtrosAtuais: FiltroSegmento = {};
  const rerenderFornecedorPorSegmento = (): void =>
    void renderFornecedorPorSegmentoGrafico(
      "chart-fornecedor-por-segmento",
      "legenda-fornecedor-por-segmento",
      filtrosAtuais,
    );
  rerenderFornecedorPorSegmento();
  initFiltroSegmento("filtro-ramo", (ramo_atividade) => {
    filtrosAtuais = { ...filtrosAtuais, ramo_atividade };
    rerenderFornecedorPorSegmento();
  });
  initFiltroPeriodo("filtro-periodo-de", "filtro-periodo-ate", (periodo) => {
    filtrosAtuais = { ...filtrosAtuais, ...periodo };
    rerenderFornecedorPorSegmento();
  });
} else if (page === "relatorio-fornecedor-por-segmento") {
  let filtrosAtuais: FiltroSegmentoBusca = {};
  const rerenderFornecedorPorSegmentoRelatorio = (): void =>
    void renderFornecedorPorSegmentoRelatorio(
      "tabela-fornecedor-por-segmento",
      "btn-ver-mais-fornecedor-por-segmento",
      "legenda-fornecedor-por-segmento",
      filtrosAtuais,
    );
  rerenderFornecedorPorSegmentoRelatorio();
  initFiltroSegmento("filtro-ramo", (ramo_atividade) => {
    filtrosAtuais = { ...filtrosAtuais, ramo_atividade };
    rerenderFornecedorPorSegmentoRelatorio();
  });
  initFiltroBuscaTexto("filtro-nome-fornecedor", (nm_contratado) => {
    filtrosAtuais = { ...filtrosAtuais, nm_contratado };
    rerenderFornecedorPorSegmentoRelatorio();
  });
  initFiltroPeriodo("filtro-periodo-de", "filtro-periodo-ate", (periodo) => {
    filtrosAtuais = { ...filtrosAtuais, ...periodo };
    rerenderFornecedorPorSegmentoRelatorio();
  });
} else if (page === "relatorio-qualidade-orgao") {
  const rerenderQualidadeDadoOrgao = (filtros: FiltroAnoIntervalo): void =>
    void renderQualidadeDadoOrgao("tabela-qualidade-dado-orgao", "btn-ver-mais-qualidade-dado-orgao", filtros);
  rerenderQualidadeDadoOrgao({});
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", rerenderQualidadeDadoOrgao);
} else if (page === "relatorio-variacao-custo") {
  const rerenderVariacaoCustoModalidade = (filtros: FiltroAnoIntervalo): void =>
    void renderVariacaoCustoModalidade(
      "chart-variacao-custo-modalidade",
      "tabela-variacao-custo-modalidade",
      "btn-ver-mais-variacao-custo-modalidade",
      "insight-variacao-custo-modalidade",
      filtros,
    );
  rerenderVariacaoCustoModalidade({});
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", rerenderVariacaoCustoModalidade);
} else if (page === "relatorio-variacao-prazo") {
  const rerenderVariacaoPrazoModalidade = (filtros: FiltroAnoIntervalo): void =>
    void renderVariacaoPrazoModalidade(
      "chart-variacao-prazo-modalidade",
      "tabela-variacao-prazo-modalidade",
      "btn-ver-mais-variacao-prazo-modalidade",
      filtros,
    );
  rerenderVariacaoPrazoModalidade({});
  initFiltroAnoIntervalo("filtro-ano-inicio", "filtro-ano-fim", rerenderVariacaoPrazoModalidade);
}
