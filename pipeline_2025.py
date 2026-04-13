"""
pipeline_2025.py
Replica o pipeline do notebook jaum_DTC_2025_otimizado_v2.ipynb
Adaptado para Streamlit: usa st.secrets e st.cache_data
"""

import warnings
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from supabase import create_client

warnings.filterwarnings("ignore")

# ── Emails de teste a remover ─────────────────────────────────────────────────
EMAILS_REMOVER = {
    "andrestine@email.com",
    "stine@email.com",
    "stine2@email.com",
    "teste@email.com",
    "raullanconi@gmail.com",
    "augusto.frizon@gmail.com",
    "aferreira@stineseed.com",
    "eng.andre.julio@gmail.com",
}

BASE_DIR = Path(__file__).parent


# ── Conexão Supabase ──────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


# ── Extração bruta do Supabase ────────────────────────────────────────────────
def _extrair(supabase, nome: str) -> pd.DataFrame:
    response = supabase.table(nome).select("*").execute()
    return pd.DataFrame(response.data)


TABELAS = [
    "av1TratamentoSoja", "av1DetalheTratamentoSoja",
    "av2TratamentoSoja", "av2DetalheTratamentoSoja",
    "av3TratamentoSoja", "av3DetalheTratamentoSoja",
    "av4TratamentoSoja", "av4DetalheTratamentoSoja",
    "av5TratamentoSoja", "av5DetalheTratamentoSoja",
    "av6TratamentoSoja", "av6DetalheTratamentoSoja",
    "av7TratamentoSoja", "av7DetalheTratamentoSoja",
    "avaliacao", "fazenda", "cidade",
    "estado", "pais", "tratamentoBase", "users",
]


# ── Transformações de apoio ───────────────────────────────────────────────────
def _proc_estado(df):
    df = df.drop(columns=[c for c in ["firebase","dataSync","acao"] if c in df.columns])
    return df.rename(columns={"codigoEstado": "nomeEstado", "nomeEstado": "siglaEstado"})


def _calcular_safra(data_plantio):
    dt = pd.to_datetime(data_plantio, errors="coerce")
    if pd.isna(dt) or dt.year < 2000:
        return np.nan
    mes, ano = dt.month, dt.year
    return f"{ano}/{str(ano+1)[-2:]}" if mes >= 8 else f"{ano-1}/{str(ano)[-2:]}"


def _calcular_epoca(data_plantio):
    dt = pd.to_datetime(data_plantio, errors="coerce")
    if pd.isna(dt) or dt.year < 2000:
        return np.nan
    return "Safra" if dt.month in [9, 10, 11, 12] else "Safrinha"


def _normalizar_nome(nome_cidade):
    nome_norm = (
        unicodedata.normalize("NFKD", str(nome_cidade))
        .encode("ascii", "ignore")
        .decode("ascii")
        .upper()
    )
    stopwords = {"DE","DO","DA","DOS","DAS","E","O","A"}
    palavras = [p for p in nome_norm.replace("-", " ").split() if p not in stopwords]
    return "".join(palavras)


def _gerar_cod_cidade(nome_cidade, sigla_estado, n_chars=5):
    if pd.isna(nome_cidade) or pd.isna(sigla_estado):
        return np.nan
    return _normalizar_nome(nome_cidade)[:n_chars] + sigla_estado.upper()


# ── Processamento av1 ─────────────────────────────────────────────────────────
def _proc_av1(dfs):
    df = dfs["av1TratamentoSoja"].copy()
    df = df.drop(columns=[c for c in ["firebase","dataSync","acao","cultivar"] if c in df.columns])
    df["gm"] = pd.to_numeric(df["gm"], errors="coerce")
    df = df.rename(columns={
        "nota0QualidadeInicialPlot":    "notaQualidadeInicial",
        "nota1UniformidadeEmergencia":  "notaUniformidade",
        "nota2DensidadePlantas":        "notaDensidade",
        "nota3VigorPlantas":            "notaVigor",
        "nota4PresencaDaninhas":        "notaDaninhas",
        "nota5PresencaPragas":          "notaPragas",
        "nota6PresencaDoencas":         "notaDoencas",
        "nota7HomogenidadeCrescimento": "notaHomogenidade",
        "nota8EstadoGeralSolo":         "notaSolo",
    })
    df["notaMedia"] = df[["notaUniformidade","notaDensidade","notaVigor",
                           "notaDaninhas","notaPragas","notaDoencas",
                           "notaHomogenidade","notaSolo"]].mean(axis=1)
    cols = ["uuid","avaliacaoRef","idBaseRef","tipoTeste","nome","populacao","gm","indexTratamento",
            "notaUniformidade","notaDensidade","notaVigor","notaDaninhas","notaPragas",
            "notaDoencas","notaHomogenidade","notaSolo","notaQualidadeInicial","notaMedia"]
    return df[[c for c in cols if c in df.columns]]


