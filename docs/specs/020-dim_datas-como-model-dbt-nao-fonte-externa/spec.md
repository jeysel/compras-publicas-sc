# 020 — `dim_datas` como model dbt, não fonte externa

## Tipo

Decisão de arquitetura.

## Status

Implementado e validado. `dbt build` completo: 127/127 verde (1 seed, 12 table models, 12 view models, 102 data tests). `marts.dim_datas` com 5.844 linhas, batendo com a expectativa documentada.

## Resumo

`raw.dim_datas` hoje é populada por uma procedure Postgres (`raw.sp_popula_dim_datas()`) chamada automaticamente pelo mecanismo `docker-entrypoint-initdb.d` (`postgres/init/01_init.sql`) — que só dispara na primeira inicialização do **volume de dados do container inteiro**, não por banco/schema novo criado dentro de um container já existente. Isso é incompatível com o modelo de deploy de produção (spec 003: schema dedicado dentro do Postgres compartilhado, container já rodando há muito tempo) — o gap nunca poderia ter sido evitado só ajustando configuração, é incompatibilidade estrutural entre mecanismo e arquitetura.

Decisão: reconstruir `dim_datas` como **model dbt** que gera a dimensão de calendário via computação pura (`dbt_utils.date_spine`), eliminando a dependência de qualquer mecanismo externo ao dbt. Funciona identicamente em qualquer ambiente (dev, produção, um servidor novo daqui a um ano) sem bootstrap especial.

## Contexto

- Achado da investigação (sessão anterior): `raw.dim_datas` é `source` (não seed), documentado em `dbt/models/sources.yml` como "populada pela procedure `raw.sp_popula_dim_datas()` executada automaticamente no `01_init.sql`", período `2015-01-01` a `2030-12-31`, 5.844 linhas esperadas.
- `dbt_utils` já é dependência do projeto (`dbt deps` já resolve, usado em outros models/testes — confirmado em investigações anteriores desta sessão).
- Consistente com a decisão já tomada pro `pipeline_metadata` (spec 009/019): tirar estado/lógica de um mecanismo externo frágil e trazer pra dentro do que o próprio pipeline controla e testa.

## Requirements

### Funcionais

1. O sistema DEVE gerar a dimensão de calendário via um model dbt novo (ex.: `dbt/models/staging/stg_dim_datas.sql` ou `intermediate/int_dim_datas_base.sql` — nome exato a confirmar na implementação, seguindo a convenção do projeto), usando `dbt_utils.date_spine` para o intervalo `2015-01-01` a `2030-12-31`.
2. O model `marts/dim_datas.sql` existente DEVE ser atualizado para referenciar (`ref()`) o model novo em vez de `source('raw', 'dim_datas')` — preservando as colunas descritivas já calculadas hoje (`nm_mes`, `nm_trimestre`, `sigla_trimestre`, `fl_fim_de_semana`, `primeiro_dia_mes`, `ultimo_dia_mes`, e quaisquer outras que a implementação confirmar existir).
3. A entrada `dim_datas` DEVE ser removida de `dbt/models/sources.yml` (não é mais fonte externa).
4. `postgres/init/01_init.sql` (criação da tabela/procedure `raw.dim_datas`/`sp_popula_dim_datas`) DEVE ser removido ou claramente marcado como obsoleto — não deve continuar existindo como caminho paralelo e não-usado que confunde manutenção futura.
5. QUANDO o `dbt build` completo rodar (dev ou produção), O sistema NÃO DEVE mais depender de nenhum passo de setup fora do dbt para `dim_datas` estar disponível.

### Não-funcionais

