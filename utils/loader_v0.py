"""
utils/loader.py
Funções de carregamento das três safras — compartilhadas entre todas as páginas.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Garante que a raiz do projeto está no sys.path (necessário para importar pipeline_2025)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


@st.cache_data(show_spinner=False)
def carregar_2023() -> dict:
    path = DATA_DIR / "2023" / "tabelas_analiticas" / "ta_faixa.csv"
    if not path.exists():
        return {"ok": False, "erro": f"Arquivo não encontrado: {path}", "ta_faixa": None}
    try:
        df = pd.read_csv(path, low_memory=False)
        df["safra"] = "2023/24"
        return {"ok": True, "ta_faixa": df}
    except Exception as e:
        return {"ok": False, "erro": str(e), "ta_faixa": None}


@st.cache_data(show_spinner=False)
def carregar_2024() -> dict:
    resultado = {"ok": True, "tabeloes": {}, "ta_faixa": None, "ta_densidade": None, "erros": []}
    nomes = [
        "tb_av1","tb_av2","tb_av3","tb_av4","tb_av5","tb_av6","tb_av7",
        "tb_av4_detalhe","tb_av5_detalhe","tb_av5_graos","tb_av7_detalhe",
    ]
    for nome in nomes:
        for tipo in ["faixa", "densidade"]:
            path = DATA_DIR / "2024" / f"tabeloes_{tipo}" / f"{nome}_{tipo}.csv"
            if path.exists():
                try:
                    df = pd.read_csv(path, low_memory=False)
                    resultado["tabeloes"][f"{nome}_{tipo}"] = df
                except Exception as e:
                    resultado["erros"].append(f"{nome}_{tipo}: {e}")

    for nome_ta in ["ta_faixa", "ta_densidade"]:
        path = DATA_DIR / "2024" / "tabelas_analiticas" / f"{nome_ta}.csv"
        if path.exists():
            try:
                df = pd.read_csv(path, low_memory=False)
                resultado[nome_ta] = df
            except Exception as e:
                resultado["erros"].append(f"{nome_ta}: {e}")

    if not resultado["tabeloes"] and resultado["ta_faixa"] is None:
        resultado["ok"] = False
        resultado["erros"].append("Nenhum arquivo de 2024 encontrado em data/2024/")

    return resultado


def carregar_2025() -> dict:
    try:
        from pipeline_2025 import rodar_pipeline
        dados = rodar_pipeline()
        return {"ok": True, **dados}
    except Exception as e:
        return {"ok": False, "erro": str(e)}


def carregar_todas_safras() -> dict:
    d23 = carregar_2023()
    d24 = carregar_2024()
    d25 = carregar_2025()

    frames_faixa     = []
    frames_densidade = []

    if d23["ok"] and d23.get("ta_faixa") is not None:
        frames_faixa.append(d23["ta_faixa"])
    if d24["ok"]:
        if d24.get("ta_faixa")     is not None: frames_faixa.append(d24["ta_faixa"])
        if d24.get("ta_densidade") is not None: frames_densidade.append(d24["ta_densidade"])
    if d25["ok"]:
        if d25.get("ta_faixa")     is not None: frames_faixa.append(d25["ta_faixa"])
        if d25.get("ta_densidade") is not None: frames_densidade.append(d25["ta_densidade"])

    return {
        "2023": d23, "2024": d24, "2025": d25,
        "ta_faixa":     pd.concat(frames_faixa,     ignore_index=True) if frames_faixa     else pd.DataFrame(),
        "ta_densidade": pd.concat(frames_densidade, ignore_index=True) if frames_densidade else pd.DataFrame(),
    }
