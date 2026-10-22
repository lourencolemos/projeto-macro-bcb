"""Acesso a dados resiliente: PostgreSQL (Supabase) com contingência em CSV local."""
import pandas as pd
import streamlit as st

from src import config

TABELAS_PERMITIDAS = {"fato_macro_mensal", "fato_selic_diaria", "fato_ptax_diaria", "dim_calendario", "dim_serie"}


@st.cache_data(ttl=3600, show_spinner="Carregando dados...")
def carregar_tabela(tabela: str, arquivo_csv: str) -> tuple[pd.DataFrame, str]:
    """Retorna (DataFrame, origem). Tenta o banco na nuvem; se falhar, lê o CSV local."""
    assert tabela in TABELAS_PERMITIDAS, "Tabela não permitida"
    try:
        conn = st.connection("postgresql", type="sql")
        df = conn.query(f"SELECT * FROM {tabela} ORDER BY 1", ttl=3600)
        if df.empty:
            raise ValueError("tabela vazia")
        origem = "PostgreSQL (Supabase)"
    except Exception:
        df = pd.read_csv(config.DATA_PROCESSED / arquivo_csv)
        origem = "CSV local (contingência)"
    primeira = df.columns[0]
    if primeira in ("mes", "data"):
        df[primeira] = pd.to_datetime(df[primeira])
    return df, origem
