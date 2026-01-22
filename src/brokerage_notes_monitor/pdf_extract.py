# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from PyPDF2 import PdfReader

logger = logging.getLogger("brokerage_notes_monitor.pdf")


# =========================================================
# =================== PADRÕES / CONFIG =====================
# =========================================================

PADRAO_QNEG = re.compile(r"^\d+\-(BOVESPA|BMF)$")

# Opções B3: 4 letras + letra do mês + 2-3 dígitos (+ opcional sufixo)
PADRAO_OPCAO_B3 = re.compile(r"^[A-Z]{4}[A-Z]\d{2,3}[A-Z]?$")

# Linha única (achatada) - B3
PADRAO_LINHA_B3_UNICA = re.compile(
    r"^(?P<qneg>\d+\-BOVESPA)\s+"
    r"(?P<cv>C|V)\s+"
    r"(?P<tipo_mercado>\S+)\s+"
    r"(?P<meio>.+?)\s+"
    r"(?P<quantidade>\d+)\s+"
    r"(?P<preco>\d{1,3}(?:\.\d{3})*,\d+)\s+"
    r"(?P<valor>\d{1,3}(?:\.\d{3})*,\d+)\s+"
    r"(?P<dc>C|D)$"
)


# =========================================================
# =================== LEGENDA OFICIAL XP ==================
# =========================================================

OBS_LEGENDA = {
    "A": "Posição futuro",
    "T": "Liquidação pelo Bruto",
    "C": "Clubes e fundos de Ações",
    "I": "POP",
    "#": "Negócio direto",
    "8": "Liquidação Institucional",
    "D": "Day Trade",
    "F": "Cobertura",
    "B": "Debêntures",
    "P": "Carteira Própria",
    "H": "Home Broker",
    "X": "Box",
    "Y": "Desmanche de Box",
    "L": "Precatório",
}
OBS_TOKENS_VALIDOS = set(OBS_LEGENDA.keys())


def is_obs_token(tok: str) -> bool:
    return str(tok).strip().upper().replace("\u00A0", " ") in OBS_TOKENS_VALIDOS


# =========================================================
# ================= FUNÇÕES AUXILIARES ====================
# =========================================================

def br_to_float(num_str: str | None):
    if num_str is None:
        return None
    s = str(num_str).strip()
    if not s:
        return None
    try:
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return None


