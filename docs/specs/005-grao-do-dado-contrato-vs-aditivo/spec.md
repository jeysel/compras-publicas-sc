# 005 — Grão do dado: contrato vs. aditivo (padrão de numeração histórico)

## Tipo

Decisão de arquitetura — bloqueia parte do Design das specs 003 e, possivelmente, 004.

## Status

Decidida — hipótese de aditivo por sufixo **rejeitada** pelo dado real. Grão do dado confirmado como "1 registro = 1 contrato"; desenho da spec 003 mantido sem alteração. Fechada e aprovada pelo usuário em 2026-08-19.

## Resumo

O formato atual do portal (`contrato-demo.csv`, 2368 linhas) não tem nenhum `nucontrato` com sufixo `-NN`, e `nucontrato` sozinho é chave única. O formato histórico (`dbt/seeds/contratos.csv`, 76 mil linhas) tem colisão de `nucontrato` sem chave composta — e a memória do usuário sobre o sistema de origem indica que aditivos eram publicados historicamente com sufixo `-01`, `-02`, `-03` no número do contrato. Esta spec confirma se é isso que explica a colisão, e decide qual o grão real do dado: um registro por contrato (com aditivo como atributo de mudança) ou um registro por aditivo (contrato como agregação derivada).

**Conclusão da investigação:** a hipótese do sufixo `-NN` não se confirma — zero ocorrências no dado real. A colisão de `nucontrato` é 100% explicada pela reutilização do mesmo número sequencial por unidades gestoras diferentes (achado já validado na spec 003), não por aditivos. O grão do dado é **um registro por contrato**; aditivo aparece só como atributo cumulativo (`vladitado`, `diasaditados`), não como evento em linha própria.

## Contexto

- Achado da spec 003: `nucontrato` sozinho não é único em `seeds/contratos.csv` (76.041 linhas); chaves compostas `(cdunidadegestora, nucontrato)` e `(nuprocesso, nucontrato)` batem 100%, mas isso pode estar mascarando o problema real em vez de resolvê-lo.
- Achado da spec 004 (investigação preliminar, feita nesta sessão): `contrato-demo.csv` (formato atual) não tem nenhuma ocorrência do padrão `-NN` no final de `nucontrato`. Ou o formato mudou (deixou de sufixar aditivo), ou o recorte atual só captura contratos sem aditivo ainda.
- Conhecimento de domínio do usuário: o sistema de origem já teve um corte de formato, e historicamente aditivos apareciam como sufixo `-01`/`-02`/`-03` no número do contrato.

## Investigação

Rodada contra `dbt/seeds/contratos.csv` real (76.041 linhas, `;`-delimitado, `encoding='utf-8'` — carregou sem erro, sem precisar de fallback latin1).

```
=== 1. Padrao de sufixo -NN ===
Com sufixo -NN: 0 de 76041
[]
```

Nenhuma ocorrência do padrão `-NN` em `nucontrato` no dado histórico. A hipótese de que a colisão vem de aditivo sufixado está descartada de cara — o formato de sufixo simplesmente não existe neste arquivo.

```
=== 2. Linhas com nucontrato duplicado (amostra) ===
Total de linhas em grupos duplicados: 1864

nucontrato=2024CT000002:
cdunidadegestora  nmunidadegestora                                              nuprocesso              situacao
160084            Fundo de Melhoria da Polícia Civil                            PCSC 00128438/2023       Encerrado
280024            Fundação de Amparo à Pesquisa e Inovação do Estado de SC      FAPESC 00000388/2024     Vencido
310002            Fundação Escola de Governo - ENA                              ENA 594/2023              Encerrado
290001            Secretaria de Estado de Portos, Aeroportos e Ferrovias        SEA 00014634/2022         Encerrado
330092            Fundo Estadual de Recursos Hídricos                          SEMA 00000667/2021        Em Execução Especial
330001            Secretaria de Estado do Meio Ambiente e da Economia Verde     SEMAE 00001306/2023       A Empenhar
```

As 6 linhas com `nucontrato = 2024CT000002` pertencem a **6 unidades gestoras completamente diferentes**, com `nuprocesso`, `situacao`, `vlatual` e `dtfimatual` sem relação entre si. Não é um contrato com histórico de aditivos — são contratos distintos que só coincidem no número sequencial, porque `nucontrato` segue o padrão `AAAACTNNNNNN` (ano + sequência), aparentemente reiniciado por unidade gestora, não global.

```
=== 3. nucontrato_base (sem sufixo) vs nucontrato original ===
nucontrato_base: 74843 unicos de 76041 (1198 ainda duplicadas)
nucontrato (original): 74843 unicos de 76041 (1198 duplicadas)
```

Extrair o "sufixo" (que não existe) não muda nada — `nucontrato_base` é idêntico a `nucontrato`. Confirma que o passo 1 já esgotou a hipótese.

```
=== 4. Quantas colisoes desaparecem com cada chave composta ===
Linhas em colisao de nucontrato puro: 1864
Linhas em colisao de (cdunidadegestora, nucontrato): 0
Linhas em colisao de (nuprocesso, nucontrato): 0
```

