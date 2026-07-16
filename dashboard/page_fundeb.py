import streamlit as st
import plotly.express as px
from constants import TEMPLATE

def render(enem, fundeb, sisu_mun):
    st.markdown("""<div class="sec"><h2>FUNDEB & Correlação com Desempenho — Baixada Fluminense</h2>
    <p>13 municípios · O dinheiro público importa? Análise em dois níveis — municipal e individual</p></div>""",
                unsafe_allow_html=True)

    # Série temporal FUNDEB top5 — exclui 2026 (ano parcial) e converte ano para int
    top5_fund = fundeb.groupby("municipio")["total_geral"].sum().nlargest(5).index.tolist()
    fund_long = fundeb[
        fundeb["municipio"].isin(top5_fund) & (fundeb["ano"] <= 2024)
    ].copy()
    fund_long["ano"] = fund_long["ano"].astype(int)
    fund_long["total_bi"] = fund_long["total_geral"] / 1e9
    fund_long = fund_long.sort_values(["municipio","ano"])
    fig_fund = px.line(fund_long, x="ano", y="total_bi", color="municipio", markers=True,
                       title="Evolução dos Repasses do FUNDEB — Top 5 Municípios (R$ bilhões, 2011–2024)",
                       labels={"total_bi":"Repasse (R$ bi)","municipio":"Município","ano":"Ano"},
                       template=TEMPLATE)
    fig_fund.update_layout(height=360, margin=dict(l=0,r=10,t=50,b=10),
                           xaxis=dict(tickmode="linear", dtick=1))
    st.plotly_chart(fig_fund, width='stretch')
    # st.markdown("""<div class="ins">
    # <strong>Análise teórica da evolução orçamentária:</strong><br>
    # Os dados deflacionados pelo IPCA a preços de Dezembro/2024 mostram o real incremento de recursos na educação da Baixada Fluminense. 
    # Duque de Caxias lidera isoladamente com o maior volume de repasses do FUNDEB da região ao longo de toda a série histórica. 
    # Contudo, a literatura de Finanças Públicas capitaneada por <strong>Eric Hanushek (2003)</strong> aponta para o paradoxo de que incrementos de verba na educação básica 
    # não se traduzem automaticamente em ganho de qualidade ou desempenho, se não houver metas de gestão pedagógica clara e incentivos focados na eficiência escolar.
    # Sem controle de alocação de insumos, a verba incremental tende a ser capturada por despesas correntes de manutenção administrativa e folha de pagamentos inercial.
    # </div>""", unsafe_allow_html=True)

    st.markdown("---")
    # Figura 4 — Scatter FUNDEB × Nota (idêntico ao notebook)
    st.markdown("#### Dispersão: Repasses do FUNDEB × Nota Média do ENEM")
    enem_mun = enem.groupby(["NO_MUNICIPIO_ESC","NU_ANO"])["NOTA_MEDIA_OBJ"].mean().reset_index()
    enem_mun.columns = ["municipio","ano","nota_media"]
    df_master = fundeb.merge(enem_mun, on=["municipio","ano"], how="inner")
    df_master["total_milhoes"] = df_master["total_geral"] / 1e6
    fig4 = px.scatter(df_master, x="total_milhoes", y="nota_media",
                      hover_name="municipio", trendline="ols",
                      title="Dispersão: Repasses do FUNDEB vs. Nota Média do ENEM — Baixada Fluminense",
                      labels={"total_milhoes":"Total FUNDEB (Milhões R$)","nota_media":"Nota Média Objetiva"},
                      template=TEMPLATE)
    fig4.update_traces(marker=dict(opacity=0.5))
    fig4.update_layout(height=400, margin=dict(l=0,r=10,t=50,b=10))
    st.plotly_chart(fig4, width='stretch')

    # st.markdown("""<div class="ins">
    # <strong>Análise do Gráfico de Dispersão:</strong><br>
    # O gráfico de dispersão com a linha de tendência (OLS) detalha a relação entre o volume total anual de repasses do FUNDEB municipal e a nota média dos municípios no ENEM:
    # <ul style="margin-top:0.5rem; margin-bottom:0.5rem; padding-left:1.5rem;">
    #     <li><strong>Ausência de Correlação (Linha Plana):</strong> A linha de regressão linear (azul) é praticamente horizontal (reta/plana). Isso demonstra visualmente que <strong>não existe relação linear relevante</strong> entre o montante total de repasses do FUNDEB recebido pelo município e o desempenho médio dos seus estudantes no ENEM.</li>
    #     <li><strong>Alta Variabilidade na Base:</strong> A grande maioria dos pontos (municípios-ano) está concentrada na faixa de menor orçamento (à esquerda, abaixo de R$ 250 Milhões). Nessa mesma faixa, a variação das notas é máxima, indo de cerca de 470 a 560 pontos. Ou seja, sob os mesmos patamares de repasses, os municípios atingem resultados completamente distintos.</li>
    #     <li><strong>Grandes Repasses com Resultados Medianos:</strong> Os poucos pontos na extrema direita (acima de R$ 1 Bilhão) representam municípios com grandes volumes absolutos de repasses, mas que registram notas médias apenas intermediárias (entre 500 e 520 pontos), sem qualquer ganho de desempenho proporcional ao volume orçamentário.</li>
    #     <li><strong>Descasamento de Competências:</strong> Deve-se recordar que o repasse municipal do FUNDEB atende à educação infantil e ao ensino fundamental, ao passo que o ENEM avalia concluintes do Ensino Médio (gerido majoritariamente pelo Estado ou rede privada), o que reforça por que não observamos efeito direto ou linear no gráfico.</li>
    # </ul>
    # </div>""", unsafe_allow_html=True)
