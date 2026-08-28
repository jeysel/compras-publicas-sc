# 033 — Suíte de testes automatizada para a API

## Tipo
Infraestrutura de qualidade / CI (pré-requisito bloqueante, não é feature de produto)

## Status
Proposta

## Contexto

O CI de `compras-publicas-sc` hoje faz build da imagem, publicação no GHCR e um smoke test
(container efêmero, `curl` num endpoint de saúde) antes do push. Isso confirma que a imagem
sobe e responde, mas não confirma que a lógica de negócio está correta — nenhuma suíte de
testes automatizada existe neste repositório hoje (confirmado por investigação direta do CI
atual, não presumido).

Isso é o único bloqueador do lado deste repositório para a equipe de infra considerar avançar
de "staging automático com selfHeal" para "CD completo até produção". Não há prazo apertado;
a automação de produção também depende de um item externo (bug do Argo CD) que é responsabilidade
do repositório `infra`, independente deste.

Modelo de referência: `jeysel-auth`, que já roda uma suíte real contra um Postgres real como
serviço do GitHub Actions (não mockado), com testes marcados `-m integration` separados dos
testes rápidos, em um job `test` que roda **antes** do build/push da imagem.

## Requirements (EARS)

1. **Quando** um push ocorrer na branch `main`, o sistema **deve** executar a suíte de testes
   automatizada antes de iniciar o build da imagem Docker.
2. **Se** algum teste da suíte falhar, **então** o sistema **deve** impedir a publicação da
   imagem no GHCR e a promoção automática para staging.
3. **Enquanto** a suíte de testes estiver rodando, o sistema **deve** utilizar uma instância real
   de Postgres provisionada como serviço do CI (não uma conexão mockada).
4. **Onde** existir lógica de cálculo/agregação de KPI a partir de dados brutos (contratos,
   fornecedores, órgãos), o sistema **deve** ter cobertura de teste de integração validando o
   resultado esperado contra dados conhecidos.
5. **Onde** uma rota principal da API aceitar parâmetros de filtro, o sistema **deve** ter pelo
   menos um teste cobrindo o cenário normal (dado existe, formato esperado) e um cenário de
   borda (filtro sem resultado, parâmetro inválido).
6. O sistema **deve** permitir a execução isolada dos testes marcados como `-m integration`,
   separando-os dos testes rápidos/unitários, para uso local sem dependência do CI.
7. O novo job de teste **não deve** substituir nem remover o smoke test existente — ambos
   coexistem como etapas complementares.

## Design (visão geral)

| Componente | Decisão |
|---|---|
| Framework de teste | `pytest`, com marker `-m integration` para os que dependem de Postgres real |
| Banco de dados nos testes | Postgres real como serviço do GitHub Actions, populado do zero a cada execução (mesmo padrão do `jeysel-auth`) |
| Posição no pipeline | Novo job `test`, executado **antes** do job de build/push da imagem |
| Escopo de cobertura | Rotas principais da API (`/api/v1/anos-disponiveis`, `/api/v1/kpis-resumo`, entre outras) + lógica de cálculo/agregação de KPI |
| Relação com o smoke test | Complementar — smoke test valida "sobe e responde"; suíte valida "lógica está correta" |
| Relação com `/health` | Não coberto por esta suíte — `/health` testa conectividade (usado por readiness/liveness probes), não lógica de negócio |
| Pipeline de ingestão (dbt) | Fora do escopo desta spec |

## Casos de borda

- Falha de teste **intermitente/flaky**: antes de considerar a suíte "sinal verde" para infra
  reconsiderar CD de produção, os testes devem passar de forma consistente, não apenas uma vez.
- Filtros de ano/órgão/modalidade/segmento sem nenhum resultado: deve retornar formato esperado
  (lista vazia ou equivalente), não erro.
- Dados marcados como `fl_valor_suspeito` ou `fl_aditivo_inconsistente`: se algum teste de KPI
  usar dados de fixture, deve validar que esses registros são corretamente excluídos das
  agregações de valor (herdando o mesmo cuidado já documentado como bug real passado).
- Banco de teste populado do zero a cada execução: não deve haver dependência de estado residual
  entre execuções do CI.

## Fora do escopo

- Migrar produção para CD automático (decisão do `infra`, ainda bloqueada por bug externo do
  Argo CD).
- Testar o pipeline de ingestão de dados (dbt), hoje manual — sistema separado, ciclo de vida
  próprio.
- Qualquer mudança de infraestrutura (Kustomize, Argo CD, NetworkPolicy) — já resolvido do lado
  `infra`.
- Cobertura 100% de testes — o objetivo é destravar confiança mínima razoável para deploy
  automático, não exaustividade.

## Ver também

- `infra`: specs 082, 086, 088 (relacionadas a `compras-publicas-sc`)
- `infra`: `docs/steering/pendencias.md`
- Handoff de origem: sessão de infraestrutura, 26–28/08/2026