Tanto `(cdunidadegestora, nucontrato)` quanto `(nuprocesso, nucontrato)` zeram a colisão — consistente com o achado já registrado na spec 003 (76.041/76.041 combinações únicas para ambas).

**Verificação adicional — existe rastro de aditivo em outra coluna?** As 51 colunas do arquivo foram listadas; não há coluna de evento (`tipo_registro`, `numero_aditivo`, `data_aditivo` etc.) nem valores em `situacao` que indiquem "este registro é um aditivo" (`situacao` tem 17 valores, todos estados de contrato: `Encerrado`, `Em Execução Especial`, `Em edição`, `Concluído`, `A Empenhar`, `Vencido`, `Andamento`, `Rescindido`, `Em Execução`, `Em Alteração`, `Paralisado`, `A iniciar`, `Não definido`, `Inativado`, `Pendência admin.`, `Ajustar Empenho`, `Em Sub-Rogação`). O que existe são colunas de **valor acumulado** — `vladitado` (valor aditado), `diasaditados` (dias aditados), ao lado de `vloriginal`/`diasoriginais` e `vlatual`/`diasatuais` — ou seja, aditivo já vem pré-agregado como atributo numérico do contrato, não como linha própria.

## Requirements

### Funcionais

- O sistema DEVE tratar `(cdunidadegestora, nucontrato)` como chave única do grão "contrato" em todo o pipeline (staging, mart), consistente com o achado da spec 003.
- O sistema NÃO DEVE implementar lógica de parsing de sufixo `-NN` em `nucontrato` — o padrão não existe no dado real, nem histórico nem atual.
- O sistema DEVE tratar `vladitado`/`diasaditados` como atributos do contrato (valor/prazo aditado acumulado), não como um evento em tabela separada.

### Não-funcionais

- A decisão desta spec DEVE ser referenciada (via `[[005-grao-do-dado-contrato-vs-aditivo]]`) em qualquer spec futura que decida sobre staging incremental ou snapshot de histórico, para não reabrir a hipótese de sufixo já descartada aqui.

## Design

| Decisão | Escolha | Razão |
|---|---|---|
| Grão do dado | 1 registro = 1 contrato (não 1 registro = 1 aditivo) | Não existe padrão de sufixo `-NN` nem coluna de evento no dado real; aditivo é atributo cumulativo (`vladitado`, `diasaditados`), não linha própria |
| Chave única | `(cdunidadegestora, nucontrato)` | Já validada 100% na spec 003; confirmada aqui como a explicação real da colisão (reuso do mesmo número sequencial por unidade gestora diferente), não um remendo em cima do problema |
| Staging/mart | Mantém desenho já proposto na spec 003 (upsert por chave composta) — **não precisa reestruturar para staging append-only por aditivo** | O grão "aditivo como evento" não existe nos dados de origem; construir staging append-only pra um evento que a fonte não expõe seria especulativo |

Componentes afetados: nenhuma mudança de código necessária a partir desta spec — ela remove uma pendência de design da spec 003/004, não adiciona trabalho novo.

## Casos de borda

- Contrato sem nenhum aditivo: já coberto — `vladitado`/`diasaditados` ficam zerados ou iguais ao original, mesmo grão, sem tratamento especial.
- Reuso de `nucontrato` entre unidades gestoras diferentes (achado desta spec, não um caso raro: 1.864 linhas / 76.041, ~2,5%): já resolvido pela chave composta.
- **Pendência aberta, fora do que esta spec resolve:** o `nucontrato` puro colidir entre unidades gestoras diferentes sugere que a numeração é sequencial *por unidade gestora*, não global — isso é uma inferência a partir do dado, não uma regra confirmada na documentação do Transparência SC. Não afeta a decisão de grão/chave (que já está validada), mas vale registrar como observação para quem for interpretar `nucontrato` fora do contexto da unidade gestora.
- **`nmunidadegestora` não é estável entre fontes/períodos** — achado da [[006-backfill-historico]]: comparando `seeds/contratos.csv` contra o arquivo `contratos-2011-2021.csv` do portal, 753 códigos de `cdunidadegestora` aparecem associados a nomes diferentes entre as duas fontes (reorganização administrativa real ao longo de 14+ anos, não erro de dado — ex.: código `410001` aparece como "Casa Civil", "Secretaria de Estado da Casa Civil" e "Secretaria Executiva de Assuntos Internacionais" dependendo da fonte/período). **Nunca usar `nmunidadegestora` em join, filtro ou agrupamento — só `cdunidadegestora`.** Não reabre a decisão de chave (`(cdunidadegestora, nucontrato)`, já validada acima), só reforça que o componente de nome dela é decorativo, não identificador.

## Fora do escopo

- Decisão de origem do dado (API vs. arquivo) — tratada na spec 004.
- Decisão de storage (motor de banco) — já fechada na spec 003.
- Confirmar se a numeração `nucontrato` é de fato sequencial por unidade gestora junto à documentação oficial do Transparência SC (observação registrada em Casos de borda, não investigada formalmente aqui).

## Referências de código

_A preencher conforme a implementação — nenhuma mudança de código motivada por esta spec até o momento._

## Ver também

- [[003-storage-e-chave-unica]]
- [[004-origem-dados-api-vs-arquivo]]
