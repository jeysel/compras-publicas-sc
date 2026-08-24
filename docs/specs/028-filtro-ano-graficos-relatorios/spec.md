# Spec 028 — Filtro de ano/intervalo de ano em gráficos e relatórios

## Tipo

Nova funcionalidade (filtro interativo, reaproveitando parâmetros de query já existentes em 2 endpoints e adicionando parâmetros novos em outros 3) + registro de pendência conhecida (4 endpoints que não suportam o filtro sem redesenho de model dbt).

## Status

Implementado e validado em 2026-08-24. Item de paginação (tamanho de página 30→15 em `pagination.ts`) já estava concluído antes desta spec, como trabalho relacionado de UX na mesma área — incluído no mesmo commit.

### Validação

**Grupo B (3 endpoints com WHERE novo) — volume antes/depois do filtro, dado real de dev, confirmado via `fetch` (não presumido):**

```
qualidade-dado-orgao:        sem_filtro=76041 (414 linhas) | ano=2020: 5916 (105 linhas) | restringiu=true
variacao-custo-modalidade:   sem_filtro=37095 (18 linhas)  | ano=2020: 3537 (11 linhas)  | restringiu=true
variacao-prazo-modalidade:   sem_filtro=707 (1 linha)      | ano=2020: 6 (1 linha)       | restringiu=true
```

Intervalo (não só ano único) confirmado monotônico — janela maior nunca retorna menos que uma janela contida nela:

```
qualidade-dado-orgao:        ano=2020: 5916 | 2018-2020: 20915 | monotonico=true
variacao-custo-modalidade:   ano=2020: 3537 | 2018-2020: 11126 | monotonico=true
```

**`tsc --noEmit`**: sem erros. **`npm run build`**: sucesso (`vite build` gerou `main-edWk76jG.js`/`main-jcjRDNxD.css`, manifest atualizado).

**Verificação visual (Playwright ad-hoc via `chromium.launch()`, `npx playwright install chromium` — mesma ressalva já registrada na spec 026: não há suíte Playwright configurada no repo):**

- `/graficos/escalada-custo`: dropdown "Ano" populado com 2016–2026 (11 opções + "Todos os anos"); selecionar 2023 muda o gráfico de 13 barras (2013–2025, nota de qualidade "1121 de 76041 contratos excluídos") para 1 barra (2023, nota "78 de 6554"). Filtro de ano combinado com órgão testado explicitamente: sequência órgão→ano gerou as chamadas `?cod_unidade_gestora=920021` → `?cod_unidade_gestora=920021&ano=2022` — o segundo filtro não apaga o primeiro. 0 erros de console.
- `/graficos/serie-temporal`: 2 dropdowns "Ano inicial"/"Ano final" populados; selecionar "Ano inicial = 2023" muda a série de 2013-01→2025-12 para 2023-01→2025-12 e o gráfico de sazonalidade mensal recalcula (picos de Jan/Dez mudam de magnitude). Combinação ano→órgão testada: `?ano_inicio=2019` → `?cod_unidade_gestora=920021&ano_inicio=2019` — ano preservado ao trocar órgão depois. 0 erros de console.
- `/relatorios/qualidade-dado-orgao`: tabela reordena e recontabiliza com Ano inicial=2023 (1º lugar muda de "Fundo de Melhoria da Polícia Militar" pra "Secretaria de Estado da Educação (SED)", contagens batem com a validação de volume acima). 0 erros de console.
- `/relatorios/variacao-custo-modalidade`: gráfico + insight + tabela recalculam juntos (insight textual muda de "Pregão Eletrônico... 6,7%" pra "...17,9%" com Ano inicial=2023); sem série residual do filtro anterior sobreposta no gráfico (confirmado visualmente — fix de `notMerge`/reuso de instância aplicado nos 2 gráficos de barra que antes recriavam `echarts.init()` a cada chamada, ver Design). 0 erros de console.
- `/relatorios/variacao-prazo-modalidade`: gráfico + tabela recalculam (707→130 contratos, 202.7→152.9 dias médios com Ano inicial=2023). 0 erros de console.

