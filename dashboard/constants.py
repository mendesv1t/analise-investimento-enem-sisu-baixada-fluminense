from pathlib import Path

ROOT = Path(__file__).parent.parent
CURATED = ROOT / "curated" / "parquet"
OUT  = ROOT / "output"
MOD  = ROOT / "artigo" / "modelos"

# ─── Paleta ──────────────────────────────────────────────────────────────────
CORES_REDE = {
    "Federal": "#1a6fbd", "Estadual": "#e67e22",
    "Municipal": "#27ae60", "Privada": "#8e44ad",
    "Pública": "#2ecc71", "Não informado": "#95a5a6",
}
CLUSTER_LABELS  = {
    0: "Vulnerabilidade",
    1: "Eficiência Relativa",
    2: "Paradoxo Invest."
}
CLUSTER_COLORS  = {
    0: "#ef4444",
    1: "#22c55e",
    2: "#eab308"
}
TEMPLATE = "plotly_white"
MAPA_NOME = {
    "PARACAMBI": "Paracambi", "NILOPOLIS": "Nilópolis", "SEROPEDICA": "Seropédica",
    "NOVA IGUACU": "Nova Iguaçu", "GUAPIMIRIM": "Guapimirim",
    "DUQUE DE CAXIAS": "Duque de Caxias", "ITAGUAI": "Itaguaí",
    "SAO JOAO DE MERITI": "São João de Meriti", "MAGE": "Magé", "MESQUITA": "Mesquita",
    "QUEIMADOS": "Queimados", "BELFORD ROXO": "Belford Roxo", "JAPERI": "Japeri",
}

# Os 13 municípios da Baixada Fluminense (nomes canônicos pós-normalização)
BAIXADA = [
    "Belford Roxo", "Duque de Caxias", "Guapimirim", "Itaguaí", "Japeri",
    "Magé", "Mesquita", "Nilópolis", "Nova Iguaçu", "Paracambi",
    "Queimados", "São João de Meriti", "Seropédica",
]
