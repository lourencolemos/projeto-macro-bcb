"""Construtores das figuras Plotly. Uma função por visual, sempre recebendo o DataFrame já filtrado."""
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

# TODO (feature/graficos-*): fig_cambio_media, fig_dispersao_macro, fig_ibcbr_ciclos, fig_heatmap_correlacao
