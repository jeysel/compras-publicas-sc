# Spec 003 — Storage e chave única (Fase 1: levantamento complementar)

Status: rascunho, aguardando revisão humana antes de virar tarefa executável.

Levantamento somente leitura. Nenhum comando abaixo alterou dado, schema, container ou config — inclusive as consultas SQL do Bloco A são todas `SELECT`.

**Nota (2026-08-19):** o Bloco A desta spec foi reescrito para remover dado operacional físico (nomes literais de containers de outros projetos rodando no mesmo host) que não deveria estar num repo público — ver regra em `docs/memory/constitution.md`. O output literal completo (incluindo `docker stats` de todos os containers do host) foi movido para a spec equivalente no mono-repo de infra privado (`docs/specs/078-compras-publicas-estado-infra-k3s/spec.md`). Aqui ficam só os achados de capacidade que informam a decisão de storage.

## Investigação

### Bloco A — Recurso da VPS e do container Postgres

**Correção de premissa:** o container assumido no prompt (`postgres-redis`) não existe. `docker ps -a` no host mostra `postgres` (postgres:16-alpine) e `redis` (redis:7-alpine) como containers separados. Os comandos abaixo rodaram contra `postgres` e `redis` individualmente.

```
--- free -h ---
               total        used        free      shared  buff/cache   available
Mem:           7,8Gi       3,5Gi       266Mi        78Mi       4,4Gi       4,3Gi
Swap:          2,0Gi       162Mi       1,8Gi

--- nproc ---
2

--- df -h ---
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           795M  4,8M  790M   1% /run
/dev/sda1        96G   41G   56G  43% /
tmpfs           3,9G     0  3,9G   0% /dev/shm
tmpfs           5,0M     0  5,0M   0% /run/lock
/dev/sda16      881M  117M  703M  15% /boot
/dev/sda15      105M  6,2M   99M   6% /boot/efi
tmpfs           795M   12K  795M   1% /run/user/1000
```

```
--- docker inspect postgres (limites) ---
Memory: 2147483648        (2 GiB)
MemorySwap: 2621440000    (~2.44 GiB total mem+swap)
CpuShares: 0
CpuQuota: 0
NanoCpus: 0

--- docker inspect redis (limites) ---
Memory: 201326592         (192 MiB)
MemorySwap: 268435456     (256 MiB total mem+swap)
CpuShares: 0
CpuQuota: 0
NanoCpus: 0
```

```
--- docker stats postgres --no-stream ---
CONTAINER ID   NAME       CPU %     MEM USAGE / LIMIT   MEM %     NET I/O           BLOCK I/O        PIDS
5b43cc125b2b   postgres   0.00%     85.34MiB / 2GiB     4.17%     25.9MB / 83.5MB   94.9MB / 210MB   15

--- docker stats redis --no-stream ---
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O         BLOCK I/O         PIDS
f285693b9c7f   redis     0.42%     3.945MiB / 192MiB   2.05%     405MB / 475MB   8.69MB / 2.38MB   7
```

**Achado (contexto geral do host, detalhe completo em `docs/specs/078-compras-publicas-estado-infra-k3s/spec.md` no repo de infra privado):** o host roda, além de `postgres`/`redis`, outros 6 containers de projetos distintos (CI/pipeline, workers, apps web) dividindo os mesmos 2 vCPUs — um deles chegou a ~43% de CPU no momento da medição. Isso reforça a conclusão abaixo: CPU compartilhada é o recurso a vigiar, não RAM/disco.

**Achado (nomes literais de banco/projeto no repo de infra privado — `docs/specs/078-...`):** o container `postgres` compartilhado já hospeda 4 bancos de outras aplicações, todos pequenos (7–20 MB cada, `pg_stat_activity`/`pg_database_size` confirmam).

**Observação:** a VPS tem só **2 vCPUs** e **7,8Gi de RAM total**, com apenas **266Mi livre "de verdade"** no momento da medição (4,3Gi "available" conta buff/cache reclamável, não memória livre real). Disco tem folga (56G disponíveis de 96G, 43% usado). O container `postgres` compartilhado já tem limite de 2GiB de memória configurado (usando só 85MiB agora) e hospeda os 4 bancos de outras aplicações citados acima. Somar `compras_publicas` a este mesmo container é viável em termos de tamanho de dado (a seed atual tem ~76 mil linhas, ordem de MB, não GB), mas a CPU (2 vCPUs, já dividida entre os containers de todos os projetos do host, incluindo workloads de CI que picam alto durante builds) é o recurso mais apertado do host, não RAM nem disco — relevante para decidir se `compras_publicas` entra como schema/database adicional no `postgres` compartilhado ou como container próprio.

