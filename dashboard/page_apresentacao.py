import streamlit as st
import plotly.express as px
from constants import TEMPLATE

def render(enem, sisu_mun):
    st.markdown("""<div class="hero">
    <h1>Análise Multidimensional sobre Financiamento Público da Educação e
Desempenho Escolar na Baixada Fluminense</h1>
""", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    kpis = [
        (f"{len(enem):,}".replace(",","."), "Concludentes Identificados (ENEM)<br>(2013–2022)"),
        (f"{sisu_mun['total_aprovados'].sum():,.0f}".replace(",","."), "Matrículas no SISU<br>(2014–2023)"),
        (f"{enem['NOTA_MEDIA_OBJ'].mean():.1f}", "Nota Média Objetiva<br>Baixada Fluminense (13 municípios)"),
    ]
    for col,(val,lbl) in zip([c1,c2,c3], kpis):
        col.markdown(f'<div class="kpi"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
                     unsafe_allow_html=True)

    st.markdown("---")
    col_l, col_r = st.columns([3,2])
    with col_l:
        st.markdown("### Contexto e Perguntas de Pesquisa")
        st.markdown("""
A **Baixada Fluminense** concentra ~3,7 milhões de habitantes in 13 municípios,
com IDH entre os mais baixos da região metropolitana do Rio de Janeiro.

**Integramos três bases públicas:**
- **ENEM** (INEP): microdados individuais de concludentes identificados em escolas da Baixada Fluminense, 10 edições (2013–2022)
- **FUNDEB** (FNDE): repasses municipais reais 2011–2024
- **SISU** (MEC): matrículas de moradores da Baixada Fluminense, 10 edições (2014–2023)

**Três perguntas de pesquisa:**
1. O volume de repasses do FUNDEB se correlaciona com as notas do ENEM?
2. Qual o papel das variáveis socioeconômicas nessa relação?
3. Como é configurado o acesso ao ensino superior via SISU?
        """)
        st.markdown("""<div class="ins">
        <strong>Resultado principal:</strong> O FUNDEB <strong>não é preditor significativo</strong>
        da nota individual no ENEM (r = −0,07; p = 0,85). Renda familiar, escolaridade materna
        e tipo de rede dominam a variação no desempenho.
        </div>""", unsafe_allow_html=True)
    with col_r:
        med_mun = enem.groupby("NO_MUNICIPIO_ESC")["NOTA_MEDIA_OBJ"].mean().reset_index()
        med_mun.columns = ["Município","Nota Média"]
        fig = px.bar(med_mun.sort_values("Nota Média"), x="Nota Média", y="Município",
                     orientation="h", color="Nota Média", color_continuous_scale="Blues",
                     title="Nota Média ENEM por Município — Baixada Fluminense (2013–2022)",
                     template=TEMPLATE)
        fig.update_layout(height=400, showlegend=False, coloraxis_showscale=False,
                          margin=dict(l=0,r=10,t=50,b=10))
        st.plotly_chart(fig, width='stretch')
