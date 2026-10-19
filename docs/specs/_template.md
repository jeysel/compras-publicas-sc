# [Nome da Feature]

## Tipo
[ ] Nova feature  [ ] Melhoria  [ ] Bug fix  [ ] Refatoração  [ ] Spec retroativa

## Status
[ ] draft  [ ] em implementação  [ ] implementado  [ ] arquivado

## Resumo
Uma linha descrevendo o que esta spec cobre.

## Contexto
(Só para spec retroativa) Origem do achado — de onde veio, quando, quem trouxe.

## Investigação
(Só para spec retroativa) Evidência, comandos rodados, causa raiz confirmada.
Dado operacional físico (IP, hostname, nome de identity/credential, nome
literal de outros projetos no cluster, nome de arquivo de script de infra)
nunca entra aqui — ver `docs/memory/constitution.md`, regra 1. Esse tipo de
output literal vai para a spec equivalente no repo de infra privado; aqui
fica só o achado abstraído (padrão, limite, decisão) com uma nota apontando
pra lá.

## Requirements (EARS)

### Funcionais
- WHEN [condição], the system SHALL [comportamento]
- IF [condição], the system SHALL [comportamento]

### Não-funcionais
- The system SHALL [comportamento] WITHIN [limite]

## Design
### Decisões de arquitetura
| Decisão | Alternativa considerada | Motivo |
|---------|------------------------|--------|
| | | |

### Componentes afetados
- `app/arquivo.py` — descrição do impacto

## Casos de borda
- [caso] → [comportamento esperado]

## Fora do escopo
- [o que esta spec explicitamente não cobre]

## Referências de código
- `caminho/arquivo.ext` — o que tem lá relevante para esta spec

## Ver também
- [[NNN-outra-spec]] — por que é relacionada
