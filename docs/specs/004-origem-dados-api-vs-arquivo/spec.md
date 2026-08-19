# 004 — Origem dos dados: API vs. arquivo (contratos SC)

## Tipo

Decisão de arquitetura (não é spec retroativa — é decisão nova, ainda sem implementação).

## Status

Concluída. Decisão: manter ingestão via arquivo (CSV). API do DataStore não está disponível nesta instância do CKAN — ver Investigação.

## Resumo

Hoje a ingestão de `compras-publicas` é feita baixando o XLS/CSV publicado mensalmente pelo portal de Dados Abertos SC (`https://dados.sc.gov.br/dataset/contratos`) e processando via dbt. O portal roda CKAN 2.8.3, que nativamente pode expor os recursos via API (`/api/3/action/datastore_search`), o que tornaria a ingestão uma chamada HTTP paginada em vez de parse de arquivo. Esta spec decide se vale migrar pra API, manter o arquivo, ou usar as duas conforme o caso.

## Contexto

- Achado da spec 003 (storage/pipeline): a chave primária do dataset é `nucontrato` (confirmado empiricamente: 0 duplicadas em 2368 linhas de uma carga real de `contratos-demo.csv`).
- O CSV vem em encoding ISO-8859-1, com 51 colunas de nomes pouco descritivos (`cdunidadegestora`, `nmgestao`, etc.) — sujeito a erro de parse se não tratado com cuidado.
- Publicação é mensal, aparentemente como snapshot do estado atual (não delta) — ver spec 003 pro racional completo de upsert + dbt snapshot.
- Resource ID do arquivo atual (`contratos.csv`, atualizado em 09/09/2025 segundo a página do dataset): `8bb98383-7043-4d2f-ae32-9377656e71ee`.
- **Não confirmado ainda**: se esse resource_id está de fato carregado no DataStore do CKAN (nem todo recurso é indexado — alguns ficam só como arquivo bruto pra download).

## Investigação

### Bloco 1 — o recurso está no DataStore?

Comando executado (nota: `python3` neste ambiente resolve pro stub da Microsoft Store, sem interpretador real — usado `python` em vez disso):

```
$ curl -s "https://dados.sc.gov.br/api/3/action/datastore_search?resource_id=8bb98383-7043-4d2f-ae32-9377656e71ee&limit=5" | python -m json.tool
"Requisição incorreta - Action name not known: datastore_search"
```

A action `datastore_search` não existe nesta instância — não é um erro de "resource not found", é a própria action não estar registrada.

Confirmação: `status_show` lista as extensions ativas no CKAN e `datastore` não está entre elas.

```
$ curl -s "https://dados.sc.gov.br/api/3/action/status_show" | python -m json.tool
{
    "help": "https://dados.sc.gov.br/api/3/action/help_show?name=status_show",
    "success": true,
    "result": {
        "ckan_version": "2.8.3",
        "site_url": "https://dados.sc.gov.br",
        "site_description": "Abrindo dados governamentais de Santa Catarina",
        "site_title": "Dados Abertos SC",
        "error_emails_to": null,
        "locale_default": "pt_BR",
        "extensions": [
            "stats",
            "text_view",
            "image_view",
            "recline_view",
            "webpage_view"
        ]
    }
}
```

Confirmação adicional via `resource_show` — o recurso existe e é válido, mas é só `url_type: "upload"` (arquivo bruto), sem nenhum campo `datastore_active`:

```
$ curl -s "https://dados.sc.gov.br/api/3/action/resource_show?id=8bb98383-7043-4d2f-ae32-9377656e71ee" | python -m json.tool
{
    "help": "https://dados.sc.gov.br/api/3/action/help_show?name=resource_show",
    "success": true,
    "result": {
        "mimetype": "text/csv",
        "cache_url": null,
        "file": "<FileStorage: u'contratos.csv' ('text/html; charset=ISO-8859-1')>",
        "hash": "",
        "description": "contratos.csv created on: 20250909_070200",
        "last_modified": "2025-09-09T10:02:02.711974",
        "format": "CSV",
        "url": "https://dados.sc.gov.br/dataset/93dab950-e805-4388-8418-cfb3b73f1623/resource/8bb98383-7043-4d2f-ae32-9377656e71ee/download/contratos.csv",
        "name": "contratos.csv",
        "cache_last_updated": null,
        "package_id": "93dab950-e805-4388-8418-cfb3b73f1623",
        "created": "2024-05-15T17:57:54.803530",
        "state": "active",
        "mimetype_inner": null,
        "key": "contratos",
        "position": 6,
        "revision_id": "5c58457f-e409-4e33-b7a1-d113fff4d57e",
        "url_type": "upload",
        "id": "8bb98383-7043-4d2f-ae32-9377656e71ee",
        "resource_type": null,
        "size": 122184246
    }
}
```

**Investigação termina aqui**, conforme a própria spec previu: a extensão DataStore não está instalada/habilitada nesta instância do CKAN. Não existe `/api/3/action/datastore_search`, `datastore_search_sql`, nem qualquer variante — não é uma questão de esse recurso específico não estar indexado, é a funcionalidade inteira não existir no portal. Blocos 2–6 não se aplicam.

## Requirements

### Funcionais

- A ingestão DEVE continuar baixando o recurso `contratos.csv` via URL de download direto (`resource.url` retornado por `resource_show`, ou a URL fixa do dataset), não via DataStore API — porque a DataStore API não existe nesta instância do CKAN.
- A rotina de ingestão DEVE seguir tratando o CSV como snapshot mensal completo (não delta), conforme já decidido na spec 003.

### Não-funcionais

- SE o portal Dados Abertos SC eventualmente habilitar a extensão DataStore (mudança fora do controle deste projeto), ENTÃO a decisão desta spec DEVE ser revisitada — não presumir que a ausência de hoje é permanente.

## Design

| Opção | Decisão | Motivo |
|---|---|---|
| API (DataStore) | Rejeitada | Extensão `datastore` não está instalada nesta instância do CKAN 2.8.3 — `datastore_search` retorna "Action name not known", confirmado via `status_show` (extensions ativas: `stats`, `text_view`, `image_view`, `recline_view`, `webpage_view`, sem `datastore`). |
| Arquivo (CSV) | Mantida | Único caminho disponível hoje. Sem mudança na rotina de ingestão/dbt existente. |
| Híbrido | N/A | Não há API funcional pra compor com o arquivo. |

Componentes afetados: nenhum — decisão preserva o pipeline atual (download do CSV + dbt). Nenhuma mudança de código motivada por esta spec.

## Casos de borda

- Se o portal habilitar DataStore no futuro, reabrir esta spec (ou criar uma nova referenciando-a) e repetir os Blocos 2–6 antes de qualquer migração.

## Fora do escopo

- Mudança de storage (Postgres vs. BigQuery) — já tratada na spec 003.
- Mudança de frontend — fora do escopo desta spec.

## Referências de código

_A preencher conforme a implementação._

## Ver também

- [[003-storage-e-chave-unica]]
- [[005-grao-do-dado-contrato-vs-aditivo]]
