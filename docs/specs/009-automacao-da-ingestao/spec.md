# 009 — Automação da ingestão (download + trigger do pipeline)

## Tipo

Decisão de arquitetura — fecha o eixo pipeline (specs 003-008).

## Status

**Decisão revertida nesta sessão** (achado de deploy real): "Onde a rotina roda" muda de `CronJob` k3s para **crontab do host + `docker-compose run`**, seguindo o precedente real dos dois projetos vizinhos (nenhum usa CronJob k8s para rotina agendada, mesmo tendo cluster/Argo CD disponíveis — ambos usam crontab do host). O resto do Design (cadência via `ETag`/`HEAD`, validação de schema antes do `dbt run`, sequenciamento num único script) permanece válido — só o mecanismo de execução muda.

## Resumo

Hoje a carga do CSV do portal SC é manual (download + colocar no lugar certo pro dbt processar). Esta spec decide se — e como — automatizar: onde a rotina roda (script local, CronJob no k3s, etapa isolada em GH Actions), como ela detecta que há dado novo, e como ela se conecta ao pipeline já desenhado (specs 003-006: upsert por `(cdunidadegestora, nucontrato)`, snapshot de mudança, backfill separado).

## Contexto

- Spec 004 decidiu **arquivo, não API** — mas isso descartou só a API de *consulta* (`datastore_search`), não necessariamente a possibilidade de baixar o arquivo via HTTP de forma automatizada. O link de download de um recurso CKAN (`.../download/contratos.csv`) é um arquivo estático servido por URL fixa — não depende do DataStore estar habilitado. Precisa confirmar que esse link é estável e automatizável antes de assumir que "automação" significa simular clique num navegador.
- Publicação do portal é mensal (confirmado na investigação da spec 004/002).
- Deploy já decidido: Argo CD observando o repo do app, workloads em k3s (fronteira definida no CLAUDE.md) — isso segue valendo para o futuro `Deployment` do FastAPI (spec 012). Uma rotina agendada se encaixa naturalmente como `CronJob` do Kubernetes, mas isso não foi formalmente decidido — é a opção mais consistente com o que já existe, não uma conclusão automática. **Nota (revertida nesta sessão):** essa hipótese foi testada no Bloco 3 abaixo e adotada inicialmente, mas depois revertida — a decisão final é crontab do host, não `CronJob`; ver Status.
- Não sabemos ainda se existe hoje algum script (mesmo que rudimentar) que já automatiza parte do processo — precisa levantar antes de desenhar do zero.

## Investigação

### Bloco 1 — o que já existe hoje

```
$ find . -iname "*ingest*" -o -iname "*download*" -o -iname "*fetch*" | grep -v node_modules
./.git/FETCH_HEAD
./docs/backlog-archived/epics/epic-01-ingestao.md
./docs/backlog-archived/features/feature-01.1-base_ingestao.md
./docs/backlog-archived/stories/01-Criar classe base de ingestao.md
./docs/backlog-archived/stories/13-Testes de ingestao.md
./docs/specs/009-automacao-da-ingestao

$ git log --oneline -- dbt/seeds/contratos.csv | tail -5
15037ee Configurações validadas e executadas até o passo 6 do readme. PostGresSQL e DBT em execução com os 78000 contratos importados no raw
1ee2397 Removido arquivo corrompido de seeds
ea06e35 Configuração dos serviços dbt, postgre e inclusão do seed: contratos.csv
```

**Achado:** não existe nenhum script de ingestão real no repo hoje, nem rascunho. O que existe é só planejamento arquivado (`docs/backlog-archived/`) de uma "classe base de ingestão" que nunca foi implementada — esse backlog foi explicitamente marcado obsoleto no commit `f1d5824` (pré-pivot). O CSV chega em `dbt/seeds/contratos.csv` hoje por commit manual direto no repo (confirmado: só 3 commits na história do arquivo, todos de setup inicial/correção, nenhum automatizado).

### Bloco 2 — o link de download é estável e automatizável?

