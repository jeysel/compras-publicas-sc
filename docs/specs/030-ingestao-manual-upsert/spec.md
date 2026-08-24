# 030 — Ingestão manual via SCP com upsert (substitui o CKAN morto)

## Tipo

Decisão de arquitetura — fecha a lacuna aberta pelas specs 016/018/019 (schema real do portal) e pela [[009-automacao-da-ingestao]] (rotina automática hoje presa a uma fonte morta).

## Status

**Mecanismo validado em produção em 2026-08-24** (carga inicial real executada
passo a passo). Esta revisão substitui o design anterior (proposto, nunca
implementado, baseado em upload para S3) pelo mecanismo que de fato foi
usado — SCP, não S3 — e formaliza num script único e repetível o que naquele
dia foi feito comando a comando. O script (repositório de infraestrutura,
privado — fora deste repo) foi testado localmente com um CSV de amostra
nesta revisão, mas **ainda não foi executado em produção**; a carga real de
2026-08-24 foi feita antes de o script existir, direto via linha de comando.

## Resumo

A fonte CKAN original (`dados.sc.gov.br`) está congelada desde set/2025 —
o `ETag`/`Last-Modified` do arquivo não muda desde então (confirmado nas
specs 016/018/019/029, mesmo valor em todas). O cron diário (spec 009)
continua rodando sem falha, mas em no-op puro: a Secretaria simplesmente
parou de publicar atualização naquele link. A fonte viva é o portal de
busca (`transparencia.sc.gov.br`), que expõe as mesmas 51 colunas via
export manual da UI — decisão consciente de **não** integrar com a API por
trás dessa busca (não documentada, instável demais pra depender em
produção). O fluxo passa a ser: usuário exporta manualmente pelo portal,
envia o arquivo para o servidor via SCP, dispara o pipeline manualmente.
**Decisão final: SCP, não S3** (avaliado no design anterior desta spec) —
mais simples e sem a pendência de permissão de IAM que o caminho via S3
teria exigido resolver antes de funcionar.

A mudança de fonte muda a premissa estrutural do pipeline: `raw.contratos`
era recarregada por inteiro a cada execução (`dbt seed`, DROP+CREATE)
porque a fonte CKAN sempre publicava o histórico completo. Um export
manual do portal de busca não tem essa garantia — pode ser um recorte
(período, órgão). Um reload ingênuo apagaria tudo fora daquele recorte.
Por isso o mecanismo de carga é **upsert por chave**
(`cdunidadegestora`, `nucontrato` — já validada como chave única desde a
[[003-storage-e-chave-unica]]), preservando o que estiver fora do arquivo.

**Carga inicial executada em 2026-08-24**: upsert de um export
2011–2026 (103.455 registros) sobre uma base que tinha 95.508 —
resultado **95.508 → 104.574** (9.066 registros novos, 6.172
atualizados — a maioria variação de valor/prazo por aditivo legítimo,
1.119 registros fora do export mas preservados por design, nunca
apagados). Validado ponta a ponta: `dbt build` completo sem erro (108/108
testes), API pública confirmando a contagem nova.

## Contexto

