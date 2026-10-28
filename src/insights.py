"""Textos da aba Visão Executiva, calculados a partir dos dados filtrados."""
from src import graficos, indicadores

_MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _mes(ts) -> str:
    return f"{_MESES[ts.month - 1]}/{ts.year}"


def _n(v: float, casas: int = 2) -> str:
    return f"{v:.{casas}f}".replace(".", ",")


def _pct(v: float, casas: int = 2) -> str:
    return _n(v, casas) + "%"


def _brl(v: float) -> str:
    return "R$ " + _n(v)


def _cartao_custo_dinheiro(d) -> dict:
    ini, fim = d.iloc[0], d.iloc[-1]
    pico_selic = d.loc[d["selic"].idxmax()]
    pico_jr = d.loc[d["juro_real"].idxmax()]
    pico_ipca = d.loc[d["ipca_12m"].idxmax()]
    pct_positivo = (d["juro_real"] > 0).mean() * 100
    if len(d) == 1:
        contexto = f"Em {_mes(ini['mes'])}, a Selic Meta estava em {_pct(ini['selic'])} e o IPCA em 12 meses em {_pct(ini['ipca_12m'])}."
    else:
        contexto = (
            f"A Selic Meta foi de {_pct(ini['selic'])} em {_mes(ini['mes'])} para {_pct(fim['selic'])} em {_mes(fim['mes'])}, "
            f"com máximo de {_pct(pico_selic['selic'])} em {_mes(pico_selic['mes'])}. "
            f"O IPCA em 12 meses chegou a {_pct(pico_ipca['ipca_12m'])} em {_mes(pico_ipca['mes'])}."
        )
    insight = (
        f"O juro real ex-post atingiu {_pct(pico_jr['juro_real'])} em {_mes(pico_jr['mes'])} "
        f"e ficou positivo em {_n(pct_positivo, 0)}% dos meses analisados."
    )
    acao = "Avaliar o custo do crédito e o retorno de aplicações pelo juro real, e não só pela Selic nominal."
    return {"titulo": "Custo do dinheiro: Selic, inflação e juro real", "contexto": contexto, "insight": insight, "acao": acao}


def _cartao_cambio(ptax_d, periodo) -> dict:
    titulo = "Câmbio: o dólar frente à média do quinquênio"
    media = ptax_d["ptax_venda"].mean()  # média de todo o quinquênio, independente dos filtros
    per = ptax_d[(ptax_d["data"] >= periodo[0].isoformat()) & (ptax_d["data"] <= periodo[1].isoformat())]
    if per.empty:
        return {"titulo": titulo, "contexto": "Sem cotações no período selecionado.", "insight": "-", "acao": "-"}
    pico = per.loc[per["ptax_venda"].idxmax()]
    pct_acima = (per["ptax_venda"] > media).mean() * 100
    contexto = (
        f"A média da PTAX no quinquênio 2019–2023 foi {_brl(media)}. "
        f"No período, a cotação máxima foi {_brl(pico['ptax_venda'])} em {pico['data'].strftime('%d/%m/%Y')}."
    )
    insight = f"O dólar ficou acima da média do quinquênio em {_n(pct_acima, 0)}% dos dias úteis do período filtrado."
    acao = ("Usar a média e as janelas acima dela como referência de estresse cambial em orçamentos e na proteção de "
            "contas em dólar. A associação com a inflação está na aba Correlações.")
    return {"titulo": titulo, "contexto": contexto, "insight": insight, "acao": acao}


def _cartao_atividade(d) -> dict:
    titulo = "Atividade econômica: IBC-Br e ciclos da Selic"
    ini, fim = d.iloc[0], d.iloc[-1]
    base = d.dropna(subset=["var_ibcbr_m"])
    if len(d) == 1 or base.empty:
        return {"titulo": titulo, "contexto": "Selecione mais de um mês para ver a evolução do IBC-Br.", "insight": "-", "acao": "-"}
    var_total = f"{(fim['ibcbr'] / ini['ibcbr'] - 1) * 100:+.2f}".replace(".", ",")
    queda = base.loc[base["var_ibcbr_m"].idxmin()]
    contexto = f"O IBC-Br dessazonalizado variou {var_total}% entre {_mes(ini['mes'])} e {_mes(fim['mes'])}. "
    if queda["var_ibcbr_m"] < 0:
        contexto += f"A maior queda mensal foi {_pct(queda['var_ibcbr_m'])} em {_mes(queda['mes'])}."
    else:
        contexto += f"Não houve queda mensal no período; o menor crescimento foi {_pct(queda['var_ibcbr_m'])} em {_mes(queda['mes'])}."
    por_regime = base.groupby("regime")["var_ibcbr_m"].agg(["mean", "count"])
    if len(por_regime) < 2:
        insight = f"O filtro atual contém só meses de {por_regime.index[0].lower()}. Amplie os filtros para comparar os regimes."
    else:
        melhor = por_regime["mean"].idxmax()
        insight = (
            f"A maior variação mensal média ocorreu nos meses de {melhor.lower()} "
            f"({_pct(por_regime.loc[melhor, 'mean'])}, {int(por_regime.loc[melhor, 'count'])} meses). "
            "A comparação é descritiva e sensível ao choque de 2020."
        )
    acao = "Comparar os regimes com e sem 2020 (aba Atividade) antes de tirar conclusões sobre política monetária e crescimento."
    return {"titulo": titulo, "contexto": contexto, "insight": insight, "acao": acao}


def _cartao_correlacao(d) -> dict:
    titulo = "Associações entre as séries"
    if len(d) < 12:
        return {"titulo": titulo, "contexto": "Selecione ao menos 12 meses para calcular correlações.", "insight": "-", "acao": "-"}
    corr, pval = indicadores.matriz_correlacao(d, graficos.COLUNAS_VARIACOES)
    top = indicadores.maiores_correlacoes(corr, pval, n=2)
    if top.empty:
        return {"titulo": titulo, "contexto": "Não há variação suficiente nos dados filtrados.", "insight": "-", "acao": "-"}
    pares = [
        f"{graficos.ROTULOS[r.serie_a]} × {graficos.ROTULOS[r.serie_b]} (r = {_n(r.pearson)}, p = {_n(r.p_valor, 3)})"
        for r in top.itertuples()
    ]
    contexto = "Nas variações mensais, os pares de maior correlação absoluta foram " + "; ".join(pares) + "."
    significativa = top.iloc[0]["p_valor"] < 0.05
    insight = (
        "A associação mais forte " + ("é" if significativa else "não é")
        + " estatisticamente significativa a 5%, sem correção para múltiplos testes."
    )
    acao = "Tratar as associações como hipóteses a investigar: correlações sozinhas não permitem inferir causalidade."
    return {"titulo": titulo, "contexto": contexto, "insight": insight, "acao": acao}


def gerar_cartoes(dff, ptax_d, periodo) -> list[dict]:
    """Quatro cartões (contexto, insight, ação) que se atualizam com os filtros."""
    return [_cartao_custo_dinheiro(dff), _cartao_cambio(ptax_d, periodo), _cartao_atividade(dff), _cartao_correlacao(dff)]