```
$ curl -sI "https://dados.sc.gov.br/dataset/93dab950-e805-4388-8418-cfb3b73f1623/resource/8bb98383-7043-4d2f-ae32-9377656e71ee/download/contratos.csv"
HTTP/1.1 200 OK
Server: nginx/1.10.3 (Ubuntu)
Date: Wed, 19 Aug 2026 14:25:57 GMT
Content-Type: text/csv
Connection: keep-alive
Pragma: no-cache
Cache-Control: no-cache
Accept-Ranges: bytes
ETag: "1757412122.95-122184246"
Last-Modified: Tue, 09 Sep 2025 10:02:02 GMT
Content-Range: bytes 0-122184245/122184246

$ curl -sI "https://dados.sc.gov.br/dataset/93dab950-e805-4388-8418-cfb3b73f1623/resource/8bb98383-7043-4d2f-ae32-9377656e71ee/download/contratos.csv" | grep -iE "last-modified|etag|content-length"
ETag: "1757412122.95-122184246"
Last-Modified: Tue, 09 Sep 2025 10:02:02 GMT
```

**Achado:** o resource_id da spec 004 ainda é válido (`200 OK`, sem redirect) — não precisou trocar. O link responde a `HEAD` sem sessão/cookie/JS, ou seja, é automatizável por `curl`/`wget` puro. Tem `ETag` e `Last-Modified` estáveis, então dá pra detectar arquivo novo sem baixar o corpo inteiro (`If-Modified-Since` ou comparação de `ETag`). Nota: não veio `Content-Length` isolado — o servidor respondeu com `Accept-Ranges: bytes` + `Content-Range` no HEAD (122.184.246 bytes é o tamanho total), comportamento um pouco atípico de servidor mas não impede automação.

### Bloco 3 — onde a rotina deveria rodar (k3s CronJob vs. alternativas)

Acesso de leitura ao cluster de produção via SSH, mesmo padrão de acesso usado nas specs 002/003 (detalhe de conexão no repo de infra privado).

```
$ sudo -n kubectl get cronjobs -A
No resources found

$ sudo -n kubectl top nodes
NAME       CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
<node>     155m         7%       3969Mi          49%
```

**Achado:** não existe nenhum CronJob rodando no cluster hoje — não há padrão de outro projeto pra reaproveitar, seria o primeiro. CPU está em 7% de uso (155m) e memória em 49% — confirma o achado da spec 003 de que CPU é o recurso com mais folga no momento, não é o teto imediato pra um job leve de download+dbt.

**Nota (adicionada nesta sessão):** o fato acima ("não existe CronJob no cluster") segue literalmente verdadeiro — mas a conclusão de que a ingestão *seria* esse primeiro CronJob foi revertida. A investigação de deploy desta sessão (spec 015, adendo da spec 003) achou que os dois projetos vizinhos, mesmo com Argo CD/k3s disponível, não usam `CronJob` k8s para nenhuma rotina agendada — ambos usam crontab do host. A decisão final desta spec segue esse precedente real; ver Status e Design.

### Bloco 4 — sequenciamento download → dbt run

```
$ find .github/workflows -name "*.yml" -exec grep -l "dbt" {} \;
.github/workflows/compras-publicas.yml
```

Conteúdo relevante do workflow (`.github/workflows/compras-publicas.yml`): roda `dbt deps` / `dbt seed` / `dbt build` a partir de `working-directory: compras-publicas/dbt`, disparado em `push` para `main` filtrado por `paths: compras-publicas/**`.

**Achado:** o workflow existe e roda dbt, mas está quebrado/obsoleto — referencia o path `compras-publicas/` como prefixo (`compras-publicas/dbt`, `compras-publicas/postgres/init/01_init.sql`), mas a raiz do repo hoje tem `dbt/`, `postgres/`, `evidence/` diretamente, sem esse prefixo (confirmado via `ls` na raiz). Isso é resíduo de uma reestruturação de repo (commit `2d42a54`, "Migração de evidence para streamlit + ajustes para criação de projetos separados").

```
$ gh run list --workflow=compras-publicas.yml --limit 5
completed	failure	Feat: Migração de evidence para streamlit + ajustes para criação de p…	Pipeline Compras Publicas	main	push	25052513263	36s	2026-04-28T12:22:19Z
```

Última execução (2026-04-28) falhou em 36s — consistente com o path quebrado. Ou seja: **não existe hoje nenhum `dbt run`/`dbt test` ativo em CI**, nem pro build do site estático. Qualquer automação de ingestão que planeje "reaproveitar" a execução dbt do GH Actions precisa primeiro decidir se conserta esse workflow ou se abandona GH Actions de vez em favor do CronJob k3s — não há infraestrutura dbt funcionando hoje pra reaproveitar como está.

**Nota (adicionada nesta sessão):** a alternativa citada aqui ("CronJob k3s") foi descartada — ver Status. A conclusão sobre o workflow do GH Actions (consertar vs. abandonar) não depende de qual mecanismo de execução foi escolhido depois — segue "remover, não consertar" (Requirement funcional 9), agora em favor do crontab do host, não do CronJob.

