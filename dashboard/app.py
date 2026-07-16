"""
Dashboard — Análise ENEM · FUNDEB · SISU · Baixada Fluminense
UFRJ · PPGI · Fundamentos em Ciência de Dados · 2026
"""

import sys
from pathlib import Path

# Adiciona o diretório atual ao PYTHONPATH para garantir que os módulos sejam encontrados
dashboard_dir = str(Path(__file__).parent.resolve())
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

import streamlit as st
import pandas as pd
from constants import (
    ROOT, CURATED, OUT, MOD, MAPA_NOME, BAIXADA, CORES_REDE, CLUSTER_LABELS, CLUSTER_COLORS, TEMPLATE
)

# Importações dos módulos de página
import page_apresentacao
import page_desempenho
import page_fundeb
import page_socioeconomico
import page_modelagem
import page_clusters
import page_sisu
import page_conclusoes

# ─── Configuração da página (DEVE ser a primeira chamada da Streamlit) ───────
st.set_page_config(page_title="Baixada · ENEM, FUNDEB & SISU",
                   layout="wide",
                   initial_sidebar_state="expanded")

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
section[data-testid="stSidebar"]{background:linear-gradient(160deg,#0f1b2d,#1a2f4a);}
section[data-testid="stSidebar"] *{color:#dce9f5!important;}
.hero{background:linear-gradient(135deg,#0f1b2d,#163152 60%,#1e4470);border-radius:16px;
      padding:2.5rem 3rem;margin-bottom:1.5rem;border:1px solid #2a4d72;}
.hero h1{color:#fff;font-size:1.9rem;font-weight:700;margin:0;}
.hero p{color:#a8c4e0;font-size:1rem;margin:.4rem 0 0;}
.kpi{background:linear-gradient(135deg,#1a2f4a,#163152);border:1px solid #2a4d72;
     border-radius:12px;padding:1.2rem 1.5rem;text-align:center;}
.kpi .val{font-size:2.1rem;font-weight:700;color:#58a6ff;}
.kpi .lbl{font-size:.8rem;color:#8ab4d4;margin-top:.2rem;}
.sec{border-left:4px solid #2563eb;padding-left:.75rem;margin:1.5rem 0 1rem;}
.sec h2{color:#1e293b;font-size:1.3rem;font-weight:700;margin:0;}
.sec p{color:#64748b;font-size:.87rem;margin:.2rem 0 0;}
.ins{background:#eff6ff;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;
     padding:.9rem 1.1rem;margin:1rem 0;color:#1e3a5f;font-size:.9rem;line-height:1.5;}
.wrn{background:#fff7ed;border-left:4px solid #f59e0b;border-radius:0 8px 8px 0;
     padding:.9rem 1.1rem;margin:1rem 0;color:#78350f;font-size:.9rem;}
.cnc{background:#f0fdf4;border-left:4px solid #22c55e;border-radius:0 8px 8px 0;
     padding:.9rem 1.1rem;margin:1rem 0;color:#14532d;font-size:.9rem;}
.sources-title{font-size:0.95rem;font-weight:600;color:#475569;margin:2.5rem 0 0.8rem 0;display:flex;align-items:center;gap:0.5rem;}
.sources-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.75rem;margin-bottom:2rem;}
.source-card{background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:0.75rem 1rem;
             transition:all 0.2s ease-in-out;display:flex;flex-direction:column;justify-content:space-between;
             min-height:90px;box-shadow:0 1px 3px rgba(0,0,0,0.02);color:inherit!important;text-decoration:none!important;}
.source-card:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,0.05);border-color:#2563eb;}
.source-tag{font-size:0.65rem;font-weight:700;text-transform:uppercase;color:#2563eb;letter-spacing:0.05em;margin-bottom:0.2rem;}
.source-name{font-size:0.8rem;font-weight:600;color:#1e293b;margin:0 0 0.4rem 0;line-height:1.25;}
.source-link-text{font-size:0.7rem;color:#64748b;display:flex;align-items:center;gap:0.25rem;}
</style>""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Análise Educacional")
    st.markdown("**Baixada Fluminense · RJ**")
    st.markdown("---")
    page = st.radio("Navegação",["Desempenho ENEM",
        "FUNDEB","Perfil Socioeconômico","Acesso ao SISU",
        "Modelagem Preditiva","Clusters Municipais","Conclusões",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<small style='color:#6b8fa8'>Alekssander Santos<br>Vitória M. C. Chaves<br>PPGI · UFRJ · Fundamentos em Ciência de Dados · 2026</small>",
                unsafe_allow_html=True)

# ─── Carregamento ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Carregando dados…")
def load_all():
    enem = pd.read_parquet(CURATED/"enem/dataset_enem_microdados_baixada.parquet")
    
    # Para 2013–2015 o ENEM usava TP_ESCOLA; preenche TP_DEPENDENCIA_ADM_ESC quando ausente
    if "TP_ESCOLA" in enem.columns:
        enem["TP_DEPENDENCIA_ADM_ESC"] = enem["TP_DEPENDENCIA_ADM_ESC"].fillna(enem["TP_ESCOLA"])

    enem = enem[
        (enem["TP_PRESENCA_CN"]==1)&(enem["TP_PRESENCA_CH"]==1)&
        (enem["TP_PRESENCA_LC"]==1)&(enem["TP_PRESENCA_MT"]==1)&
        (enem["IN_TREINEIRO"].fillna(0)==0)
    ].copy()
    enem["REDE"] = enem["TP_DEPENDENCIA_ADM_ESC"].map(
        {1.:"Federal",2.:"Estadual",3.:"Municipal",4.:"Privada"}).fillna("Não informado")
    enem["SETOR"] = enem["REDE"].apply(lambda x: "Privada" if x=="Privada" else "Pública")
    enem["NO_MUNICIPIO_ESC"] = enem["NO_MUNICIPIO_ESC"].str.upper().str.strip().map(MAPA_NOME).fillna(enem["NO_MUNICIPIO_ESC"])
    
    # Filtrar APENAS os 13 municípios da Baixada Fluminense + período 2013–2022
    enem = enem[
        enem["NO_MUNICIPIO_ESC"].isin(BAIXADA) &
        enem["NU_ANO"].between(2013, 2022)
    ].copy()

    fundeb = pd.read_parquet(CURATED/"fundeb/dataset_fundeb_municipio_ano.parquet")
    fundeb["municipio"] = fundeb["municipio"].str.upper().str.strip().map(MAPA_NOME).fillna(fundeb["municipio"])

    sisu_mun = pd.read_parquet(CURATED/"sisu/dataset_sisu_municipio_ano.parquet")
    sisu_mun["municipio_candidato"] = sisu_mun["municipio_candidato"].str.upper().str.strip().map(MAPA_NOME).fillna(sisu_mun["municipio_candidato"])
    # SISU: apenas 2014–2023 (referente ao ENEM de 2013–2022)
    sisu_mun = sisu_mun[sisu_mun["ano"].between(2014, 2023)].copy()

    clusters = pd.read_csv(OUT/"modelos/municipios_clusters.csv")
    clusters["NO_MUNICIPIO_ESC"] = clusters["NO_MUNICIPIO_ESC"].str.upper().str.strip().map(MAPA_NOME).fillna(clusters["NO_MUNICIPIO_ESC"])

    sisu_cotas = pd.read_parquet(CURATED/"sisu/dataset_sisu_cotas_ano.parquet")
    return enem, fundeb, sisu_mun, clusters, sisu_cotas

enem, fundeb, sisu_mun, clusters, sisu_cotas = load_all()

# ─── Roteamento das Páginas ──────────────────────────────────────────────────
if page == "Início":
    page_apresentacao.render(enem, sisu_mun)
elif page == "Desempenho ENEM":
    page_desempenho.render(enem)
elif page == "FUNDEB":
    page_fundeb.render(enem, fundeb, sisu_mun)
elif page == "Perfil Socioeconômico":
    page_socioeconomico.render(enem)
elif page == "Modelagem Preditiva":
    page_modelagem.render(enem)
elif page == "Clusters Municipais":
    page_clusters.render(clusters)
elif page == "Acesso ao SISU":
    page_sisu.render(sisu_mun, sisu_cotas)
elif page == "Conclusões":
    page_conclusoes.render()

# ─── Fontes de Dados (Footer) ────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div class="sources-title">
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:#2563eb;vertical-align:middle;margin-right:4px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
    <span>Fontes de Dados do Painel</span>
</div>
<div class="sources-grid">
    <a href="https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem" target="_blank" class="source-card">
        <div>
            <div class="source-tag">INEP</div>
            <div class="source-name">Microdados do ENEM</div>
        </div>
        <div class="source-link-text">Acessar dados abertos ↗</div>
    </a>
    <a href="https://dadosabertos.mec.gov.br/sisu?__cf_chl_f_tk=Um45T_Ra7e1xuOCDwtVLsgfkaB7UJuIj9HMwjI_BTII-1782997269-1.0.1.1-i6ZbArqqNsVNIlZFGMaE.nsGcSuS4vlU_y3G2UG3qTs" target="_blank" class="source-card">
        <div>
            <div class="source-tag">MEC</div>
            <div class="source-name">Dados Abertos do SiSU</div>
        </div>
        <div class="source-link-text">Acessar portal ↗</div>
    </a>
    <a href="https://portal.fazenda.rj.gov.br/tesouro/relatorios/transferencias-aos-municipios/" target="_blank" class="source-card">
        <div>
            <div class="source-tag">SEFAZ / RJ</div>
            <div class="source-name">Transferências aos Municípios</div>
        </div>
        <div class="source-link-text">Visualizar relatórios ↗</div>
    </a>
    <a href="https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json&dataInicial=01/01/2011&dataFinal=31/12/2024" target="_blank" class="source-card">
        <div>
            <div class="source-tag">SGS / BCB</div>
            <div class="source-name">Série 433 — IPCA (Inflação)</div>
        </div>
        <div class="source-link-text">Acessar API JSON ↗</div>
    </a>
</div>
""", unsafe_allow_html=True)

