"""Data App: Inteligência Macroeconômica do Brasil (BACEN/SGS, 2019-2023)."""
import streamlit as st 
from scipy import stats

from src import db, graficos

st.set_page_config(page_title="Macro Brasil 2019–2023", page_icon="📈", layout="wide")


# ---------- Formatação ----------
def pct(v: float) -> str:
    return f"{v:.2f}%".replace(".", ",")


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------- Dados ----------
df, origem = db.carregar_tabela("fato_macro_mensal", "macro_mensal.csv")
ptax_d, _ = db.carregar_tabela("fato_ptax_diaria", "ptax_diaria.csv")

MIN_DATA, MAX_DATA = df["mes"].min().date(), df["mes"].max().date()
ANOS = sorted(df["ano"].unique().tolist())
REGIMES = ["Aperto", "Estável", "Corte"]


# ---------- Estado e filtros (session_state) ----------
def filtros_padrao() -> dict:
    return {"f_periodo": (MIN_DATA, MAX_DATA), "f_anos": ANOS, "f_regimes": REGIMES}


for chave, valor in filtros_padrao().items():
    st.session_state.setdefault(chave, valor)


def resetar_filtros() -> None:
    """Callback do botão: roda ANTES do rerun, por isso pode alterar chaves de widgets."""
    st.session_state.update(filtros_padrao())


with st.sidebar:
    st.header("Filtros")
    st.date_input("Período", min_value=MIN_DATA, max_value=MAX_DATA, key="f_periodo")
    st.multiselect("Ano", ANOS, key="f_anos")
    st.multiselect("Regime monetário", REGIMES, key="f_regimes")
    st.button("Resetar filtros", on_click=resetar_filtros, width="stretch")
    st.caption(f"Fonte dos dados: {origem}")

periodo = st.session_state["f_periodo"]
if len(periodo) != 2:
    st.info("Selecione a data inicial e a data final no filtro de período.")
    st.stop()

mask = (
    (df["mes"] >= periodo[0].isoformat())
    & (df["mes"] <= periodo[1].isoformat())
    & df["ano"].isin(st.session_state["f_anos"])
    & df["regime"].isin(st.session_state["f_regimes"])
)
dff = df[mask]
if dff.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# ---------- Cabeçalho e KPIs ----------
st.title("Inteligência Macroeconômica do Brasil (2019–2023)")
st.caption("Selic, inflação, câmbio e atividade econômica. Fonte: SGS/Banco Central do Brasil.")

ult = dff.iloc[-1]
ref = dff.iloc[-13] if len(dff) > 12 else dff.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Selic Meta vigente", pct(ult["selic"]), f"{ult['selic'] - ref['selic']:+.2f} p.p. vs. 12m antes".replace(".", ","))
c2.metric("IPCA 12m", pct(ult["ipca_12m"]), f"{ult['ipca_12m'] - ref['ipca_12m']:+.2f} p.p. vs. 12m antes".replace(".", ","))
c3.metric("Juro real ex-post", pct(ult["juro_real"]), f"{ult['juro_real'] - ref['juro_real']:+.2f} p.p. vs. 12m antes".replace(".", ","))
c4.metric("Dólar PTAX (média do mês)", brl(ult["ptax_media"]), f"{ult['ptax_media'] - dff['ptax_media'].mean():+.2f} vs. média do período".replace(".", ","))

# ---------- Abas ----------
abas = st.tabs(["Visão Executiva", "Política Monetária", "Câmbio", "Atividade", "Correlações", "Dados"])

with abas[0]:
    st.subheader("Contexto → Insight → Ação")
    st.info("TODO: resumo executivo em pirâmide invertida, com números reais calculados a partir de `dff`.")

with abas[1]:
    st.plotly_chart(graficos.fig_politica_monetaria(dff), width="stretch")
    st.caption("Limitações: o juro real ex-post usa a inflação passada (IPCA 12m), não a expectativa de inflação.")

with abas[2]:
    ptax_per = ptax_d[(ptax_d["data"] >= periodo[0].isoformat()) & (ptax_d["data"] <= periodo[1].isoformat())]
    media_5a = ptax_d["ptax_venda"].mean()  # média de todo o quinquênio, independente dos filtros
    if ptax_per.empty:
        st.warning("Sem cotações no período selecionado.")
    else:
        pct_acima = (ptax_per["ptax_venda"] > media_5a).mean() * 100
        st.plotly_chart(graficos.fig_cambio_media(ptax_per, media_5a), width="stretch")
        st.caption(f"Média do quinquênio 2019–2023: {brl(media_5a)}. No período filtrado, o dólar ficou acima dela em {pct(pct_acima)} dos dias úteis. Este gráfico responde ao filtro de período.")
    st.plotly_chart(graficos.fig_dispersao_macro(dff), width="stretch")
    par = dff[["ptax_media", "ipca_12m"]].dropna()
    if len(par) > 2:
        r, p = stats.pearsonr(par["ptax_media"], par["ipca_12m"])
        st.caption(f"Pearson entre PTAX e IPCA 12m (níveis, {len(par)} meses): r = {r:.2f}, p = {p:.3f}".replace(".", ",") + ". Séries com tendência podem gerar correlação espúria, e associação não implica causalidade.")

with abas[3]:
    st.info("TODO: IBC-Br dessazonalizado com faixas de aperto/corte monetário.")

with abas[4]:
    st.info("TODO: heatmap de Pearson (níveis e variações) + correlação defasada câmbio → IPCA. Associação, não causalidade.")

with abas[5]:
    st.dataframe(dff, width="stretch", hide_index=True)
    st.download_button(
        "Baixar dados filtrados (CSV)",
        data=dff.to_csv(index=False).encode("utf-8"),
        file_name="macro_filtrado.csv",
        mime="text/csv",
    )
