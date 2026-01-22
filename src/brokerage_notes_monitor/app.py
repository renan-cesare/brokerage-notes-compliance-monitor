from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import Config
from .logging_config import setup_logging
from .excel_store import load_history, backup_if_needed, save_history
from .pdf_extract import extract_operations_from_pdfs, reorder_columns
from .rules import apply_compliance_flags

logger = logging.getLogger("brokerage_notes_monitor.app")


def run(config_path: str, dry_run: bool = False) -> None:
    cfg = Config.load(config_path)
    setup_logging(cfg.log_level)

    pdf_dir = Path(cfg.pdf_input_dir).resolve()
    excel_path = Path(cfg.excel_output_path).resolve()

    logger.info("Iniciando monitor de notas de corretagem")
    logger.info(f"PDF dir: {pdf_dir}")
    logger.info(f"Excel: {excel_path} (aba={cfg.excel_sheet_name})")
    logger.info(f"Dry-run: {dry_run}")

    if not pdf_dir.exists():
        raise FileNotFoundError(f"Pasta de PDFs não existe: {pdf_dir}")

    historico_df = load_history(excel_path, cfg.excel_sheet_name)

    novos_df = extract_operations_from_pdfs(pdf_dir)
    if novos_df.empty:
        logger.info("Nenhuma operação extraída. Encerrando.")
        return

    if historico_df.empty:
        combinado_df = novos_df
    else:
        combinado_df = pd.concat([historico_df, novos_df], ignore_index=True)
        if "id_operacao" in combinado_df.columns:
            combinado_df.drop_duplicates(subset=["id_operacao"], inplace=True)

    combinado_df = apply_compliance_flags(combinado_df)
    combinado_df = reorder_columns(combinado_df)

    logger.info(f"Total no histórico (pós-dedup): {len(combinado_df)}")

    if dry_run:
        logger.info("Dry-run: não salvou Excel.")
        return

    if cfg.backup_before_save and excel_path.exists():
        backup_if_needed(excel_path)

    save_history(
        df=combinado_df,
        path=excel_path,
        sheet_name=cfg.excel_sheet_name,
        apply_conditional_formatting=True,
    )

    logger.info("OK.")