# ── Processamento av2 ─────────────────────────────────────────────────────────
def _proc_av2(dfs):
    df = dfs["av2TratamentoSoja"].copy()
    df = df.drop(columns=[c for c in ["firebase","dataSync","acao","cultivar"] if c in df.columns])
    df["gm"] = pd.to_numeric(df["gm"], errors="coerce")
    df = df.rename(columns={
        "nota1NivelPhytophthora":  "notaPhytophthora",
        "nota2NivelAnomalia":      "notaAnomalia",
        "nota3NivelOidio":         "notaOidio",
        "nota4NivelManchaParda":   "notaManchaParda",
        "nota5NivelManchaAlvo":    "notaManchaAlvo",
        "nota6NivelManchaOlhoRa":  "notaManchaOlhoRa",
        "nota7NivelCercospora":    "notaCercospora",
        "nota8NivelAntracnose":    "notaAntracnose",
        "nota8NivelDfc":           "notaDFC",       # presente em 2024 e 2025
    })
    # notaDFC: campo direto do Supabase (2024/2025), incluído na lista de doenças
    doencas = ["notaPhytophthora","notaAnomalia","notaOidio","notaManchaParda",
               "notaManchaAlvo","notaManchaOlhoRa","notaCercospora","notaAntracnose","notaDFC"]
    for col in doencas:
        if col in df.columns:
            df[f"inc_{col}"] = (df[col].notna() & (df[col] > 0)).astype(int)
            df[f"class_{col}"] = pd.cut(
                df[col], bins=[-1,0,2,4,np.inf],
                labels=["Ausente","Baixo","Médio","Alto"]
            )
    # notaMedia = média das doenças disponíveis
    df["notaMedia"] = df[[c for c in doencas if c in df.columns]].mean(axis=1)
    return df


# ── Processamento av3 ─────────────────────────────────────────────────────────
def _proc_av3(dfs):
    df = dfs["av3TratamentoSoja"].copy()
    df = df.drop(columns=[c for c in ["firebase","dataSync","acao","cultivar"] if c in df.columns])
    df["gm"] = pd.to_numeric(df["gm"], errors="coerce")
    for col in ["dataInicioFloracao","dataFimFloracao"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit="s", errors="coerce").dt.date
    for col in ["corFlor","habitoCrescimento"]:
        if col in df.columns:
            df[col] = df[col].replace("null", np.nan)
    if "corFlor" in df.columns:
        df["corFlor"] = df["corFlor"].str.split(" - ").str[0].str.strip()
        df["corFlorNome"]  = df["corFlor"].map({"R":"Roxa","B":"Branca","MB":"Maioria Branca","MR":"Maioria Roxa"})
        df["corFlorGrupo"] = df["corFlor"].map({"R":"Roxa","MR":"Roxa","B":"Branca","MB":"Branca"})
    if "habitoCrescimento" in df.columns:
        df["habitoCrescimentoNome"]  = df["habitoCrescimento"].map({"I":"Indeterminado","D":"Determinado","SI":"Semi-Indeterminado"})
        df["habitoCrescimentoGrupo"] = df["habitoCrescimento"].map({"I":"Indeterminado","D":"Determinado","SI":"Indeterminado"})
    if "corPub" in df.columns:
        df["corPubNome"]  = df["corPub"].map({"C":"Cinza","MC":"Maioria Cinza","M":"Marrom","MM":"Maioria Marrom"})
        df["corPubGrupo"] = df["corPub"].map({"C":"Cinza","MC":"Cinza","M":"Marrom","MM":"Marrom"})
    return df


# ── Processamento av4 ─────────────────────────────────────────────────────────
def _proc_av4(dfs):
    df = dfs["av4TratamentoSoja"].copy()
    df = df.drop(columns=[c for c in ["firebase","dataSync","acao","cultivar"] if c in df.columns])
    df["gm"] = pd.to_numeric(df["gm"], errors="coerce")
    rename_map = {}
    for i in range(1, 6):
        rename_map[f"planta{i}CorPubescencia"]         = f"p{i}_corPub"
        rename_map[f"planta{i}Engalhamento"]            = f"p{i}_ENG"
        rename_map[f"planta{i}AlturaInsercaoPrimVagem"] = f"p{i}_AIV"
        rename_map[f"planta{i}AlturaPlanta"]            = f"p{i}_ALT"
    df = df.rename(columns=rename_map)
    for col in [f"p{i}_corPub" for i in range(1, 6)]:
        if col in df.columns:
            df[col] = df[col].replace("null", np.nan).str.split(" - ").str[0].str.strip()
    pub_cols = [f"p{i}_corPub" for i in range(1, 6) if f"p{i}_corPub" in df.columns]
    if pub_cols:
        df["corPub"]      = df[pub_cols].mode(axis=1)[0]
        df["corPubNome"]  = df["corPub"].map({"C":"Cinza","MC":"Maioria Cinza","M":"Marrom","MM":"Maioria Marrom"})
        df["corPubGrupo"] = df["corPub"].map({"C":"Cinza","MC":"Cinza","M":"Marrom","MM":"Marrom"})
    for sigla in ["ENG","AIV","ALT"]:
        colunas = [f"p{i}_{sigla}" for i in range(1, 6) if f"p{i}_{sigla}" in df.columns]
        df[f"n_{sigla}"]     = df[colunas].count(axis=1)
        df[f"media_{sigla}"] = df[colunas].mean(axis=1)
        df[f"std_{sigla}"]   = df[colunas].std(axis=1)
    # Detalhe por planta
    cols_id = ["uuid","avaliacaoRef","idBaseRef","tipoTeste","nome","populacao","gm","indexTratamento"]
    registros = []
    for i in range(1, 6):
        temp = df[cols_id + [c for c in [f"p{i}_ENG",f"p{i}_AIV",f"p{i}_ALT"] if c in df.columns]].copy()
        temp = temp.rename(columns={f"p{i}_ENG":"ENG",f"p{i}_AIV":"AIV",f"p{i}_ALT":"ALT"})
        temp["planta"] = i
        registros.append(temp)
    df_detalhe = pd.concat(registros, ignore_index=True)
    colunas_planta = [c for c in df.columns if c.startswith("p") and "_" in c]
    df = df.drop(columns=colunas_planta)
    return df, df_detalhe