## Resumo

Filtro de ano (dropdown único) ou intervalo de ano (par "Ano inicial"/"Ano final") em 5 páginas: `EscaladaCusto` (parâmetro `ano`, já existia no endpoint) e `ContratosTemporal` (`ano_inicio`/`ano_fim`, já existia) só precisavam de UI; `QualidadeDadoOrgao`, `VariacaoCustoModalidade` e `VariacaoPrazoModalidade` precisaram de `ano_inicio`/`ano_fim` novos no router (`WHERE` antes do `GROUP BY`, mesmo padrão dos 2 endpoints que já tinham) além da UI. Um componente reutilizável (`initFiltroAnoUnico`/`initFiltroAnoIntervalo` em `filtros.ts`) cobre os dois formatos, seguindo o mesmo padrão dos filtros de órgão/modalidade introduzidos antes desta spec (commit `aab8e3a`).

Fica pendente, registrado nesta spec e não implementado nesta rodada: 4 endpoints (`DiversidadeVencedores`, `ConcentracaoFornecedor`, `PerfilFornecedores`, `Orgaos`) cujas marts agregam por processo/fornecedor/órgão sobre todo o histórico, sem coluna de ano — filtrar por ano exigiria redesenho do grão do model dbt, não é um `WHERE` adicional no router. Ver Investigação e Fora do escopo.

## Contexto

Continuação direta da spec que introduziu filtro de órgão/modalidade nos 4 gráficos (commit `aab8e3a`, 2026-08-24) — mesmo padrão de UX, mesma decomposição client-side/server-side, dimensão nova (ano) em vez de órgão/modalidade.

## Investigação

**1. Confirmado antes de implementar: quais endpoints já suportavam filtro de ano e quais precisavam de mudança de SQL.**

```
api/app/routers/escalada_custo.py:        já tem `ano: int | None` (WHERE ano_assinatura = %(ano)s)
api/app/routers/contratos_temporal.py:    já tem `ano_inicio`/`ano_fim` (WHERE ano_assinatura >= / <=)
api/app/routers/qualidade_dado_orgao.py:      SEM filtro — GROUP BY direto sobre mart_escalada_custo
api/app/routers/variacao_custo_modalidade.py: SEM filtro — GROUP BY direto sobre mart_escalada_custo
api/app/routers/variacao_prazo_modalidade.py: SEM filtro — GROUP BY direto sobre mart_escalada_custo
```

Os 3 sem filtro leem da mesma `marts.mart_escalada_custo` que já tem `ano_assinatura` (usada pelos 2 primeiros) — adicionar `WHERE ano_assinatura BETWEEN` antes do `GROUP BY` já existente é suficiente, sem tocar em dbt.

**2. Não existe endpoint que liste "quais anos têm dado real"** (`grep -rn "ano" api/app/routers/orgaos.py api/app/routers/modalidades.py` não retornou nada relacionado a ano). Confirmado com o footer do `layout.html` ("a partir de 2016") como fonte da faixa fixa usada no dropdown: `2016` até o ano corrente do navegador (`new Date().getFullYear()`), populado nos 5 dropdowns. Não é uma consulta ao dataset carregado — decisão consciente de simplicidade (ver Design), já que os 3 endpoints de Grupo B carregam a mart inteira do servidor de qualquer forma; um ano sem dado no intervalo simplesmente retorna 0 linhas, mesmo comportamento já documentado como não-erro nas specs 025/026 para `GROUP BY` sem correspondência.

