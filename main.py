import argparse
from brokerage_notes_monitor.app import run


def parse_args():
    p = argparse.ArgumentParser(
        description="Monitor de notas de corretagem (XP) - Extração PDF -> Excel + flags de compliance."
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
