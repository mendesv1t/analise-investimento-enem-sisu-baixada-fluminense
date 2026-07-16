import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from constants import CLUSTER_LABELS, CLUSTER_COLORS, TEMPLATE

def render(clusters):
    # Seletor dinâmico de K na barra lateral ou no início da página
    k_sel = st.slider("Selecione o número de clusters (k):", min_value=2, max_value=7, value=3, step=1)

    st.markdown(f"""<div class="sec"><h2>Clusters K-Means — Baixada Fluminense (k = {k_sel})</h2>
    <p>13 municípios · Tipologias de eficiência educacional</p></div>""", unsafe_allow_html=True)

    cl = clusters.copy()
    cl["Repasse FUNDEB (R$M)"] = (cl["INVESTIMENTO_TOTAL"] / 1e6).round(1)
    cl["Taxa SISU (%)"] = (cl["TAXA_APROVACAO_SISU"]*100).round(1)
    cl["Nota ENEM"] = cl["NOTA_MEDIA"].round(1)

    # Execução do K-Means dinâmico
    X = cl[["NOTA_MEDIA","INVESTIMENTO_TOTAL","TAXA_APROVACAO_SISU"]].values
    Xs = StandardScaler().fit_transform(X)
    
    km = KMeans(n_clusters=k_sel, random_state=42, n_init=10)
    cl["Cluster"] = km.fit_predict(Xs)

    # Determinação das cores e nomes dos clusters
    if k_sel == 3:
        means = cl.groupby("Cluster")[["TAXA_APROVACAO_SISU", "INVESTIMENTO_TOTAL"]].mean()
        idx_high_inv = means["INVESTIMENTO_TOTAL"].idxmax()
        idx_low_score = means["TAXA_APROVACAO_SISU"].idxmin()
        idx_efficient = [i for i in range(3) if i not in (idx_high_inv, idx_low_score)][0]
        
        label_map = {
            idx_low_score: "Vulnerabilidade",
            idx_efficient: "Eficiência Relativa",
            idx_high_inv: "Paradoxo Invest."
        }
        color_map = {
            idx_low_score: "#ef4444",    # Vermelho (Pior Chances no SISU)
            idx_high_inv: "#eab308",     # Laranja/Amarelo (Chances Intermediárias)
            idx_efficient: "#22c55e"     # Verde (Melhores Chances no SISU)
        }
        cl["Label"] = cl["Cluster"].map(label_map)
        cl["Cor"] = cl["Cluster"].map(color_map)
    else:
        # Ordenar os clusters pela taxa média de aprovação no SISU para distribuir cores do pior ao melhor
        cluster_means = cl.groupby("Cluster")["TAXA_APROVACAO_SISU"].mean().sort_values()
        sorted_clusters = cluster_means.index.tolist()
        
        # Paleta de gradiente do Vermelho (pior) para o Verde (melhor) para diferentes valores de K
        gradient_colors = {
            2: ["#ef4444", "#22c55e"],
            3: ["#ef4444", "#eab308", "#22c55e"],
            4: ["#ef4444", "#f97316", "#84cc16", "#22c55e"],
            5: ["#ef4444", "#f97316", "#eab308", "#10b981", "#22c55e"],
            6: ["#ef4444", "#f97316", "#f59e0b", "#84cc16", "#0d9488", "#22c55e"],
            7: ["#ef4444", "#be123c", "#f97316", "#f59e0b", "#84cc16", "#0d9488", "#22c55e"]
        }
        selected_colors = gradient_colors.get(k_sel, px.colors.diverging.RdYlGn[::-1])
        
        label_map = {}
        color_map = {}
        for rank, c_id in enumerate(sorted_clusters):
            if rank == 0:
                label_map[c_id] = f"Cluster {c_id} (Piores Chances)"
            elif rank == k_sel - 1:
                label_map[c_id] = f"Cluster {c_id} (Melhores Chances)"
            else:
                label_map[c_id] = f"Cluster {c_id} (Intermediário {rank})"
            color_map[c_id] = selected_colors[rank]
            
        cl["Label"] = cl["Cluster"].map(label_map)
        cl["Cor"] = cl["Cluster"].map(color_map)

    color_map_pca = dict(zip(cl["Label"], cl["Cor"]))

    # Elbow + Silhouette interativo (reproduz notebook exato)
    st.markdown("#### Seleção de k ótimo — Elbow & Silhouette")
    inertia, sil = [], []
    K_range = range(2, 10)
    for k in K_range:
        km_eval = KMeans(n_clusters=k, random_state=42)
        lab = km_eval.fit_predict(Xs)
        inertia.append(km_eval.inertia_)
        sil.append(silhouette_score(Xs, lab))

    fig_elbow = make_subplots(specs=[[{"secondary_y":True}]])
    fig_elbow.add_trace(go.Scatter(x=list(K_range), y=inertia,
        name="Inércia (Elbow)", mode="lines+markers",
        marker=dict(color="blue")), secondary_y=False)
    fig_elbow.add_trace(go.Scatter(x=list(K_range), y=sil,
        name="Silhouette Score", mode="lines+markers",
        marker=dict(color="red")), secondary_y=True)
    fig_elbow.update_layout(title="Avaliação de k ótimo: Elbow vs Silhouette",
        xaxis_title="Número de Clusters (k)", template=TEMPLATE,
        height=380, margin=dict(l=0,r=10,t=50,b=10))
    fig_elbow.update_yaxes(title_text="Inércia", secondary_y=False, color="blue")
    fig_elbow.update_yaxes(title_text="Silhouette Score", secondary_y=True, color="red")
    st.plotly_chart(fig_elbow, width='stretch')

    # st.markdown("""<div class="ins">
    # <strong>Justificativa da escolha de k = 3 (Heurística e Qualitativa):</strong><br>
    # Com um espaço amostral reduzido (n = 13 municípios), critérios matemáticos puros como o Método do Cotovelo e o Escore de Silhouette não oferecem um ponto ótimo óbvio ou indiscutível devido à alta sensibilidade das métricas a observações individuais (instabilidade). Dessa forma:
    # <ul style="margin-top:0.5rem; margin-bottom:0.5rem; padding-left:1.5rem;">
    #     <li><strong>Heurística Visual ("No Olho"):</strong> A escolha de k = 3 é uma decisão predominantemente qualitativa e visual a partir das curvas de validação. O gráfico orienta a partição, mas não a determina matematicamente.</li>
    #     <li><strong>Interpretabilidade e Consistência Regional:</strong> K = 3 foi escolhido por gerar tipologias com forte aderência prática e teórica à realidade da Baixada (Eficiência Relativa, Paradoxo do Repasse e Vulnerabilidade Estrutural). Um k menor (k = 2) misturaria realidades muito distintas, enquanto um k maior (k ≥ 4) isolaria municípios em microgrupos artificiais (singletons).</li>
    # </ul>
    # </div>""", unsafe_allow_html=True)

    # PCA scatter interativo (reproduz notebook exato)
    st.markdown("#### Projeção PCA dos Clusters (Visualização Interativa)")
    X_pca = PCA(n_components=2, random_state=42).fit_transform(Xs)
    df_pca = pd.DataFrame(X_pca, columns=["PCA1","PCA2"])
    df_pca["Cluster"] = cl["Cluster"].astype(str).values
    df_pca["Label"]   = cl["Label"].values
    df_pca["Município"] = cl["NO_MUNICIPIO_ESC"].values
    fig_pca = px.scatter(df_pca, x="PCA1", y="PCA2", color="Label",
        text="Município", hover_name="Município",
        color_discrete_map=color_map_pca,
        title="Clusters dos Municípios (Visualização PCA)", template=TEMPLATE)
    fig_pca.update_traces(marker=dict(size=16, line=dict(width=1,color="DarkSlateGrey")),
                          textposition="top center")
    fig_pca.update_layout(height=460, margin=dict(l=0,r=10,t=50,b=10))
    st.plotly_chart(fig_pca, width='stretch')

    st.markdown("---")
    
    # Renderização dinâmica dos cards
    if k_sel == 3:
        st.markdown("### Descrição e Análise das Tipologias Municipais")
        col1, col2, col3 = st.columns(3)
        
        # 1. Eficiência Relativa
        df_eff = cl[cl["Cluster"] == idx_efficient]
        muns_eff = ", ".join(sorted(df_eff["NO_MUNICIPIO_ESC"].tolist()))
        avg_nota_eff = df_eff["Nota ENEM"].mean()
        avg_rep_eff = df_eff["Repasse FUNDEB (R$M)"].mean()
        avg_sisu_eff = df_eff["Taxa SISU (%)"].mean()
        
        with col1:
            st.markdown(f"""<div style="background:#f0fdf4; border-left:4px solid #22c55e; border-radius:0 8px 8px 0; padding:.9rem 1.1rem; margin:1rem 0; color:#14532d; font-size:.9rem;">
            <strong>Eficiência Relativa</strong><br>
            <span style="font-size: 0.85rem; color: #166534;">{muns_eff}</span><br><br>
            • <strong>Nota ENEM média:</strong> {avg_nota_eff:.1f} pts<br>
            • <strong>Repasse Médio:</strong> R$ {avg_rep_eff:.1f} M/ano<br>
            • <strong>Chances no SISU:</strong> {avg_sisu_eff:.1f}%<br><br>
            <strong>Análise:</strong> Unifica municípios com bom rendimento relativo sob orçamentos moderados. Mostra que a otimização de recursos e o capital social de vizinhança podem compensar investimentos nominais moderados.
            </div>""", unsafe_allow_html=True)
            
        # 2. Paradoxo do Repasse
        df_para = cl[cl["Cluster"] == idx_high_inv]
        muns_para = ", ".join(sorted(df_para["NO_MUNICIPIO_ESC"].tolist()))
        avg_nota_para = df_para["Nota ENEM"].mean()
        avg_rep_para = df_para["Repasse FUNDEB (R$M)"].mean()
        avg_sisu_para = df_para["Taxa SISU (%)"].mean()
        
        with col2:
            st.markdown(f"""<div style="background:#fefce8; border-left:4px solid #eab308; border-radius:0 8px 8px 0; padding:.9rem 1.1rem; margin:1rem 0; color:#713f12; font-size:.9rem;">
            <strong>Paradoxo do Repasse</strong><br>
            <span style="font-size: 0.85rem; color: #a16207;">{muns_para}</span><br><br>
            • <strong>Nota ENEM média:</strong> {avg_nota_para:.1f} pts<br>
            • <strong>Repasse Médio:</strong> R$ {avg_rep_para:.1f} M/ano<br>
            • <strong>Chances no SISU:</strong> {avg_sisu_para:.1f}%<br><br>
            <strong>Análise:</strong> Agrupa os municípios com maiores repasses orçamentários do FUNDEB. Contudo, o volume bruto de verba não se traduz proporcionalmente em melhora de proficiência, mantendo notas medianas.
            </div>""", unsafe_allow_html=True)
            
        # 3. Vulnerabilidade Estrutural
        df_vuln = cl[cl["Cluster"] == idx_low_score]
        muns_vuln = ", ".join(sorted(df_vuln["NO_MUNICIPIO_ESC"].tolist()))
        avg_nota_vuln = df_vuln["Nota ENEM"].mean()
        avg_rep_vuln = df_vuln["Repasse FUNDEB (R$M)"].mean()
        avg_sisu_vuln = df_vuln["Taxa SISU (%)"].mean()
        
        with col3:
            st.markdown(f"""<div style="background:#fef2f2; border-left:4px solid #ef4444; border-radius:0 8px 8px 0; padding:.9rem 1.1rem; margin:1rem 0; color:#991b1b; font-size:.9rem;">
            <strong>Vulnerabilidade Estrutural</strong><br>
            <span style="font-size: 0.85rem; color: #b91c1c;">{muns_vuln}</span><br><br>
            • <strong>Nota ENEM média:</strong> {avg_nota_vuln:.1f} pts<br>
            • <strong>Repasse Médio:</strong> R$ {avg_rep_vuln:.1f} M/ano<br>
            • <strong>Chances no SISU:</strong> {avg_sisu_vuln:.1f}%<br><br>
            <strong>Análise:</strong> Embora recebam patamares razoáveis de repasses, os determinantes socioeconômicos de alta vulnerabilidade social se sobrepõem ao impacto do investimento público.
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"### Descrição e Análise das Tipologias Municipais (k = {k_sel})")
        for c in sorted(cl["Cluster"].unique()):
            df_c = cl[cl["Cluster"] == c]
            muns = ", ".join(sorted(df_c["NO_MUNICIPIO_ESC"].tolist()))
            avg_nota = df_c["Nota ENEM"].mean()
            avg_rep = df_c["Repasse FUNDEB (R$M)"].mean()
            avg_sisu = df_c["Taxa SISU (%)"].mean()
            color = df_c["Cor"].iloc[0]
            st.markdown(f"""
            <div style="border-left: 5px solid {color}; background-color: #f8fafc; padding: 0.8rem 1.2rem; margin: 0.8rem 0; border-radius: 0 6px 6px 0;">
                <h5 style="margin: 0; color: #1e293b;">Cluster {c}</h5>
                <p style="margin: 0.3rem 0; font-size: 0.9rem; color: #475569;"><strong>Municípios:</strong> {muns}</p>
                <div style="display: flex; gap: 2rem; margin-top: 0.4rem; font-size: 0.85rem; color: #64748b;">
                    <span>• <strong>Nota ENEM média:</strong> {avg_nota:.1f} pts</span>
                    <span>• <strong>Repasse Médio:</strong> R$ {avg_rep:.1f} M/ano</span>
                    <span>• <strong>Chances no SISU:</strong> {avg_sisu:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Diagnóstico Regional")

    # Coordenadas e diagnóstico dos 13 municípios para o mapa
    coords = {
        "Belford Roxo": {"lat": -22.7641, "lon": -43.3995, "Atenção": "Nota ENEM baixa (474,7 pts) and menor taxa de aprovação no SISU (20,5%)"},
        "Duque de Caxias": {"lat": -22.7856, "lon": -43.3122, "Atenção": "Orçamento massivo do FUNDEB, mas nota apenas mediana no ENEM (493,7 pts)"},
        "Guapimirim": {"lat": -22.5358, "lon": -42.9825, "Atenção": "Volume considerável de repasse, porém nota ENEM intermediária"},
        "Itaguaí": {"lat": -22.8522, "lon": -43.7753, "Atenção": "Repasse elevado, contudo rendimento cognitivo mediano"},
        "Japeri": {"lat": -22.6425, "lon": -43.6533, "Atenção": "Pior nota média do ENEM da região (469,6 pts) e alta vulnerabilidade social"},
        "Magé": {"lat": -22.6517, "lon": -43.0311, "Atenção": "Nota ENEM baixa (486,1 pts) e baixa aprovação no SISU (19,7%)"},
        "Mesquita": {"lat": -22.7811, "lon": -43.4286, "Atenção": "Eficiência relativa: boa nota média sob orçamento moderado"},
        "Nilópolis": {"lat": -22.8089, "lon": -43.4175, "Atenção": "Boa nota média (501,9 pts) e forte engajamento no SISU"},
        "Nova Iguaçu": {"lat": -22.7533, "lon": -43.4489, "Atenção": "Maior polo educacional regional; nota média de 495,9 pts"},
        "Paracambi": {"lat": -22.6083, "lon": -43.7125, "Atenção": "Melhor nota média da Baixada (504,1 pts) sob orçamento moderado"},
        "Queimados": {"lat": -22.7153, "lon": -43.5539, "Atenção": "Baixo desempenho (472,3 pts) e alta vulnerabilidade econômica familiar"},
        "São João de Meriti": {"lat": -22.8039, "lon": -43.3719, "Atenção": "Eficiência média-alta com elevada densidade populacional"},
        "Seropédica": {"lat": -22.7431, "lon": -43.7072, "Atenção": "Beneficiada pelo capital de vizinhança acadêmica da UFRRJ; nota de 503,1 pts"}
    }

    # Criar DataFrame do mapa
    df_coords = pd.DataFrame.from_dict(coords, orient="index").reset_index().rename(columns={"index": "NO_MUNICIPIO_ESC"})
    
    # Fazer o merge direto (ambos usam nomes acentuados e padronizados do MAPA_NOME)
    df_map = cl.merge(df_coords, on="NO_MUNICIPIO_ESC")
    df_map["Município"] = df_map["NO_MUNICIPIO_ESC"]

    fig_map = px.scatter_mapbox(
        df_map,
        lat="lat",
        lon="lon",
        color="Label",
        size=[15] * len(df_map),
        hover_name="Município",
        hover_data={"lat": False, "lon": False, "Label": True, "Nota ENEM": ":.1f", "Repasse FUNDEB (R$M)": ":.1f", "Atenção": True},
        color_discrete_map=color_map_pca,
        zoom=9.3,
        template=TEMPLATE
    )

    fig_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": -22.70, "lon": -43.40},
        height=480,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.85)"
        )
    )
    fig_map.update_traces(marker=dict(opacity=0.9))
    st.plotly_chart(fig_map, width='stretch')
