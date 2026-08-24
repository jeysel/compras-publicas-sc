import { renderEscaladaCusto } from "./charts/escalada-custo";
import { renderDiversidadeVencedores } from "./charts/diversidade-vencedores";
import { renderContratosTemporal } from "./charts/contratos-temporal";
import { renderConcentracaoFornecedor } from "./charts/concentracao-fornecedor";
import { renderQualidadeDadoOrgao } from "./charts/qualidade-dado-orgao";
import { renderVariacaoCustoModalidade } from "./charts/variacao-custo-modalidade";
import { renderVariacaoPrazoModalidade } from "./charts/variacao-prazo-modalidade";
import { renderAchadosHome } from "./charts/achados-home";
import { renderKpisResumo } from "./charts/kpis-resumo";
import { renderPerfilFornecedores } from "./charts/perfil-fornecedores";
import { renderPerfilOrgaos } from "./charts/perfil-orgaos";
import {
  initFiltrosGrafico,
  initFiltroAnoUnico,
  initFiltroAnoIntervalo,
  type FiltrosGrafico,
  type FiltroAnoIntervalo,
} from "./charts/filtros";
import { initNavbarToggle } from "./nav";
import "./style.css";

initNavbarToggle();

const page = document.body.dataset.page;

if (page === "home") {
  void renderKpisResumo();
  void renderAchadosHome();
} else if (page === "relatorio-perfil-fornecedores") {
  void renderPerfilFornecedores("chart-perfil-fornecedores");
} else if (page === "relatorio-perfil-orgaos") {
  void renderPerfilOrgaos(
    "chart-perfil-orgaos",
    "tabela-ranking-quantidade",
    "tabela-ranking-valor",
  );
} else if (page === "grafico-escalada-custo") {
  let filtrosAtuais: FiltrosGrafico = {};
  const rerenderEscaladaCusto = (): void =>
    void renderEscaladaCusto("chart-escalada-custo", "legenda-escalada-custo", filtrosAtuais);
  rerenderEscaladaCusto();
  initFiltrosGrafico("filtro-orgao", "filtro-modalidade", (filtros) => {
    filtrosAtuais = { ...filtrosAtuais, ...filtros };
    rerenderEscaladaCusto();
  });
  initFiltroAnoUnico("filtro-ano", (ano) => {
    filtrosAtuais = { ...filtrosAtuais, ano };
    rerenderEscaladaCusto();
  });
} else if (page === "grafico-diversidade-vencedores") {
  void renderDiversidadeVencedores("chart-diversidade-vencedores");
  initFiltrosGrafico("filtro-orgao", null, (filtros) =>
    void renderDiversidadeVencedores("chart-diversidade-vencedores", filtros),
  );
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
  void renderConcentracaoFornecedor("chart-concentracao-fornecedor", "legenda-concentracao-fornecedor");
  initFiltrosGrafico("filtro-orgao", null, (filtros) =>
    void renderConcentracaoFornecedor("chart-concentracao-fornecedor", "legenda-concentracao-fornecedor", filtros),
  );
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
