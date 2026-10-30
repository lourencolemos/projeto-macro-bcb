# Inteligência Macroeconômica do Brasil (2019–2023)

> Projeto Avaliativo Final · Visualização de Dados e Business Intelligence · Linha 3 (BACEN/SGS)

## 1. Título e Resumo Executivo
**Inteligência Macroeconômica do Brasil (2019–2023)**
Integra cinco séries do SGS/Banco Central (Selic Meta, IPCA mensal e em 12 meses, dólar PTAX e IBC-Br) entre 2019 e 2023 para analisar a relação entre política monetária, inflação, câmbio e atividade econômica. Os dados são extraídos por API, tratados em Python, modelados em tabelas fato e dimensão no PostgreSQL (Supabase) e servidos em um painel interativo com filtros, KPIs e gráficos Plotly.

## 2. Contexto de Negócio e Pergunta Orientadora
Entre 2019 e 2023, o Brasil viveu uma Selic Meta de 2% a.a. (mínimo do período), o choque inflacionário pós-pandemia e um ciclo intenso de aperto monetário. Gestores financeiros, tesourarias e analistas precisam entender como o custo do dinheiro, o câmbio e a inflação se relacionaram com a atividade para decidir sobre crédito, orçamento e investimentos.

**Pergunta orientadora:** como a política monetária, a inflação e o câmbio evoluíram entre 2019 e 2023, e o que os dados permitem (e não permitem) concluir sobre sua relação com a atividade econômica?

**Perguntas de negócio:**
1. Como a Selic Meta evoluiu no ciclo 2019–2023 e quando o juro real ex-post foi mais alto frente ao IPCA 12m?
2. Qual foi a trajetória do dólar PTAX e em quais janelas ele ficou acima da média do quinquênio?
3. Há correlação visual e estatística entre os choques cambiais e o avanço posterior da inflação?
4. Como o IBC-Br reagiu aos períodos de aperto e de corte da Selic?
5. Quais pares de variáveis tiveram os maiores coeficientes de correlação de Pearson?