def parse_data_pregao(data_str: str):
    try:
        dt = datetime.strptime(data_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return data_str


def normalizar_numero_nota(numero_str: str, tamanho: int = 7) -> str:
    if not numero_str:
        return ""
    s = re.sub(r"\D", "", str(numero_str))
    if not s:
        return ""
    if len(s) >= tamanho:
        return s
    return s.zfill(tamanho)


def gerar_chave_unica(reg: dict) -> str:
    campos = [
        reg.get("arquivo_pdf", ""),
        reg.get("pagina", ""),
        reg.get("numero_nota", ""),
        reg.get("folha", ""),
        reg.get("data_pregao", ""),
        reg.get("codigo_cliente", ""),
        reg.get("nome_cliente", ""),
        reg.get("cpf_cliente", ""),
        reg.get("assessor", ""),
        reg.get("q_negociacao", ""),
        reg.get("cv", ""),
        reg.get("tipo_mercado", ""),
        reg.get("ativo", ""),
        reg.get("obs", ""),
        str(reg.get("quantidade", "")),
        reg.get("preco_str", ""),
        reg.get("valor_str", ""),
        reg.get("dc", ""),
        reg.get("linha_bruta", ""),
    ]
    return "|".join(str(c) for c in campos)


def gerar_id_operacao(chave_unica: str) -> str:
    return hashlib.md5(chave_unica.encode("utf-8")).hexdigest()


def tokens_obs(obs_str: str) -> list:
    if not obs_str:
        return []
    s = str(obs_str).strip().upper()
    s = s.replace("\u00A0", " ")
    raw = re.split(r"[\s\|/]+", s)
    return [t for t in raw if t]


def extrair_codigos_obs_robusto(obs_str: str) -> set:
    cods = set()
    if not obs_str:
        return cods

    for t in tokens_obs(obs_str):
        t_up = str(t).upper().replace("\u00A0", " ")
        t_norm = re.sub(r"[^A-Z0-9#]", "", t_up)

        if not t_norm:
            continue

        if t_norm in OBS_LEGENDA:
            cods.add(t_norm)
            continue

        if "#" in t_norm and "#" in OBS_LEGENDA:
            cods.add("#")

        if len(t_norm) <= 3:
            partes = re.findall(r"(#|[A-Z0-9])", t_norm)
            for p in partes:
                if p in OBS_LEGENDA:
                    cods.add(p)

    return cods


def obs_para_significado(cods: set) -> str:
    if not cods:
        return ""
    return "; ".join(OBS_LEGENDA.get(c, c) for c in sorted(cods))


def separar_desc_e_obs(meio: str):
    s = str(meio).strip().replace("\u00A0", " ")
    toks = s.split()
    obs_toks = []
    while toks and is_obs_token(toks[-1]):
        obs_toks.insert(0, toks.pop())
    desc = " ".join(toks).strip()
    obs = " ".join(obs_toks).strip()
    return desc, obs


# =========================================================
# ================== CABEÇALHO POR PÁGINA =================
# =========================================================

def extrair_header_pagina(texto: str) -> dict:
    header = {
        "numero_nota": "",
        "folha": "",
        "data_pregao": "",
        "codigo_cliente": "",
        "nome_cliente": "",
        "cpf_cliente": "",
        "codigo_cliente_detalhado": "",
        "assessor": "",
    }

    m = re.search(r"Nr\.?\s*nota\s+(\d[\d\.]*)", texto, flags=re.IGNORECASE)
    if m:
        header["numero_nota"] = normalizar_numero_nota(m.group(1), tamanho=7)

    m = re.search(r"Folha\s+(\d+)", texto, flags=re.IGNORECASE)
    if m:
        header["folha"] = m.group(1).strip()

    m = re.search(r"Data preg[aã]o\s+([0-3]\d/[01]\d/\d{4})", texto, flags=re.IGNORECASE)
    if m:
        header["data_pregao"] = parse_data_pregao(m.group(1).strip())

    m = re.search(r"Cliente\s+(\d+)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{5,})", texto)
    if m:
        header["codigo_cliente"] = m.group(1).strip()
        header["nome_cliente"] = " ".join(m.group(2).split())

    if not header["codigo_cliente"]:
        m = re.search(r"C[oó]digo do Cliente\s+(\d+)", texto, flags=re.IGNORECASE)
        if m:
            header["codigo_cliente"] = m.group(1).strip()

    if not header["nome_cliente"]:
        m = re.search(r"\n([A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{5,})\n[^\n]*\n\d{5}-\d{3}", texto)
        if m:
            header["nome_cliente"] = " ".join(m.group(1).split())

    cpf_m = re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto)
    if cpf_m:
        header["cpf_cliente"] = cpf_m.group(0)

    m = re.search(r"C[oó]digo cliente\s+([^\n]+)", texto, flags=re.IGNORECASE)
    if m:
        header["codigo_cliente_detalhado"] = m.group(1).strip()

    m = re.search(r"Assessor\s+(\d+)", texto)
    if m:
        header["assessor"] = m.group(1).strip()

    return header


# =========================================================
# ==================== EXTRAÇÃO BOVESPA ===================
# =========================================================

def identificar_ticker_bovespa(descricao: str) -> str:
    tokens = descricao.split()
    padrao_ticker = re.compile(r"^[A-Z]{3,}[0-9]{1,2}[A-Z0-9]*$")
    for tk in reversed(tokens):
        if padrao_ticker.match(tk.upper()):
            return tk.upper()
    return ""


