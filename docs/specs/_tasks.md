# Tasks — Spec NNN (nome curto)

Status: [ ] draft  [ ] aprovado em DD/MM/AAAA  [ ] em execução  [ ] concluído

Formato de tarefa: `Nível` (risco da tarefa em si — baixo/médio/alto; não é
uma classificação fixa do repositório, é julgamento por tarefa), `Caminhos`
(quais arquivos a tarefa pode tocar — se a tarefa só lê/roda comando, dizer
"nenhum arquivo"), `Aceite` (comando + saída esperada, literal — nunca
"funciona" ou "deve passar" sem o comando que prova isso), `Parar antes de
commit` (sempre "sim" neste repo — ver regra 2 do `CLAUDE.md`, commit e
push são gesto humano fora destas tarefas).

Todas as tarefas rodam numa branch dedicada (ex.: `spec/NNN-nome-curto`),
nunca direto na `main`. Nenhuma tarefa comita: comitar — e, com mais razão,
dar push — fica para o usuário revisar o `git diff`/`git show` real do que
vai subir (regra 2 do `CLAUDE.md`), depois que todas as tarefas abaixo
terminarem.

---

### T1 — [nome da tarefa]

Nível: [baixo/médio/alto] ([por quê — o que torna essa tarefa simples ou
arriscada]).
Caminhos: [arquivo(s) que esta tarefa pode alterar, ou "nenhum arquivo" se
só lê/roda comando].
Aceite:
- [comando] → [saída literal esperada, não "deve funcionar"].
- [comando antes da mudança] → [estado atual, pra provar que o antes era
  diferente do depois — não presumir].
- [comando depois da mudança] → [estado esperado].
Parar antes de commit: sim.

### T2 — [nome da tarefa]

Nível: [baixo/médio/alto].
Caminhos: [arquivo(s)].
Aceite:
- SE [condição de falha esperada — ex.: falta de variável de ambiente,
  dependência externa fora do ar], a tarefa PARA, registra o erro exato, e
  NÃO tenta adivinhar ou inventar o valor/comportamento que falta (regra 4
  do `CLAUDE.md` — validação real, não presumida). Parar aqui é o
  resultado correto, não uma falha da tarefa.
Parar antes de commit: sim.

### TN — Encerrar a execução e relatar (sem commit)

Nível: baixo.
Caminhos: nenhum.
Aceite:
- `git status --porcelain` lista exatamente os arquivos esperados pelas
  tarefas anteriores — nenhum arquivo fora da lista de `Caminhos` já
  declarada.
- `git diff --stat` é anexado ao relatório final para o usuário revisar.
- Nenhum `git commit` foi executado por esta tarefa ou por qualquer
  tarefa anterior.
Parar antes de commit: sim — este é o ponto de parada definitivo da
execução.

---

## Depois das tarefas

1. Usuário revisa `git diff`/`git show` real na branch (regra 2 do
   `CLAUDE.md`) — nunca presumir que o diff está limpo.
2. Usuário decide: comitar (e, se for o caso, dar push) ou pedir ajustes
   antes.
3. Atualizar o Status desta spec em `spec.md` (`[ ] em implementação` →
   `[x] implementado`, ou registrar o que ficou pendente/parado em T[N] —
   distinguir sempre "decisão tomada e documentada" de "problema
   resolvido", regra do `CLAUDE.md`).
