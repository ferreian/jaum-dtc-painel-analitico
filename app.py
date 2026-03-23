"""
app.py — Painel Analítico JAUM DTC — Home
"""
from pathlib import Path
import streamlit as st
from utils.theme import aplicar_tema, page_header

st.set_page_config(
    page_title="Painel JAUM DTC",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_tema()
st.markdown("<style>.jaum-header img { height: 60px !important; }</style>", unsafe_allow_html=True)
page_header("Painel Analítico de Cultivares de Soja", "JAUM DTC · Stine Seed")

BASE_DIR = Path(__file__).parent

# ── Layout: intro + imagem | cards ───────────────────────────────────────────
col_esq, col_dir = st.columns([2, 3], gap="large")

with col_esq:
    st.markdown("""
<div style="margin-top: 1rem;">
    <p style="font-size:15px; color:#1A1A1A; line-height:1.8;">
        Painel multiano de análise de cultivares de soja do programa
        <strong>JAUM DTC</strong> — produtividade, doenças, caracterização
        agronômica e efeito de densidade de plantio.
    </p>
    <p style="font-size:13px; color:#6B7280; line-height:1.6; margin-top: 0.5rem;">
        &#127463;&#127479; Departamento Técnico de Culturas · Stine Brasil
    </p>
    <p style="font-size:14px; color:#374151; line-height:1.8; margin-top: 0.8rem;">
        Comece pelo <strong>Diagnóstico</strong> para confirmar o status
        dos dados antes de usar as análises.
    </p>
</div>
""", unsafe_allow_html=True)
    img_path = BASE_DIR / "assets" / "App development-amico.png"
    if img_path.exists():
        st.image(str(img_path), use_container_width=True)

# ── Cards de navegação ────────────────────────────────────────────────────────
PAGINAS = [
    {
        "icone": "🔄",
        "titulo": "Diagnóstico",
        "subtitulo": "Status dos dados",
        "descricao": "Verifique o carregamento das três safras, identifique inconsistências e confirme que os dados estão prontos antes de usar as análises.",
        "tags": ["Safras", "Integridade", "Pré-análise"],
    },
    {
        "icone": "📊",
        "titulo": "Análise Conjunta",
        "subtitulo": "Produtividade por cultivar",
        "descricao": "Compare sc/ha entre cultivares com LSD estatístico, análise de estabilidade, índice de confiança e ranking geral por safra e região.",
        "tags": ["sc/ha", "LSD", "Estabilidade", "Ranking"],
    },
    {
        "icone": "⚔️",
        "titulo": "Head-to-Head",
        "subtitulo": "Confronto direto entre materiais",
        "descricao": "Tabela de classificação de um cultivar versus todos os adversários. Analise vitórias, empates e derrotas local a local com donut e barras.",
        "tags": ["H2H", "Vitórias", "Confronto", "Local"],
    },
    {
        "icone": "🦠",
        "titulo": "Doenças",
        "subtitulo": "Reação e pressão de doenças",
        "descricao": "Avalie a reação dos cultivares às principais doenças da soja — Phytophthora, Oídio, Mancha Parda, Mancha Alvo, Cercospora e DFC — com classificação AS a R.",
        "tags": ["Doenças", "Resistência", "Pressão", "Classificação"],
    },
    {
        "icone": "🌿",
        "titulo": "Caracterização",
        "subtitulo": "Perfil agronômico da planta",
        "descricao": "Visualize o perfil visual da planta — distribuição de vagens por terço, altura, ciclo, PMG, inserção da 1ª vagem, cor da flor e hábito de crescimento.",
        "tags": ["Planta", "Vagens", "Altura", "Ciclo", "PMG"],
    },
    {
        "icone": "🌿",
        "titulo": "Análise de Densidade",
        "subtitulo": "Efeito da população de plantas",
        "descricao": "Avalie como a densidade de plantio afeta a produtividade. Grupos K-Means, regressão polinomial, perfil visual da planta por densidade e distribuição com LSD.",
        "tags": ["Densidade", "Regressão", "Grupos", "População"],
    },
    {
        "icone": "🗺️",
        "titulo": "Mapa",
        "subtitulo": "Desempenho por região geográfica",
        "descricao": "Visualize a produtividade média dos cultivares por estado, macro e microrregião. Identifique onde cada material se destaca geograficamente.",
        "tags": ["Mapa", "Estado", "Macro", "Micro", "Região"],
    },
    {
        "icone": "📷",
        "titulo": "Fotos e Comentários",
        "subtitulo": "Registros de campo",
        "descricao": "Acesse fotos e comentários registrados pelos técnicos em cada avaliação de campo, filtrados por cultivar, safra, local e fase fenológica.",
        "tags": ["Fotos", "Campo", "Comentários", "Avaliações"],
    },
]

with col_dir:
    st.markdown("""
<div style="margin: 0.2rem 0 1rem;">
    <p style="font-size:12px;font-weight:600;color:#6B7280;text-transform:uppercase;
              letter-spacing:0.07em;margin:0 0 4px;">Páginas do Painel</p>
    <h2 style="font-size:1.4rem;font-weight:700;color:#1A1A1A;margin:0;">
        O que você quer analisar hoje?
    </h2>
</div>
""", unsafe_allow_html=True)

    # Renderizar em grid 2 colunas dentro da coluna direita
    _linhas = [PAGINAS[i:i+2] for i in range(0, len(PAGINAS), 2)]

    for _linha in _linhas:
        _cols = st.columns(2, gap="small")
        for _ci, _pg in enumerate(_linha):
            with _cols[_ci]:
                _tags_html = "".join([
                    f'<span style="display:inline-block;background:#E9F7EF;color:#1E8449;'
                    f'font-size:10px;font-weight:600;padding:2px 8px;border-radius:20px;'
                    f'margin:2px 2px 0 0;">{t}</span>'
                    for t in _pg["tags"]
                ])
                st.markdown(f"""
<div style="border:1px solid #E5E7EB;border-radius:12px;padding:14px;
            background:#FFFFFF;min-height:180px;
            box-shadow:0 1px 4px rgba(0,0,0,0.06);">
  <div style="font-size:22px;margin-bottom:6px;">{_pg['icone']}</div>
  <p style="font-size:14px;font-weight:700;color:#1A1A1A;margin:0 0 2px;">{_pg['titulo']}</p>
  <p style="font-size:11px;color:#6B7280;margin:0 0 8px;font-weight:500;">{_pg['subtitulo']}</p>
  <p style="font-size:12px;color:#374151;line-height:1.5;margin:0 0 10px;">{_pg['descricao']}</p>
  <div>{_tags_html}</div>
</div>
""", unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

st.divider()
st.markdown(
    '<p style="font-size:13px;color:#374151;text-align:center;">Painel JAUM DTC · Stine Seed · '
    'Desenvolvido por <a href="https://www.linkedin.com/in/eng-agro-andre-ferreira/" '
    'target="_blank" style="color:#27AE60;text-decoration:none;">Andre Ferreira</a></p>',
    unsafe_allow_html=True,
)