## Requirements

### Funcionais

1. O sistema DEVE executar a verificação de arquivo novo via entrada de `crontab` no host, disparando `docker-compose run` de uma imagem publicada no GHCR (ver [[015-convencao-build-imagem]]). O arquivo `docker-compose.pipeline.yml` (ou nome equivalente à convenção do `infra`) e a entrada de `crontab` vivem no repo `infra` (privado), consistente com a fronteira de dado físico já estabelecida — não no repo `compras-publicas-sc`.

2. A rotina (crontab do host) DEVE rodar em cadência diária, realizando um `HEAD` request ao link de download do portal antes de qualquer download completo do arquivo.

3. QUANDO o `ETag` retornado for igual ao último valor salvo, O sistema DEVE encerrar sem baixar ou processar o arquivo (no-op).

4. QUANDO o `ETag` for diferente do último valor salvo, O sistema DEVE baixar o arquivo e validar o schema mínimo (colunas esperadas presentes; contagem de linhas maior que zero) antes de acionar o `dbt run`.

5. SE a validação de schema falhar, ENTÃO O sistema NÃO DEVE sobrescrever o dado já processado, NÃO DEVE atualizar o `ETag` salvo, e DEVE encerrar com erro visível (exit code não-zero do `docker-compose run`, refletido no log de arquivo — Requirement não-funcional 1).

6. O sistema DEVE executar download, validação e `dbt run`/`dbt snapshot` como passos sequenciais de uma única execução (`docker-compose run`) — não como execuções ou entradas de crontab separadas.

7. O sistema DEVE armazenar o último `ETag` processado em uma tabela no Postgres já provisionado (spec 003), não em `ConfigMap` ou outro mecanismo de config do cluster.

8. Na primeira execução (sem `ETag` salvo ainda), O sistema DEVE tratar a ausência como "mudança" e processar incondicionalmente.

9. O sistema DEVE remover o workflow do GitHub Actions que hoje roda `dbt` (quebrado desde a reestruturação do repo, sem uso) — não tentar consertá-lo.

### Não-funcionais

1. Já que não há `CronJob`/Argo CD nesta rota, falha DEVE ficar visível via log do `docker-compose run` — redirecionar stdout/stderr pra um arquivo de log com rotação (ou usar o mecanismo de log que o `weather-pipeline` já usa, se houver um — confirmar na implementação). Alertas ativos (notificação proativa) ficam explicitamente fora do escopo desta spec.

2. O merge por `(cdunidadegestora, nucontrato)` (spec 003) DEVE permanecer idempotente sob reprocessamento — reexecutar a mesma carga não pode gerar duplicata nem corromper dado já correto, mesmo em caso de `ETag` mudar sem alteração de conteúdo real.

## Design

Primeiro job agendado de produção do projeto — sem precedente de `CronJob` k8s nos projetos vizinhos (achado desta sessão), por isso a decisão de seguir o padrão real de crontab do host em vez de introduzir um mecanismo novo.

| Decisão | Escolha | Razão |
|---|---|---|
| Onde a rotina roda | **Crontab do host + `docker-compose run`** de uma imagem publicada no GHCR (ver [[015-convencao-build-imagem]]) | Nenhum projeto vizinho usa `CronJob` k8s para rotina agendada — ambos usam crontab do host, mesmo padrão do `weather-pipeline`. Motivo real descoberto nesta sessão: o Postgres compartilhado roda fora do k3s (container Docker no host); um `CronJob` k8s precisaria de uma ponte `Service`+`Endpoints` com IP fixo da bridge Docker, frágil a restart do container. Rodando via `docker-compose run` na mesma rede Docker do host, a ingestão alcança o `postgres` direto pelo nome do container (DNS interno do Docker), sem IP fixo, sem ponte. |
| Cadência | Verificação frequente (proposta: diária), ação só quando há mudança real | `ETag`/`Last-Modified` estáveis (achado do Bloco 2) tornam isso barato: a rotina faz só um `HEAD`, compara o `ETag` contra o último valor conhecido (guardado numa tabela pequena no Postgres já provisionado — proposta `pipeline_metadata` ou similar, não `ConfigMap`, pra não misturar estado de aplicação com config do cluster). Se igual: no-op, log e sai. Se diferente: segue pro download. Evita reprocessar 76 mil+ linhas todo dia sem necessidade e detecta arquivo novo cedo, sem depender de "sei que é sempre início do mês". |
| Sequenciamento | Uma única execução (`docker-compose run`), passos internos sequenciais: download → validação mínima de schema → `dbt run`/`dbt snapshot` → atualizar `ETag` salvo | São passos que só fazem sentido em conjunto (não há valor em ter o dado baixado sem processar, nem processar sem confirmar que o download foi bem-sucedido) — separar em duas execuções/entradas de crontab independentes adicionaria complexidade de orquestração sem benefício real nessa escala. |
| Validação antes do `dbt run` | Checagem mínima de schema: colunas esperadas presentes, contagem de linhas não-zero, não é arquivo corrompido (tipo o `contratos-2022.csv` com aspas malformadas da spec 006) | Se falhar: o Job termina com erro, **não sobrescreve** o dado bom já processado, e o `ETag` salvo **não é atualizado** (tenta de novo no próximo ciclo, não fica preso presumindo que já processou). |
| Workflow do GH Actions que roda dbt hoje (achado do Bloco 4 — quebrado desde a reestruturação do repo) | Remover, não consertar | A automação real passa a viver no job de crontab do host (spec 015); manter um segundo lugar (quebrado ou não) que também roda `dbt` duplica responsabilidade e cria ambiguidade sobre qual é a fonte de verdade da execução. Consistente com a fronteira já estabelecida (Actions não é mais o dono do deploy nem da execução de pipeline deste projeto). |

