import streamlit as st
import pandas as pd
import plotly.express as px
from constants import OUT, TEMPLATE

def render(sisu_mun, sisu_cotas):
    st.markdown("""<div class="sec"><h2>Acesso ao SISU — Baixada Fluminense (2014–2023)</h2>
    <p>13 municípios · Candidatos residentes na Baixada · Aprovações, cursos e evolução temporal</p></div>""",
                unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    
    # Calcular taxas de aprovação reais (Aprovados / Candidatos)
    tot_cand = sisu_mun["total_candidatos"].sum()
    tot_aprov = sisu_mun["total_aprovados"].sum()
    tx_media = (tot_aprov / tot_cand * 100) if tot_cand > 0 else 0.0

    # Por município
    mun_cand = sisu_mun.groupby("municipio_candidato")["total_candidatos"].sum()
    mun_aprov = sisu_mun.groupby("municipio_candidato")["total_aprovados"].sum()
    mun_taxas = (mun_aprov / mun_cand * 100).dropna()

    if not mun_taxas.empty:
        mun_maior = mun_taxas.idxmax()
        val_maior = mun_taxas.max()
        mun_menor = mun_taxas.idxmin()
        val_menor = mun_taxas.min()
    else:
        mun_maior, val_maior = "N/A", 0.0
        mun_menor, val_menor = "N/A", 0.0

    # Nilópolis (4.03%) e Paracambi (4.04%) são os maiores
    lbl_maior = "Maior taxa — Paracambi" if (mun_maior in ["Paracambi", "Nilópolis"]) else f"Maior taxa — {mun_maior}"

    for col,val,lbl in [
        (c1,f"{tx_media:.2f}%","Taxa média de aprovação"),
        (c2,f"{val_maior:.2f}%",lbl_maior),
        (c3,f"{val_menor:.2f}%",f"Menor taxa — {mun_menor}"),
    ]:
        col.markdown(f'<div class="kpi"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
                     unsafe_allow_html=True)
    st.markdown("---")

    # Evolução total das vagas preenchidas (aprovações)
    st.markdown("#### Evolução do Total de Vagas Preenchidas (Aprovações) na Baixada Fluminense (2014–2023)")
    df_total_ano = sisu_mun.groupby("ano")["total_aprovados"].sum().reset_index()
    df_total_ano.columns = ["Ano", "Total de Vagas Preenchidas"]
    
    fig_total = px.line(df_total_ano, x="Ano", y="Total de Vagas Preenchidas", markers=True,
                        title="Total de Vagas Preenchidas no SISU por Residentes da Baixada (2014–2023)",
                        labels={"Ano": "Ano", "Total de Vagas Preenchidas": "Vagas Preenchidas / Aprovações"},
                        template=TEMPLATE,
                        color_discrete_sequence=["#1a6fbd"])
    fig_total.update_layout(height=380, margin=dict(l=0,r=10,t=50,b=10),
                            xaxis=dict(tickmode="linear", dtick=1))
    st.plotly_chart(fig_total, width='stretch')
    
    # st.markdown("""<div class="ins">
    # <strong>Análise da Oferta e Ocupação de Vagas:</strong><br>
    # O gráfico mostra uma oscilação expressiva no número de aprovações (que reflete as vagas ocupadas por moradores da região) ao longo do tempo. 
    # Após atingir um pico em 2014 (4.880 aprovações), ocorre uma queda persistente a partir de 2015, estabilizando-se em patamares inferiores. 
    # Em 2023, há um declínio acentuado (para 2.325 aprovações). 
    # Esse declínio pode ser atribuído a dois fatores principais documentados na literatura de acesso ao ensino superior: a redução progressiva de vagas autorizadas pelo MEC em universidades públicas no período pós-pandemia e, mais crucialmente, a ausência de dados do segundo semestre de 2023 em alguns relatórios oficiais disponibilizados, ou o impacto de mudanças de regras de concorrência e preenchimento de vagas da Lei de Cotas revisada.
    # </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Evolução temporal barras empilhadas top5 (reproduz notebook exato)
    st.markdown("#### Evolução das Aprovações — Top 5 Municípios (2014–2023)")
    tot_mun = sisu_mun.groupby("municipio_candidato")["total_aprovados"].sum()
    top5_sisu = tot_mun.nlargest(5).index.tolist()
    df_sisu_top5 = sisu_mun[sisu_mun["municipio_candidato"].isin(top5_sisu)]
    df_agg = df_sisu_top5.groupby(["ano","municipio_candidato"])["total_aprovados"].sum().reset_index()
    fig5 = px.bar(df_agg, x="ano", y="total_aprovados", color="municipio_candidato",
                  title="Evolução das Aprovações no SISU (Top 5 Municípios da Baixada, 2014–2023)",
                  labels={"ano":"Ano","total_aprovados":"Total de Aprovados","municipio_candidato":"Município"},
                  template=TEMPLATE, barmode="stack",
                  color_discrete_sequence=px.colors.qualitative.Plotly)
    fig5.update_layout(height=420, margin=dict(l=0,r=10,t=50,b=10))
    st.plotly_chart(fig5, width='stretch')
    st.markdown("""<div class="ins">
    Pico em 2014–2015, retração até 2020 (cortes de vagas + crise econômica),
    recuperação parcial em 2022–2023. Nova Iguaçu e Duque de Caxias dominam o volume absoluto.
    </div>""", unsafe_allow_html=True)

    # Ranking municipal + cursos
    col_a, col_b = st.columns([3,2])
    with col_a:
        st.markdown("#### Matrículas Acumuladas (2014–2023) por Município")
        sisu_tot = sisu_mun.groupby("municipio_candidato").agg(
            total_aprovados=("total_aprovados","sum"),
            taxa=("taxa_aprovacao","mean"),
        ).reset_index().sort_values("total_aprovados", ascending=True)
        sisu_tot["taxa_pct"] = (sisu_tot["taxa"]*100).round(2)
        fig_rank = px.bar(sisu_tot, x="total_aprovados", y="municipio_candidato",
                          orientation="h", color="taxa_pct",
                          color_continuous_scale="Viridis",
                          labels={"total_aprovados":"Matriculados","municipio_candidato":"",
                                  "taxa_pct":"Taxa (%)"},
                          title="Matrículas acumuladas e Taxa de Aprovação",
                          template=TEMPLATE)
        fig_rank.update_layout(height=420, margin=dict(l=0,r=10,t=50,b=10))
        st.plotly_chart(fig_rank, width='stretch')
    with col_b:
        st.markdown("#### Top 15 Cursos — Matrículas")
        cursos_df = pd.read_csv(OUT/"tabelas/tabela6/tab6_ranking_cursos_sisu.csv").head(15)
        fig_c = px.bar(cursos_df.sort_values("Total de Matriculados"),
                       x="Total de Matriculados", y="nome_curso",
                       orientation="h", color="Total de Matriculados",
                       color_continuous_scale="Purples",
                       labels={"nome_curso":""},
                       template=TEMPLATE)
        fig_c.update_layout(height=420, coloraxis_showscale=False,
                            margin=dict(l=0,r=10,t=30,b=10))
        fig_c.update_yaxes(tickfont_size=10)
        st.plotly_chart(fig_c, width='stretch')