## 3. Fonte de Dados e Licença
- **Fonte:** Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil (API pública).
- **Período:** 01/01/2019 a 31/12/2023.
- **Séries:** 432 (Meta Selic), 433 (IPCA mensal), 13522 (IPCA 12m), 1 (Dólar PTAX venda), 24364 (IBC-Br dessazonalizado).
- **Extração:** `python -m src.etl` (blocos anuais, pausa entre requisições).
- Dados públicos do Banco Central do Brasil, obtidos pela API do SGS (https://api.bcb.gov.br).

## 4. Pipeline de Engenharia de Dados
1. Extração: `src/etl.py` consulta a API do SGS em blocos anuais, com pausa entre requisições, e salva os dados brutos em `data/raw/`.
2. Limpeza: conversão de datas e valores, remoção de duplicados e nulos.
3. Harmonização: Selic diária com forward-fill; PTAX agregada em média e fechamento mensais; séries mensais indexadas pelo primeiro dia do mês.
4. Indicadores: juro real ex-post, variações do PTAX e do IBC-Br e regime monetário (`src/indicadores.py`).
5. Validação: 60 meses completos, sem nulos, datas ordenadas e IPCA 12m conferido contra o acumulado do IPCA mensal.
6. Carga: tabelas fato e dimensão no PostgreSQL do Supabase (`src/carga_postgres.py`), com CSVs em `data/processed/` como contingência.

## 5. Dicionário de Dados (`fato_macro_mensal`)
| Coluna | Tipo | Significado financeiro / regra de cálculo |
|---|---|---|
| mes | datetime | Primeiro dia do mês de referência |
| selic | float | Meta Selic no último dia do mês (% a.a.), série 432 |
| ipca_mensal | float | IPCA, variação mensal (%), série 433 |
| ipca_12m | float | IPCA acumulado em 12 meses (%), série 13522 |
| ptax_media | float | Média mensal do dólar PTAX venda (R$), série 1 |
| ptax_fim | float | PTAX venda no último dia útil do mês (R$) |
| ibcbr | float | IBC-Br dessazonalizado (índice), série 24364 |
| ano | int | Ano do mês de referência |
| juro_real | float | ((1 + Selic) / (1 + IPCA 12m) − 1) × 100 (% a.a.) |
| var_ptax_pct | float | Variação % mensal da PTAX média |
| var_ibcbr_12m | float | Variação % do IBC-Br em 12 meses (vazio nos 12 primeiros meses) |
| regime | texto | Aperto / Corte / Estável: variação da Selic em 3 meses (±0,25 p.p.) |

**Granularidade:** `fato_macro_mensal` tem uma linha por mês (60 linhas, jan/2019 a dez/2023). As tabelas diárias têm uma linha por dia. As dimensões descrevem calendário e séries.

**`fato_selic_diaria`** (1826 linhas)
| Coluna | Tipo | Significado |
|---|---|---|
| data | datetime | Dia corrido (inclui fins de semana e feriados) |
| selic_meta | float | Meta Selic vigente (% a.a.), série 432, com forward-fill nos dias sem reunião do Copom |

**`fato_ptax_diaria`** (1255 linhas)
| Coluna | Tipo | Significado |
|---|---|---|
| data | datetime | Dia útil com cotação |
| ptax_venda | float | Taxa de câmbio R$/US$ (venda), série 1 do SGS |

**`dim_calendario`** (60 linhas)
| Coluna | Tipo | Significado |
|---|---|---|
| mes | datetime | Primeiro dia do mês (chave para `fato_macro_mensal`) |
| ano | int | Ano |
| trimestre | int | Trimestre (1 a 4) |
| mes_num | int | Número do mês (1 a 12) |
| regime | texto | Aperto, Corte ou Estável |

**`dim_serie`** (5 linhas)
| Coluna | Tipo | Significado |
|---|---|---|
| codigo_sgs | int | Código da série no SGS |
| nome | texto | Nome interno da série no projeto |
| descricao | texto | Descrição e unidade |
| frequencia | texto | Diária ou mensal |

## 6. Tecnologias e Bibliotecas
| Tecnologia | Uso e justificativa |
|---|---|
| Python e pandas | Tratamento e transformação das séries temporais |
| requests | Consumo da API do SGS |
| SQLAlchemy e psycopg2 | Carga e conexão com o PostgreSQL |
| Supabase (PostgreSQL) | Banco na nuvem, gratuito, para o modelo fato e dimensão |
| Streamlit | Data App interativo, com cache e publicação gratuita |
| Plotly | Gráficos interativos |
| SciPy | Correlações de Pearson e p-valores |

## 7. Principais Resultados e Evidências Numéricas

**Custo do dinheiro.** A Selic Meta atingiu o máximo de 13,75% em ago/2022. O IPCA em 12 meses chegou ao pico de 12,13% em abr/2022, antes do pico da Selic. O juro real ex-post, por sua vez, alcançou 10,27% em jun/2023, quando a inflação já desacelerava com a Selic ainda alta, e ficou positivo em 67% dos meses do período. O juro real não positivo (33% dos meses) deve se concentrar na fase de Selic baixa e inflação em alta, o que o gráfico da aba Política Monetária permite conferir.

**Câmbio.** A PTAX (venda) teve média de R$ 4,93 no quinquênio e máxima de R$ 5,94 em 14/05/2020. Ficou acima da média em 64,81% dos dias úteis. Esse percentual é descritivo: a média inclui os valores baixos de 2019, e o dólar operou em patamar mais alto depois disso. A correlação de Pearson entre a PTAX média mensal e o IPCA em 12 meses foi de r = 0,36 (p = 0,005, n = 60), uma associação positiva moderada (r² ≈ 0,13). Como se trata de séries em nível, com tendência, e de um IPCA 12m com janelas sobrepostas, o p-valor tende a superestimar a significância.

**Atividade econômica.** A maior queda mensal do IBC-Br foi de 9,10% em abr/2020. A variação mensal média do IBC-Br foi de 0,14% nos meses de aperto (n = 20), 0,19% nos de corte (n = 20) e 0,12% nos estáveis (n = 19). Excluindo 2020, a média dos meses de corte sobe para 0,32% (n = 10), enquanto as de aperto (0,14%, n = 20) e estável (0,12%, n = 17) permanecem. Dos 12 meses de 2020, 10 foram classificados como corte, 2 como estáveis e nenhum como aperto, o que mostra que o choque da pandemia se concentrou nesse regime. Nessa amostra, os meses de corte sem 2020 coincidem com crescimento mais rápido, mas a subamostra é pequena e a análise é descritiva.

**Correlações entre as séries.** Em níveis, as maiores correlações foram Selic × Juro real (r = 0,78, p < 0,001), Selic × IBC-Br (r = 0,73, p < 0,001) e Juro real × IBC-Br (r = 0,55, p < 0,001). A primeira é em parte mecânica, já que o juro real é calculado a partir da Selic. As demais refletem tendências comuns das séries no período e não permitem concluir que juros mais altos elevem a atividade.

Nas variações mensais, que reduzem o efeito das tendências, os três maiores pares foram:
- **Δ Selic × IPCA mensal:** r = 0,47 (p < 0,001). Os meses de alta da Selic coincidem com IPCA mensal mais alto, padrão compatível com o Banco Central reagindo à inflação. A causalidade pode ir da inflação para a Selic, e não o contrário.
- **Δ% PTAX × Δ% IBC-Br:** r = −0,41 (p = 0,001). Os meses de alta do dólar coincidem com queda da atividade, associação possivelmente influenciada pelo episódio de 2020, quando ambos se moveram em direções adversas ao mesmo tempo.
- **IPCA mensal × Δ% PTAX:** r = −0,32 (p = 0,012). O sinal é oposto ao de um repasse cambial para os preços e deve ser lido com cautela. Com 6 pares comparados, o limiar corrigido para múltiplos testes seria de cerca de 0,008, e este par não o atinge.

**Defasagens.** Para o par Câmbio → IPCA mensal, testando defasagens de 0 a 12 meses, a maior correlação absoluta foi r = −0,33 com defasagem de 1 mês (p = 0,012, n = 58), valor próximo ao da correlação contemporânea (r = −0,32), sem uma defasagem claramente dominante. Com 13 defasagens testadas, o limiar corrigido seria de cerca de 0,004, e o resultado não o atinge. Para o par Selic → IBC-Br, a maior correlação foi r = 0,11 com defasagem de 7 meses (p = 0,439, n = 52), sem evidência de associação nas defasagens testadas, o que não equivale a evidência de ausência de efeito em uma amostra de 60 meses.

## 8. Discussão e Limitações da Análise
- **Associação, não causalidade.** As correlações descrevem movimentos conjuntos das séries. Nenhuma delas permite afirmar que uma variável provocou a outra.
**Causalidade reversa.** A Selic é ajustada em resposta à inflação, então a correlação positiva entre variação da Selic e IPCA mensal pode refletir a reação do Banco Central, e não um efeito da Selic sobre os preços.
- **Episódio de 2020.** Parte das correlações entre variações (câmbio × IBC-Br e câmbio × IPCA) pode refletir os meses de março a maio de 2020, quando o dólar disparou e a atividade e a inflação caíram. A análise não isola esse período nas defasagens, que usam a série completa.
- **Séries com tendência.** Correlações entre níveis (Selic, IPCA 12m, PTAX, IBC-Br) podem ser espúrias. Por isso o painel também calcula as correlações das variações mensais.
- **Testes múltiplos.** A busca pela melhor defasagem testa 13 defasagens (0 a 12 meses). Alguma defasagem "significativa" pode surgir por acaso.
- **Regime monetário mecânico.** Aperto, Corte e Estável são classificados pela variação da Selic em 3 meses (±0,25 p.p.). A defasagem com que a política monetária atinge a atividade não é modelada.
- **Juro real ex-post.** Usa o IPCA acumulado em 12 meses (inflação passada), e não as expectativas de inflação do mercado.
- **Choque de 2020.** A pandemia concentrou quedas do IBC-Br nos meses classificados como Corte. A exclusão de 2020 no painel é uma escolha analítica, e os dois cenários são apresentados.
- **Amostra curta.** São 60 observações mensais, em um quinquênio atípico (pandemia e ciclo intenso de aperto). Os resultados podem não se repetir em outros períodos.
**Correlação espúria em níveis.** Selic e IBC-Br mostram r = 0,73 em níveis, mas ambas as séries tiveram tendência de alta no período. Por isso o painel destaca as correlações entre variações mensais.
- **Qualidade das séries.** O IBC-Br é um indicador de atividade dessazonalizado, sujeito a revisões. A PTAX mensal é a média das cotações diárias e suaviza picos de curto prazo. A variação do IBC-Br em 12 meses fica vazia nos 12 primeiros meses.

## 9. Aplicação Profissional e Decisões de Negócio
| Perfil | Como usa o painel | Decisão apoiada |
|---|---|---|
| Gestor financeiro de empresa que toma crédito | Acompanha a Selic e o juro real na aba Política Monetária | Momento e prazo de captação, e comparação do custo real do dinheiro |
| Analista de investimentos ou economista | Cruza regimes monetários, IBC-Br e correlações | Formação de hipóteses sobre ciclos e atividade, a testar com métodos adicionais |
| Equipe de risco de crédito | Observa o juro real e o ritmo da atividade | Cenários de inadimplência e apetite por crédito |

O painel apoia a leitura do cenário macroeconômico e a formulação de hipóteses. Ele não substitui modelos preditivos nem constitui recomendação de investimento.

## 10. Demonstração do Data App (Streamlit)
- Link: (https://macro-bcb-lourencoflemos.streamlit.app/)
| Aba | O que mostra |
|---|---|
| Visão Executiva | Quatro cartões (contexto, insight e ação) gerados dos dados filtrados |
| Política Monetária | Selic Meta, IPCA 12m e juro real ex-post no mesmo plano |
| Câmbio | PTAX diária com a média do quinquênio e dispersão PTAX × IPCA 12m |
| Atividade | IBC-Br com ciclos de aperto e corte e variação mensal média por regime |
| Correlações | Heatmap de Pearson (níveis e variações) e correlação defasada |
| Dados | Tabela filtrada e download em CSV |

**Guia de navegação:** a barra lateral filtra período, ano e regime monetário e tem o botão **Resetar filtros**. Os quatro KPIs do topo (Selic, IPCA 12m, juro real e PTAX) mostram a variação em relação a 12 meses antes.

![Visão Executiva](docs/img/01_visao_executiva.png)
![Política Monetária](docs/img/02_politica_monetaria.png)
![Câmbio](docs/img/03_cambio.png)
![Atividade](docs/img/04_atividade.png)
![Correlações](docs/img/05_correlacoes.png)

## 11. Como Executar Localmente
```bash
git clone <URL_DO_REPOSITORIO> && cd projeto-macro-bcb
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.etl                                   # gera data/processed/
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # opcional: sem banco, usa o CSV local
streamlit run app.py
```

## 12. Estrutura de Pastas
```
├── data/raw/            # séries brutas do SGS
├── data/processed/      # base tratada (também usada como contingência pelo app)
├── notebooks/           # exploração dos dados
├── src/
│   ├── config.py        # caminhos, séries e período
│   ├── etl.py           # extração, limpeza, modelagem e validação
│   ├── indicadores.py   # juro real, regimes e correlações
│   ├── insights.py      # textos da Visão Executiva
│   ├── graficos.py      # figuras Plotly
│   ├── db.py            # acesso ao PostgreSQL com contingência em CSV
│   └── carga_postgres.py
├── docs/                # backlog do Trello e imagens do README
├── .streamlit/          # config.toml e secrets.toml.example
├── app.py               # Data App
└── requirements.txt
```

## 13. Gestão Ágil e Links do Projeto
- Quadro Kanban (Trello, público): https://trello.com/b/dMtjZEog/macroeconomia-taxas-de-juros-indicadores-economicos-banco-central-ipea
![Quadro Kanban no Trello](docs/img/06_trello.png)
- App em produção:(https://macro-bcb-lourencoflemos.streamlit.app/)
- Vídeo de apresentação: TODO

## 14. Autoria e Créditos
- Autor(a): Lourenço Fernandes Lemos · LinkedIn: www.linkedin.com/in/lourencolemos
- Referências: 
- Banco Central do Brasil. Sistema Gerenciador de Séries Temporais (SGS): https://www3.bcb.gov.br/sgspub
- Banco Central do Brasil. Portal de Dados Abertos: https://dadosabertos.bcb.gov.br
- Streamlit. Documentação: https://docs.streamlit.io
- Plotly. Documentação do Plotly para Python: https://plotly.com/python
- pandas. Documentação: https://pandas.pydata.org/docs
- Supabase. Documentação: https://supabase.com/docs