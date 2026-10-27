"""Construtores das figuras Plotly. Uma função por visual, sempre recebendo o DataFrame já filtrado."""
import plotly.express as px
import plotly.graph_objects as go


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
