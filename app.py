"""
Aplicação principal Gabriel - Análise de Contratos.
Streamlit: home (seleção de tipo/idioma), autenticação e roteamento para páginas de análise.
"""
# --- Event loop: desabilitar uvloop para compatibilidade com nest_asyncio ---
# Manter no início do arquivo, antes de qualquer import que use asyncio.
import sys
import logging
import asyncio

try:
    if "uvloop" in sys.modules or hasattr(asyncio, "_uvloop_policy"):
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        print("[APP] uvloop detectado; usando event loop padrão para compatibilidade.")
except Exception as e:
    print(f"[APP] Aviso ao configurar event loop: {e}")

import streamlit as st

# --- Log: suprimir aviso "missing ScriptRunContext" ---
# O orquestrador usa ThreadPoolExecutor; callbacks on_progress/on_log rodam em worker threads sem contexto Streamlit.
class _FiltroScriptRunContext(logging.Filter):
    def filter(self, record):
        return "missing ScriptRunContext" not in (record.getMessage() or "")

_filtro_src = _FiltroScriptRunContext()
for h in logging.root.handlers:
    h.addFilter(_filtro_src)
logging.root.addFilter(_filtro_src)
for name in ("streamlit", "streamlit.runtime", "streamlit.runtime.scriptrunner_utils.script_run_context"):
    log = logging.getLogger(name)
    for h in log.handlers:
        h.addFilter(_filtro_src)
    log.addFilter(_filtro_src)
from modulos.t1_nda import render as render_nda
from modulos.t2_spa_cotas import render as render_spa_cotas
from modulos.t3_spa_aquisicao import render as render_spa_aquisicao
from modulos.t4_spa_desinvestimento import render as render_spa_desinvestimento
from modulos.t5_reg_fip import render as render_reg_fip
from modulos.t6_reg_fidc import render as render_reg_fidc
from modulos.t7_consultoria import render as render_consultoria
from modulos.t8_contrato_social_search import render as render_contrato_social_search
from modulos.t9_acordo_socios_search import render as render_acordo_socios_search
from modulos.t10_reg_fip_acquisition import render as render_reg_fip_acquisition
from modulos.t11_acordo_cotistas_acquisition import render as render_acordo_cotistas_acquisition
from modulos.auth import tela_login_inicial, obter_senha_app, esta_autenticado_app

# --- Autenticação e configuração da página ---
precisa_login = obter_senha_app()
esta_autenticado = esta_autenticado_app() if precisa_login else True

if precisa_login and not esta_autenticado:
    st.set_page_config(page_title="Acesso", page_icon="🔐", layout="centered")
else:
    st.set_page_config(page_title="Gabriel - Análise de Contratos", page_icon="📄", layout="wide")

if not tela_login_inicial():
    st.stop()

if "pagina" not in st.session_state:
    st.session_state.pagina = "home"
if "tipo_documento" not in st.session_state:
    st.session_state.tipo_documento = None
if "idioma_contrato" not in st.session_state:
    st.session_state.idioma_contrato = "pt"

# --- Página inicial ---
if st.session_state.pagina == "home":
    st.title("Gabriel - Análise de Contratos")
    
    idioma_selecionado = st.radio(
        "Idioma do documento:",
        options=["pt", "en"],
        format_func=lambda x: "Português" if x == "pt" else "English",
        index=0 if st.session_state.idioma_contrato == "pt" else 1,
        horizontal=True,
        key="select_idioma_home"
    )
    st.session_state.idioma_contrato = idioma_selecionado
    st.write("Selecione o tipo de documento para iniciar a análise:")

    st.write("Contratos Gerais")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("NDA", use_container_width=True):
            st.session_state.tipo_documento = "NDA"
            st.session_state.pagina = "analise"
            st.rerun()

    with col2:
        if st.button("Contrato de Consultoria/Side Letter", use_container_width=True):
            st.session_state.tipo_documento = "CONSULTORIA_SIDE_LETTER"
            st.session_state.pagina = "analise"
            st.rerun()

    st.write("SPAs (Share Purchase Agreements)")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("SPA de cotas de fundos (secundários)", use_container_width=True):
            st.session_state.tipo_documento = "SPA_COTAS"
            st.session_state.pagina = "analise"
            st.rerun()

    with col2:
        if st.button("SPA de aquisição de companhia", use_container_width=True):
            st.session_state.tipo_documento = "SPA_AQUISICAO"
            st.session_state.pagina = "analise"
            st.rerun()

    with col3:
        if st.button("SPA de desinvestimento de companhia", use_container_width=True):
            st.session_state.tipo_documento = "SPA_DESINVESTIMENTO"
            st.session_state.pagina = "analise"
            st.rerun()

    st.write("Regulamentos de Fundos (Primários)")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Regulamento de FIPs (primário)", use_container_width=True):
            st.session_state.tipo_documento = "REG_FIP"
            st.session_state.pagina = "analise"
            st.rerun()

    with col2:
        if st.button("Regulamento de FIDCs (primário)", use_container_width=True):
            st.session_state.tipo_documento = "REG_FIDC"
            st.session_state.pagina = "analise"
            st.rerun()

    st.write("Search Funds - Search Phase")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Contrato social de sociedade limitada", use_container_width=True):
            st.session_state.tipo_documento = "CONTRATO_SOCIAL_SEARCH"
            st.session_state.pagina = "analise"
            st.rerun()

    with col2:
        if st.button("Acordo de Sócios (search phase)", use_container_width=True):
            st.session_state.tipo_documento = "ACORDO_SOCIOS_SEARCH"
            st.session_state.pagina = "analise"
            st.rerun()

    st.write("Search Funds - Acquisition Phase")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Regulamento de FIP (acquisition phase)", use_container_width=True):
            st.session_state.tipo_documento = "REG_FIP_ACQUISITION"
            st.session_state.pagina = "analise"
            st.rerun()

    with col2:
        if st.button("Acordo de Cotistas (acquisition phase)", use_container_width=True):
            st.session_state.tipo_documento = "ACORDO_COTISTAS_ACQUISITION"
            st.session_state.pagina = "analise"
            st.rerun()

# --- Páginas de análise (roteamento por tipo de documento) ---
elif st.session_state.pagina == "analise":
    if st.session_state.tipo_documento == "NDA":
        render_nda()
    elif st.session_state.tipo_documento == "SPA_COTAS":
        render_spa_cotas()
    elif st.session_state.tipo_documento == "SPA_AQUISICAO":
        render_spa_aquisicao()
    elif st.session_state.tipo_documento == "SPA_DESINVESTIMENTO":
        render_spa_desinvestimento()
    elif st.session_state.tipo_documento == "REG_FIP":
        render_reg_fip()
    elif st.session_state.tipo_documento == "REG_FIDC":
        render_reg_fidc()
    elif st.session_state.tipo_documento == "CONSULTORIA_SIDE_LETTER":
        render_consultoria()
    elif st.session_state.tipo_documento == "CONTRATO_SOCIAL_SEARCH":
        render_contrato_social_search()
    elif st.session_state.tipo_documento == "ACORDO_SOCIOS_SEARCH":
        render_acordo_socios_search()
    elif st.session_state.tipo_documento == "REG_FIP_ACQUISITION":
        render_reg_fip_acquisition()
    elif st.session_state.tipo_documento == "ACORDO_COTISTAS_ACQUISITION":
        render_acordo_cotistas_acquisition()
