import streamlit as st

def render():
    st.markdown("""<div class="sec"><h2>Conclusões e Implicações de Política Pública</h2>
    <p>Síntese dos achados · Limitações · Agenda futura</p></div>""", unsafe_allow_html=True)

    st.markdown("""<div class="cnc">
    <strong>Questão (a) — Financiamento vs. Desempenho</strong><br>
    <em>"Em que medida a magnitude dos repasses do FUNDEB se correlaciona com o desempenho médio no ENEM nos municípios da Baixada Fluminense?"</em><br>
    <strong>Resposta:</strong> O volume de repasses do FUNDEB <strong>não é preditor significativo</strong> do desempenho individual no ENEM (r = −0,07; p = 0,85; R² = 0,18 com modelo completo). O financiamento é condição necessária, mas não suficiente, para a melhoria direta das notas.
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="cnc">
    <strong>Questão (b) — Mediação Socioeconômica e Tipologias</strong><br>
    <em>"Qual o papel das variáveis socioeconômicas na mediação dessa relação?"</em><br>
    <strong>Resposta:</strong> Renda familiar, escolaridade materna e tipo de rede (Privada, Estadual, Municipal ou Federal) explicam a maior parte da variância predizível do desempenho escolar.<br>
    Além disso, a análise de agrupamento revelou três tipologias de eficiência educacional na Baixada Fluminense (k = 3, Silhouette ≈ 0,42):<br>
    • <strong>Eficiência Relativa</strong> (Mesquita, Nilópolis, Nova Iguaçu, Paracambi, São João de Meriti, Seropédica): melhor nota média (496,0 pts) com repasse médio anual de R$ 156,6 Milhões por município.<br>
    • <strong>Paradoxo do Investimento</strong> (Duque de Caxias, Guapimirim, Itaguaí): maior repasse médio anual da região (R$ 493,1 Milhões por município), porém com rendimento cognitivo mediano.<br>
    • <strong>Vulnerabilidade Estrutural</strong> (Belford Roxo, Japeri, Magé, Queimados): pior desempenho cognitivo médio (475,7 pts) com repasse médio anual de R$ 123,1 Milhões por município.
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="cnc">
    <strong>Questão (c) — Padrões de Acesso via SISU</strong><br>
    <em>"Como se configuram os padrões de acesso ao ensino superior via SISU para os egressos dessas escolas?"</em><br>
    <strong>Resposta:</strong> O acesso ao ensino superior público é estruturalmente limitado para os egressos locais, apresentando uma taxa bruta de apenas 2,84%. Os candidatos da rede pública estão concentrados na faixa de menor competitividade ("Acesso Amplo", &lt;540 pts). A predominância de aprovações em Pedagogia (869), Química (719) e Administração (704) reflete restrições de desempenho mais do que preferências vocacionais puras.
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Implicações para Política Pública")
    col_a,col_b,col_c = st.columns(3)
    col_a.markdown("""**Foco em Eficiência**\n\nRedirecionar o debate do *quanto*
para o *como* os recursos são gastos. Gestão pedagógica supera volume de investimento.""")
    col_b.markdown("""**Intervenção Socioeconômica**\n\nRenda e escolaridade materna são os maiores preditores. Políticas de transferência de renda têm maior impacto
esperado que aumento nominal do FUNDEB.""")
    col_c.markdown("""**Ampliação de Vagas SISU**\n\nTaxa de 2,84% evidencia gargalo
severo. Expansão de vagas federais nas instituições públicas que atendem a Baixada (como UFRRJ e UFRJ) pode ser uma via para ampliar o acesso.""")

    st.markdown("---")
    st.markdown("### Limitações e Agenda Futura")
    st.markdown("""
| Limitação | Encaminhamento |
|---|---|
| **n = 13 municípios** — clusters instáveis | Testar **Ward Linkage** (fusões hierárquicas estáveis) e **DBSCAN** (identificação de ruído/outliers) |
| **Análise correlacional** — não causal | Desenhos quase-experimentais (Diferenças-em-diferenças, variáveis instrumentais) |
| **Descasamento Institucional do FUNDEB** — O repasse municipal avaliado atende infantil/fundamental (competência do município), enquanto o ENEM avalia o ensino médio (competência estadual/privada). | Incorporar dados de gastos estaduais com educação na região e detalhar despesas municipais por subfunção de ensino (via SIOPE). |
| **Recorte regional** | Expandir para outros estados para validar a generalização das tipologias |
    """)

    st.markdown("""<div class="ins">
    <strong>Validação de Agrupamento Proposta:</strong><br>
    <ul>
        <li><strong>Ward Linkage:</strong> Agrupamento hierárquico que minimiza a variância interna. Permite inspecionar a árvore de fusões (dendrograma) de forma contínua, ideal para amostras pequenas como $n=13$ sem impor um $K$ fixo.</li>
        <li><strong>DBSCAN:</strong> Agrupamento baseado em densidade que identifica regiões concentradas e classifica pontos isolados como ruído. Serve para verificar se algum município é um outlier estrutural completo que não deve pertencer a nenhum cluster.</li>
    </ul>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""<div style="text-align:center;color:#64748b;font-size:.85rem;padding:1rem;">
    <strong>Análise Multidimensional · ENEM · FUNDEB · SISU · Baixada Fluminense</strong><br>
    Alekssander Santos &amp; Vitória M. C. Chaves — PPGI · UFRJ · 2026<br>
    Python 3.10 · Polars · Scikit-Learn · Streamlit · Plotly
    </div>""", unsafe_allow_html=True)
