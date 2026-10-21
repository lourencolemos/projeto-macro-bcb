"""Pipeline de ETL: extração (SGS/BACEN), limpeza, transformação e modelagem.

Uso (a partir da raiz do repositório):
    python -m src.etl               # baixa do SGS e gera data/processed/
    python -m src.etl --usar-raw    # reprocessa a partir de data/raw/ (sem rede)
"""
import argparse
import time

import numpy as np
import pandas as pd
import requests

from src import config, indicadores


# ---------- Extração ----------
def baixar_serie(codigo: int) -> pd.DataFrame:
    """Baixa uma série do SGS em blocos anuais (evita limite de janela da API)."""
    partes = []
    for ano in range(config.ANO_INICIAL, config.ANO_FINAL + 1):
        params = {"formato": "json", "dataInicial": f"01/01/{ano}", "dataFinal": f"31/12/{ano}"}
        resp = requests.get(config.SGS_URL.format(codigo=codigo), params=params, timeout=30)
        resp.raise_for_status()
        partes.append(pd.DataFrame(resp.json()))
        time.sleep(config.PAUSA_ENTRE_REQUISICOES)
    return pd.concat(partes, ignore_index=True)


# ---------- Limpeza ----------
def limpar_serie(bruto: pd.DataFrame, nome: str) -> pd.DataFrame:
    """Padroniza datas (datetime), converte valores para float, remove nulos e duplicados."""
    df = bruto.copy()
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["data", "valor"]).drop_duplicates(subset="data", keep="last")
    return df.sort_values("data").rename(columns={"valor": nome}).reset_index(drop=True)


def _mensal(df: pd.DataFrame, coluna: str) -> pd.Series:
    """Indexa uma série mensal do SGS pelo primeiro dia do mês."""
    mes = df["data"].dt.to_period("M").dt.to_timestamp()
    return df.set_index(mes)[coluna].rename(coluna)


# ---------- Transformação / modelagem ----------
def construir_selic_diaria(selic: pd.DataFrame) -> pd.DataFrame:
    """Calendário diário completo, com forward-fill nos dias sem reunião do Copom."""
    calendario = pd.date_range(config.DATA_INICIAL_ISO, config.DATA_FINAL_ISO, freq="D")
    serie = selic.set_index("data")["selic_meta"].reindex(calendario)
    # bfill cobre o caso de a série registrar só as datas de mudança da meta
    serie = serie.ffill().bfill()
    return serie.rename_axis("data").reset_index()


def construir_base_mensal(selic_d, ptax, ipca_m, ipca_12m, ibcbr) -> pd.DataFrame:
    selic_mes = selic_d.set_index("data")["selic_meta"].resample("MS").last().rename("selic")
    ptax_mes = ptax.set_index("data")["ptax_venda"].resample("MS").agg(["mean", "last"])
    ptax_mes.columns = ["ptax_media", "ptax_fim"]
    base = pd.concat(
        [selic_mes, _mensal(ipca_m, "ipca_mensal"), _mensal(ipca_12m, "ipca_12m"), ptax_mes, _mensal(ibcbr, "ibcbr")],
        axis=1,
    ).rename_axis("mes").reset_index()
    return indicadores.adicionar_indicadores(base)


def construir_dimensoes(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    dim_cal = base[["mes", "ano", "regime"]].copy()
    dim_cal["trimestre"] = base["mes"].dt.quarter
    dim_cal["mes_num"] = base["mes"].dt.month
    dim_serie = pd.DataFrame(
        [{"codigo_sgs": c, "nome": m["nome"], "descricao": m["descricao"], "frequencia": m["freq"]}
         for c, m in config.SERIES.items()]
    )
    return dim_cal, dim_serie


# ---------- Validação ----------
def validar_base(base: pd.DataFrame) -> None:
    """Falha cedo se a base violar as expectativas (60 meses, sem nulos, séries coerentes)."""
    assert len(base) == 60, f"Esperado 60 meses, encontrado {len(base)}"
    assert base["mes"].is_monotonic_increasing and not base["mes"].duplicated().any()
    nucleo = ["selic", "ipca_mensal", "ipca_12m", "ptax_media", "ibcbr", "juro_real"]
    assert not base[nucleo].isna().any().any(), "Nulos encontrados nas colunas-núcleo"
    assert base["selic"].between(0, 20).all(), "Selic fora do intervalo plausível"
    # IPCA 12m (série 13522) deve bater com o acumulado da série mensal (433)
    acum = ((1 + base["ipca_mensal"] / 100).rolling(12).apply(np.prod, raw=True) - 1) * 100
    dif = (acum - base["ipca_12m"]).abs().dropna()
    assert dif.max() < 0.05, f"IPCA 12m diverge do acumulado mensal (dif máx {dif.max():.3f} p.p.)"


# ---------- Orquestração ----------
def executar(usar_raw: bool = False) -> None:
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    series = {}
    for codigo, meta in config.SERIES.items():
        arquivo = config.DATA_RAW / f"sgs_{codigo}_{meta['nome']}.csv"
        if usar_raw:
            bruto = pd.read_csv(arquivo, dtype=str)
        else:
            bruto = baixar_serie(codigo)
            bruto.to_csv(arquivo, index=False)
        series[meta["nome"]] = limpar_serie(bruto, meta["nome"])

    selic_d = construir_selic_diaria(series["selic_meta"])
    base = construir_base_mensal(selic_d, series["ptax_venda"], series["ipca_mensal"], series["ipca_12m"], series["ibcbr"])
    validar_base(base)
    dim_cal, dim_serie = construir_dimensoes(base)

    saidas = {"macro_mensal": base, "selic_diaria": selic_d, "ptax_diaria": series["ptax_venda"],
              "dim_calendario": dim_cal, "dim_serie": dim_serie}
    for nome, df in saidas.items():
        df.to_csv(config.DATA_PROCESSED / f"{nome}.csv", index=False, encoding="utf-8")
    print(f"ETL concluído: {len(base)} meses em {config.DATA_PROCESSED}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--usar-raw", action="store_true", help="reprocessa data/raw sem acessar a API")
    executar(ap.parse_args().usar_raw)
