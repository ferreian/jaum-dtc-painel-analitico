"""
pages/6_Fotos_Comentarios.py — Fotos e Comentários de Campo
"""
import pandas as pd
import streamlit as st

from utils.theme import aplicar_tema, page_header, secao_titulo
from utils.loader import carregar_detalhe_enriquecidas
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

st.set_page_config(
    page_title="Fotos e Comentários · JAUM DTC",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded",
)

aplicar_tema()

st.markdown("""
<style>
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] { color: #374151 !important; opacity: 1 !important; }
.foto-card {
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    overflow: hidden;
    background: #FFFFFF;
    margin-bottom: 12px;
}
.foto-card img {
    width: 100%;
    height: 200px;
    object-fit: cover;
    display: block;
}
.foto-info {
    padding: 8px 10px;
    font-size: 12px;
    color: #374151;
    font-family: 'Helvetica Neue', sans-serif;
}
.foto-cultivar {
    font-weight: 700;
    font-size: 13px;
    color: #111827;
    margin-bottom: 2px;
}
.foto-fazenda { color: #6B7280; margin-bottom: 2px; }
.foto-data    { color: #9CA3AF; font-size: 11px; }
.nota-badge {
    background: #F3F4F6;
    border-left: 3px solid #27AE60;
    padding: 4px 8px;
    border-radius: 0 4px 4px 0;
    font-size: 12px;
    color: #374151;
    margin-top: 4px;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)

AG_CSS = {
    ".ag-header":                  {"background-color": "#4A4A4A !important"},
    ".ag-header-row":              {"background-color": "#4A4A4A !important"},
    ".ag-header-cell":             {"background-color": "#4A4A4A !important"},
    ".ag-header-cell-label":       {"color": "#FFFFFF !important", "font-weight": "700"},
    ".ag-header-cell-text":        {"color": "#FFFFFF !important", "font-size": "13px !important", "font-weight": "700 !important"},
    ".ag-icon":                    {"color": "#FFFFFF !important", "opacity": "1 !important"},
    ".ag-header-cell-menu-button": {"opacity": "1 !important", "visibility": "visible !important"},
    ".ag-icon-menu":               {"color": "#FFFFFF !important", "opacity": "1 !important"},
    ".ag-icon-filter":             {"color": "#FFFFFF !important", "opacity": "1 !important"},
    ".ag-row":                     {"font-size": "13px !important"},
}

def ag_table(df, height=400):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        resizable=True, sortable=True, filter=True,
        cellStyle={"fontSize": "13px", "fontFamily": "Helvetica Neue, sans-serif"},
        wrapText=True, autoHeight=True,
    )
    gb.configure_grid_options(headerHeight=36, rowHeight=32, domLayout="normal")
    go = gb.build()
    go["defaultColDef"]["headerClass"] = "ag-header-black"
    AgGrid(
        df,
        gridOptions=go,
        height=height,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        custom_css=AG_CSS,
        theme="streamlit",
        use_container_width=True,
    )


# ── Nomes descritivos das avaliações ──────────────────────────────────────────
AV_NOMES = {
    "av1": "AV1 · Qualidade Faixa Inicial",
    "av2": "AV2 · Avaliação de Doenças",
    "av3": "AV3 · Floração Hábito de Crescimento",
    "av4": "AV4 · Arquitetura de Planta",
    "av5": "AV5 · Caracterização Agronômica",
    "av6": "AV6 · Acamamento de Planta",
    "av7": "AV7 · Colheita",
}

# ── Carregamento ──────────────────────────────────────────────────────────────
page_header(
    "Fotos e Comentários de Campo",
    "Registros fotográficos e observações feitas pelos responsáveis DTC durante as avaliações.",
    imagem="Taking notes-amico.png",
)

with st.spinner("Carregando registros..."):
    det = carregar_detalhe_enriquecidas()

# Verificar se tem algum dado
total = sum(len(df) for df in det.values())
if total == 0:
    st.error("❌ Nenhum dado disponível. Verifique se as pastas tabelas_detalhe_enriquecidas estão preenchidas.")
    st.stop()

# ── Concatenar tudo para extrair opções de filtro ────────────────────────────
df_all = pd.concat(
    [df.assign(_av=av_key) for av_key, df in det.items() if not df.empty],
    ignore_index=True,
)

# ── Sidebar — Filtros ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<p style="font-size:11px;font-weight:600;color:#6B7280;text-transform:uppercase;'
        'letter-spacing:0.05em;padding:0.5rem;">Filtros</p>',
        unsafe_allow_html=True,
    )

    if st.button("🔄 Limpar filtros", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith("fc_"):
                del st.session_state[key]
        st.rerun()

    def checkboxes_fc(opcoes, prefix, default_all=False):
        sel = []
        for o in opcoes:
            if st.checkbox(str(o), value=default_all, key=f"{prefix}_{o}"):
                sel.append(o)
        return sel

    # Safra — todos desmarcados por default
    with st.expander("📅 Safra", expanded=True):
        safras_all = sorted(df_all["safra"].dropna().unique().tolist()) if "safra" in df_all.columns else []
        safras_sel = []
        for o in safras_all:
            if st.checkbox(str(o), value=False, key=f"fc_safra_{o}"):
                safras_sel.append(o)

    df_f1 = df_all[df_all["safra"].isin(safras_sel)] if safras_sel and "safra" in df_all.columns else df_all.copy()

    # Status — default desmarcado
    with st.expander("🏷️ Status", expanded=False):
        status_all = sorted(df_f1["status_material"].dropna().unique().tolist()) if "status_material" in df_f1.columns else []
        status_sel = checkboxes_fc(status_all, "fc_status", default_all=False)

    df_f2 = df_f1[df_f1["status_material"].isin(status_sel)] if status_sel and "status_material" in df_f1.columns else df_f1.copy()

    # Tipo de Teste
    with st.expander("🔬 Tipo de Teste", expanded=False):
        tipos_all = sorted(df_f2["tipoTeste"].dropna().unique().tolist()) if "tipoTeste" in df_f2.columns else []
        tipos_sel = checkboxes_fc(tipos_all, "fc_tipo", default_all=False)

    df_f2b = df_f2[df_f2["tipoTeste"].isin(tipos_sel)] if tipos_sel and "tipoTeste" in df_f2.columns else df_f2.copy()

    # Fazenda
    with st.expander("🏡 Fazenda", expanded=False):
        fazendas_all = sorted(df_f2b["nomeFazenda"].dropna().unique().tolist()) if "nomeFazenda" in df_f2b.columns else []
        fazendas_sel = checkboxes_fc(fazendas_all, "fc_fazenda", default_all=False)

    df_f3 = df_f2b[df_f2b["nomeFazenda"].isin(fazendas_sel)] if fazendas_sel and "nomeFazenda" in df_f2b.columns else df_f2b.copy()

    # Cultivar
    with st.expander("🌱 Cultivar", expanded=False):
        cultivares_all = sorted(df_f3["dePara"].dropna().unique().tolist()) if "dePara" in df_f3.columns else []
        cultivares_sel = checkboxes_fc(cultivares_all, "fc_cult", default_all=False)

    df_filtrado = df_f3[df_f3["dePara"].isin(cultivares_sel)] if cultivares_sel and "dePara" in df_f3.columns else df_f3.copy()

    # Mostrar só com foto / comentário
    st.markdown("---")
    mostrar_fotos    = st.checkbox("Somente com foto",       value=False, key="fc_so_foto")
    mostrar_notas    = st.checkbox("Somente com comentário", value=False, key="fc_so_nota")

if df_filtrado.empty:
    st.warning("⚠️ Nenhum registro para os filtros selecionados.")
    st.stop()

# ── Abas por avaliação ────────────────────────────────────────────────────────
avs_com_dados = [av for av in AV_NOMES if not det[av].empty]
tab_labels    = [AV_NOMES[av] for av in avs_com_dados]
tabs          = st.tabs(tab_labels)

for tab, av_key in zip(tabs, avs_com_dados):
    with tab:
        # Filtrar para esta avaliação
        df_av = df_filtrado[df_filtrado["_av"] == av_key].copy()

        if "photoUrl" in df_av.columns and mostrar_fotos:
            df_av = df_av[df_av["photoUrl"].notna() & (df_av["photoUrl"] != "")]
        if "nota" in df_av.columns and mostrar_notas:
            df_av = df_av[df_av["nota"].notna() & (df_av["nota"] != "")]

        if df_av.empty:
            st.info("Nenhum registro para os filtros ativos nesta avaliação.")
            continue

        tem_foto  = "photoUrl" in df_av.columns and df_av["photoUrl"].notna().any()
        tem_nota  = "nota"     in df_av.columns and df_av["nota"].notna().any()

        n_fotos = df_av["photoUrl"].notna().sum() if "photoUrl" in df_av.columns else 0
        n_notas = df_av["nota"].notna().sum()     if "nota"     in df_av.columns else 0

        st.caption(
            f"ℹ️ {len(df_av)} registros · {n_fotos} com foto · {n_notas} com comentário"
        )

        # ── Galeria de fotos ──────────────────────────────────────────────────
        if tem_foto:
            secao_titulo("Galeria de Fotos", "", "")
            df_fotos = df_av[df_av["photoUrl"].notna() & (df_av["photoUrl"] != "")].copy()

            if df_fotos.empty:
                st.info("Nenhuma foto disponível para os filtros ativos.")
            else:
                import streamlit.components.v1 as _components

                # Montar HTML da galeria com modal
                cards_html = ""
                for _, rec in df_fotos.iterrows():
                    cultivar = str(rec.get("dePara",      "—")).replace("'", "&#39;")
                    fazenda  = str(rec.get("nomeFazenda", "—")).replace("'", "&#39;")
                    data_val = rec.get("dataCriacao", None)
                    data_str = pd.to_datetime(data_val, errors="coerce").strftime("%d/%m/%Y") if pd.notna(data_val) else "—"
                    nota_val = rec.get("nota", None)
                    nota_str = str(nota_val).strip() if pd.notna(nota_val) and str(nota_val).strip() not in ("", "nan") else ""
                    foto_url = str(rec.get("photoUrl", "")).replace("'", "%27")

                    nota_badge = f'<div class="nota-badge">{nota_str}</div>' if nota_str else ""
                    cards_html += f"""
<div class="foto-card" onclick="openModal('{foto_url}','{cultivar}','{fazenda}','{data_str}')">
  <img src="{foto_url}" alt="{cultivar}" onerror="this.parentElement.style.display='none'"/>
  <div class="foto-info">
    <div class="foto-cultivar">{cultivar}</div>
    <div class="foto-fazenda">{fazenda}</div>
    <div class="foto-data">{data_str}</div>
    {nota_badge}
  </div>
</div>"""

                gallery_html = f"""
<!DOCTYPE html><html><head><style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Helvetica Neue',sans-serif;}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:4px;}}
.foto-card{{border:1px solid #E5E7EB;border-radius:10px;overflow:hidden;background:#fff;cursor:pointer;transition:transform .15s,box-shadow .15s;}}
.foto-card:hover{{transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.12);}}
.foto-card img{{width:100%;height:180px;object-fit:cover;display:block;}}
.foto-info{{padding:8px 10px;}}
.foto-cultivar{{font-weight:700;font-size:13px;color:#111827;margin-bottom:2px;}}
.foto-fazenda{{font-size:12px;color:#6B7280;margin-bottom:2px;}}
.foto-data{{font-size:11px;color:#9CA3AF;}}
.nota-badge{{background:#F3F4F6;border-left:3px solid #27AE60;padding:4px 8px;border-radius:0 4px 4px 0;font-size:11px;color:#374151;margin-top:4px;font-style:italic;}}
/* Modal */
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;align-items:center;justify-content:center;flex-direction:column;}}
.modal-overlay.active{{display:flex;}}
.modal-img{{max-width:90vw;max-height:80vh;object-fit:contain;border-radius:8px;box-shadow:0 8px 40px rgba(0,0,0,.5);}}
.modal-info{{color:#fff;text-align:center;margin-top:12px;}}
.modal-cultivar{{font-size:18px;font-weight:700;}}
.modal-sub{{font-size:13px;color:#D1D5DB;margin-top:4px;}}
.modal-close{{position:fixed;top:20px;right:28px;font-size:32px;color:#fff;cursor:pointer;line-height:1;opacity:.8;}}
.modal-close:hover{{opacity:1;}}
</style></head><body>
<div class="grid">{cards_html}</div>
<div class="modal-overlay" id="modal" onclick="closeModal(event)">
  <span class="modal-close" onclick="document.getElementById('modal').classList.remove('active')">✕</span>
  <img class="modal-img" id="modal-img" src="" alt=""/>
  <div class="modal-info">
    <div class="modal-cultivar" id="modal-cultivar"></div>
    <div class="modal-sub" id="modal-sub"></div>
    <a id="modal-download" href="" download="" target="_blank"
       style="display:inline-block;margin-top:12px;padding:8px 20px;background:#27AE60;color:#fff;
              border-radius:6px;font-size:13px;font-weight:600;text-decoration:none;cursor:pointer;">
      ⬇️ Baixar foto
    </a>
  </div>
</div>
<script>
function openModal(url,cultivar,fazenda,data){{
  document.getElementById('modal-img').src=url;
  document.getElementById('modal-cultivar').textContent=cultivar;
  document.getElementById('modal-sub').textContent=fazenda+' · '+data;
  var dl=document.getElementById('modal-download');
  dl.href=url;
  dl.download=cultivar.replace(/[^a-zA-Z0-9]/g,'_')+'_'+data.replace(/[/]/g,'-')+'.jpg';
  document.getElementById('modal').classList.add('active');
}}
function closeModal(e){{
  if(e.target===document.getElementById('modal'))
    document.getElementById('modal').classList.remove('active');
}}
document.addEventListener('keydown',function(e){{
  if(e.key==='Escape') document.getElementById('modal').classList.remove('active');
}});
</script>
</body></html>"""

                altura_galeria = max(250, (len(df_fotos) // 4 + 1) * 240 + 40)
                _components.html(gallery_html, height=altura_galeria, scrolling=True)

        # ── Tabela de comentários ─────────────────────────────────────────────
        if tem_nota:
            secao_titulo("Comentários", "", "")
            df_notas = df_av[df_av["nota"].notna() & (df_av["nota"].astype(str).str.strip() != "")].copy()

            if df_notas.empty:
                st.info("Nenhum comentário disponível para os filtros ativos.")
            else:
                col_map = {
                    "safra":          "Safra",
                    "nomeFazenda":    "Fazenda",
                    "dePara":         "Cultivar",
                    "status_material":"Status",
                    "tipoTeste":      "Tipo",
                    "dataCriacao":    "Data",
                    "nota":           "Comentário",
                }
                cols_disp = [c for c in col_map if c in df_notas.columns]
                df_show   = df_notas[cols_disp].rename(columns=col_map).copy()

                if "Data" in df_show.columns:
                    df_show["Data"] = pd.to_datetime(df_show["Data"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")

                ag_table(df_show, height=min(500, 36 + 40 * len(df_show) + 20))

st.divider()
st.markdown(
    '<p style="font-size:13px;color:#374151;text-align:center;">Painel JAUM DTC · Stine Seed · '
    'Desenvolvido por <a href="https://www.linkedin.com/in/eng-agro-andre-ferreira/" '
    'target="_blank" style="color:#27AE60;text-decoration:none;">Andre Ferreira</a></p>',
    unsafe_allow_html=True,
)
