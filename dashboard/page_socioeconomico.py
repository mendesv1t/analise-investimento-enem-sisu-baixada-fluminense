import streamlit as st
import pandas as pd
import plotly.express as px
from constants import TEMPLATE

def render(enem):
    st.markdown("""<div class="sec"><h2>Perfil Socioeconômico — Baixada Fluminense (2013–2022)</h2>
    <p>13 municípios · Distribuição de renda por rede · Renda vs. Desempenho</p></div>""", unsafe_allow_html=True)

    FAIXAS = {
        "Sem renda": ["Nenhuma renda"],
        "Até 1 SM": ["Até 1 SM"],
        "1–2 SM": ["De 1 a 1,5 SM", "De 1,5 a 2 SM"],
        "2–3 SM": ["De 2 a 2,5 SM", "De 2,5 a 3 SM"],
        "3–5 SM": ["De 3 a 4 SM", "De 4 a 5 SM"],
        "> 5 SM": [
            "De 5 a 6 SM", "De 6 a 7 SM", "De 7 a 8 SM", "De 8 a 9 SM", "De 9 a 10 SM",
            "De 10 a 12 SM", "De 12 a 15 SM", "De 15 a 20 SM", "Mais de 20 SM"
        ],
    }

    df_soc = enem[enem["REDE"].isin(["Federal","Estadual","Municipal","Privada"])].copy()
    df_soc["Faixa"] = "Outros"
    for faixa, vals in FAIXAS.items():
        mask = df_soc["RENDA_FAMILIAR"].isin(vals)
        df_soc.loc[mask,"Faixa"] = faixa
    df_soc_grp = df_soc.groupby(["REDE","Faixa"]).size().reset_index(name="n")
    tot = df_soc_grp.groupby("REDE")["n"].transform("sum")
    df_soc_grp["pct"] = (df_soc_grp["n"]/tot*100).round(1)
    df_soc_grp = df_soc_grp[df_soc_grp["Faixa"]!="Outros"]

    fig_soc = px.bar(df_soc_grp, x="REDE", y="pct", color="Faixa",
                     barmode="stack",
                     title="Distribuição de Renda Familiar por Rede de Ensino (%)",
                     labels={"pct":"Proporção (%)","REDE":"Rede de Ensino"},
                     category_orders={"Faixa":list(FAIXAS.keys())},
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     template=TEMPLATE)
    fig_soc.update_layout(height=420, margin=dict(l=0,r=10,t=50,b=10))
    st.plotly_chart(fig_soc, width='stretch')

    # st.markdown("""<div class="ins">
    # <strong>Composição Socioeconômica e a Teoria do Capital Cultural:</strong><br>
    # O sociólogo francês <strong>Pierre Bourdieu</strong> teoriza que o sistema educacional tende a reproduzir as desigualdades de classe de origem. 
    # O capital cultural (incorporado sob a forma de hábitos de leitura, linguagem e escolaridade dos pais) atua como o principal facilitador acadêmico.
    # O gráfico ilustra a severa segregação socioeconômica no território da Baixada:
    # A rede <strong>Estadual</strong> funciona como um amortecedor social direto, concentrando 48% de alunos pertencentes a famílias com renda até 1 salário mínimo. 
    # Já as redes <strong>Federal e Privada</strong> exibem proporções substancialmente maiores nas faixas superiores de renda (>5 salários mínimos).
    # Dessa forma, a variação de desempenho entre as redes escolares não reflete apenas a qualidade do ensino dentro da escola, mas principalmente
    # o <em>efeito de composição</em> da renda familiar e escolaridade que cada rede capta.
    # </div>""", unsafe_allow_html=True)

    st.markdown("#### Renda × Nota Média por Área de Conhecimento")
    areas = {
        "Ciências da Natureza":"NU_NOTA_CN",
        "Ciências Humanas":"NU_NOTA_CH",
        "Linguagens":"NU_NOTA_LC",
        "Matemática":"NU_NOTA_MT",
    }
    map_renda2 = {chr(i): i-ord('A')+1 for i in range(ord('A'), ord('Q')+1)}
    df_renda = enem.copy()
    df_renda["renda_num"] = df_renda["Q006"].map(map_renda2)
    df_renda = df_renda.dropna(subset=["renda_num"])
    df_renda["renda_faixa"] = pd.cut(df_renda["renda_num"],
        bins=[0,3,6,10,17], labels=["Até 2 SM","2–5 SM","5–10 SM","Acima 10 SM"])

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        area_sel = st.selectbox("Área de Conhecimento:", list(areas.keys()), key="socio_area_sel")
    with col_s2:
        rede_sel = st.selectbox("Rede de Ensino:", ["Todas", "Federal", "Estadual", "Municipal", "Privada"], index=0, key="socio_rede_sel")

    # Filtrar dados pela rede selecionada
    df_plot = df_renda.copy()
    if rede_sel != "Todas":
        df_plot = df_plot[df_plot["REDE"] == rede_sel]

    nota_col = areas[area_sel]
    
    if len(df_plot) > 0:
        df_ar = df_plot.groupby("renda_faixa")[nota_col].mean().reset_index()
        df_ar.columns = ["Faixa de Renda","Nota Média"]
        fig_ar = px.bar(df_ar, x="Faixa de Renda", y="Nota Média",
                        color="Nota Média", color_continuous_scale="Blues",
                        title=f"Renda Familiar × Nota — {area_sel} ({'Todas as Redes' if rede_sel == 'Todas' else 'Rede ' + rede_sel})",
                        template=TEMPLATE)
        fig_ar.update_layout(height=380, coloraxis_showscale=False,
                             margin=dict(l=0,r=10,t=50,b=10))
        st.plotly_chart(fig_ar, width='stretch')
    else:
        st.warning("Sem dados suficientes para a rede selecionada.")
    # st.markdown("""<div class="ins">
    # <strong>Inclinação do Gradiente Socioeconômico por Área:</strong><br>
    # O gráfico de barras interativo exibe o gradiente socioeconômico (a inclinação de melhora da nota conforme a renda cresce).
    # A literatura de avaliação em larga escala demonstra que o gradiente tende a ser mais íngreme nas disciplinas exatas, como 
    # <strong>Matemática e Ciências da Natureza</strong>. O aprendizado dessas matérias é altamente dependente da infraestrutura escolar 
    # (laboratórios, qualidade docente específica e material instrucional) e de suporte extracurricular privado (cursinhos). 
    # Já as notas de <strong>Linguagens e Ciências Humanas</strong>, embora também correlacionadas com a renda, exibem gradientes ligeiramente mais suaves,
    # pois dependem em parte do capital comunicativo familiar cotidiano.
    # </div>""", unsafe_allow_html=True)
