# 🧱 Arquitetura do Pipeline — Compras Públicas

Este documento descreve a arquitetura completa do pipeline de dados do projeto **Compras Públicas**, incluindo fluxo de dados, camadas, componentes, decisões técnicas e padrões adotados.

---

# 📌 Visão Geral da Arquitetura

O pipeline segue o padrão clássico de Analytics Engineering:

Ele foi projetado para ser:

- **Modular** — cada etapa é independente  
- **Extensível** — novas fontes podem ser adicionadas facilmente  
- **Configurável** — comportamento controlado via `config.yaml`  
- **Auditável** — logs e validações em todas as etapas  
- **Reprodutível** — execução determinística e versionada  

---

# 🔌 1. Fontes de Dados

Atualmente, o pipeline utiliza duas fontes principais:

### **1. Transparência SC**
- Dados de compras, licitações e contratos
- Formatos: HTML, JSON, CSV (dependendo do endpoint)
- Requer scraping estruturado

### **2. Betha Transparência**
- Dados de compras e contratos de municípios
- API e endpoints JSON
- Requer autenticação simples ou scraping leve

### **Futuras fontes previstas**
- IPM Sistemas  
- Portal Nacional de Compras Públicas (PNCP)  
- Portal da Transparência Federal  

---

# 🏗️ 2. Ingestão

A ingestão é baseada em um modelo **orientado a fontes**, com uma classe base:

Cada fonte implementa:

- Autenticação (se necessário)
- Paginação
- Extração de dados brutos
- Normalização mínima
- Salvamento em `/data/raw`

### Estrutura:

### Decisões técnicas:
- Cada fonte é um módulo independente  
- O `ingestion_runner.py` lê o `config.yaml` e executa as fontes selecionadas  
- Logs centralizados em `utils/logger.py`  

---

# 🧹 3. Staging

A camada **staging** padroniza os dados brutos:

- Normalização de campos  
- Conversão de datas  
- Conversão de valores monetários  
- Padronização de códigos  
- Validações de qualidade  

### Arquivos principais:

### Saída:
Arquivos limpos em:

---

# 🧩 4. Core (Modelagem)

A camada **core** representa o modelo de dados principal do domínio de compras públicas.

### Entidades:

- **Órgão**
- **Compra**
- **Item**
- **Fornecedor**
- **Modalidade**
- **Contrato**

### Objetivo:
Criar um modelo relacional consistente e analítico.

### Arquivos:

---

# 📊 5. Marts Analíticos

A camada **marts** contém tabelas analíticas e métricas derivadas:

### Métricas principais:

- Valor licitado vs contratado  
- Competitividade (nº de fornecedores)  
- Modalidade mais utilizada  
- Tempo médio do processo  
- Ranking de órgãos  
- Ranking de fornecedores  

### Arquivos:

---

# 🧪 6. Testes

Testes unitários garantem estabilidade:

---

# 📚 7. Documentação

Documentos auxiliares:

- `data_dictionary.md` — dicionário de dados  
- `decisions.md` — decisões arquiteturais  
- `roadmap.md` — evolução planejada  

---

# 🧭 8. Fluxo Completo do Pipeline

---

# 🧠 9. Decisões Arquiteturais Importantes

- **Separação por camadas** para clareza e reuso  
- **Configuração externa** via YAML  
- **Fontes plugáveis** (Strategy Pattern)  
- **Logs centralizados**  
- **Estrutura orientada a engenharia**, não notebooks  

---

# 🏁 Conclusão

A arquitetura foi projetada para ser clara, escalável e alinhada às práticas modernas de Analytics Engineering, permitindo evolução contínua e adição de novas fontes e métricas.