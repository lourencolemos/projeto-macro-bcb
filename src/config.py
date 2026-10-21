"""Configurações centrais do projeto (caminhos relativos, séries do SGS, período)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

# Janela obrigatória do enunciado: 01/01/2019 a 31/12/2023
ANO_INICIAL = 2019
ANO_FINAL = 2023
DATA_INICIAL_ISO = f"{ANO_INICIAL}-01-01"
DATA_FINAL_ISO = f"{ANO_FINAL}-12-31"

SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
PAUSA_ENTRE_REQUISICOES = 1.0  # segundos: respeita os limites da API

# código SGS -> metadados
SERIES = {
    432: {"nome": "selic_meta", "descricao": "Meta Selic (% a.a.)", "freq": "Diária"},
    433: {"nome": "ipca_mensal", "descricao": "IPCA variação mensal (%)", "freq": "Mensal"},
    13522: {"nome": "ipca_12m", "descricao": "IPCA acumulado em 12 meses (%)", "freq": "Mensal"},
    1: {"nome": "ptax_venda", "descricao": "Dólar PTAX venda (R$)", "freq": "Diária"},
    24364: {"nome": "ibcbr", "descricao": "IBC-Br dessazonalizado (índice)", "freq": "Mensal"},
}
