import argparse
import sys
from pathlib import Path

# Garante que o Python encontre o pacote em /src sem precisar instalar.
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from brokerage_notes_monitor.app import run


def parse_args():
    p = argparse.ArgumentParser(
        description="Monitor de notas de corretagem - Extração PDF -> Excel + flags de compliance."
    )
    p.add_argument(
        "--config",
        required=True,
        help="Caminho do config.json (baseado em configs/config.example.json).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa extração e dedup, mas não salva Excel.",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(config_path=args.config, dry_run=args.dry_run)
