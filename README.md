# 🛒 Compras Públicas — Pipeline de Dados  
### Fontes iniciais: Transparência SC e Betha Sistemas

Este projeto implementa um pipeline completo para coleta, padronização, modelagem e análise de **compras públicas** do estado de Santa Catarina, utilizando:

- **Transparência SC** → https://www.transparencia.sc.gov.br/  
- **Betha Transparência** → https://transparencia.betha.cloud/#/

O objetivo central é comparar **valores licitados x valores contratados**, identificar padrões de compras, analisar competitividade entre fornecedores e entender o comportamento dos órgãos públicos ao longo do ciclo de aquisição.

---

## ❓ Por que este projeto é importante?

Compras públicas movimentam bilhões de reais todos os anos.  
Entender **quanto foi planejado (licitado)** e **quanto realmente foi contratado** permite:

- Identificar economia ou sobrepreço  
- Avaliar eficiência dos processos  
- Medir competitividade entre fornecedores  
- Detectar padrões de comportamento dos órgãos  
- Aumentar transparência e controle social  

Este projeto transforma dados brutos e dispersos em **informação estruturada, confiável e analítica**.

---

## 🎯 Objetivos do Projeto

- Criar um pipeline de ingestão configurável para múltiplas fontes  
- Padronizar dados brutos em uma camada staging  
- Modelar entidades principais (core)  
- Construir marts analíticos com métricas relevantes  
- Documentar arquitetura, decisões e dicionário de dados  
- Demonstrar práticas reais de Analytics Engineering  

---

## 🧱 Arquitetura do Pipeline


### **Ingestão**
- Transparência SC  
- Betha Sistemas  
- Configuração via `config.yaml`  
- Módulo de ingestão extensível para novas fontes  

### **Staging**
- Normalização de campos  
- Padronização de datas, valores e códigos  
- Validações de qualidade  

### **Core**
Entidades principais:
- Órgão  
- Compra  
- Item  
- Fornecedor  
- Modalidade  
- Contrato  

### **Marts**
Métricas analíticas:
- Valor licitado vs contratado  
- Competitividade (nº de fornecedores)  
- Modalidades mais utilizadas  
- Tempo médio do processo  
- Órgãos com maior volume de compras  

---

## 📁 Estrutura do Projeto

compras-publicas/
│
├── data/
│   ├── raw/                  # Dados brutos extraídos das fontes
│   ├── staging/              # Dados normalizados e padronizados
│   ├── core/                 # Entidades modeladas (Órgão, Compra, Item...)
│   └── marts/                # Tabelas analíticas e métricas
│
├── docs/
│   ├── architecture.md       # Arquitetura completa do pipeline
│   ├── backlog.md            # Backlog técnico (épicos, features, histórias)
│   ├── data_dictionary.md    # Dicionário de dados (campos e descrições)
│   ├── decisions.md          # Decisões arquiteturais registradas
│   └── roadmap.md            # Roadmap de evolução do projeto
│
├── src/
│   ├── ingestion/
│   │   ├── sources/
│   │   │   ├── base_source.py        # Classe abstrata para padronizar fontes
│   │   │   └── transparencia_sc.py   # Fonte Transparência SC (em desenvolvimento)
│   │   ├── config.yaml               # Configurações do pipeline
│   │   └── ingestion_runner.py       # Orquestrador da ingestão
│   │
│   ├── transformations/
│   │   ├── staging_transform.py      # Transformações da camada staging
│   │   ├── core_transform.py         # Modelagem das entidades core
│   │   └── marts_builder.py          # Construção das métricas analíticas
│   │
│   ├── pipelines/
│   │   ├── pipeline_staging.py       # Pipeline: raw → staging
│   │   ├── pipeline_core.py          # Pipeline: staging → core
│   │   └── pipeline_marts.py         # Pipeline: core → marts
│   │
│   └── utils/
│       ├── logger.py                 # Logger padronizado
│       ├── validators.py             # Validações de qualidade
│       └── helpers.py                # Funções auxiliares
│
└── tests/
    ├── test_ingestion.py             # Testes da ingestão
    ├── test_transformations.py       # Testes das transformações
    └── test_marts.py                 # Testes das métricas

---

## 📊 Métricas que serão geradas

- Economia (valor licitado – contratado)  
- Competitividade (nº de fornecedores por compra)  
- Modalidade mais utilizada  
- Tempo médio entre abertura e contratação  
- Ranking de órgãos por volume de compras  
- Ranking de fornecedores por participação  

---

## 🚦 Status do Projeto

- **Em desenvolvimento**  
- Ingestão Transparência SC → Em andamento  
- Ingestão Betha → Backlog  
- Modelagem Core → Backlog  
- Marts Analíticos → Backlog  

---

## 🗺️ Roadmap Inicial

### 🔹 **Fase 1 — Estrutura e Ingestão**
- [ ] Criar estrutura de pastas  
- [ ] Implementar `base_source.py`  
- [ ] Implementar ingestão Transparência SC  
- [ ] Implementar ingestão Betha  

### 🔹 **Fase 2 — Staging e Core**
- [ ] Criar camada staging  
- [ ] Criar validações de qualidade  
- [ ] Criar modelagem core  

### 🔹 **Fase 3 — Marts e Métricas**
- [ ] Criar marts analíticos  
- [ ] Criar métricas licitado x contratado  
- [ ] Criar métricas de competitividade  

### 🔹 **Fase 4 — Documentação e Testes**
- [ ] Documentar arquitetura  
- [ ] Criar dicionário de dados  
- [ ] Criar testes unitários  

---

## 📄 Licença
Uso educacional e demonstrativo.
