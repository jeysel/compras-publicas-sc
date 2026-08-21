import { renderEscaladaCusto } from "./charts/escalada-custo";
import { renderDiversidadeVencedores } from "./charts/diversidade-vencedores";
import { renderContratosTemporal } from "./charts/contratos-temporal";
import { renderConcentracaoFornecedor } from "./charts/concentracao-fornecedor";
import "./style.css";

const page = document.body.dataset.page;

if (page === "home") {
  void renderEscaladaCusto("chart-escalada-custo", "legenda-escalada-custo");
  void renderDiversidadeVencedores("chart-diversidade-vencedores");
  void renderContratosTemporal("chart-contratos-temporal", "legenda-contratos-temporal");
  void renderConcentracaoFornecedor("chart-concentracao-fornecedor", "legenda-concentracao-fornecedor");
}
