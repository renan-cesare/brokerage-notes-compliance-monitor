from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import Config
from .logging_config import setup_logging


logger = logging.getLogger("brokerage_notes_monitor")


def run(config_path: str, dry_run: bool = False) -> None:
    """
    Orquestra o pipeline:
      - carrega config
      - inicializa logging
      - chama extração/transformação (módulos seguintes)
      - salva histórico em Excel (com backup, se habilitado)

    Obs: Os módulos de parsing e Excel serão adicionados nos próximos passos.
    """
    cfg = Config.load(config_path)
    setup_logging(cfg.log_level)

    logger.info("Iniciando monitor de notas de corretagem")
    logger.info(f"Config: {Path(config_path).resolve()}")
    logger.info(f"PDF dir: {cfg.pdf_input_dir}")
    logger.info(f"Excel: {cfg.excel_output_path} (aba={cfg.excel_sheet_name})")
    logger.info(f"Dry-run: {dry_run}")

    # Valida pasta de PDFs
    if not cfg.pdf_input_dir.exists():
        raise FileNotFoundError(f"Pasta de PDFs não existe: {cfg.pdf_input_dir}")

    # --- Placeholders: próximos passos ---
    # Aqui vamos chamar:
    #   - carregar histórico do Excel (se existir)
    #   - extrair operações dos PDFs
    #   - deduplicar por id_operacao
    #   - aplicar flags
    #   - salvar Excel (com backup)
    #
    # Por ora, só para o projeto "rodar" sem erro estrutural:
    logger.info("Pipeline ainda não conectado (parsing e Excel serão adicionados nos próximos passos).")
    logger.info("OK (estrutura base).")


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
