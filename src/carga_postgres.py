"""Carrega data/processed/*.csv no PostgreSQL (Supabase).

Uso: defina DATABASE_URL no ambiente (NUNCA no repositório) e rode
    python -m src.carga_postgres
"""
import os

import pandas as pd
from sqlalchemy import create_engine

from src import config

TABELAS = {
    "fato_macro_mensal": "macro_mensal.csv",
    "fato_selic_diaria": "selic_diaria.csv",
    "fato_ptax_diaria": "ptax_diaria.csv",
    "dim_calendario": "dim_calendario.csv",
    "dim_serie": "dim_serie.csv",
}


def executar() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Defina a variável de ambiente DATABASE_URL (string de conexão do pooler do Supabase).")
    engine = create_engine(url)
    for tabela, arquivo in TABELAS.items():
        df = pd.read_csv(config.DATA_PROCESSED / arquivo)
        for col in ("mes", "data"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        df.to_sql(tabela, engine, if_exists="replace", index=False)
        print(f"{tabela}: {len(df)} linhas")


if __name__ == "__main__":
    executar()
