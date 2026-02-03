"""
Módulo de autenticação da plataforma Gabriel - Análise de Contratos.

- **APP_PASSWORD**: senha de acesso geral; se definida, exige login antes de qualquer conteúdo.
- **ADMIN_PASSWORD**: senha de administrador; obrigatória para editar cláusulas e prompts.
"""
import streamlit as st
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

SESSION_KEY_AUTH = "admin_authenticated"
SESSION_KEY_APP_AUTH = "app_authenticated"


def obter_senha_admin() -> str:
    """
    Obtém a senha de administrador do arquivo .env.
    
    Returns:
        Senha de administrador ou string vazia se não configurada
    """
    return os.getenv("ADMIN_PASSWORD", "")


def obter_senha_app() -> str:
    """
    Obtém a senha geral da aplicação do arquivo .env.
    
    Returns:
        Senha geral da aplicação ou string vazia se não configurada
    """
    return os.getenv("APP_PASSWORD", "")


def verificar_senha(senha_digitada: str, senha_correta: str) -> bool:
    """
    Verifica se a senha digitada está correta.
    Usa comparação segura para evitar timing attacks.
    
    Args:
        senha_digitada: Senha fornecida pelo usuário
        senha_correta: Senha correta para comparação
        
    Returns:
        True se a senha estiver correta, False caso contrário
    """
    if not senha_correta:
        return True
    hash_digitado = hashlib.sha256(senha_digitada.encode()).hexdigest()
    hash_correto = hashlib.sha256(senha_correta.encode()).hexdigest()
    return hash_digitado == hash_correto


# ========= Autenticação de Administrador =========

def esta_autenticado() -> bool:
    """
    Verifica se o usuário está autenticado como administrador.
    Retorna True se não houver ADMIN_PASSWORD configurada.
    """
    if not obter_senha_admin():
        return True
    
    return st.session_state.get(SESSION_KEY_AUTH, False)


def autenticar(senha: str) -> bool:
    """
    Autentica o usuário com a senha de administrador fornecida.
    
    Args:
        senha: Senha fornecida pelo usuário
        
    Returns:
        True se a autenticação foi bem-sucedida, False caso contrário
    """
    senha_correta = obter_senha_admin()
    if verificar_senha(senha, senha_correta):
        st.session_state[SESSION_KEY_AUTH] = True
        return True
    return False


def desautenticar():
    """Remove a autenticação de administrador do usuário."""
    if SESSION_KEY_AUTH in st.session_state:
        del st.session_state[SESSION_KEY_AUTH]


# ========= Autenticação Geral da Aplicação =========

def esta_autenticado_app() -> bool:
    """
    Verifica se o usuário está autenticado para usar a aplicação.
    Retorna True se não houver APP_PASSWORD configurada.
    """
    if not obter_senha_app():
        return True
    
    return st.session_state.get(SESSION_KEY_APP_AUTH, False)


def autenticar_app(senha: str) -> bool:
    """
    Autentica o usuário com a senha geral da aplicação.
    
    Args:
        senha: Senha fornecida pelo usuário
        
    Returns:
        True se a autenticação foi bem-sucedida, False caso contrário
    """
    senha_correta = obter_senha_app()
    if verificar_senha(senha, senha_correta):
        st.session_state[SESSION_KEY_APP_AUTH] = True
        return True
    return False


def tela_login_inicial():
    """
    Exibe tela de login inicial da aplicação.
    Esta tela aparece antes de qualquer conteúdo se APP_PASSWORD estiver configurada.
    
    Returns:
        True se o usuário está autenticado, False caso contrário
    """
    if not obter_senha_app():
        return True
    if esta_autenticado_app():
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.title("🔐 Acesso à Plataforma")
        
        with st.form("login_form", clear_on_submit=False):
            senha = st.text_input(
                "Senha de Acesso",
                type="password",
                key="input_senha_app",
                help="Digite a senha e pressione Enter ou clique em Entrar"
            )
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        
        if submitted:
            if senha:
                if autenticar_app(senha):
                    st.success("✅ Autenticação bem-sucedida!")
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta. Tente novamente.")
            else:
                st.warning("⚠️ Digite a senha")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("💡 Entre em contato com o administrador se você não possui a senha de acesso.")
    
    return False


