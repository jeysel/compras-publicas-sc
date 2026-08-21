import { renderEscaladaCusto } from "./charts/escalada-custo";
import { renderDiversidadeVencedores } from "./charts/diversidade-vencedores";
import { renderContratosTemporal } from "./charts/contratos-temporal";
import { renderConcentracaoFornecedor } from "./charts/concentracao-fornecedor";
import { renderQualidadeDadoOrgao } from "./charts/qualidade-dado-orgao";
import { renderVariacaoCustoModalidade } from "./charts/variacao-custo-modalidade";
import { renderVariacaoPrazoModalidade } from "./charts/variacao-prazo-modalidade";
import { renderAchadosHome } from "./charts/achados-home";
import "./style.css";

const page = document.body.dataset.page;

if (page === "home") {
  void renderAchadosHome();
} else if (page === "grafico-escalada-custo") {
  void renderEscaladaCusto("chart-escalada-custo", "legenda-escalada-custo");
} else if (page === "grafico-diversidade-vencedores") {
  void renderDiversidadeVencedores("chart-diversidade-vencedores");
} else if (page === "grafico-serie-temporal") {
  void renderContratosTemporal("chart-contratos-temporal", "legenda-contratos-temporal");
} else if (page === "grafico-concentracao-fornecedor") {
  void renderConcentracaoFornecedor("chart-concentracao-fornecedor", "legenda-concentracao-fornecedor");
} else if (page === "relatorio-qualidade-orgao") {
  void renderQualidadeDadoOrgao("tabela-qualidade-dado-orgao");
} else if (page === "relatorio-variacao-custo") {
  void renderVariacaoCustoModalidade("chart-variacao-custo-modalidade", "tabela-variacao-custo-modalidade");
} else if (page === "relatorio-variacao-prazo") {
  void renderVariacaoPrazoModalidade("chart-variacao-prazo-modalidade", "tabela-variacao-prazo-modalidade");
}