def extrair_operacoes_pagina_bovespa(texto: str):
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    operacoes = []

    def is_int_str(s: str) -> bool:
        return re.match(r"^\d+$", s.strip()) is not None

    # 1) Linha única achatada
    for linha in linhas:
        m = PADRAO_LINHA_B3_UNICA.match(linha.replace("\u00A0", " "))
        if not m:
            continue

        q_neg = m.group("qneg").strip()
        cv = m.group("cv").strip()
        tipo_mercado = m.group("tipo_mercado").strip()
        meio = m.group("meio").strip().replace("\u00A0", " ")

        descricao, obs = separar_desc_e_obs(meio)
        cods = extrair_codigos_obs_robusto(obs)

        quantidade_str = m.group("quantidade").strip()
        preco_str = m.group("preco").strip()
        valor_str = m.group("valor").strip()
        dc = m.group("dc").strip()

        ticker = identificar_ticker_bovespa(descricao)
        ativo = ticker if ticker else descricao

        try:
            quantidade = int(quantidade_str)
        except Exception:
            quantidade = quantidade_str

        operacoes.append({
            "layout_origem": "BOVESPA",
            "q_negociacao": q_neg,
            "cv": cv,
            "tipo_mercado": tipo_mercado,
            "descricao_completa": descricao,
            "obs": obs,
            "obs_codigos": " ".join(sorted(cods)),
            "obs_significado": obs_para_significado(cods),
            "ativo": ativo,
            "quantidade": quantidade,
            "quantidade_str": quantidade_str,
            "preco": br_to_float(preco_str),
            "preco_str": preco_str,
            "valor": br_to_float(valor_str),
            "valor_str": valor_str,
            "dc": dc,
            "linha_bruta": linha,
        })

    if operacoes:
        return operacoes

    # 2) Multilinha
    i = 0
    while i < len(linhas):
        linha = linhas[i].replace("\u00A0", " ").strip()

        if PADRAO_QNEG.match(linha) and "BOVESPA" in linha:
            q_neg = linha
            if i + 3 >= len(linhas):
                i += 1
                continue

            cv = linhas[i + 1].strip()
            tipo_mercado = linhas[i + 2].strip()

            desc_parts = []
            obs_parts = []
            j = i + 3

            while j < len(linhas) and not is_int_str(linhas[j]):
                t = linhas[j].replace("\u00A0", " ").strip()

                if len(t.split()) == 1 and is_obs_token(t):
                    obs_parts.append(t)
                    j += 1
                    continue

                t_desc, t_obs = separar_desc_e_obs(t)
                if t_desc:
                    desc_parts.append(t_desc)
                if t_obs:
                    obs_parts.append(t_obs)

                j += 1

            if j >= len(linhas) or j + 3 >= len(linhas):
                i += 1
                continue

            quantidade_str = linhas[j].strip()
            preco_str = linhas[j + 1].strip()
            valor_str = linhas[j + 2].strip()
            dc = linhas[j + 3].strip()

            descricao = " ".join(p for p in desc_parts if p).strip()
            obs = " ".join(p for p in obs_parts if p).strip()

            ticker = identificar_ticker_bovespa(descricao)
            ativo = ticker if ticker else descricao

            try:
                quantidade = int(quantidade_str)
            except Exception:
                quantidade = quantidade_str

            linha_bruta = " | ".join([
                q_neg, cv, tipo_mercado, descricao, obs,
                quantidade_str, preco_str, valor_str, dc
            ])

            cods = extrair_codigos_obs_robusto(obs)

            operacoes.append({
                "layout_origem": "BOVESPA",
                "q_negociacao": q_neg,
                "cv": cv,
                "tipo_mercado": tipo_mercado,
                "descricao_completa": descricao,
                "obs": obs,
                "obs_codigos": " ".join(sorted(cods)),
                "obs_significado": obs_para_significado(cods),
                "ativo": ativo,
                "quantidade": quantidade,
                "quantidade_str": quantidade_str,
                "preco": br_to_float(preco_str),
                "preco_str": preco_str,
                "valor": br_to_float(valor_str),
                "valor_str": valor_str,
                "dc": dc,
                "linha_bruta": linha_bruta,
            })

            i = j + 4
        else:
            i += 1

    return operacoes


# =========================================================
# ====================== EXTRAÇÃO BM&F ====================
# =========================================================

def extrair_operacoes_pagina_bmf(texto: str):
    linhas = [l.strip() for l in texto.splitlines()]
    operacoes = []

    idx_cv = None
    for i, l in enumerate(linhas):
        if l == "C/V" and i + 8 < len(linhas):
            if (linhas[i + 1] == "Mercadoria"
                and linhas[i + 2] == "Vencimento"
                and linhas[i + 3] == "Quantidade"
                and "Preço" in linhas[i + 4]
                and "Tipo Negócio" in linhas[i + 5]):
                idx_cv = i
                break

    if idx_cv is None:
        return operacoes

    data_idx = idx_cv + 9

    while data_idx + 8 < len(linhas):
        cv = linhas[data_idx]
        if not cv:
            break
        if cv.upper().startswith("NOTA DE NEGOCIA"):
            break

        mercadoria_raw = linhas[data_idx + 1]
        data_venc = linhas[data_idx + 2]
        quantidade_str = linhas[data_idx + 3]
        preco_str = linhas[data_idx + 4]
        tipo_negocio = linhas[data_idx + 5]
        valor_str = linhas[data_idx + 6]
        dc = linhas[data_idx + 7]
        taxa_str = linhas[data_idx + 8]

        if cv not in ("C", "V"):
            break
        if not quantidade_str.isdigit():
            break

        tokens = mercadoria_raw.split()
        contrato = tokens[0].upper() if tokens else mercadoria_raw.upper()
        vcto_cod = tokens[1].upper() if len(tokens) >= 2 else ""

        try:
            quantidade = int(quantidade_str)
        except Exception:
            quantidade = quantidade_str

        descricao = f"{mercadoria_raw} {data_venc} {tipo_negocio}".strip()

        linha_bruta = " | ".join([
            cv, mercadoria_raw, data_venc,
            quantidade_str, preco_str,
            tipo_negocio, valor_str, dc, taxa_str
        ])

        operacoes.append({
            "layout_origem": "BMF",
            "q_negociacao": "",
            "cv": cv,
            "tipo_mercado": "BM&F",
            "descricao_completa": descricao,
            "obs": "",
            "obs_codigos": "",
            "obs_significado": "",
            "ativo": contrato,
            "quantidade": quantidade,
            "quantidade_str": quantidade_str,
            "preco": br_to_float(preco_str),
            "preco_str": preco_str,
            "valor": br_to_float(valor_str),
            "valor_str": valor_str,
            "dc": dc,
            "linha_bruta": linha_bruta,
            "bmf_mercadoria": mercadoria_raw,
            "bmf_vencimento_codigo": vcto_cod,
            "bmf_data_vencimento": data_venc,
            "bmf_tipo_negocio": tipo_negocio,
            "bmf_taxa_operacional_str": taxa_str,
            "bmf_taxa_operacional": br_to_float(taxa_str),
        })

        data_idx += 9

    return operacoes