# ── Processamento av5 ─────────────────────────────────────────────────────────
def _proc_av5(dfs):
    df = dfs["av5TratamentoSoja"].copy()
    df = df.drop(columns=[c for c in ["firebase","dataSync","acao","cultivar"] if c in df.columns])
    df["gm"] = pd.to_numeric(df["gm"], errors="coerce")
    rename_map = {}
    for i in range(1, 6):
        rename_map[f"planta{i}NumeroRamosVegetativos"]    = f"p{i}_RV"
        rename_map[f"planta{i}NumeroRamosReprodutivos"]   = f"p{i}_RR"
        rename_map[f"planta{i}NumeroVagensTercoSuperior"] = f"p{i}_VTS"
        rename_map[f"planta{i}NumeroVagensTercoMedio"]    = f"p{i}_VTM"
        rename_map[f"planta{i}NumeroVagensTercoInferior"] = f"p{i}_VTI"
        for t in ["TS","TM","TI"]:
            for g in range(1, 5):
                rename_map[f"planta{i}NumGraoVagem{t}{g}"] = f"p{i}_{t}{g}"
    df = df.rename(columns=rename_map)
    cols_id = ["uuid","avaliacaoRef","idBaseRef","tipoTeste","nome","populacao","gm","indexTratamento"]
    for sigla in ["RV","RR","VTS","VTM","VTI"]:
        colunas = [f"p{i}_{sigla}" for i in range(1, 6) if f"p{i}_{sigla}" in df.columns]
        df[f"n_{sigla}"]     = df[colunas].count(axis=1)
        df[f"media_{sigla}"] = df[colunas].mean(axis=1).round(1)
        df[f"std_{sigla}"]   = df[colunas].std(axis=1).round(1)
    df["media_totalVagens"] = df[["media_VTS","media_VTM","media_VTI"]].sum(axis=1)
    # Detalhe por planta
    registros = []
    for i in range(1, 6):
        cols_p = [c for c in [f"p{i}_RV",f"p{i}_RR",f"p{i}_VTS",f"p{i}_VTM",f"p{i}_VTI"] if c in df.columns]
        temp = df[cols_id + cols_p].copy()
        temp = temp.rename(columns={f"p{i}_RV":"RV",f"p{i}_RR":"RR",f"p{i}_VTS":"VTS",f"p{i}_VTM":"VTM",f"p{i}_VTI":"VTI"})
        temp["planta"] = i
        for col in ["VTS","VTM","VTI"]:
            if col not in temp.columns:
                temp[col] = np.nan
        temp["totalVagens"] = temp[["VTS","VTM","VTI"]].sum(axis=1)
        registros.append(temp)
    df_detalhe = pd.concat(registros, ignore_index=True)
    # Grãos por terço
    registros_graos = []
    for i in range(1, 6):
        temp = df[cols_id].copy()
        temp["planta"] = i
        for t in ["TS","TM","TI"]:
            cg = [f"p{i}_{t}{g}" for g in range(1, 5) if f"p{i}_{t}{g}" in df.columns]
            temp[f"totalVagens{t}"] = df[cg].sum(axis=1) if cg else np.nan
            if cg:
                temp[f"vagPond{t}"] = sum(
                    df[f"p{i}_{t}{g}"] * g for g in range(1, 5) if f"p{i}_{t}{g}" in df.columns
                )
                temp[f"mediaGrao{t}"] = (
                    temp[f"vagPond{t}"] / temp[f"totalVagens{t}"].replace(0, np.nan)
                ).round(1)
        registros_graos.append(temp)
    df_graos = pd.concat(registros_graos, ignore_index=True)
    colunas_planta = [c for c in df.columns if c.startswith("p") and "_" in c]
    df = df.drop(columns=colunas_planta)
    return df, df_detalhe, df_graos