---

### Bloco B — Verificação de chave única

**Desvio do prompt original:** não foi encontrado nenhum arquivo `.xls`/`.xlsx` em `compras-publicas-sc` nem nas cópias locais do mesmo repo (`c:\Dev\Analytics-Engineer\compras-publicas`, mesmo remote `github.com/jeysel/Analytics-Engineer`). O único dado real baixado do portal presente no repo é `dbt/seeds/contratos.csv` (`;`-delimitado, 76.041 linhas, sem cabeçalho duplicado). Não existe segundo arquivo de período diferente em lugar nenhum do disco local, nem script de ingestão implementado (`docs/backlog/features/feature-01.2-transparencia_sc.md` e a story correspondente descrevem a extração como funcionalidade **planejada**, ainda não codificada — não há `.py` de ingestão no repo). Rodei o Bloco B contra o único arquivo real disponível, ajustando os nomes de coluna candidatos (as colunas do prompt — `numero_processo`, `numero_empenho`, `numero_licitacao`, `id` — não existem neste arquivo; os nomes reais são os do dicionário de dados do Transparência SC, ex. `nucontrato`, `nuprocesso`).

```
--- colunas disponiveis ---
['cdunidadegestora', 'nmunidadegestora', 'cdgestao', 'nmgestao', 'nucontrato',
 'idcontratado', 'contratado', 'resumo', 'objeto', 'dtinicio', 'dtfim',
 'dtfimatual', 'dtassinatura', 'situacao', 'nuprocesso', 'vloriginal',
 'vlatual', 'nmfiscal', 'nuedital', 'nmbempublico', 'nmregimeexecucao',
 'detipocontrato', 'detipodocumentolegal', 'nudocumentolegal', 'demulta',
 'nuautorizacaoorgao', 'nuprazo', 'nminterveniente', 'nmlocalexecucao',
 'nmmodalidade', 'nmrepcredor', 'nmrepinterveniente', 'nmrepug',
 'dtautorizacao', 'dtinclusao', 'dtlimiteproposta', 'vlgarantia',
 'vlpercgarantia', 'vlpercmulta', 'nutitulo', 'vladitado', 'cdugfiscalizador',
 'ugfiscalizador', 'cdgestaofiscalizador', 'gestaofiscalizador', 'bempublico',
 'deesptitulo', 'dataproposta', 'diasoriginais', 'diasaditados', 'diasatuais']

--- total de linhas ---
76041

--- colunas candidatas individuais ---
Coluna 'nucontrato': 74843 valores unicos de 76041 linhas (1198 duplicadas)
Coluna 'nuprocesso': 42349 valores unicos de 76041 linhas (33692 duplicadas)
Coluna 'nuedital': 21831 valores unicos de 76041 linhas (54210 duplicadas)
Coluna 'nuautorizacaoorgao': 2550 valores unicos de 76041 linhas (73491 duplicadas)
Coluna 'nutitulo': 5508 valores unicos de 76041 linhas (70533 duplicadas)
Coluna 'idcontratado': 11406 valores unicos de 76041 linhas (64635 duplicadas)

--- chaves compostas ---
Chave composta ['cdunidadegestora', 'nucontrato']: 76041 combinacoes unicas de 76041 linhas (0 duplicadas)
Chave composta ['nucontrato', 'dtassinatura']: 76037 combinacoes unicas de 76041 linhas (4 duplicadas)
Chave composta ['nuprocesso', 'nucontrato']: 76041 combinacoes unicas de 76041 linhas (0 duplicadas)
```

**Observação:** nenhuma coluna isolada é chave única — `nucontrato` chega mais perto (74.843/76.041) mas tem 1.198 duplicadas, esperado já que o mesmo número de contrato pode se repetir entre unidades gestoras diferentes. Duas chaves compostas testadas deram **100% únicas, batendo exatamente com o total de linhas**: `(cdunidadegestora, nucontrato)` e `(nuprocesso, nucontrato)` — ambas com 76.041/76.041 combinações únicas, 0 duplicadas.