**3. Confirmado, ao editar `variacao-custo-modalidade.ts`/`variacao-prazo-modalidade.ts`, um bug pré-existente que o filtro de ano exporia:** as duas funções chamavam `echarts.init(container)` incondicionalmente a cada render, sem checar se já existia uma instância no elemento — diferente do padrão já usado em `escalada-custo.ts`/`contratos-temporal.ts` (`echarts.getInstanceByDom(container) ?? echarts.init(container)`, com `notMerge: true`). Sem filtro (1 render só, carregamento inicial) isso nunca dava problema visível; com filtro (múltiplos renders na mesma navegação) acumularia 1 listener de `resize` por troca de filtro. Corrigido como parte desta spec, replicando o padrão já estabelecido — não é escopo novo, é alinhar 2 arquivos que ficaram para trás quando o padrão foi criado.

**4. Confirmado, lendo os models dbt por trás dos 4 endpoints do Grupo C, que nenhum tem coluna de ano no grão da mart** (Fora do escopo, detalhado abaixo):

- `mart_diversidade_vencedores.sql` → `int_processos`: grão `(cod_unidade_gestora, nu_processo)`, tem `dt_primeiro_contrato`/`dt_ultimo_contrato` mas não `ano_assinatura` — um processo pode abranger mais de um ano.
- `dim_orgaos.sql` → `int_contratos_por_orgao`: grão `cod_unidade_gestora`, agregado sobre todo o histórico (`qt_contratos`, `vl_total_atual` já somados).
- `dim_fornecedores.sql` → `int_contratos_por_fornecedor`: mesmo padrão, grão `id_contratado`.
- `mart_concentracao_fornecedor.sql` → `int_concentracao_fornecedor_por_orgao`/`_estado`: grão `(órgão, fornecedor)` ou `(estado, fornecedor)`, também agregado sobre todo o histórico.

## Requirements

### Funcionais

- REQ-1: A página `/graficos/escalada-custo` DEVE exibir um dropdown "Ano" (opção inicial "Todos os anos" + 2016 até o ano corrente), reconectado ao parâmetro `ano` já suportado por `GET /api/v1/escalada-custo`.
- REQ-2: A página `/graficos/serie-temporal` DEVE exibir dois dropdowns "Ano inicial"/"Ano final" (mesma faixa do REQ-1), reconectados aos parâmetros `ano_inicio`/`ano_fim` já suportados por `GET /api/v1/contratos-temporal`.
- REQ-3: `GET /api/v1/qualidade-dado-orgao` DEVE aceitar `ano_inicio`/`ano_fim` opcionais (`int`) e aplicar `WHERE ano_assinatura >= ano_inicio AND ano_assinatura <= ano_fim` (condicional, cada lado independente) antes do `GROUP BY cod_unidade_gestora, nm_unidade_gestora` já existente. A página `/relatorios/qualidade-dado-orgao` DEVE expor os mesmos 2 dropdowns do REQ-2, reconectados a esses parâmetros.
- REQ-4: `GET /api/v1/variacao-custo-modalidade` DEVE aceitar `ano_inicio`/`ano_fim` opcionais, mesmo padrão de `WHERE` do REQ-3, combinado com os 3 filtros de linha já existentes (`vl_variacao <> 0`, `fl_aditivo_inconsistente IS NOT TRUE`, `fl_valor_suspeito IS NOT TRUE`) antes do `GROUP BY nm_modalidade_norm`. A página `/relatorios/variacao-custo-modalidade` DEVE expor os mesmos 2 dropdowns.
- REQ-5: `GET /api/v1/variacao-prazo-modalidade` DEVE aceitar `ano_inicio`/`ano_fim` opcionais, mesmo padrão do REQ-4 (substituindo `vl_variacao <> 0` por `dias_variacao <> 0`). A página `/relatorios/variacao-prazo-modalidade` DEVE expor os mesmos 2 dropdowns.
- REQ-6: Os dropdowns de ano DEVEM usar o mesmo componente visual (`.filter-bar`/`.filter-field`, CSS já existente) dos filtros de órgão/modalidade — sem CSS novo.
- REQ-7: QUANDO nenhum filtro de ano for selecionado, o sistema DEVE mostrar todo o histórico disponível (2016 até o mais recente) — mesmo comportamento padrão já estabelecido pros filtros de órgão/modalidade.
- REQ-8: QUANDO um filtro de ano for combinado com o filtro de órgão/modalidade já existente (nas páginas que têm os dois), trocar um DEVE preservar o valor atual do outro — confirmado explicitamente na Validação (sequência de troca gera query string com os 2 parâmetros).