- **Fonte CKAN congelada, não removida** (confirmado nesta revisão): a
  rotina automática (spec 009, cron diário) continua ativa e não foi
  desligada — decisão do design anterior desta mesma spec ("remover o
  CKAN") foi **revertida na prática**: em 2026-08-24, antes da carga
  manual, o cron real rodou e baixou o CSV do CKAN normalmente (primeira
  execução depois de uma investigação de regressão não relacionada a esta
  spec — ver Casos de borda para o risco real que essa coexistência cria).
- **Schema do export do portal de busca**: confirmado nesta revisão contra
  a carga real de 2026-08-24 — as mesmas 51 colunas de `raw.contratos`,
  mesmo nome e mesma ordem. Ponto que a revisão anterior desta spec listava
  como "não reconfirmado" (nota de proveniência) está agora validado com
  execução real, não só relato.
- **Encoding e separador decimal divergentes, confirmado com dado real**:
  o export do portal de busca vem em ISO-8859-1 com separador decimal
  vírgula (vírgula, sem separador de milhar, em 6 colunas monetárias:
  `vloriginal`, `vlatual`, `vladitado`, `vlgarantia`, `vlpercgarantia`,
  `vlpercmulta`). `raw.contratos` guarda essas colunas como `numeric` —
  incompatível com vírgula.
- **Achado de metodologia (custou 2 tentativas na carga real)**: um
  "dry-run" de validação de cast no formato `SELECT count(*) FROM
  (SELECT col::numeric ...) t` **não valida nada** — o planner do
  Postgres pode podar a projeção (nada fora do `count(*)` referencia o
  valor) e nunca avaliar a expressão de cast, escondendo um erro que só
  aparece no `INSERT` real. Documentado aqui porque não é peculiaridade
  pontual: é um buraco sistemático em qualquer fluxo "valida primeiro,
  roda de verdade depois" contra Postgres. A validação real precisa que o
  cast seja o próprio argumento do agregado (`count(col::tipo)`), não algo
  dentro de uma subquery cujo resultado não é referenciado.
- **`raw.contratos` tem tipos além de varchar/text**: além das 6 colunas
  `numeric`, o `dbt seed` original também tipou 5 colunas como `integer`
  (`diasoriginais`, `diasaditados`, `diasatuais`, `cdugfiscalizador`,
  `cdgestaofiscalizador`) e 8 colunas de data como `timestamp` — inferido
  automaticamente pelo `dbt seed` a partir do conteúdo do CSV original,
  não só do que está declarado explicitamente em
  `dbt/seeds/schema/contratos.yml`. Qualquer mecanismo de carga que
  bypassa o `dbt seed` (como este) precisa replicar esse mapeamento de
  tipo manualmente — divergência encontrada e corrigida durante o teste
  local desta revisão, antes de chegar em produção.
- **Upsert por `(cdunidadegestora, nucontrato)` já é a chave validada do
  projeto** — [[003-storage-e-chave-unica]] confirmou unicidade dessa
  chave composta e a spec 009 já documentava a decisão original de
  "upsert (merge)", nunca implementada de fato porque o CKAN sempre trazia
  o histórico inteiro (reload bastava). Esta spec é a primeira vez que o
  upsert de verdade roda contra produção.
- **`stg_contratos.sql` não precisou mudar** (achado desta revisão,
  simplifica o design anterior): `{{ ref('contratos') }}` resolve para o
  nome físico `raw.contratos` independente de quem populou a tabela —
  `dbt seed` ou um `INSERT` manual escrevem no mesmo lugar. A proposta
  anterior de trocar para `{{ source(...) }}` não é necessária para este
  mecanismo funcionar; documentado como decisão revista, não pendência.

## Requirements

### Funcionais

- REQ-1: QUANDO o usuário disparar a rotina manualmente informando o
  caminho de um CSV já recebido via SCP no servidor, o sistema DEVE usar
  esse arquivo diretamente — sem download de rede, sem CKAN, sem S3.
- REQ-2: O sistema DEVE tratar o arquivo como ISO-8859-1 (decisão fixa,
  confirmada com export real — não detecção heurística) e normalizar
  separador decimal de vírgula para ponto nas 6 colunas monetárias
  conhecidas via substituição direta antes do cast (`REPLACE(col, ',',
  '.')::numeric`) — não um passo de pré-processamento externo separado.
- REQ-3: O sistema DEVE fazer upsert das linhas em `raw.contratos` por
  chave `(cdunidadegestora, nucontrato)`: chave já existente é
  atualizada (UPDATE); chave nova é inserida; nenhuma linha de
  `raw.contratos` fora do arquivo processado é apagada ou alterada.
- REQ-4: `raw.contratos` DEVE ter constraint `UNIQUE` em
  `(cdunidadegestora, nucontrato)` como pré-requisito do upsert — **já
  aplicada em produção** (2026-08-24).
- REQ-5: O sistema NÃO DEVE rodar `dbt seed` como parte deste fluxo —
  upsert via SQL direto contra `raw.contratos`, seguido de `dbt run` +
  `dbt test` (sem `--full-refresh`) sobre o dado já upsertado. Nenhuma
  mudança em `stg_contratos.sql` é necessária (ver Contexto).
- REQ-6: O sistema DEVE fazer backup de `raw.contratos` (dump completo da
  tabela) antes de qualquer escrita.
- REQ-7: A rotina automática do CKAN (spec 009) permanece ativa — **não**
  é removida por esta spec (decisão revertida em relação à revisão
  anterior). Ver Casos de borda para o risco de colisão que essa
  coexistência cria — **superado em 2026-08-24**: o disparo automático foi
  desligado (cron removido do host), decisão tomada fora desta spec; ver
  Casos de borda.
- REQ-8: QUANDO o arquivo informado estiver vazio, não existir, ou o
  cabeçalho não bater exatamente com as 51 colunas esperadas (mesma
  ordem, comparação case-insensitive), o sistema DEVE abortar sem
  alterar `raw.contratos`, com mensagem de erro visível.
- REQ-9: QUANDO o mesmo arquivo contiver duas ou mais linhas com a mesma
  chave `(cdunidadegestora, nucontrato)`, o sistema DEVE manter só a
  última ocorrência (ordem de aparição no arquivo) antes do upsert — um
  `INSERT ... ON CONFLICT DO UPDATE` batelado falha
  (`cannot affect row a second time`) se a mesma chave aparecer duas
  vezes no mesmo comando.
- REQ-10: Depois do upsert e antes de aplicar qualquer alteração real, o
  sistema DEVE reportar o impacto esperado (quantas linhas são novas,
  quantas já existem e serão atualizadas, quantos registros de
  `raw.contratos` ficam fora do arquivo e são preservados) e pedir
  confirmação explícita do usuário.
- REQ-11: Após upsert bem-sucedido, o sistema DEVE arquivar (não apagar)
  o CSV fonte processado, com timestamp, num diretório separado do que
  recebe o arquivo original.

### Não-funcionais

- REQ-12: O upsert DEVE ser idempotente — reprocessar o mesmo arquivo, ou
  um arquivo com sobreposição parcial de linhas já carregadas, não pode
  duplicar linha nem corromper dado já correto.
- REQ-13: O log da execução DEVE reportar quantas linhas foram inseridas
  e quantas foram atualizadas de fato (contagem real pós-upsert via
  `RETURNING`, não uma estimativa do preview de REQ-10) — atualização de
  contrato já existente pode mudar valor já publicado, mesmo nível de
  cautela já exigido pelo fix de `fl_valor_suspeito`
  ([[021-levantamento-outliers-valor-extremo]]).
- REQ-14: A validação de cast (numérico, inteiro, data) DEVE forçar
  avaliação real por linha antes do upsert (ver achado de metodologia no
  Contexto) — nunca um dry-run cujo resultado o planner possa podar.
- REQ-15: Campo opcional em branco (comum em colunas como `vlgarantia`,
  `cdugfiscalizador`, `dtfimatual`) DEVE virar `NULL`, não erro de cast —
  só um valor realmente malformado (ex.: texto num campo numérico) deve
  abortar a execução.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Fonte de dado | Export manual do portal de busca → SCP direto pro servidor | CKAN congelado desde set/2025 (Contexto); API do portal de busca não documentada, instável demais pra depender em produção |
| Trigger | Manual, script único no repositório de infraestrutura — sem cron | Cadência não é previsível (diferente do CKAN, que publicava mensalmente); usuário controla quando/o que exportar |
| S3 vs. SCP | SCP | Decisão revista desta spec: S3 exigia resolver uma pendência de permissão IAM nunca confirmada; SCP reaproveita acesso já existente ao servidor, sem componente novo na imagem do pipeline |
| Onde `raw.contratos` vive | Fora do `dbt seed` pro fluxo manual — upsert via SQL direto contra a tabela física, que continua sendo a mesma referenciada por `{{ ref('contratos') }}` | Mesma causa raiz já resolvida pra `control.pipeline_metadata` (spec 009); `ref()` resolve pelo nome físico, não pelo mecanismo de carga — não precisa virar `source()` (Contexto) |
| Mecanismo de upsert | `INSERT ... ON CONFLICT (cdunidadegestora, nucontrato) DO UPDATE SET ...` via script, com validação de cast prévia forçada (REQ-14) | Upsert nativo do Postgres é atômico e idempotente por linha |
| Pré-processamento decimal | `REPLACE(col, ',', '.')` imediatamente antes do `::numeric`, só nas 6 colunas monetárias conhecidas | Confirmado com dado real (Contexto) — nunca há ponto nessas colunas na fonte, então a substituição não corrompe um valor que já estivesse correto |
| Pré-processamento encoding | Nativo do `COPY`/`\copy` do Postgres (parâmetro `ENCODING`), sem passo externo (`iconv`) | Mais simples que o design anterior (que previa detecção heurística fora do banco) — o Postgres já resolve a conversão no load, decisão fixa documentada (REQ-2) |
| Deduplicação dentro do arquivo | `DISTINCT ON (chave) ... ORDER BY chave, ctid DESC` antes do upsert — mantém a última ocorrência | Evita o erro conhecido do Postgres em `ON CONFLICT` batelado; testado localmente com chave duplicada no arquivo de amostra |
| Confirmação antes da escrita real | Prompt interativo, depois de mostrar o impacto esperado (REQ-10) | Nunca aplicar upsert silenciosamente — mesmo nível de cautela já exigido pra qualquer mudança que possa alterar valor já publicado |
| Rotina do CKAN (spec 009) | Mantida ativa, não removida | Decisão revertida em relação à revisão anterior desta spec — ver Casos de borda para o risco que isso cria, não resolvido aqui |

### Componentes afetados

- `dbt/models/staging/stg_contratos.sql` — **sem mudança** (achado desta
  revisão, ver Contexto).
- `dbt/scripts/ingest.sh`, `dbt/scripts/process_csv.py` — sem mudança;
  continuam sendo o mecanismo do fluxo automático do CKAN (spec 009),
  que permanece ativo em paralelo (REQ-7).
- Infra (repositório privado, fora deste repo): novo script operacional
  que consolida o fluxo manual descrito nesta spec (backup, staging,
  validação, preview, confirmação, upsert, `dbt run`/`dbt test`,
  arquivamento) — testado localmente contra um CSV de amostra nesta
  revisão. Comandos, caminhos e nomes de container ficam documentados só
  no repo de infra (Constitution, regra 1), não aqui.

## Casos de borda

- **Colisão entre o cron do CKAN e o fluxo manual — resolvido em
  2026-08-24, cron desligado.** A rotina automática (spec 009) chamava
  `dbt seed --select contratos` sempre que o `ETag` do CKAN mudasse. Isso
  fazia DROP+CREATE de `raw.contratos` a partir do CSV do CKAN, que **não
  tem** o histórico estendido (2011–2020) trazido só pelo fluxo manual.
  Enquanto o CKAN continuou congelado (Contexto), o cron rodou em no-op
  sem risco real — mas o risco de a Secretaria voltar a publicar naquele
  link e o próximo disparo automático apagar silenciosamente todo o ganho
  deste fluxo era real e permanecia aberto. Resolvido removendo a entrada
  do crontab do host (`ubuntu`, servidor de produção) que disparava
  `docker compose -f docker-compose.pipeline.yml run --rm
  compras-publicas-pipeline` (30 9 * * *) — a fonte CKAN foi definitivamente
  substituída pelo fluxo manual desta spec, não há mais motivo para manter
  a automação rodando em paralelo. O script `ingest.sh` e a imagem do
  pipeline **não foram apagados** (mantidos como histórico/referência,
  podem ser reativados manualmente se necessário) — só o disparo
  automático foi removido. Ver [[009-automacao-da-ingestao]], marcada
  como superada por esta decisão.
- **Contrato já existente com dado corrigido na fonte** (mesma chave,
  valores diferentes): upsert atualiza — pode mudar número já publicado.
  Confirmado na carga real (6.172 registros atualizados, maioria aditivo
  legítimo). Log visível do que foi inserido vs. atualizado (REQ-13) é o
  mínimo; revisão manual do resumo fica responsabilidade operacional.
- **Export é um recorte/subconjunto** (período, órgão, ou outro filtro
  aplicado na UI do portal): é o cenário que motiva upsert em vez de
  reload completo (Resumo) — mas o upsert **nunca remove**. Se um
  contrato for excluído na fonte, este mecanismo não detecta/reflete a
  exclusão — fica desatualizado até intervenção manual. Limitação
  consciente, confirmada na carga real (1.119 registros fora do export
  2011–2026, preservados por design, causa exata de estarem fora do
  export não totalmente esclarecida).
- **Duplicata de chave dentro do próprio arquivo** (REQ-9): resolvida por
  "última ocorrência vence" — testado localmente com um CSV de amostra
  contendo a mesma chave duas vezes, comportamento confirmado correto
  antes desta spec ser fechada.
- **Campo opcional em branco** (REQ-15): testado localmente — coluna
  numérica/inteira/data em branco vira `NULL`, não aborta a execução; só
  um valor realmente malformado (testado com texto num campo numérico)
  aborta antes de qualquer escrita.
- **Dry-run de cast que não valida nada** (achado de metodologia,
  Contexto): mitigado usando `count(col::tipo)` em vez de `count(*)`
  sobre uma subquery — testado localmente confirmando que um valor
  malformado é pego nesse passo, antes do upsert real.

## Fora do escopo

- Resolver a colisão entre o cron do CKAN e o fluxo manual (ver Casos de
  borda) — registrado como risco conhecido para decisão futura.
- Recarga do histórico anterior a 2011 — não avaliado, sem export
  correspondente até o momento.
- Integração automatizada com a API não documentada do portal de busca.
- Automação/cron do fluxo manual — é manual por decisão do usuário.
- Tratamento de exclusão de contrato na fonte (upsert nunca remove — ver
  Casos de borda).
- Upload via S3 — avaliado e descartado (Design), em favor de SCP.

## Referências de código

- `dbt/models/staging/stg_contratos.sql` — `{{ ref('contratos') }}`,
  confirmado nesta revisão que não precisa mudar.
- `dbt/scripts/ingest.sh`, `dbt/scripts/process_csv.py` — mecanismo do
  fluxo automático do CKAN (spec 009/019), sem mudança, permanece ativo.
- `dbt/seeds/schema/contratos.yml` — `column_types` parcial (6 numeric +
  3 integer); a carga real revelou 2 colunas `integer` e 8 colunas
  `timestamp` adicionais inferidas pelo `dbt seed` original, não
  declaradas explicitamente aqui (Contexto).
- `docs/specs/003-storage-e-chave-unica/spec.md` — validação original da
  chave `(cdunidadegestora, nucontrato)`.
- `docs/specs/009-automacao-da-ingestao/spec.md` — rotina do CKAN,
  precedente de design pro item "tabela fora do dbt seed".

## Ver também

- [[009-automacao-da-ingestao]] (rotina do CKAN, ainda ativa em paralelo)
- [[019-processamento-robusto-do-CSV-real]] (`process_csv.py`, sem mudança)
- [[003-storage-e-chave-unica]] (validação da chave composta)
- [[016-levantamento-schema-csv-portal]] e [[018-levantamento-bloqueios-seed-csv-real]] (evidência do CKAN congelado)
- [[021-levantamento-outliers-valor-extremo]] (precedente de cautela ao mudar valor já publicado)
- [[029-filtro-ano-marts-sem-coluna-ano]] (investigação da mesma sessão que confirmou o CKAN congelado antes desta carga)