1. A contagem de linhas resultante DEVE bater com a expectativa já documentada (5.844 linhas para o intervalo 2015-2030) — validar na implementação, não presumir que `date_spine` produz exatamente o mesmo resultado sem conferir.
2. Nenhum model ou teste dbt downstream (`fct_contratos`, testes de `not_null`/`unique` já existentes em `dim_datas`) DEVE quebrar por causa da migração — validar com `dbt build` completo, 128/128 (ou o total atual) continuando 100% verde.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Mecanismo de geração | Model dbt com `dbt_utils.date_spine`, não seed nem source externa | Elimina de vez a classe de problema (bootstrap externo ao dbt que não dispara em ambiente de produção) — mesmo raciocínio já aplicado ao `pipeline_metadata` |
| Onde entra na camada do projeto | `dbt/models/staging/stg_dim_datas.sql` — só a spinha de datas (`dt_data`), materializado como view (padrão da camada staging) | Preserva as colunas descritivas já calculadas e testadas no `marts/dim_datas.sql`, minimiza mudança de superfície — só troca a origem do dado bruto, não a lógica de enriquecimento. `dim_datas` recalcula todas as colunas derivadas a partir de `dt_data` (mesma fórmula que estava em `sp_popula_dim_datas()`), não apenas repassa colunas prontas |
| `postgres/init/01_init.sql` | Removido (não só marcado obsoleto) | Nada mais referenciava o arquivo (confirmado via grep) e deixar um caminho morto é fonte de confusão futura. Consequência: `postgres/init/` ficou vazio — como não é rastreado pelo git, um clone novo perderia o diretório e quebraria o `COPY init/ /opt/init/` do Dockerfile. Removido também o `COPY` e o bloco correspondente no `entrypoint.sh` (não havia mais nada usando esse mecanismo — `pipeline_metadata`, a outra migração recente pro mesmo padrão, faz seu próprio bootstrap em `dbt/scripts/ingest.sh`, não aqui) |
| Intervalo de data | Mantido `2015-01-01` a `2030-12-31` (mesmo já documentado) | Sem motivo levantado nesta spec pra mudar o intervalo — mudança de escopo de data é decisão separada, se algum dia necessária. **Achado da implementação:** `dbt_utils.date_spine` trata `end_date` como exclusivo (offset `row_number() over (...) - 1`) — para incluir `2030-12-31` no resultado o argumento passado precisou ser `2031-01-01`, não a data final desejada. Sem esse ajuste o resultado batia 5.843, não 5.844 |

### Componentes afetados

- Novo model (staging ou intermediate) gerando o date spine.
- `dbt/models/marts/dim_datas.sql` — troca `source()` por `ref()`.
- `dbt/models/sources.yml` — remove a entrada `dim_datas`.
- `postgres/init/01_init.sql` — remover ou marcar obsoleto.
- `README.md` — remover o passo de validação manual de `dim_datas` (não é mais pré-requisito separado).

## Casos de borda

- Confirmado: `dim_datas` não tinha colunas além das já listadas no Requirement 2 (16 colunas ao todo, incluindo `dt_data`) — lista completa lida direto do `.sql` real e da procedure `sp_popula_dim_datas()` antes da implementação.
- Confirmado: `date_spine` gerava 5.843 linhas com `end_date` igual à data final desejada (exclusivo) — corrigido passando `2031-01-01`, resultando nas 5.844 linhas esperadas. Ver linha do Design sobre o intervalo de data.
- **Achado fora do escopo desta spec, não corrigido aqui:** `nm_mes`/`nm_mes_abrev`/`nm_dia_semana` saem em inglês (`January`, não `Janeiro`) tanto no model novo quanto no `raw.dim_datas` antigo (confirmado comparando os dois antes de remover o antigo) — a sessão de `psql` roda com `lc_time = C`, não `pt_BR.UTF-8`. Causa raiz provável: o pacote `postgresql-17` do Ubuntu cria um cluster default via `postinst` no build da imagem (locale `C.UTF-8`), e o `initdb --locale=pt_BR.UTF-8` do `entrypoint.sh` nunca chega a rodar porque o cluster "já existe" (`${PGDATA}/PG_VERSION` já presente) — confirmado subindo um container novo a partir da imagem sem volume: o log não mostra `>>> Inicializando cluster PostgreSQL...`. Pré-existente, independente desta migração; registrar como pendência a esclarecer em spec própria se for pra corrigir.

## Fora do escopo

- Mudar o intervalo de datas coberto.
- Qualquer mudança na lógica de enriquecimento já existente em `marts/dim_datas.sql` (mês, trimestre, fim de semana etc.) além da troca de fonte.

## Referências de código

- `dbt/models/staging/stg_dim_datas.sql` — model novo, gera a spinha de datas via `dbt_utils.date_spine`.
- `dbt/models/staging/schema/stg_dim_datas.yml` — doc/testes (`not_null`, `unique` em `dt_data`).
- `dbt/models/marts/dim_datas.sql` — atualizado: `ref('stg_dim_datas')` em vez de `source('raw', 'dim_datas')`; todas as 15 colunas derivadas agora calculadas ali (antes vinham prontas da source).
- `dbt/models/sources.yml` — removido (só continha a entrada `dim_datas`).
- `postgres/init/01_init.sql` — removido.
- `postgres/init/` — diretório removido (vazio após a remoção do arquivo acima).
- `postgres/Dockerfile` — removido `COPY init/ /opt/init/`.
- `postgres/entrypoint.sh` — removido o bloco "Executa scripts SQL de inicialização" (seção 6), que dependia de `postgres/init/`; seções renumeradas.
- `README.md` — removido o passo de validação manual de `raw.dim_datas` e a referência a `01_init.sql`/`sources.yml` na árvore de diretórios.

## Ver também

- [[009-automacao-da-ingestao]]
- [[019-processamento-robusto-do-CSV-real]]
