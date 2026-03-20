# 📌 Backlog Técnico — Compras Públicas (Scrum)

Este documento descreve o backlog técnico do projeto, organizado em **Épicos**, **Features**, **Histórias** e **Critérios de Aceite**, seguindo práticas de Scrum.

---

# 🧱 ÉPICO 1 — Ingestão de Dados

## 🎯 Objetivo
Criar um módulo de ingestão configurável e extensível para múltiplas fontes de compras públicas.

---

## ⭐ Feature 1.1 — Criar estrutura base de ingestão

### História 1.1.1 — Criar classe base de ingestão
**Como** desenvolvedor  
**Quero** uma classe abstrata `base_source.py`  
**Para** padronizar o comportamento das fontes

**Critérios de Aceite**
- Deve possuir métodos abstratos: `authenticate()`, `fetch_data()`, `normalize()`, `save_raw()`
- Deve registrar logs
- Deve lançar exceções padronizadas

---

## ⭐ Feature 1.2 — Ingestão Transparência SC

### História 1.2.1 — Implementar extração de compras
**Como** pipeline  
**Quero** extrair dados de compras do Transparência SC  
**Para** alimentar a camada raw

**Critérios de Aceite**
- Deve extrair dados de compras
- Deve salvar arquivos em `/data/raw/transparencia_sc`
- Deve registrar logs de sucesso e erro

### História 1.2.2 — Implementar extração de contratos
**Critérios de Aceite**
- Deve extrair contratos vinculados às compras
- Deve relacionar compra ↔ contrato
- Deve salvar em `/data/raw/transparencia_sc`

---

## ⭐ Feature 1.3 — Ingestão Betha

### História 1.3.1 — Implementar extração de compras Betha
**Critérios de Aceite**
- Deve consumir API ou scraping
- Deve salvar dados brutos
- Deve registrar logs

---

# 🧱 ÉPICO 2 — Staging

## ⭐ Feature 2.1 — Normalização de dados

### História 2.1.1 — Normalizar datas
**Critérios de Aceite**
- Datas devem estar no padrão ISO  
- Datas inválidas devem ser registradas em log  

### História 2.1.2 — Normalizar valores monetários
**Critérios de Aceite**
- Valores devem ser convertidos para decimal  
- Formatos diferentes devem ser tratados  

---

# 🧱 ÉPICO 3 — Core (Modelagem)

## ⭐ Feature 3.1 — Criar entidades principais

### História 3.1.1 — Criar entidade Órgão
**Critérios de Aceite**
- Deve conter ID, nome, esfera, município  
- Deve ser única por fonte  

### História 3.1.2 — Criar entidade Compra
**Critérios de Aceite**
- Deve conter modalidade, objeto, datas, valores  
- Deve relacionar órgão e fornecedor  

### História 3.1.3 — Criar entidade Contrato
**Critérios de Aceite**
- Deve conter valor contratado  
- Deve relacionar compra ↔ contrato  

---

# 🧱 ÉPICO 4 — Marts Analíticos

## ⭐ Feature 4.1 — Criar métricas principais

### História 4.1.1 — Métrica licitado vs contratado
**Critérios de Aceite**
- Deve calcular economia (licitado – contratado)
- Deve permitir agregação por órgão, modalidade e fornecedor

### História 4.1.2 — Métrica de competitividade
**Critérios de Aceite**
- Deve contar fornecedores por compra
- Deve gerar ranking

---

# 🧱 ÉPICO 5 — Documentação e Testes

## ⭐ Feature 5.1 — Documentação

### História 5.1.1 — Criar dicionário de dados
**Critérios de Aceite**
- Deve conter descrição de cada campo  
- Deve conter origem e transformações  

## ⭐ Feature 5.2 — Testes

### História 5.2.1 — Testes de ingestão
**Critérios de Aceite**
- Deve validar retorno das fontes  
- Deve validar erros esperados  

### História 5.2.2 — Testes de transformação
**Critérios de Aceite**
- Deve validar normalização  
- Deve validar cálculos de métricas  

---

# 🏁 Conclusão

Este backlog fornece uma visão clara, incremental e orientada a valor para o desenvolvimento do pipeline de Compras Públicas, seguindo práticas reais de engenharia e Scrum.