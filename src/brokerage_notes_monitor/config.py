import json
from pathlib import Path


class Config:
    def __init__(self, raw: dict):
        self.raw = raw

        self.pdf_input_dir = Path(raw["paths"]["pdf_input_dir"])
        self.excel_output_path = Path(raw["paths"]["excel_output_path"])
        self.excel_sheet_name = raw["excel"]["sheet_name"]

        self.backup_before_save = bool(raw.get("processing", {}).get("backup_before_save", True))

        self.log_level = raw.get("logging", {}).get("level", "INFO")

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        return cls(raw)