# ── Processamento av6 ─────────────────────────────────────────────────────────
def _proc_av6(dfs):
    df = dfs["av6TratamentoSoja"].copy()
    df = df.drop(columns=[c for c in ["firebase","dataSync","acao","cultivar"] if c in df.columns])
    df["gm"] = pd.to_numeric(df["gm"], errors="coerce")
    if "dataMaturacaoFisiologica" in df.columns:
        df["dataMaturacaoFisiologica"] = pd.to_datetime(df["dataMaturacaoFisiologica"], unit="s", errors="coerce").dt.date
    df = df.rename(columns={
        "dataMaturacaoFisiologica": "DMF",
        "nivelAcamenamento":        "notaAC",
        "aberturaVagens":           "notaAV",
        "qualidadeFinalPlot":       "notaQF",
        "gmVisual":                 "GM_visual",
    })
    return df


# ── Processamento av7 ─────────────────────────────────────────────────────────
def _proc_av7(dfs):
    df = dfs["av7TratamentoSoja"].copy()
    df = df.drop(columns=[c for c in ["firebase","dataSync","acao","cultivar"] if c in df.columns])
    df["gm"] = pd.to_numeric(df["gm"], errors="coerce")
    cols_id = ["uuid","avaliacaoRef","idBaseRef","tipoTeste","nome","populacao","gm","indexTratamento"]
    rename_map = {}
    for i in range(1, 9):
        rename_map[f"numeroPlantas10Metros{i}a"]      = f"p{i}_plantas"
        rename_map[f"numeroPlantas10Metros{i}aFinal"] = f"p{i}_plantasFinal"
    df = df.rename(columns=rename_map)
    for sigla in ["plantas","plantasFinal"]:
        colunas = [f"p{i}_{sigla}" for i in range(1, 9) if f"p{i}_{sigla}" in df.columns]
        # Substituir zeros por NaN — campo não preenchido não deve entrar na média
        df[colunas] = df[colunas].replace(0, np.nan)
        df[f"n_{sigla}"]     = df[colunas].count(axis=1)
        df[f"media_{sigla}"] = df[colunas].mean(axis=1).round(1)
        df[f"std_{sigla}"]   = df[colunas].std(axis=1).round(1)
    mask = df["n_plantas"] > 0
    df["pop_plantas_ha"] = np.where(mask, (df["media_plantas"] * (10000 / 1.5)).round(0), np.nan)
    df["pop_plantas_ha"] = df["pop_plantas_ha"].astype("Int64")
    mask_f = df["n_plantasFinal"] > 0
    df["pop_plantasFinal_ha"] = np.where(mask_f, (df["media_plantasFinal"] * (10000 / 1.5)).round(0), np.nan)
    df["pop_plantasFinal_ha"] = df["pop_plantasFinal_ha"].astype("Int64")
    if "numeroLinhas" in df.columns and "comprimentoLinha" in df.columns:
        df["area_parcela"]   = df["numeroLinhas"] * df["comprimentoLinha"] * 0.5
        df["peso_corrigido"] = df["pesoParcela"] * ((100 - df["umidadeParcela"]) / (100 - 13))
        mask_v = (df["area_parcela"] > 0) & (df["umidadeParcela"].between(0, 100))
        df["kg_ha"] = np.where(mask_v, (df["peso_corrigido"] / df["area_parcela"] * 10000).round(1), np.nan)
        df["sc_ha"] = np.where(mask_v, (df["kg_ha"] / 60).round(1), np.nan)
    if "pesoMilGraos" in df.columns and "umidadeAmostraPesoMilGraos" in df.columns:
        mask_pmg = (df["umidadeAmostraPesoMilGraos"].between(0, 100)) & (df["pesoMilGraos"] > 0)
        df["pesoMilGraos_corrigido"] = np.where(
            mask_pmg,
            (df["pesoMilGraos"] * ((100 - df["umidadeAmostraPesoMilGraos"]) / (100 - 13))).round(1),
            np.nan,
        )
    # Detalhe por subamostra
    registros = []
    for i in range(1, 9):
        cols_p = [c for c in [f"p{i}_plantas",f"p{i}_plantasFinal"] if c in df.columns]
        temp = df[cols_id + cols_p].copy()
        temp = temp.rename(columns={f"p{i}_plantas":"plantas",f"p{i}_plantasFinal":"plantasFinal"})
        temp["subamostra"] = i
        registros.append(temp)
    df_detalhe = pd.concat(registros, ignore_index=True)
    colunas_sub = [f"p{i}_{s}" for i in range(1, 9) for s in ["plantas","plantasFinal"]]
    df = df.drop(columns=[c for c in colunas_sub if c in df.columns])
    return df, df_detalhe