def extrair_operacoes_pagina(texto: str):
    ops = extrair_operacoes_pagina_bovespa(texto)
    if ops:
        return ops
    return extrair_operacoes_pagina_bmf(texto)


# =========================================================
# ===================== PIPELINE PDF DIR ==================
# =========================================================

def extract_operations_from_pdfs(pdf_dir: Path) -> pd.DataFrame:
    pdf_dir = Path(pdf_dir)
    arquivos_pdf = [p for p in pdf_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]

    if not arquivos_pdf:
        logger.info("Nenhum PDF encontrado na pasta de entrada.")
        return pd.DataFrame()

    registros: list[dict[str, Any]] = []

    for pdf_path in arquivos_pdf:
        logger.info(f"Processando: {pdf_path.name}")

        try:
            reader = PdfReader(str(pdf_path))
        except Exception as e:
            logger.warning(f"Não foi possível ler o PDF {pdf_path.name}: {e}")
            continue

        for num_pagina, page in enumerate(reader.pages, start=1):
            try:
                texto = page.extract_text() or ""
            except Exception as e:
                logger.warning(f"Erro ao extrair texto (PDF={pdf_path.name}, pág={num_pagina}): {e}")
                continue

            if not texto.strip():
                continue

            header = extrair_header_pagina(texto)
            operacoes = extrair_operacoes_pagina(texto)

            if not operacoes:
                continue

            for op in operacoes:
                reg = {
                    "arquivo_pdf": pdf_path.name,
                    "pagina": num_pagina,
                    "numero_nota": header.get("numero_nota", ""),
                    "folha": header.get("folha", ""),
                    "data_pregao": header.get("data_pregao", ""),
                    "codigo_cliente": header.get("codigo_cliente", ""),
                    "codigo_cliente_detalhado": header.get("codigo_cliente_detalhado", ""),
                    "nome_cliente": header.get("nome_cliente", ""),
                    "cpf_cliente": header.get("cpf_cliente", ""),
                    "assessor": header.get("assessor", ""),
                }
                reg.update(op)

                chave = gerar_chave_unica(reg)
                reg["chave_unica"] = chave
                reg["id_operacao"] = gerar_id_operacao(chave)

                registros.append(reg)

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)
    logger.info(f"Operações extraídas: {len(df)}")
    return df


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    colunas_gerais = [
        "arquivo_pdf", "pagina",
        "numero_nota", "folha", "data_pregao",
        "codigo_cliente", "codigo_cliente_detalhado",
        "nome_cliente", "cpf_cliente", "assessor",
        "id_operacao", "chave_unica",
        "layout_origem",
    ]

    colunas_operacao_comum = [
        "cv", "tipo_mercado", "ativo",
        "descricao_completa", "obs",
        "obs_codigos", "obs_significado",
        "quantidade", "quantidade_str",
        "preco", "preco_str",
        "valor", "valor_str",
        "dc", "linha_bruta",
    ]

    colunas_bovespa = ["q_negociacao"]

    colunas_bmf = [
        "bmf_mercadoria",
        "bmf_vencimento_codigo",
        "bmf_data_vencimento",
        "bmf_tipo_negocio",
        "bmf_taxa_operacional_str",
        "bmf_taxa_operacional",
    ]

    colunas_gatilhos = [
        "is_cobertura", "is_daytrade", "is_minicontrato", "is_futuro_di", "is_opcao", "is_termo",
        "flag_alerta", "flag_alerta_int"
    ]

    coluna_ordem = colunas_gerais + colunas_operacao_comum + colunas_bovespa + colunas_bmf + colunas_gatilhos

    for col in coluna_ordem:
        if col not in df.columns:
            df[col] = None

    cols_finais = [c for c in coluna_ordem if c in df.columns] + [c for c in df.columns if c not in coluna_ordem]
    return df[cols_finais]