### Não-funcionais

- REQ-9: A mudança de SQL nos 3 endpoints do Grupo B DEVE ser validada por comparação de volume antes/depois com um ano real do dataset, não só por HTTP 200 (documentado em Validação).
- REQ-10: Nenhuma mudança desta spec DEVE alterar o comportamento dos filtros de órgão/modalidade já existentes nas páginas que os têm — confirmado combinando os dois filtros na Validação, sem regressão.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Faixa de anos do dropdown | Fixa, `2016`–ano corrente (`new Date().getFullYear()`), client-side | Não existe endpoint que liste anos com dado real (Investigação item 2); footer do layout já assume "a partir de 2016" como início do dataset. Ano sem dado no intervalo retorna lista vazia, não erro. |
| Formato do filtro | Dropdown único (`ano`) só em `EscaladaCusto`; par "Ano inicial"/"Ano final" (`ano_inicio`/`ano_fim`) nos outros 4 | Reflete o parâmetro que cada endpoint já aceita ou deveria aceitar — `EscaladaCusto` já era ano único antes desta spec; os outros 4 já eram (2) ou passaram a ser (3) intervalo |
| Onde adicionar `WHERE` no Grupo B | Direto no router, antes do `GROUP BY` já existente — sem tocar em model dbt | Mesmo padrão dos 2 endpoints do Grupo A; `mart_escalada_custo` já tem `ano_assinatura`, não precisa de agregação nova |
| Componente de filtro | 2 funções novas em `filtros.ts` (`initFiltroAnoUnico`, `initFiltroAnoIntervalo`), reaproveitando o padrão de popular `<select>` + `addEventListener("change", …)` de `initFiltrosGrafico` | Mesmo arquivo, mesmo estilo de função, evita duplicar a lógica de popular/disparar em cada `main.ts` |
| Combinação de filtro de ano com órgão/modalidade | Estado combinado mantido em `main.ts` (`filtrosAtuais`, atualizado por spread a cada callback), não dentro de `filtros.ts` | `filtros.ts` já trata órgão/modalidade e ano como preocupações independentes (funções separadas); combinar é responsabilidade de quem orquestra a página, não do componente de filtro |
| Bug de `echarts.init()` sem reuso de instância em `variacao-custo-modalidade.ts`/`variacao-prazo-modalidade.ts` | Corrigido nesta spec, replicando `getInstanceByDom` + `notMerge: true` já usado em `escalada-custo.ts`/`contratos-temporal.ts` | Sem essa correção, o filtro de ano nessas 2 páginas acumularia listeners de resize a cada troca (Investigação item 3) |

### Componentes afetados

- `web/src/charts/filtros.ts` — `FiltrosGrafico` ganha `ano`/`ano_inicio`/`ano_fim` opcionais; funções novas `initFiltroAnoUnico`, `initFiltroAnoIntervalo`, tipo `FiltroAnoIntervalo`.
- `web/src/charts/escalada-custo.ts`, `contratos-temporal.ts` — adicionam o parâmetro de ano já suportado pelo backend à query string.
- `web/src/charts/qualidade-dado-orgao.ts`, `variacao-custo-modalidade.ts`, `variacao-prazo-modalidade.ts` — ganham parâmetro `filtros: FiltroAnoIntervalo` e query string; os 2 últimos também corrigem o reuso de instância ECharts (Investigação item 3).
- `api/app/routers/qualidade_dado_orgao.py`, `variacao_custo_modalidade.py`, `variacao_prazo_modalidade.py` — `ano_inicio`/`ano_fim` (`Query`), `WHERE` condicional antes do `GROUP BY`.
- `api/app/templates/grafico_escalada_custo.html`, `grafico_serie_temporal.html`, `relatorio_qualidade_orgao.html`, `relatorio_variacao_custo.html`, `relatorio_variacao_prazo.html` — dropdowns novos em `.filter-bar`.
- `web/src/main.ts` — orquestra estado combinado (`filtrosAtuais`) por página.
- `web/src/api-types.ts` — regenerado (`npm run generate-types`) para refletir os 3 parâmetros novos.
- `web/src/charts/pagination.ts` — `tamanhoPagina` 30→15 (já concluído antes desta spec, incluído no mesmo commit).

