from __future__ import annotations

import re
import pandas as pd


PADRAO_OPCAO_B3 = re.compile(r"^[A-Z]{4}[A-Z]\d{2,3}[A-Z]?$")


def _tokens_obs(obs_str: str) -> set[str]:
    if not obs_str:
        return set()
    s = str(obs_str).upper().replace("\u00A0", " ")
    parts = re.split(r"[\s\|/]+", s)
    return {p for p in parts if p}


def apply_compliance_flags(df: pd.DataFrame) -> pd.DataFrame:
    obs_series = df.get("obs", "").fillna("").astype(str).str.upper()
    obs_codigos = df.get("obs_codigos", "").fillna("").astype(str).str.upper()
    linha_bruta = df.get("linha_bruta", "").fillna("").astype(str).str.upper()

    tipo_mercado = df.get("tipo_mercado", "").fillna("").astype(str).str.upper()
    ativo = df.get("ativo", "").fillna("").astype(str).str.upper()
    layout = df.get("layout_origem", "").fillna("").astype(str).str.upper()
    bmf_tipo = df.get("bmf_tipo_negocio", "").fillna("").astype(str).str.upper()

    # Cobertura (F)
    df["is_cobertura"] = (
        obs_codigos.str.contains(r"(?:^|\s)F(?:\s|$)", regex=True)
        | obs_series.apply(lambda x: "F" in _tokens_obs(x))
        | linha_bruta.str.contains(r"(?:^|\s)F(?:\s|$)", regex=True)
    )

    # DayTrade
    df["is_daytrade"] = (
        ((layout == "BMF") & (bmf_tipo == "DAY TRADE"))
        | (
            (layout == "BOVESPA")
            & (
                obs_codigos.str.contains(r"(?:^|\s)D(?:\s|$)", regex=True)
                | obs_series.apply(lambda x: "D" in _tokens_obs(x))
            )
        )
    )

    # Mini contratos (WIN/WDO)
    df["is_minicontrato"] = ativo.str.startswith(("WIN", "WDO")) & (~df["is_cobertura"])

    # Futuro de juros (DI)
    df["is_futuro_di"] = (layout == "BMF") & ativo.str.startswith("DI") & (~df["is_cobertura"])

    # Opções (B3)
    df["is_opcao"] = (
        (layout == "BOVESPA")
        & ativo.apply(lambda x: bool(PADRAO_OPCAO_B3.match(str(x).strip())))
        & (~df["is_cobertura"])
    )

    # Termo
    df["is_termo"] = tipo_mercado.str.contains("TERMO", na=False)

    # Flag final
    df["flag_alerta"] = (
        df["is_daytrade"]
        | df["is_minicontrato"]
        | df["is_futuro_di"]
        | df["is_opcao"]
        | df["is_termo"]
    )
    df["flag_alerta_int"] = df["flag_alerta"].astype(int)

    if "obs_significado" not in df.columns:
        df["obs_significado"] = ""

    return df