# ── Montagem das tabelas analíticas ──────────────────────────────────────────
CHAVE    = ["fazendaRef","idBaseRef","tipoTeste","indexTratamento"]
CONTEXTO = {
    "uuid","avaliacaoRef","idBaseRef","fazendaRef","dtcResponsavelRef",
    "cod_fazenda","nomeFazenda","cidade_nome","estado_sigla","regiao_macro","regiao_micro",
    "safra","epoca","dataPlantioSoja","dataColheitaSoja","latitude","longitude","altitude",
    "nomeResponsavel","nome","dePara","status_material","tipoTeste","indexTratamento","populacao","gm",
}


def _montar_analitica(resultados: dict, tipo: str) -> pd.DataFrame:
    nome_base = max(resultados, key=lambda k: len(resultados[k]))
    base = resultados[nome_base].copy()
    for nome_av, av in resultados.items():
        if nome_av == nome_base:
            continue
        cols = [c for c in av.columns if c not in CONTEXTO]
        df_join = av[CHAVE + cols].copy()
        if "notaMedia" in df_join.columns:
            df_join = df_join.rename(columns={"notaMedia": f"notaMedia_{nome_av}"})
        base = base.merge(df_join, on=CHAVE, how="left")
    return base


# ── Pipeline principal ────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def rodar_pipeline() -> dict:
    """
    Executa o pipeline completo de 2025 a partir do Supabase.
    Retorna dict com tabeloes, ta_faixa, ta_densidade e av_status.
    """
    supabase = get_supabase()

    # 1. Extração bruta
    dfs = {t: _extrair(supabase, t) for t in TABELAS}

    # 2. Tabelas de apoio
    df_pais    = dfs["pais"].drop(columns=[c for c in ["firebase","dataSync","acao"] if c in dfs["pais"].columns])
    df_estado  = _proc_estado(dfs["estado"])
    df_cidade  = dfs["cidade"].drop(columns=[c for c in ["firebase","dataSync","acao"] if c in dfs["cidade"].columns])

    # 3. Fazendas — remove usuários teste
    uuids_remover = dfs["users"][dfs["users"]["email"].isin(EMAILS_REMOVER)]["uuid"].tolist()
    df_fazenda = dfs["fazenda"].copy()
    df_fazenda = df_fazenda[~df_fazenda["dtcResponsavelRef"].isin(uuids_remover)].copy()
    df_fazenda = df_fazenda.drop(columns=[c for c in ["firebase","dataSync","acao","rcResponsavel","regional","safra","epoca","hide"] if c in df_fazenda.columns])
    for col in ["dataPlantio","dataColheita"]:
        if col in df_fazenda.columns:
            df_fazenda[col] = pd.to_datetime(df_fazenda[col], unit="s", errors="coerce").dt.date
    df_fazenda = df_fazenda.rename(columns={"dataPlantio":"dataPlantioSoja","dataColheita":"dataColheitaSoja"})
    df_fazenda = df_fazenda[df_fazenda.get("isSoja", pd.Series([True]*len(df_fazenda))) == True].copy() if "isSoja" in df_fazenda.columns else df_fazenda

    # Joins cidade + estado + regiões
    cidade_lookup = df_cidade.merge(
        df_estado[["uuid","siglaEstado","nomeEstado"]].rename(columns={"uuid":"estadoRef"}),
        on="estadoRef", how="left"
    )[["uuid","nomeCidade","siglaEstado","nomeEstado"]].rename(columns={"uuid":"cidadeRef"})
    cidade_lookup["cidade_siglaEstado"] = cidade_lookup["nomeCidade"] + "_" + cidade_lookup["siglaEstado"]
    df_fazenda = df_fazenda.merge(cidade_lookup, on="cidadeRef", how="left")
    df_fazenda = df_fazenda.rename(columns={"nomeCidade":"cidade_nome","siglaEstado":"estado_sigla","nomeEstado":"estado_nome"})

    # Regiões
    path_regioes = BASE_DIR / "config" / "base_municipios_regioes_soja_milho.xlsx"
    if path_regioes.exists():
        df_regioes = pd.read_excel(path_regioes)
        df_regioes = df_regioes.drop(columns=[c for c in ["ibge","latitude","longitude","microMilho","macroMilho"] if c in df_regioes.columns])
        df_fazenda["cidade_siglaEstado"] = df_fazenda["cidade_nome"].astype(str) + "_" + df_fazenda["estado_sigla"].astype(str)
        df_fazenda = df_fazenda.merge(df_regioes[["cidade_siglaEstado","macroSoja","microSoja"]], on="cidade_siglaEstado", how="left")
        df_fazenda = df_fazenda.rename(columns={"macroSoja":"regiao_macro","microSoja":"regiao_micro"})
        df_fazenda = df_fazenda.drop(columns=["cidade_siglaEstado"], errors="ignore")

    # Safra + época
    df_fazenda["safra"] = df_fazenda["dataPlantioSoja"].apply(_calcular_safra)
    df_fazenda["epoca"] = df_fazenda["dataPlantioSoja"].apply(_calcular_epoca)

    # cod_fazenda — lógica hierárquica M4-401-A-25
    df_fazenda["nomeFazenda"] = df_fazenda.get("nomeFazenda", df_fazenda.get("nome", ""))

    def _extrair_cod_macro(regiao_macro):
        """MACRO IV → M4 | Não Identificado ou nulo → M0"""
        if pd.isna(regiao_macro) or "IDENTIFICADO" in str(regiao_macro).upper():
            return "M0"
        mapa = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6"}
        val = str(regiao_macro).strip().upper().replace("MACRO", "").strip()
        return "M" + mapa.get(val, val)

    def _extrair_cod_micro(regiao_micro):
        """REC 401 → 401 | Não Identificado ou nulo → 000"""
        import re as _re
        if pd.isna(regiao_micro) or "IDENTIFICADO" in str(regiao_micro).upper():
            return "000"
        numeros = _re.findall(r"\d+", str(regiao_micro))
        return numeros[0] if numeros else "000"

    import string as _string
    _letras = list(_string.ascii_uppercase)

    def _atribuir_letra(grupo_df):
        fazendas = sorted(grupo_df["nomeFazenda"].dropna().unique())
        mapa = {f: (_letras[i] if i < 26 else f"Z{i - 25}") for i, f in enumerate(fazendas)}
        return grupo_df["nomeFazenda"].map(mapa)

    df_fazenda["_cod_macro"] = df_fazenda["regiao_macro"].apply(_extrair_cod_macro)
    df_fazenda["_cod_micro"] = df_fazenda["regiao_micro"].apply(_extrair_cod_micro)
    df_fazenda["_ano"] = (
        pd.to_datetime(df_fazenda["dataPlantioSoja"], errors="coerce")
        .dt.year
        .apply(lambda y: str(int(y))[-2:] if pd.notna(y) else "00")
    )
    df_fazenda["_grupo"] = (
        df_fazenda["_cod_macro"] + "-" +
        df_fazenda["_cod_micro"] + "-" +
        df_fazenda["_ano"]
    )
    df_fazenda["_letra"] = (
        df_fazenda
        .groupby("_grupo", group_keys=False)
        .apply(_atribuir_letra)
    )
    df_fazenda["cod_fazenda"] = (
        df_fazenda["_cod_macro"] + "-" +
        df_fazenda["_cod_micro"] + "-" +
        df_fazenda["_letra"] + "-" +
        df_fazenda["_ano"]
    )
    df_fazenda = df_fazenda.drop(columns=["_cod_macro", "_cod_micro", "_ano", "_grupo", "_letra"])

    # 4. Avaliação
    df_avaliacao = dfs["avaliacao"].copy()
    df_avaliacao = df_avaliacao[df_avaliacao["fazendaRef"].isin(df_fazenda["uuid"])].copy()
    df_avaliacao = df_avaliacao.drop(columns=[c for c in ["firebase","dataSync","acao","rcResponsavel"] if c in df_avaliacao.columns])
    if "modificadoEm" in df_avaliacao.columns:
        df_avaliacao["modificadoEm"] = pd.to_datetime(df_avaliacao["modificadoEm"], unit="s", errors="coerce")
    if "dataAgendamento" in df_avaliacao.columns:
        df_avaliacao["dataAgendamento"] = pd.to_datetime(df_avaliacao["dataAgendamento"], unit="s", errors="coerce").dt.date

    # 5. Usuários
    df_users = dfs["users"].copy()
    df_users = df_users[~df_users["email"].isin(EMAILS_REMOVER)].copy()
    df_users["displayName"] = df_users["displayName"].str.strip()

    # 6. tratamentoBase + dePara
    df_tratamentoBase = dfs["tratamentoBase"].copy()
    df_tratamentoBase = df_tratamentoBase.drop(columns=[c for c in ["firebase","dataSync","acao","tipoTeste","pop","gm","regional"] if c in df_tratamentoBase.columns])
    if "cultura" in df_tratamentoBase.columns:
        df_tratamentoBase = df_tratamentoBase[df_tratamentoBase["cultura"] == "soja"].drop(columns=["cultura"])
    path_depara = BASE_DIR / "config" / "depara_materiais_base.csv"
    if path_depara.exists():
        df_depara = pd.read_csv(path_depara, usecols=["nome","dePara","status_material"])
        df_tratamentoBase = df_tratamentoBase.merge(df_depara, on="nome", how="left")

    # 7. Processa cada avaliação
    df_av1 = _proc_av1(dfs)
    df_av2 = _proc_av2(dfs)
    df_av3 = _proc_av3(dfs)
    df_av4, df_av4_detalhe = _proc_av4(dfs)
    df_av5, df_av5_detalhe, df_av5_graos = _proc_av5(dfs)
    df_av6 = _proc_av6(dfs)
    df_av7, df_av7_detalhe = _proc_av7(dfs)

    # 8. Filtra avaliações válidas
    avaliacoes_validas = set(df_avaliacao[df_avaliacao["fazendaRef"].isin(df_fazenda["uuid"])]["uuid"])
    for df_ref in [df_av1,df_av2,df_av3,df_av4,df_av5,df_av6,df_av7,
                   df_av4_detalhe,df_av5_detalhe,df_av5_graos,df_av7_detalhe]:
        mask = df_ref["avaliacaoRef"].isin(avaliacoes_validas)
        df_ref.drop(df_ref[~mask].index, inplace=True)
        df_ref.reset_index(drop=True, inplace=True)

    # 9. Lookups e enriquecimento
    user_lookup = df_users[["uuid","displayName"]].rename(columns={"uuid":"dtcResponsavelRef","displayName":"nomeResponsavel"})
    av_lookup   = df_avaliacao[["uuid","fazendaRef"]].rename(columns={"uuid":"avaliacaoRef"})

    def enriquecer(df_av):
        df = df_av.copy()
        df = df.merge(av_lookup, on="avaliacaoRef", how="left")
        df = df.merge(
            df_fazenda[["uuid","cod_fazenda","nomeFazenda","cidade_nome","estado_sigla",
                        "regiao_macro","regiao_micro","safra","epoca","dtcResponsavelRef",
                        "dataPlantioSoja","dataColheitaSoja","latitude","longitude","altitude"]
                      ].rename(columns={"uuid":"fazendaRef"}),
            on="fazendaRef", how="left"
        )
        df = df.merge(user_lookup, on="dtcResponsavelRef", how="left")
        df = df.merge(
            df_tratamentoBase[["uuid","dePara","status_material"]].rename(columns={"uuid":"idBaseRef"}),
            on="idBaseRef", how="left"
        )
        cols_ids      = ["uuid","avaliacaoRef","idBaseRef","fazendaRef","dtcResponsavelRef"]
        cols_contexto = ["cod_fazenda","nomeFazenda","cidade_nome","estado_sigla",
                         "regiao_macro","regiao_micro","safra","epoca",
                         "dataPlantioSoja","dataColheitaSoja","latitude","longitude","altitude",
                         "nomeResponsavel","nome","dePara","status_material",
                         "tipoTeste","indexTratamento","populacao","gm"]
        cols_metricas = [c for c in df.columns if c not in cols_ids + cols_contexto]
        return df[[c for c in cols_ids + cols_contexto + cols_metricas if c in df.columns]]

    tb_av1         = enriquecer(df_av1)
    tb_av2         = enriquecer(df_av2)
    tb_av3         = enriquecer(df_av3)
    tb_av4         = enriquecer(df_av4)
    tb_av5         = enriquecer(df_av5)
    tb_av6         = enriquecer(df_av6)
    tb_av7         = enriquecer(df_av7)
    tb_av4_detalhe = enriquecer(df_av4_detalhe)
    tb_av5_detalhe = enriquecer(df_av5_detalhe)
    tb_av5_graos   = enriquecer(df_av5_graos)
    tb_av7_detalhe = enriquecer(df_av7_detalhe)

    tabeloes = {
        "tb_av1": tb_av1, "tb_av2": tb_av2, "tb_av3": tb_av3,
        "tb_av4": tb_av4, "tb_av5": tb_av5, "tb_av6": tb_av6, "tb_av7": tb_av7,
        "tb_av4_detalhe": tb_av4_detalhe, "tb_av5_detalhe": tb_av5_detalhe,
        "tb_av5_graos": tb_av5_graos, "tb_av7_detalhe": tb_av7_detalhe,
    }

    # 10. Calcula dias_ate_DMF no tb_av6 — ANTES do split
    if "DMF" in tb_av6.columns and "dataPlantioSoja" in tb_av6.columns:
        tb_av6["dias_ate_DMF"] = (
            pd.to_datetime(tb_av6["DMF"], errors="coerce") -
            pd.to_datetime(tb_av6["dataPlantioSoja"], errors="coerce")
        ).dt.days.astype("Int64")
        tabeloes["tb_av6"] = tb_av6  # atualiza no dict

    # 11. Split faixa / densidade
    resultados = {}
    for nome, tb in tabeloes.items():
        if "tipoTeste" in tb.columns:
            resultados[f"{nome}_faixa"]     = tb[tb["tipoTeste"] == "Faixa"].reset_index(drop=True)
            resultados[f"{nome}_densidade"] = tb[tb["tipoTeste"] == "Densidade"].reset_index(drop=True)
        else:
            resultados[f"{nome}_faixa"]     = tb.copy()
            resultados[f"{nome}_densidade"] = tb.iloc[0:0].copy()

    # 12. Tabelas analíticas (dias_ate_DMF já está em tb_av6_faixa/densidade)
    ta_faixa = _montar_analitica({
        "av1": resultados["tb_av1_faixa"], "av2": resultados["tb_av2_faixa"],
        "av3": resultados["tb_av3_faixa"], "av4": resultados["tb_av4_faixa"],
        "av5": resultados["tb_av5_faixa"], "av6": resultados["tb_av6_faixa"],
        "av7": resultados["tb_av7_faixa"],
    }, tipo="Faixa")

    ta_densidade = _montar_analitica({
        "av1": resultados["tb_av1_densidade"], "av2": resultados["tb_av2_densidade"],
        "av3": resultados["tb_av3_densidade"], "av4": resultados["tb_av4_densidade"],
        "av5": resultados["tb_av5_densidade"], "av6": resultados["tb_av6_densidade"],
        "av7": resultados["tb_av7_densidade"],
    }, tipo="Densidade")

    # 13. av_status
    df_av_status = df_avaliacao[df_avaliacao.get("cultura", pd.Series(["soja"]*len(df_avaliacao))) == "soja"].copy() if "cultura" in df_avaliacao.columns else df_avaliacao.copy()
    df_av_status = df_av_status.merge(
        df_fazenda[["uuid","cod_fazenda","nomeFazenda","cidade_nome","estado_sigla",
                    "regiao_macro","regiao_micro","safra","epoca"]].rename(columns={"uuid":"fazendaRef"}),
        on="fazendaRef", how="left"
    )
    if "tipoAvaliacao" in df_av_status.columns:
        df_av_status["av"] = "av" + df_av_status["tipoAvaliacao"].str.extract(r"^(\d+)")[0]
    if "faseFenologica" in df_av_status.columns:
        df_av_status["faseFenologica"] = df_av_status["faseFenologica"].replace("null", np.nan)

    # 14. Tabelas detalhe enriquecidas (fotos + comentários)
    TABELAS_DETALHE = [
        "av1DetalheTratamentoSoja", "av2DetalheTratamentoSoja",
        "av3DetalheTratamentoSoja", "av4DetalheTratamentoSoja",
        "av5DetalheTratamentoSoja", "av6DetalheTratamentoSoja",
        "av7DetalheTratamentoSoja",
    ]
    MAPA_TABELOES = {
        "av1DetalheTratamentoSoja": tb_av1, "av2DetalheTratamentoSoja": tb_av2,
        "av3DetalheTratamentoSoja": tb_av3, "av4DetalheTratamentoSoja": tb_av4,
        "av5DetalheTratamentoSoja": tb_av5, "av6DetalheTratamentoSoja": tb_av6,
        "av7DetalheTratamentoSoja": tb_av7,
    }
    COLS_CONTEXTO_DET = ["uuid", "nomeFazenda", "nome", "dePara", "status_material",
                         "tipoTeste", "indexTratamento", "safra"]
    fazendas_validas = set(df_fazenda["uuid"])
    detalhe_enriquecidas = {}
    for tabela in TABELAS_DETALHE:
        av_key = tabela.replace("DetalheTratamentoSoja", "").lower()  # av1, av2...
        df_det = dfs.get(tabela, pd.DataFrame()).copy()
        if df_det.empty:
            detalhe_enriquecidas[av_key] = pd.DataFrame()
            continue
        # Limpar
        df_det = df_det.drop(columns=[c for c in ["firebase","dataSync","acao","fotoBase64"] if c in df_det.columns])
        if "dataCriacao" in df_det.columns:
            df_det["dataCriacao"] = pd.to_datetime(df_det["dataCriacao"], unit="s", errors="coerce")
        for col in ["nota", "photoUrl"]:
            if col in df_det.columns:
                df_det[col] = df_det[col].astype(str).str.strip().replace({"": np.nan, "None": np.nan, "nan": np.nan})
        cols_keep = [c for c in ["uuid","tratamentoRef","fazendaRef","dataCriacao","nota","photoUrl"] if c in df_det.columns]
        df_det = df_det[cols_keep]
        # Remover fazendas teste
        if "fazendaRef" in df_det.columns:
            df_det = df_det[df_det["fazendaRef"].isin(fazendas_validas)].copy()
        # Enriquecer com contexto do tabelão principal
        tb_principal = MAPA_TABELOES.get(tabela)
        if tb_principal is not None and "uuid" in tb_principal.columns:
            cols_disp = [c for c in COLS_CONTEXTO_DET if c in tb_principal.columns]
            lookup = tb_principal[cols_disp].rename(columns={"uuid": "tratamentoRef"})
            if "tratamentoRef" in df_det.columns:
                df_det = df_det.merge(lookup, on="tratamentoRef", how="left")
        detalhe_enriquecidas[av_key] = df_det.reset_index(drop=True)

    return {
        "tabeloes":             tabeloes,
        "resultados":           resultados,
        "ta_faixa":             ta_faixa,
        "ta_densidade":         ta_densidade,
        "av_status":            df_av_status,
        "detalhe_enriquecidas": detalhe_enriquecidas,
    }
