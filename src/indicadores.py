"""Funções de cálculo dos indicadores macroeconômicos."""
import numpy as np
import pandas as pd
from scipy import stats


def juro_real_ex_post(selic_aa: pd.Series, ipca_12m: pd.Series) -> pd.Series:
    """Juro real ex-post (% a.a.) = ((1 + Selic) / (1 + IPCA 12m) - 1) * 100."""
    return ((1 + selic_aa / 100) / (1 + ipca_12m / 100) - 1) * 100


def classificar_regime(selic: pd.Series, janela: int = 3, tolerancia: float = 0.25) -> pd.Series:
    """Classifica o regime monetário pela variação da Selic nos últimos `janela` meses.

    Aperto: variação >= +tolerancia p.p.; Corte: <= -tolerancia p.p.; senão Estável.
    Os primeiros `janela` meses (sem base de comparação) entram como Estável.
    """
    delta = selic - selic.shift(janela)
    regime = np.select([delta >= tolerancia, delta <= -tolerancia], ["Aperto", "Corte"], "Estável")
    return pd.Series(regime, index=selic.index, name="regime")


def adicionar_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas derivadas à base mensal (ordenada por `mes`)."""
    df = df.sort_values("mes").reset_index(drop=True).copy()
    df["ano"] = df["mes"].dt.year
    df["juro_real"] = juro_real_ex_post(df["selic"], df["ipca_12m"])
    df["var_ptax_pct"] = df["ptax_media"].pct_change() * 100
    df["var_ibcbr_12m"] = df["ibcbr"].pct_change(12) * 100
    df["regime"] = classificar_regime(df["selic"])
    return df


def matriz_correlacao(df: pd.DataFrame, colunas: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (matriz de Pearson, matriz de p-valores)."""
    corr = pd.DataFrame(index=colunas, columns=colunas, dtype=float)
    pval = corr.copy()
    for a in colunas:
        for b in colunas:
            par = df[[a, b]].dropna()
            r, p = stats.pearsonr(par[a], par[b]) if len(par) > 2 else (np.nan, np.nan)
            corr.loc[a, b], pval.loc[a, b] = r, p
    return corr, pval


def correlacao_defasada(x: pd.Series, y: pd.Series, max_defasagem: int = 12) -> pd.DataFrame:
    """Correlação de Pearson entre x(t) e y(t+k), k = 0..max_defasagem (associação, não causalidade)."""
    linhas = []
    for k in range(max_defasagem + 1):
        par = pd.concat([x, y.shift(-k)], axis=1).dropna()
        r, p = stats.pearsonr(par.iloc[:, 0], par.iloc[:, 1])
        linhas.append({"defasagem_meses": k, "pearson": r, "p_valor": p, "n": len(par)})
    return pd.DataFrame(linhas)
