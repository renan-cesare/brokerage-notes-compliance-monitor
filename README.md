# Brokerage Notes Compliance Monitor

> Pipeline corporativo em Python para extração, normalização e monitoramento de notas de corretagem (B3 / Bovespa / BM&F) a partir de arquivos PDF, com geração de histórico consolidado em Excel e aplicação automática de flags de compliance.

---

## 📌 Contexto de Negócio

Em escritórios de investimento, as áreas de **risco e compliance** precisam monitorar continuamente as operações dos clientes para identificar **atividades restritas ou sensíveis**, tais como:

* Operações de Day Trade
* Mini contratos (WIN / WDO)
* Contratos futuros (ex.: DI)
* Opções
* Operações a termo
* Outras condições especiais de negociação (cobertura, negócios diretos, etc.)

Essas operações são reportadas diariamente por meio de **notas de corretagem em PDF**, que:

* Possuem múltiplos layouts (Bovespa e BM&F)
* Não são estruturadas para leitura por máquina
* Frequentemente quebram a estrutura de tabelas quando convertidas para texto

Este projeto foi criado para **automatizar integralmente esse processo**.

---

## 🧠 O Que Este Sistema Faz

Este pipeline:

1. Lê **todas as notas de corretagem em PDF** a partir de uma pasta
2. Faz o parsing de:

   * Layout Bovespa (incluindo tabelas quebradas em linha única e multilinha)
   * Layout BM&F
3. Extrai:

   * Dados do cliente
   * Dados das operações
   * Ativo negociado
   * Quantidades, preços e valores
   * Códigos OBS e seus significados
4. Gera um **ID único de operação** para evitar duplicidades
5. Consolida os novos dados com um **histórico existente em Excel**
6. Aplica **regras de compliance** e flags para identificar:

   * Day trade
   * Mini contratos
   * Futuros (DI)
   * Opções
   * Operações a termo
7. Salva tudo em um **arquivo Excel** com:

   * Base histórica completa
   * Deduplicação automática
   * Formatação condicional destacando operações sinalizadas

---

## 🗂️ Estrutura do Projeto

```
brokerage-notes-compliance-monitor/
├─ src/
│  └─ brokerage_notes_monitor/
│     ├─ app.py            # Orquestra o pipeline
│     ├─ config.py         # Carrega configurações
│     ├─ logging_config.py # Configuração de logging
│     ├─ pdf_extract.py    # Lógica de parsing dos PDFs (núcleo do sistema)
│     ├─ rules.py          # Regras e flags de compliance
│     └─ excel_store.py    # Persistência e formatação no Excel
├─ configs/
│  └─ config.example.json
├─ main.py                 # Entrypoint da aplicação (CLI)
├─ requirements.txt
└─ README.md
```

---

## ⚙️ Instalação

Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv .venv
.venv\\Scripts\\activate   # Windows
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## 🛠️ Configuração

Copie o arquivo de exemplo:

```bash
cp configs/config.example.json configs/config.json
```

Edite o arquivo `configs/config.json`:

```json
{
  "paths": {
    "pdf_input_dir": "data/input_pdfs",
    "excel_output_path": "data/output/historico_notas.xlsx"
  },
  "excel": {
    "sheet_name": "Plan1"
  },
  "processing": {
    "backup_before_save": true
  },
  "logging": {
    "level": "INFO"
  }
}
```

---

## ▶️ Como Executar

Coloque as notas de corretagem em PDF na pasta:

```
data/input_pdfs/
```

Execute:

```bash
python main.py --config configs/config.json
```

Modo de simulação (não salva o Excel):

```bash
python main.py --config configs/config.json --dry-run
```

---

## 📊 Resultado

O sistema gera:

* Um arquivo Excel consolidado contendo:

  * Base histórica completa
  * Uma linha por operação
  * Deduplicação por hash da operação
  * Flags de compliance:

    * `is_daytrade`
    * `is_minicontrato`
    * `is_futuro_di`
    * `is_opcao`
    * `is_termo`
  * Flag final: `flag_alerta`
* As linhas com `flag_alerta_int = 1` são **destacadas automaticamente** por formatação condicional.

---

## 🧩 Por Que Este Não É Um Projeto de Brinquedo

Este projeto lida com:

* PDFs reais e problemáticos
* Múltiplos layouts quebrados
* Parsing heurístico
* Estratégia de deduplicação
* Base histórica incremental
* Regras reais de compliance
* Salvaguardas operacionais (backup, dry-run, logging)

Este é exatamente o tipo de **sistema interno de automação** construído em áreas de operações, risco e compliance no mercado financeiro.

---

## 🔒 Sanitização de Dados

Todos os nomes, códigos e identificadores de clientes utilizados neste repositório são **exemplos ou placeholders**.
O sistema real opera exclusivamente em ambiente interno com dados reais.

---

## 🚀 Autor

Desenvolvido como parte de uma stack de automações internas para operações, risco e compliance em um escritório de investimentos.
