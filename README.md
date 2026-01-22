# Brokerage Notes Compliance Monitor

> Corporate-grade Python pipeline for extracting, normalizing and monitoring brokerage notes (B3 / Bovespa / BM&F) from PDF files, generating a consolidated Excel history with automatic compliance flags.

---

## 📌 Business Context

In brokerage offices, compliance and risk teams must continuously monitor clients' operations to detect **restricted or sensitive activities**, such as:

* Day Trade operations
* Mini contracts (WIN / WDO)
* Futures (e.g. DI)
* Options
* Term operations
* Other special trading conditions (coverage, direct trades, etc.)

These operations are reported daily in **PDF brokerage notes**, which:

* Have multiple layouts (Bovespa and BM&F)
* Are not machine-friendly
* Often break table structure when converted to text

This project was built to **automate this entire process**.

---

## 🧠 What This System Does

This pipeline:

1. Reads **all PDF brokerage notes** from a folder
2. Parses:

   * Bovespa layout (including single-line and multi-line broken tables)
   * BM&F layout
3. Extracts:

   * Client data
   * Trade data
   * Asset
   * Quantities, prices, values
   * OBS codes and their meanings
4. Generates a **unique operation ID** to avoid duplicates
5. Merges new data with an **existing Excel history**
6. Applies **compliance rules** and flags:

   * Day trade
   * Mini contracts
   * Futures (DI)
   * Options
   * Term operations
7. Saves everything to an **Excel file** with:

   * Full historical base
   * Automatic deduplication
   * Conditional formatting highlighting flagged operations

---

## 🗂️ Project Structure

```
brokerage-notes-compliance-monitor/
├─ src/
│  └─ brokerage_notes_monitor/
│     ├─ app.py            # Orchestrates the pipeline
│     ├─ config.py         # Loads configuration
│     ├─ logging_config.py # Logging setup
│     ├─ pdf_extract.py    # All PDF parsing logic (core)
│     ├─ rules.py          # Compliance rules and flags
│     └─ excel_store.py    # Excel persistence and formatting
├─ configs/
│  └─ config.example.json
├─ main.py                 # CLI entrypoint
├─ requirements.txt
└─ README.md
```

---

## ⚙️ Installation

Create a virtual environment (optional but recommended):

```bash
python -m venv .venv
.venv\\Scripts\\activate   # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🛠️ Configuration

Copy the example config:

```bash
cp configs/config.example.json configs/config.json
```

Edit `configs/config.json`:

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

## ▶️ How to Run

Put your PDF brokerage notes in:

```
data/input_pdfs/
```

Run:

```bash
python main.py --config configs/config.json
```

Dry-run mode (does not save Excel):

```bash
python main.py --config configs/config.json --dry-run
```

---

## 📊 Output

The system generates:

* A consolidated Excel file with:

  * Full historical base
  * One row per operation
  * Deduplication by operation hash
  * Compliance flags:

    * `is_daytrade`
    * `is_minicontrato`
    * `is_futuro_di`
    * `is_opcao`
    * `is_termo`
  * Final flag: `flag_alerta`
* Rows with `flag_alerta_int = 1` are **highlighted automatically**.

---

## 🧩 Why This Is Not a Toy Project

This is:

* A real-world messy PDF parsing problem
* With multiple broken layouts
* Heuristic extraction
* Deduplication strategy
* Incremental historical base
* Compliance logic
* And operational safeguards (backup, dry-run, logging)

This is the kind of **internal automation system** built in real brokerage and financial operations teams.

---

## 🔒 Data Sanitization

All client names, codes and identifiers used in this repository are **placeholders or examples**.
The real system runs only on internal environments and data.

---

## 🚀 Author

Built as part of a corporate automation and compliance tooling stack for brokerage operations.
