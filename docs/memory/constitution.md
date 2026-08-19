# Constitution — compras-publicas-sc

Regras não-negociáveis deste repositório. Mudanças aqui só acontecem por decisão explícita registrada em conversa/spec, não por edição silenciosa.

**Nota (2026-08-19):** este arquivo foi criado nesta data contendo só a regra abaixo. O `CLAUDE.md` da raiz do repo cita um "resumo operacional" de 6 regras que precede este arquivo — essas 6 regras ainda não foram migradas pra cá; até que sejam, `CLAUDE.md` é a única fonte para elas.

## Regras

### 1. Dado operacional físico nunca em spec do repositório público

Dado operacional físico (IP, hostname, identity/credential name, nome literal de outros sistemas/projetos, nome de arquivo de script de infra) nunca é registrado em spec do repositório público, mesmo como "output literal de investigação". Quando uma investigação produzir esse tipo de dado, o output literal completo vai para a spec equivalente no repo de infra privado; o repo público recebe só o achado abstraído (padrão, limite, decisão), com uma nota apontando pro repo privado para quem tiver acesso.

**Motivo:** `compras-publicas-sc` é um repositório público. A spec 002 (`docs/specs/002-estado-atual-infra-k3s`) originalmente registrou, como output literal de uma investigação somente-leitura, IP de servidor, ARN/nome de identity IAM, nomes de outros projetos rodando no mesmo cluster k3s, e nomes de script de sync de secret — nada disso havia sido pushado ainda, mas o conteúdo não deveria existir num repo público mesmo em commit local. Corrigido em 2026-08-19: a spec 002 pública foi reescrita para reter só os achados arquiteturais; o conteúdo físico completo foi movido para `docs/specs/078-compras-publicas-estado-infra-k3s/spec.md` no mono-repo de infra privado.

**Adendo (2026-08-19, mesma revisão):** a spec 003 (`docs/specs/003-storage-e-chave-unica`, Bloco A) tinha o mesmo problema — `docker stats` literal do host expondo nomes de containers de outros projetos, e nomes de outros bancos de dados no mesmo Postgres compartilhado. Passou despercebido na primeira remediação (que cobriu só a spec 002); pego numa checagem explícita antes do commit, não pela auditoria original. Mesmo tratamento aplicado: achado abstraído fica na spec pública, output literal completo movido para a spec 078 no repo de infra.