**Limitação real, não contornada:** só havia um arquivo/período disponível localmente. O teste acima confirma unicidade *dentro* deste arquivo, mas **não confirma que a mesma chave composta permanece estável *entre* cargas diferentes** do portal (pré-requisito real para merge/incremental) — isso pediria pelo menos um segundo arquivo baixado em outro momento, que não existe no ambiente local nem foi gerado nesta investigação (nenhum download novo foi feito — fora do escopo desta fase, que é só leitura do que já existe). Fica como pendência explícita para a Fase 2 ou para uma Fase 1 complementar, caso o usuário disponibilize ou aponte um segundo arquivo de período diferente.

---

## Design

Decisão de grão e chave confirmada em [[005-grao-do-dado-contrato-vs-aditivo]] — não reaberta aqui.

| Decisão | Escolha | Razão |
|---|---|---|
| Motor de banco | Postgres | Volume médio (dezenas de milhares de linhas), sem necessidade de BigQuery para este projeto; ver achados de recurso da VPS abaixo |
| Instância | Schema/banco dedicado dentro do container `postgres` já existente (não container novo) | VPS é KVM 2 vCPU / 8GB — CPU é o teto real, não RAM; container novo duplica overhead de baseline sem resolver o gargalo de CPU. Reversível: migrar pra instância própria (ou servidor melhor) fica em aberto se o padrão de uso justificar depois |
| Grão do dado | 1 registro = 1 contrato | Confirmado em [[005-grao-do-dado-contrato-vs-aditivo]] — não existe padrão de aditivo como evento em linha própria nos dados de origem (nem sufixo `-NN`, nem coluna de evento); `vladitado`/`diasaditados` são atributos cumulativos do contrato |
| Chave única | `(cdunidadegestora, nucontrato)` | Validada 100% (76.041/76.041, spec 003) e confirmada como explicação real das colisões (reuso de numeração sequencial entre unidades gestoras diferentes — spec 005), não um remendo em cima de ambiguidade real |
| Estratégia de carga | Upsert (merge) por `(cdunidadegestora, nucontrato)` | Grão = contrato, sem necessidade de staging append-only por aditivo (rejeitado em 005) |
| Histórico de mudança | `dbt snapshot` sobre campos que importam analiticamente (`situacao`, `vlatual`, `vladitado`, `dtfimatual`) | Snapshot mensal do estado atual pode alterar esses campos entre cargas (contrato aditivado, status mudando) — snapshot captura a mudança sem duplicar o dataset inteiro a cada carga |
| Origem do dado | Arquivo CSV (não API) | [[004-origem-dados-api-vs-arquivo]] — CKAN do portal não tem DataStore habilitado, API indisponível para este recurso |
| Escopo temporal | Definido em spec própria (backfill histórico separado do fluxo corrente) | Ver pendência aberta abaixo |
| Dev local vs. validação pré-deploy | Dois ambientes distintos, não concorrentes: dev local descartável (`compras_postgres`, container próprio deste repo) para iteração; Postgres compartilhado do `infra` (schema dedicado, decisão original desta spec) só para validação pré-deploy, tratado com o mesmo cuidado de produção | Reprodutibilidade do portfólio (fluxo `git clone` → `docker compose up` não pode depender do repo privado `infra`) e isolamento de risco (iteração destrutiva de `dbt build`/`dbt test`, inclusive em loop por agente, não deve rodar contra recurso compartilhado com outros projetos) |

### Ambiente de desenvolvimento vs. ambiente de produção — distinção formal

A decisão original desta spec (schema/banco dedicado dentro do Postgres
compartilhado, produção) não implica que o desenvolvimento do dia a dia deva
rodar contra esse mesmo Postgres. São dois ambientes com propósitos
diferentes, ambos válidos, não concorrentes:

| Ambiente | Onde roda | Propósito | Descartável? |
|---|---|---|---|
| **Dev local** | `compras_postgres` (container próprio, `docker-compose.yml` deste repo) | Iteração rápida: `dbt build`/`dbt test` repetido, full-refresh, `DROP SCHEMA`, qualquer operação destrutiva sem medo | Sim — recriar do zero é trivial (`docker compose up postgres -d` + `dbt seed`) |
| **Validação pré-deploy** | Postgres compartilhado do projeto `infra` (schema dedicado, spec 003 original) | Confirmar, antes do corte de produção, que o schema/permissão/isolamento se comportam como esperado no ambiente real, compartilhado com `jeysel-auth`/`weather-analytics` | Não — é o ambiente real, tratado com o mesmo cuidado de produção |

#### Por que não desenvolver direto contra o Postgres compartilhado do `infra`

1. **Reprodutibilidade do portfólio**: o README de `compras-publicas-sc`
   documenta um fluxo (`git clone` → `docker compose up` → `dbt build`) que
   qualquer pessoa roda sozinha, sem acesso a nada privado. Acoplar o dev do
   dia a dia ao projeto `infra` (privado) quebraria esse fluxo pra qualquer
   avaliador externo do portfólio.
2. **Iteração destrutiva sem risco**: testes de dbt em loop (inclusive
   rodados por agente, como o Claude Code fazendo várias rodadas de
   `dbt build`/`dbt test` numa sessão) podem envolver operação destrutiva
   por natureza. Contra um container descartável, sem consequência. Contra o
   Postgres compartilhado — mesmo com schema isolado — um erro de teste vira,
   na pior hipótese, contenção de recurso ou efeito colateral nos ambientes
   de dev de outros projetos.

#### O que muda no fluxo de deploy

Antes de qualquer deploy real pra produção (specs 010/011, ainda não
implementadas em código), fica formalizada uma etapa explícita de
**validação contra o schema real** no Postgres compartilhado do `infra` —
não pra desenvolver ali, só pra confirmar isolamento/permissão antes do
corte. Essa etapa é nova nesta spec; não existia antes desta sessão.

#### Fora do escopo deste adendo

- Migrar o dev local pra depender do `infra` — decidido explicitamente que
  não, pelos dois motivos acima.
- Definir o passo a passo exato da validação pré-deploy — fica para quando
  o deploy real (specs 010/011) for de fato implementado.

### Pendências que permanecem em aberto após este fechamento

- **Estabilidade da chave entre cargas do formato atual**: só temos um arquivo do formato atual (`contrato-demo.csv`). A validação de `(cdunidadegestora, nucontrato)` contra um segundo mês do formato atual ainda não foi feita — fica para quando a ingestão mensal rodar pela segunda vez, ou para um teste manual antecipado se o usuário preferir.
- **Backfill histórico (76 mil linhas, `seeds/contratos.csv`)**: tratado como spec separada, ainda não aberta — este Design cobre o fluxo corrente (formato atual, daí pra frente), não a normalização do histórico 2011+.
- **`nmunidadegestora` não é estável entre fontes/períodos** — achado da [[006-backfill-historico]]: 753 códigos de `cdunidadegestora` têm nomes divergentes entre `seeds/contratos.csv` e o arquivo `contratos-2011-2021.csv` do portal (reorganização administrativa real, não erro de dado). A chave `(cdunidadegestora, nucontrato)` validada acima usa só o código, não o nome — permanece válida. Mas qualquer join, filtro ou agrupamento futuro por `nmunidadegestora` (em vez de `cdunidadegestora`) vai produzir resultado errado. Não reabre a decisão de chave, só registra a ressalva pra quem for implementar consultas/relatórios.

### Componentes afetados

- Modelo de staging dbt: upsert por `(cdunidadegestora, nucontrato)`.
- Novo: `dbt snapshot` para os 4 campos de mudança de estado.
- Schema/banco novo no Postgres existente (`postgres`), sem provisionar container adicional.

## Fora do escopo desta fase

Decisão de storage (schema dedicado no `postgres` compartilhado vs. container próprio) e de estratégia de carga (full-refresh vs. incremental/merge por `(cdunidadegestora, nucontrato)` ou `(nuprocesso, nucontrato)`) ficam para a Fase 2, condicionadas à resolução da pendência de verificação entre períodos acima.

## Ver também

- [[005-grao-do-dado-contrato-vs-aditivo]] — confirma que a colisão de `nucontrato` é reuso de número entre unidades gestoras, não aditivo mal identificado; chave composta `(cdunidadegestora, nucontrato)` validada aqui é a resposta final, sem necessidade de reestruturar o grão.