## Casos de borda

- Ano inicial maior que ano final (ex.: inicial=2023, final=2020): `WHERE ano_assinatura >= 2023 AND ano_assinatura <= 2020` nunca é satisfeito — retorna lista vazia, mesmo comportamento de "sem dado no intervalo" já aceito em outros filtros; não há validação client-side impedindo essa seleção (mesma decisão de simplicidade dos filtros de órgão/modalidade, que também não previnem combinações vazias).
- Ano fora da faixa 2016–corrente digitado manualmente na URL (o dropdown não permite, mas a API aceita qualquer `int`): `WHERE` simplesmente não bate com nenhuma linha — comportamento seguro, sem erro 500.
- Trocar órgão para um valor que não tem contrato no ano selecionado: tabela/gráfico ficam vazios — mesmo comportamento já existente na combinação órgão+modalidade antes desta spec.

## Fora do escopo

- **Filtro de ano em `DiversidadeVencedores`, `ConcentracaoFornecedor`, `PerfilFornecedores` e `Orgaos`.** Confirmado via leitura dos models (Investigação item 4): as 4 marts por trás desses endpoints agregam sobre todo o histórico, no grão de processo/fornecedor/órgão — não têm coluna de ano. Filtrar por ano exigiria redesenhar o grão (ex.: `(cod_unidade_gestora, ano_assinatura)` em vez de só `cod_unidade_gestora`), o que muda a semântica da mart (deixa de ser "perfil histórico do órgão" e passa a ser "perfil do órgão naquele ano") — decisão de modelagem que merece spec própria, não um `WHERE` incremental. Mesmo formato de registro de pendência já usado pro gap de `fl_valor_suspeito` em `top-aditivos` (spec 026, Fora do escopo).
- Endpoint que liste os anos com dado real (em vez de faixa fixa 2016–corrente) — ver Design; não implementado porque o efeito prático (ano sem dado retorna lista vazia) já é aceitável e o dataset já é conhecido por começar em 2016 (footer do `layout.html`).
- Persistir o filtro de ano entre navegações (ex.: querystring própria, `localStorage`) — mesma decisão já tomada pros filtros de órgão/modalidade (estado não persiste, cada carga de página volta para "Todos").

## Referências de código

- `api/app/routers/escalada_custo.py`, `contratos_temporal.py` — padrão de `WHERE ano_assinatura` já existente, replicado nos 3 endpoints do Grupo B.
- `web/src/charts/filtros.ts` — `initFiltrosGrafico` (órgão/modalidade), padrão replicado por `initFiltroAnoUnico`/`initFiltroAnoIntervalo`.
- `web/src/main.ts` — dispatch por `data-page`, onde os filtros de ano são combinados com órgão/modalidade já existentes.
- `dbt/models/marts/mart_diversidade_vencedores.sql`, `dim_orgaos.sql`, `dim_fornecedores.sql`, `mart_concentracao_fornecedor.sql` — marts sem coluna de ano (Fora do escopo).

## Ver também

- [[025-navbar-paginas-relatorios]] (padrão de página-por-relatório, `.filter-bar`/`.filter-field` original)
- [[026-kpis-classificacoes-rankings]] (formato de registro de pendência conhecida reaproveitado no Fora do escopo)
