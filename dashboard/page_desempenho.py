import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from constants import TEMPLATE, CORES_REDE

def render(enem):
    st.markdown("""<div class="sec"><h2>Desempenho no ENEM — Baixada Fluminense (2013–2022)</h2>
    <p>13 municípios · Evolução temporal · Distribuição por rede de ensino</p></div>""", unsafe_allow_html=True)

    # KPIs dinâmicos calculados a partir dos dados
    med_mun = enem.groupby("NO_MUNICIPIO_ESC")["NOTA_MEDIA_OBJ"].mean()
    media_regiao = enem["NOTA_MEDIA_OBJ"].mean()
    mun_maior = med_mun.idxmax()
    mun_menor = med_mun.idxmin()
    val_maior = med_mun.max()
    val_menor = med_mun.min()
    diferenca = val_maior - val_menor

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, f"{media_regiao:.1f}", "Média da região"),
        (c2, f"{val_maior:.1f}", f"Maior média — {mun_maior}"),
        (c3, f"{val_menor:.1f}", f"Menor média — {mun_menor}"),
        (c4, f"{diferenca:.1f} pts", "Diferença entre municípios"),
    ]:
        col.markdown(f'<div class="kpi"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>',
                     unsafe_allow_html=True)
    st.markdown("---")

    # Figura 1 — Série temporal como nos notebooks (linha + IC)
    st.markdown("#### Evolução da Nota Média Objetiva (Série Histórica)")
    serie = enem.groupby("NU_ANO")["NOTA_MEDIA_OBJ"].agg(["mean","sem"]).reset_index()
    serie.columns = ["Ano","Média","Erro"]
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=serie["Ano"], y=serie["Média"]+1.96*serie["Erro"],
        fill=None, mode="lines", line_color="rgba(37,99,235,0.15)", showlegend=False,
    ))
    fig1.add_trace(go.Scatter(
        x=serie["Ano"], y=serie["Média"]-1.96*serie["Erro"],
        fill="tonexty", mode="lines", line_color="rgba(37,99,235,0.15)",
        fillcolor="rgba(37,99,235,0.15)", name="IC 95%",
    ))
    fig1.add_trace(go.Scatter(
        x=serie["Ano"], y=serie["Média"], mode="lines+markers",
        line=dict(color="#2563eb", width=2.5), marker=dict(size=7),
        name="Nota Média Objetiva",
    ))
    fig1.update_layout(
        title="Evolução da Nota Média Objetiva do ENEM — Baixada Fluminense (2013–2022)",
        xaxis_title="Ano", yaxis_title="Nota Média Objetiva",
        template=TEMPLATE, height=380, margin=dict(l=0,r=10,t=50,b=10),
    )
    st.plotly_chart(fig1, width='stretch')
    # st.markdown("""<div class="ins">
    # <strong>Interpretação da Tendência Temporal:</strong><br>
    # Observa-se um período de estagnação de notas entre 2013 e 2019, que é rompido por uma queda severa nas edições de 2020 e 2021.
    # Esta retração coincide com o fechamento das escolas presenciais durante a pandemia de COVID-19. 
    # A literatura de Economia da Educação aponta que o impacto da crise pandêmica foi altamente assimétrico, penalizando estudantes de redes públicas periféricas
    # pela falta de infraestrutura de conectividade e ensino remoto. A recuperação parcial em 2022 ainda não atinge a média pré-pandemia,
    # sinalizando um efeito cicatriz de aprendizado que exigirá políticas de recomposição de longo prazo.
    # </div>""", unsafe_allow_html=True)

    # Figura 2 — Boxplot anual por rede (idêntico ao notebook)
    st.markdown("#### Distribuição Anual por Rede de Ensino")
    df_box = enem[enem["REDE"].isin(["Federal","Estadual","Municipal","Privada"])].copy()
    df_box["NU_ANO"] = df_box["NU_ANO"].astype(str)
    fig2 = px.box(df_box, x="NU_ANO", y="NOTA_MEDIA_OBJ", color="REDE",
                  color_discrete_map=CORES_REDE,
                  title="Evolução Anual da Distribuição de Notas por Rede (2013–2022)",
                  labels={"NU_ANO":"Ano","NOTA_MEDIA_OBJ":"Nota Média Objetiva","REDE":"Rede de Ensino"},
                  template=TEMPLATE)
    fig2.update_traces(marker=dict(size=2))
    fig2.update_layout(height=450, margin=dict(l=0,r=10,t=50,b=10))
    st.plotly_chart(fig2, width='stretch')
    # st.markdown("""<div class="ins">
    # <strong>Análise de Dispersão e Desigualdade de Rede:</strong><br>
    # O gráfico de caixa (boxplot) ilustra a severa estratificação educacional da região. 
    # A linha central de cada caixa representa a mediana (percentil 50) e as bordas representam o primeiro e terceiro quartil (Q1 e Q3). 
    # Notavelmente, a linha do terceiro quartil (Q3) da <strong>rede estadual</strong> (limite superior de 75% dos alunos) situa-se consistentemente abaixo da 
    # linha mediana da <strong>rede privada</strong>. Isso indica que apenas 25% dos alunos das escolas estaduais conseguem superar o aluno mediano privado.
    # A <strong>rede federal</strong>, devido ao seu processo seletivo próprio (vestibulinho) e alta atratividade, exibe a maior mediana geral e a menor amplitude
    # entre quartis, indicando homogeneidade de excelência selecionada na entrada.
    # </div>""", unsafe_allow_html=True)

    # Figura 6a/6b — Histograma + Violino (idêntico ao notebook)
    st.markdown("#### Distribuição de Notas: Pública vs Privada · Federal vs Estadual")
    col_a, col_b = st.columns(2)
    with col_a:
        fig6a = px.histogram(df_box, x="NOTA_MEDIA_OBJ", color="SETOR",
                             marginal="violin", barmode="overlay",
                             category_orders={"SETOR":["Pública","Privada"]},
                             color_discrete_map=CORES_REDE,
                             title="Pública vs Privada",
                             labels={"NOTA_MEDIA_OBJ":"Nota Média Objetiva","SETOR":"Rede"},
                             template=TEMPLATE)
        fig6a.update_traces(opacity=0.6)
        fig6a.update_layout(height=420, margin=dict(l=0,r=10,t=50,b=10))
        st.plotly_chart(fig6a, width='stretch')
    with col_b:
        df_fe = df_box[df_box["REDE"].isin(["Federal","Estadual"])]
        fig6b = px.histogram(df_fe, x="NOTA_MEDIA_OBJ", color="REDE",
                             marginal="violin", barmode="overlay",
                             category_orders={"REDE":["Federal","Estadual"]},
                             color_discrete_map=CORES_REDE,
                             title="Federal vs Estadual",
                             labels={"NOTA_MEDIA_OBJ":"Nota Média Objetiva","REDE":"Rede"},
                             template=TEMPLATE)
        fig6b.update_traces(opacity=0.6)
        fig6b.update_layout(height=420, margin=dict(l=0,r=10,t=50,b=10))
        st.plotly_chart(fig6b, width='stretch')

    # st.markdown("""<div class="ins">
    # <strong>Teoria de Densidade (Curvas de Kernel e Violinos):</strong><br>
    # Os gráficos de densidade com violinos integrados revelam o comportamento distributivo completo das notas.
    # A curva de densidade da rede <strong>Pública</strong> (que agrega estadual, federal e municipal) exibe um formato unimodal centrado
    # em torno de 470 pontos, com cauda estreita à direita. Em contraste, a rede <strong>Privada</strong>, embora também tenha alta dispersão, desloca todo o seu corpo 
    # distributivo para a direita (moda próxima a 540 pontos). <br>
    # O gráfico <strong>Federal vs Estadual</strong> ilustra o abismo intra-rede pública: a rede federal exibe uma densidade
    # simétrica e deslocada para notas de excelência (acima de 550 pts), assemelhando-se ou superando o perfil privado, 
    # enquanto a rede estadual (responsável pela maior parte das matrículas de ensino médio) concentra-se massivamente na base do gráfico.
    # </div>""", unsafe_allow_html=True)

    # Seção para cálculo e exibição da Moda de Notas
    st.markdown("---")
    st.markdown("""<div class="sec"><h2>Moda e Tendências Centrais de Desempenho</h2>
    <p>Comparação de Média, Mediana e Moda (Valor Mais Frequente) das notas</p></div>""", unsafe_allow_html=True)

    # Filtros interativos para a distribuição de moda
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        redes_disponiveis = ["Federal", "Estadual", "Municipal", "Privada"]
        redes_sel = st.multiselect(
            "Selecione as Redes de Ensino:",
            options=redes_disponiveis,
            default=redes_disponiveis,
            key="moda_rede_sel"
        )
    with col_f2:
        anos_disponiveis = sorted(enem["NU_ANO"].unique().tolist())
        ano_sel = st.selectbox(
            "Selecione o Ano:",
            ["Todos"] + [str(a) for a in anos_disponiveis],
            index=0,
            key="moda_ano_sel"
        )

    # Filtrar dados para cálculo de tendências centrais
    df_filtered = enem.copy()
    if redes_sel:
        df_filtered = df_filtered[df_filtered["REDE"].isin(redes_sel)]
    else:
        df_filtered = df_filtered[df_filtered["REDE"].isin([])]
        
    if ano_sel != "Todos":
        df_filtered = df_filtered[df_filtered["NU_ANO"] == int(ano_sel)]

    if not redes_sel:
        st.warning("Selecione pelo menos uma rede de ensino para calcular as tendências centrais.")
    elif len(df_filtered) > 0:
        # Cálculos das tendências centrais
        media = df_filtered["NOTA_MEDIA_OBJ"].mean()
        mediana = df_filtered["NOTA_MEDIA_OBJ"].median()
        # Para a moda, arredondamos as notas para o inteiro mais próximo para termos uma medida estável
        moda = df_filtered["NOTA_MEDIA_OBJ"].round().mode().iloc[0]

        # KPIs das Tendências Centrais
        c_kpi1, c_kpi2 = st.columns(2)
        with c_kpi1:
            st.markdown(f'<div class="kpi" style="border-color: #ef4444;"><div class="val" style="color: #ef4444;">{moda:.1f}</div><div class="lbl">Moda (Nota Mais Comum)</div></div>', unsafe_allow_html=True)
        with c_kpi2:
            st.markdown(f'<div class="kpi" style="border-color: #10b981;"><div class="val" style="color: #10b981;">{mediana:.1f}</div><div class="lbl">Mediana (Percentil 50)</div></div>', unsafe_allow_html=True)

        # Plotar Histograma com linhas de Média, Mediana e Moda
        redes_label = ", ".join(redes_sel) if len(redes_sel) < len(redes_disponiveis) else "Todas as Redes"
        fig_moda = px.histogram(
            df_filtered, 
            x="NOTA_MEDIA_OBJ",
            nbins=60,
            title=f"Distribuição de Notas com Medidas de Tendência Central — {redes_label} ({'Todos os Anos' if ano_sel == 'Todos' else ano_sel})",
            labels={"NOTA_MEDIA_OBJ": "Nota Média Objetiva", "count": "Quantidade de Alunos"},
            template=TEMPLATE,
            color_discrete_sequence=["#94a3b8"]
        )
        
        # Adicionar linhas verticais para tendências centrais
        fig_moda.add_vline(x=moda, line_width=3, line_dash="dash", line_color="#ef4444", 
                          annotation_text=f"Moda: {moda:.1f}", annotation_position="top left",
                          annotation_font_color="#ef4444")
        fig_moda.add_vline(x=mediana, line_width=3, line_dash="dash", line_color="#10b981", 
                          annotation_text=f"Mediana: {mediana:.1f}", annotation_position="bottom right",
                          annotation_font_color="#10b981")
        fig_moda.add_vline(x=media, line_width=3, line_dash="dash", line_color="#3b82f6", 
                          annotation_text=f"Média: {media:.1f}", annotation_position="top right",
                          annotation_font_color="#3b82f6")

        fig_moda.update_layout(
            height=450, 
            margin=dict(l=0, r=10, t=50, b=10),
            yaxis_title="Quantidade de Alunos"
        )
        st.plotly_chart(fig_moda, width='stretch')

        # Texto explicativo
        # st.markdown("""<div class="ins">
        # <strong>Moda, Assimetria e Desigualdade Educacional:</strong><br>
        # A <strong>Moda</strong> indica a nota mais frequente na amostra (calculada a partir do arredondamento para o inteiro mais próximo), correspondendo ao "pico" de concentração de estudantes.
        # A relação mútua entre as três tendências centrais descreve o formato da distribuição:
        # <ul>
        #     <li><strong>Assimetria Positiva (Média > Mediana > Moda)</strong>: Frequente nas redes <strong>Estadual</strong> e <strong>Municipal</strong>. A maior parte dos estudantes acumula-se nas notas baixas (próximas à moda de ~482 e ~452 pontos), e uma minoria de notas muito altas "puxa" a média para cima de forma artificial. Isso sugere um sistema com baixa equidade e barreira de excelência para a base de alunos.</li>
        #     <li><strong>Distribuição Centrada (Média ≈ Mediana ≈ Moda)</strong>: Visível quando analisamos a rede <strong>Federal</strong> (em torno de 600 pontos) e <strong>Privada</strong> (em torno de 530 pontos), caracterizando populações com perfil de desempenho mais homogêneo e simétrico, com menor proporção de alunos em situação de extrema vulnerabilidade cognitiva.</li>
        # </ul>
        # </div>""", unsafe_allow_html=True)
    else:
        st.warning("Sem dados suficientes para os filtros selecionados.")
