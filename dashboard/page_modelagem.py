import streamlit as st
import pandas as pd
import plotly.express as px
from constants import OUT, TEMPLATE

def render(enem):
    st.markdown("""<div class="sec"><h2>Modelagem Preditiva — Baixada Fluminense</h2>
    <p>13 municípios · 50.110 observações · Random Forest · Importância das variáveis</p></div>""", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    for col,val,lbl in [
        (c1,"R² = 0,24","Random Forest — conjunto de teste"),
        (c2,"~53 pts","RMSE — Random Forest"),
        (c3,"77,7%","Rede Escolar (preditor principal)"),
    ]:
        col.markdown(f'<div class="kpi"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
                     unsafe_allow_html=True)
    st.markdown("---")
    
    st.info("No pré-processamento de codificação de variáveis (*One-Hot Encoding*), a **Rede Estadual** é omitida para servir como o nível de referência (*baseline*) em relação ao qual o ganho das redes Federal e Privada é mensurado.")
    
    # st.markdown("""<div class="ins">
    # <strong>Interpretação Científica das Métricas da Modelagem:</strong><br>
    # <ul style="margin-top:0.5rem; margin-bottom:0.5rem; padding-left:1.5rem;">
    #     <li><strong>R² (Coeficiente de Determinação) = 0,24:</strong> Indica que 24% da variabilidade das notas <em>individuais</em> do ENEM é explicada pelas variáveis socioeconômicas e regionais incluídas. Com o dataset completo de 50.110 observações, o modelo demonstra que o perfil do candidato explica quase um quarto da variabilidade total de notas.</li>
    #     <li><strong>RMSE (Raiz do Erro Quadrático Médio) ≈ 53 pontos:</strong> É a margem típica de erro nas previsões individuais. Considerando a escala do ENEM (300 a 800 pontos), o desvio de 53 pontos é uma taxa de dispersão aceitável para inferência demográfica regional.</li>
    #     <li><strong>Fator Preditor Dominante:</strong> A Renda Familiar é o preditor com maior peso isolado na árvore de decisão (84,9% da importância relativa), ratificando o forte peso das desigualdades econômicas sobre os resultados escolares individuais.</li>
    # </ul>
    # </div>""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("#### Importância das Variáveis (Random Forest)")
    rf_csv = OUT / "modelos/rf_feature_importance.csv"
    if rf_csv.exists():
        df_imp = pd.read_csv(rf_csv)
        fig_rf = px.bar(
            df_imp, x='Importance', y='Variável', orientation='h',
            color='Importance',
            color_continuous_scale='Viridis',
            labels={'Importance': 'Importância Acumulada', 'Variável': ''},
            template=TEMPLATE,
            height=400
        )
        fig_rf.update_layout(coloraxis_showscale=False, margin=dict(l=0,r=10,t=10,b=10))
        st.plotly_chart(fig_rf, width='stretch')
    else:
        st.warning("Arquivo 'rf_feature_importance.csv' não encontrado.")

    # st.markdown("""<div class="ins">
    # <strong>Importância das Variáveis (Random Forest):</strong><br>
    # Mede a contribuição e relevância de cada variável para reduzir a variabilidade (impureza) na previsão das notas:<br>
    # <ul>
    #     <li><strong>Renda e Escolaridade Materna</strong>: Lideram disparadas a importância (mais de 88% do peso explicativo somado), demonstrando que o contexto socioeconômico dita a maior parte do desempenho.</li>
    #     <li><strong>Município (Efeito Fixo)</strong>: Exibe relevância significativa, indicando que a localização e fatores locais (infraestrutura regional) influenciam a nota.</li>
    #     <li><strong>Repasse FUNDEB Municipal</strong>: Exibe a <strong>menor importância relativa</strong> do modelo, confirmando a baixíssima utilidade do repasse nominal para predizer a nota de alunos individuais.</li>
    # </ul>
    # </div>""", unsafe_allow_html=True)

    # Gráfico interativo de categorias de acesso — reproduz notebook
    st.markdown("#### Categorização de Acesso ao SISU por Nota Média")
    def categorizar(nota):
        if nota >= 700: return "Alta Demanda (≥700 pts)"
        elif nota >= 620: return "Média-Alta (620–699 pts)"
        elif nota >= 540: return "Média (540–619 pts)"
        else: return "Acesso Amplo (<540 pts)"

    df_cat = enem[enem["REDE"].isin(["Federal","Estadual","Municipal","Privada"])].copy()
    df_cat["Categoria"] = df_cat["NOTA_MEDIA_OBJ"].apply(categorizar)
    df_grp = df_cat.groupby(["REDE","Categoria"]).size().reset_index(name="n")
    tot2 = df_grp.groupby("REDE")["n"].transform("sum")
    df_grp["pct"] = (df_grp["n"]/tot2*100).round(1)
    ordem_cat = ["Alta Demanda (≥700 pts)","Média-Alta (620–699 pts)",
                 "Média (540–619 pts)","Acesso Amplo (<540 pts)"]
    fig_cat = px.bar(df_grp, x="REDE", y="pct", color="Categoria",
                     barmode="stack", category_orders={"Categoria":ordem_cat},
                     color_discrete_sequence=px.colors.qualitative.Safe,
                     title="Proporção por Categoria de Acesso ao SISU por Rede de Ensino",
                     labels={"pct":"Proporção (%)","REDE":"Rede de Ensino"},
                     template=TEMPLATE)
    fig_cat.update_layout(height=420, margin=dict(l=0,r=10,t=50,b=10))
    st.plotly_chart(fig_cat, width='stretch')
    st.markdown("""<div class="ins">
    <strong>Metodologia de Categorização e Simulação Preditiva:</strong><br>
    Como os microdados do SISU e do ENEM não possuem um identificador único comum (devido às políticas de anonimização e privacidade do INEP), foi empregada uma <strong>abordagem indireta baseada nas notas de corte históricas nacionais</strong> para classificar os candidatos do ENEM em 4 níveis de competitividade de acesso:<br>
    <ul>
        <li><strong>Alta Demanda (≥ 700 pts)</strong>: Cursos altamente concorridos (ex: Medicina, Direito, Engenharia).</li>
        <li><strong>Média-Alta (620–699 pts)</strong>: Cursos de concorrência elevada (ex: Administração, Ciência da Computação).</li>
        <li><strong>Média (540–619 pts)</strong>: Cursos de concorrência moderada (ex: Pedagogia, História, Geografia).</li>
        <li><strong>Acesso Amplo (< 540 pts)</strong>: Cursos com notas de corte baixas (ex: Licenciaturas de baixa procura, Tecnólogos).</li>
    </ul>
    </div>""", unsafe_allow_html=True)

    # Cards para os resultados do classificador
    c_cls1, c_cls2, c_cls3 = st.columns(3)
    for col, val, lbl in [
        (c_cls1, "98,0%", "Acurácia Global do Classificador"),
        (c_cls2, "0,99", "F1-Score — Acesso Amplo (Classe Majoritária)"),
        (c_cls3, "0,67", "F1-Score — Alta Demanda (Classe Minoritária)"),
    ]:
        col.markdown(f'<div class="kpi"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
                     unsafe_allow_html=True)
        

    # st.markdown("""<div class="wrn">
    # <strong>Por que R² = 0,24?</strong> O modelo prediz a nota <em>individual</em> com covariáveis
    # <em>municipais e categóricas</em> — constantes para todos os alunos do mesmo grupo.
    # Fatores não observados (esforço, qualidade docente, capital social) explicam a variância residual —
    # comportamento esperado em EDM com microdados socioeconômicos (James et al., 2023, Cap. 3).
    # </div>""", unsafe_allow_html=True)