### Componentes afetados

- Dockerfile do job de ingestão no repo `compras-publicas`; `docker-compose.pipeline.yml` + entrada de crontab no repo `infra` (spec 015).
- Imagem de container com `dbt` + dependências de download, publicada no GHCR seguindo a convenção da spec 015.
- Tabela pequena no Postgres para guardar o último `ETag` processado.
- Remoção do workflow `.github/workflows/*.yml` que rodava `dbt` (ou arquivamento, se preferir manter rastro histórico em vez de deletar puro).

## Casos de borda

- `ETag` muda mas o conteúdo é funcionalmente idêntico (republicação sem mudança real): sem problema — o merge por chave (spec 003) é idempotente, reprocessar o mesmo dado não corrompe nada, só gasta um ciclo à toa.
- Portal muda o `resource_id` sem aviso (endpoint de download passa a 404): o Job deve falhar de forma visível (log de arquivo com rotação — Requirement não-funcional 1), não silenciosamente continuar servindo dado velho pra sempre sem sinalizar.
- Primeira execução (sem `ETag` salvo ainda): tratar como "mudança", processar incondicionalmente.
- Se o container `postgres` for recriado com nome de container diferente (não deveria acontecer numa operação normal, mas documentar): o `docker-compose run` da ingestão depende do nome do serviço/container estar estável na rede Docker do host — não do IP, mas ainda depende do nome não mudar.
- **Falha parcial entre `dbt seed` e `dbt build`** (achado da implementação): se `dbt seed` tiver sucesso (sobrescrevendo `raw.contratos` com o dado novo) mas `dbt build` falhar na sequência (ex.: teste dbt pega inconsistência real no dado), `pipeline_metadata` não é atualizado (correto), mas `raw.contratos` já reflete o dado novo enquanto `staging`/`marts` podem estar num estado inconsistente até a próxima execução bem-sucedida. A próxima execução trata como "mudança" de novo (ETag salvo continua o antigo) e tenta reprocessar — resolve sozinho se a causa foi transitória; se for problema real de dado, o pipeline continua tentando e falhando visivelmente no log até intervenção manual. Não corrigido nesta sessão (exigiria mecanismo tipo schema shadow/blue-green, desproporcional ao tamanho atual do projeto) — registrado como limitação conhecida.

## Fora do escopo

- Mudança nas decisões de storage/chave/grão/backfill já fechadas (specs 003, 005, 006).
- Automação de fontes além do portal SC (Betha ou outras) — fora de escopo por decisão explícita.
- Alertas ativos (notificação em caso de falha) — não existe infra de alerta hoje; falha fica visível só via log do `docker-compose run` por enquanto. Pode virar spec própria depois.
- Consertar o workflow do GH Actions — decidido remover, não consertar.
- A ponte `Service`+`Endpoints` (IP fixo da bridge Docker) permanece documentada como necessidade **futura**, não usada por este job — ver adendo da spec 003. Será necessária quando o `Deployment` do FastAPI (spec 012) for implementado como workload k8s de verdade.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[003-storage-e-chave-unica]]
- [[004-origem-dados-api-vs-arquivo]]
- [[006-backfill-historico]]
