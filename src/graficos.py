"""Construtores das figuras Plotly. Uma função por visual, sempre recebendo o DataFrame já filtrado."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COR_REGIME = {"Aperto": "#d62728", "Corte": "#2ca02c", "Estável": "#9aa5b1"}

def fig_politica_monetaria(df):
    """Selic Meta + IPCA 12m (linhas) e Juro Real ex-post (barras) no mesmo plano."""
    fig = go.Figure()
    fig.add_bar(x=df["mes"], y=df["juro_real"], name="Juro real ex-post", opacity=0.45)
    fig.add_scatter(x=df["mes"], y=df["selic"], name="Selic Meta", mode="lines", line=dict(width=3))
    fig.add_scatter(x=df["mes"], y=df["ipca_12m"], name="IPCA 12m", mode="lines", line=dict(width=3))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_layout(
        title="Selic Meta, IPCA 12m e juro real ex-post",
        yaxis_title="% a.a.", xaxis_title=None, hovermode="x unified",
        legend=dict(orientation="h", y=-0.15),
    )
    return fig

# ---------- Câmbio ----------
def fig_cambio_media(ptax_d, media):
    """PTAX diária com a média do quinquênio; os trechos acima da média ficam em destaque."""
    acima = ptax_d["ptax_venda"].where(ptax_d["ptax_venda"] > media)
    fig = go.Figure()
    fig.add_scatter(x=ptax_d["data"], y=ptax_d["ptax_venda"], name="PTAX venda", mode="lines",
                    line=dict(width=1.5, color="#9aa5b1"))
    fig.add_scatter(x=ptax_d["data"], y=acima, name="Acima da média", mode="lines+markers",
                    line=dict(width=2.5, color="#d62728"), marker=dict(size=3), connectgaps=False)
    fig.add_hline(y=media, line_dash="dash", annotation_text=f"Média do quinquênio: R$ {media:.2f}".replace(".", ","),
                  annotation_position="top left")
    fig.update_layout(title="Dólar PTAX: dias acima da média do quinquênio", yaxis_title="R$",
                      xaxis_title=None, hovermode="x unified", legend=dict(orientation="h", y=-0.15))
    return fig


def fig_dispersao_macro(df):
    """Dispersão PTAX média x IPCA 12m: um ponto por mês, cor = ano, tamanho = Selic."""
    d = df.assign(ano=df["ano"].astype(str))
    return px.scatter(
        d, x="ptax_media", y="ipca_12m", color="ano", size="selic",
        category_orders={"ano": sorted(d["ano"].unique())},
        hover_data={"mes": "|%b/%Y", "selic": ":.2f", "ptax_media": ":.2f", "ipca_12m": ":.2f", "ano": False},
        labels={"ptax_media": "PTAX média mensal (R$)", "ipca_12m": "IPCA 12m (%)", "ano": "Ano", "selic": "Selic (% a.a.)"},
        title="Câmbio e inflação: cada ponto é um mês (tamanho = Selic)",
    )

# ---------- Atividade ----------
def faixas_regime(df):
    """Agrupa meses consecutivos com o mesmo regime em faixas (início, fim, regime)."""
    faixas = []
    for mes, regime in zip(df["mes"], df["regime"]):
        fim = mes + pd.offsets.MonthBegin(1)
        if faixas and faixas[-1][2] == regime and faixas[-1][1] == mes:
            faixas[-1] = (faixas[-1][0], fim, regime)
        else:
            faixas.append((mes, fim, regime))
    return faixas


def fig_ibcbr_ciclos(df):
    """IBC-Br dessazonalizado com faixas coloridas para os ciclos de aperto e de corte da Selic."""
    fig = go.Figure()
    for ini, fim, regime in faixas_regime(df):
        if regime != "Estável":
            fig.add_vrect(x0=ini, x1=fim, fillcolor=COR_REGIME[regime], opacity=0.15, line_width=0, layer="below")
    fig.add_scatter(x=df["mes"], y=df["ibcbr"], name="IBC-Br (dessazonalizado)", mode="lines",
                    line=dict(width=3, color="#0B5CAD"))
    for regime in ("Aperto", "Corte"):  # entradas de legenda para as faixas
        fig.add_scatter(x=[None], y=[None], mode="markers", name=f"Ciclo de {regime.lower()}",
                        marker=dict(size=12, symbol="square", color=COR_REGIME[regime], opacity=0.4))
    fig.update_layout(title="IBC-Br e ciclos da política monetária", yaxis_title="Índice",
                      xaxis_title=None, hovermode="x unified", legend=dict(orientation="h", y=-0.15))
    return fig


def fig_ibcbr_por_regime(df):
    """Variação mensal média do IBC-Br em cada regime monetário."""
    g = df.groupby("regime").agg(var_media=("var_ibcbr_m", "mean"), meses=("mes", "count")).reset_index()
    g["rotulo"] = g["regime"] + " (" + g["meses"].astype(str) + " meses)"
    fig = px.bar(
        g, x="rotulo", y="var_media", color="regime", color_discrete_map=COR_REGIME,
        text=g["var_media"].map(lambda v: f"{v:+.2f}%".replace(".", ",")),
        labels={"rotulo": "Regime monetário", "var_media": "Variação mensal média (%)"},
        title="Variação mensal média do IBC-Br por regime",
    )
    fig.update_layout(showlegend=False)
    return fig

# ---------- Correlações ----------
ROTULOS = {
    "selic": "Selic", "ipca_12m": "IPCA 12m", "juro_real": "Juro real", "ptax_media": "PTAX", "ibcbr": "IBC-Br",
    "var_selic_pp": "Δ Selic (p.p.)", "ipca_mensal": "IPCA mensal", "var_ptax_pct": "Δ% PTAX", "var_ibcbr_m": "Δ% IBC-Br",
}
COLUNAS_NIVEIS = ["selic", "ipca_12m", "juro_real", "ptax_media", "ibcbr"]
COLUNAS_VARIACOES = ["var_selic_pp", "ipca_mensal", "var_ptax_pct", "var_ibcbr_m"]
# rótulo do par -> (série que antecede, série que reage)
PARES_DEFASAGEM = {
    "Câmbio (Δ% PTAX) → IPCA mensal": ("var_ptax_pct", "ipca_mensal"),
    "Selic (Δ p.p.) → IBC-Br (Δ% mensal)": ("var_selic_pp", "var_ibcbr_m"),
}


def fig_heatmap_correlacao(corr, pval):
    """Matriz de correlação de Pearson; * marca p < 0,05 (sem correção para múltiplos testes)."""
    nomes = [ROTULOS.get(c, c) for c in corr.columns]
    n = len(nomes)
    texto = [
        [f"{corr.iloc[i, j]:.2f}".replace(".", ",") + ("*" if i != j and pval.iloc[i, j] < 0.05 else "") for j in range(n)]
        for i in range(n)
    ]
    fig = go.Figure(go.Heatmap(z=corr.values, x=nomes, y=nomes, text=texto, texttemplate="%{text}",
                               colorscale="RdBu_r", zmin=-1, zmax=1, colorbar=dict(title="r")))
    fig.update_layout(title="Matriz de correlação de Pearson (* p < 0,05)", yaxis=dict(autorange="reversed"))
    return fig


def fig_correlacao_defasada(res, titulo):
    """Correlação de x(t) com y(t+k) para cada defasagem k; azul = p < 0,05."""
    cores = ["#0B5CAD" if p < 0.05 else "#c5ccd3" for p in res["p_valor"]]
    fig = go.Figure(go.Bar(
        x=res["defasagem_meses"], y=res["pearson"], marker_color=cores,
        customdata=res[["p_valor", "n"]],
        hovertemplate="Defasagem de %{x} meses<br>r = %{y:.2f}<br>p = %{customdata[0]:.3f}<br>n = %{customdata[1]}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="gray")
    fig.update_layout(title=f"{titulo}: correlação por defasagem", xaxis_title="Defasagem (meses)",
                      yaxis_title="Pearson (r)", yaxis_range=[-1, 1], xaxis=dict(dtick=1))
    return fig