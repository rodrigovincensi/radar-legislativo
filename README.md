# Radar Legislativo

Pipeline automatizado de ETL com IA para monitoramento da Câmara dos Deputados, desenvolvido como Projeto Integrador da Pós Tech (Engenharia de Dados e IA).

## O Problema

A Bússola Pública é uma consultoria que vende inteligência legislativa para empresas e escritórios de advocacia. Dois analistas passavam o dia lendo o site da Câmara para montar relatórios semanais — processo manual, sem histórico, sem escala.

## A Solução

Pipeline completo que extrai, transforma, enriquece com IA e entrega automaticamente as informações legislativas relevantes:

```
API da Câmara → Extração (Python) → Transformação (Pandas) → Banco (Supabase) → IA (OpenAI) → Automação (n8n)
```

![Diagrama do Pipeline](assets/diagrama_pipeline.png)

## Dados Coletados

| Tabela | Registros | Descrição |
|---|---|---|
| deputados | 512 | Todos os deputados da legislatura atual |
| partidos | 21 | Partidos com representação na Câmara |
| proposicoes | ~36.300 | Projetos de lei, PECs, MPVs e outros |
| votacoes | 4.152 | Votações em plenário e comissões |
| despesas | 77.044 | Cota parlamentar por deputado |

## Camada de IA

### Resumos Executivos (GPT-4o-mini)

Cada proposição tem sua ementa resumida em 3 linhas em linguagem clara para executivos.

**Prompt utilizado:**
- System: *"Voce e um analista legislativo. Resuma proposicoes em 3 linhas, em linguagem clara para um executivo de negocios. Destaque o impacto pratico."*
- User: *"Resuma esta proposicao: {ementa}"*

**Modelo:** `gpt-4o-mini` | **max_tokens:** 150 | **temperature:** 0.3

### Classificação Temática (text-embedding-3-small)

Cada proposição é classificada automaticamente em um dos 10 temas via similaridade de cosseno entre o embedding da ementa e embeddings de referência de cada tema.

**Temas:** Tributação e impostos · Saúde pública · Educação · Meio ambiente · Trabalho · Segurança pública · Tecnologia · Infraestrutura · Economia · Direitos humanos

**Modelo:** `text-embedding-3-small` | **Método:** cosine similarity

## Estrutura do Projeto

```
├── Scripts Python/
│   ├── 01_exploracao_api.ipynb        # Exploração dos endpoints da API
│   ├── 02_extracao_dados.ipynb        # Extração com paginação e retry
│   ├── 03_transformacao_carga.ipynb   # Transformação e carga no Supabase
│   ├── 04_ia_resumos.ipynb            # Resumos executivos com GPT-4o-mini
│   ├── 05_classificacao_temas.ipynb   # Classificação temática com embeddings
│   └── pipeline_diario.py             # Orquestrador do pipeline (roda 02→05)
├── n8n/
│   └── radar-legislativo-briefing-semanal.json  # Workflow exportado
├── .gitignore
├── requirements.txt
└── README.md
```

## Modelo de Tabelas

**Tabelas fato:**
- `proposicoes`: id, siglaTipo, codTipo, numero, ano, ementa, dataApresentacao, **resumo**, **tema**
- `votacoes`: id, data, dataHoraRegistro, siglaOrgao, proposicaoObjeto, descricao, aprovacao
- `despesas`: id_deputado, ano, mes, tipoDespesa, codDocumento, valorDocumento, nomeFornecedor, valorLiquido

**Tabelas dimensão:**
- `deputados`: id, nome, siglaPartido, siglaUf, idLegislatura, urlFoto, email
- `partidos`: id, sigla, nome

**Relacionamentos:**
- `despesas.id_deputado` → `deputados.id`
- `deputados.siglaPartido` → `partidos.sigla` (relação lógica, sem FK formal)

## Como Rodar

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Crie um arquivo `.env` na raiz com:
```
DATABASE_URL=postgresql://usuario:senha@host:5432/postgres
OPENAI_API_KEY=sua_chave_aqui
```
4. Execute os notebooks em ordem: `01` → `02` → `03` → `04` → `05`

Ou rode o pipeline completo de uma vez:
```
python "Scripts Python/pipeline_diario.py"
```

## Decisões Técnicas

- **Supabase** como banco PostgreSQL — pgvector disponível, painel web para visualização, sem configuração local
- **Insert-only em proposicoes** — tabela nunca é recriada, preservando as colunas `resumo` e `tema` geradas pela IA em execuções anteriores
- **`WHERE resumo IS NULL`** na query de resumos — execução incremental, só processa proposições novas a cada rodada
- **Batch API da OpenAI** para carga inicial — 50% mais barato e sem rate limit, usada para processar as ~35k proposições históricas de uma vez
- **Ambos os caminhos de IA** (resumo + embeddings) — resumo entrega valor direto ao leitor executivo; classificação temática permite filtrar e agrupar proposições por área
- **Cosine similarity** para classificação — abordagem sem supervisão, sem necessidade de dataset rotulado

## Banco de Dados

Banco PostgreSQL hospedado no Supabase com mais de 117.000 registros.

> Link do projeto no Supabase: https://supabase.com/dashboard/project/arcasxudbwacekjffehu

## Automação

### Pipeline Diário (Task Scheduler)

O script `pipeline_diario.py` é agendado via Windows Task Scheduler para rodar às 6h diariamente, executando os notebooks 02→03→04→05 em sequência e mantendo o banco sempre atualizado.

### Briefing Semanal (n8n)

Workflow n8n configurado para toda segunda-feira às 8h:

1. **Schedule Trigger** — dispara às 8h toda segunda
2. **Postgres** — busca 1 proposição por tema (10 ao total) mais recentes do banco
3. **Code JS** — monta email em HTML formatado
4. **Send Email** — envia via Gmail SMTP

**Execução do workflow n8n:**

![Execução n8n](assets/execucao_n8n.png)

**Email recebido:**

![Email recebido](assets/email_pipeline.png)
