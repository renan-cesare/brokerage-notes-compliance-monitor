# Brokerage Notes Monitor (PDF → Excel + Flags)

Pipeline em Python para **extração, normalização e monitoramento de operações a partir de PDFs de notas de corretagem** (B3/Bovespa e BM&F), com **consolidação incremental em Excel**, **deduplicação por identificador único** e **aplicação automática de flags** para acompanhamento operacional.

> **English (short):** Python pipeline to parse brokerage note PDFs (cash equities and derivatives), normalize trades, de-duplicate records, store incremental history in Excel, and apply monitoring flags.

---

## Principais recursos

* Parsing de **PDFs reais** com múltiplos layouts (Bovespa e BM&F)
* Extração e normalização de:

  * ativos, quantidades, preços e financeiro
  * mercado (à vista, futuros, opções, termo)
  * observações e códigos relevantes da nota
* **Identificador único da operação** para evitar duplicidades
* Consolidação incremental em **Excel** (histórico único)
* **Flags automáticas** para monitoramento, como:

  * day trade
  * minicontratos
  * futuros DI
  * opções
  * operações a termo
* Destaque visual e colunas auxiliares no Excel para facilitar filtros
* Execução via CLI com logs e opção de simulação (`--dry-run`)

---

## Contexto

Em rotinas de **operações, risco e monitoramento**, é comum receber **notas de corretagem em PDF** com layouts variados, dificultando a consolidação e análise histórica das operações.

Este projeto automatiza o fluxo completo:

**PDFs → extração → normalização → deduplicação → histórico em Excel → flags de monitoramento**

Permitindo análises consistentes, reaproveitáveis e auditáveis ao longo do tempo.

---

## Aviso importante (uso autorizado)

Este repositório é apresentado como **exemplo técnico/portfólio**.

* Utilize apenas **dados e ambientes autorizados**
* Não publique PDFs reais, dados de clientes, contas ou informações sensíveis
* Respeite políticas internas e a legislação aplicável (LGPD)

---

## Estrutura do projeto

```text
.
├─ configs/
│  └─ config.example.json
├─ src/
│  └─ brokerage_notes_monitor/
│     ├─ __init__.py
│     ├─ app.py
│     ├─ config.py
│     ├─ logging_config.py
│     ├─ pdf_extract.py
│     ├─ rules.py
│     └─ excel_store.py
├─ main.py
├─ requirements.txt
├─ LICENSE
└─ README.md
```

---

## Requisitos

* Python 3.10+

---

## Instalação

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Configuração

Crie um arquivo local de configuração a partir do exemplo:

```bash
# Windows
copy configs\config.example.json configs\config.json

# Linux / macOS
cp configs/config.example.json configs/config.json
```

Campos principais do `config.json`:

* `paths.pdf_input_dir` – diretório com os PDFs das notas
* `paths.excel_output_path` – caminho do Excel consolidado
* `processing.backup_before_save` – cria backup antes de salvar
* `logging.level` – nível de log

> O arquivo `configs/config.json` deve permanecer fora do versionamento.

---

## Execução

Coloque os PDFs em:

```
data/input_pdfs/
```

Execute o pipeline:

```bash
python main.py --config configs/config.json
```

Modo simulação (não salva o Excel):

```bash
python main.py --config configs/config.json --dry-run
```

---

## Saídas geradas

O pipeline gera ou atualiza:

* Excel consolidado com histórico incremental
* Colunas de flags para monitoramento
* Destaques visuais para operações sinalizadas

---

## Sanitização de dados

Este repositório **não contém dados reais**.

* PDFs e arquivos de execução devem permanecer fora do Git
* Informações sensíveis são carregadas apenas em tempo de execução

---

## Licença

MIT
