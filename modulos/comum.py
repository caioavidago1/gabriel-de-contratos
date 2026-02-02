import streamlit as st
from pathlib import Path
import json
import hashlib
import uuid
import re
import traceback
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import platform
import sys

# ========= Upload =========
def upload_docx(label: str, key: str = "upload_docx"):
    """
    Mostra um file_uploader para .docx e retorna o arquivo enviado ou None.
    """
    arquivo = st.file_uploader(
        label,
        type=["docx"],
        key=key,
    )
    return arquivo

# ========= DB local =========
DB_DIR = Path("db")
DB_DIR.mkdir(exist_ok=True)

# ========= Histórico de Análises =========
MAX_HISTORICO = 10  # Máximo de análises no histórico

def _inicializar_historico():
    """Inicializa o histórico de análises no session_state se não existir."""
    if "historico_analises" not in st.session_state:
        st.session_state.historico_analises = []

def _adicionar_ao_historico(
    nome_arquivo: str,
    tipo_contrato: str,
    idioma: str,
    resultado
) -> None:
    """
    Adiciona uma análise ao histórico da sessão.
    Mantém apenas as últimas MAX_HISTORICO análises.
    
    Args:
        nome_arquivo: Nome do arquivo analisado
        tipo_contrato: Tipo de contrato
        idioma: Idioma da análise
        resultado: Objeto ResultadoAnalise
    """
    _inicializar_historico()
    
    # Criar entrada do histórico (sem os bytes dos documentos para economizar memória)
    entrada = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": datetime.now().isoformat(),
        "nome_arquivo": nome_arquivo,
        "tipo_contrato": tipo_contrato,
        "idioma": idioma,
        "total_violacoes": len(resultado.violacoes),
        "total_conformidades": len(resultado.conformidades),
        "total_clausulas": resultado.total_clausulas,
        "tempo_total": resultado.tempo_total,
        "modelo_llm": resultado.modelo_llm_usado,
        "modelo_embedding": resultado.modelo_embedding_usado,
        "sucesso": resultado.sucesso,
        "mensagem": resultado.mensagem,
        # Armazenar dados essenciais para visualização (sem bytes)
        "violacoes": resultado.violacoes,
        "conformidades": resultado.conformidades,
    }
    
    # Adicionar ao início (mais recente primeiro)
    st.session_state.historico_analises.insert(0, entrada)
    
    # Manter apenas MAX_HISTORICO entradas
    if len(st.session_state.historico_analises) > MAX_HISTORICO:
        st.session_state.historico_analises = st.session_state.historico_analises[:MAX_HISTORICO]

def _obter_historico() -> list:
    """Retorna o histórico de análises."""
    _inicializar_historico()
    return st.session_state.historico_analises

def _limpar_historico():
    """Limpa todo o histórico de análises."""
    st.session_state.historico_analises = []

def carregar_clausulas(tipo: str, idioma: str = None):
    """
    Carrega cláusulas do arquivo JSON correspondente ao tipo.
    Normaliza o tipo para minúsculas para compatibilidade cross-platform.
    
    Args:
        tipo: Nome do tipo de contrato (ex: "NDA")
        idioma: Idioma do contrato ("pt" ou "en"). Se None, tenta "pt" primeiro, depois formato antigo.
    
    Returns:
        Lista de cláusulas do arquivo JSON. Lista vazia se arquivo não existir.
    """
    tipo_normalizado = tipo.lower()
    
    # Sempre tentar primeiro o formato com sufixo de idioma (padrão: "pt")
    idioma_para_buscar = idioma if idioma else "pt"
    path_com_sufixo = DB_DIR / f"{tipo_normalizado}_clausulas_{idioma_para_buscar}.json"
    
    if path_com_sufixo.exists():
        return json.loads(path_com_sufixo.read_text(encoding="utf-8"))
    
    # Fallback: formato antigo sem sufixo (retrocompatibilidade)
    path_sem_sufixo = DB_DIR / f"{tipo_normalizado}_clausulas.json"
    if path_sem_sufixo.exists():
        return json.loads(path_sem_sufixo.read_text(encoding="utf-8"))
    
    return []

def salvar_clausulas(tipo: str, clausulas: list, idioma: str = None):
    """
    Salva cláusulas no arquivo JSON correspondente ao tipo.
    Normaliza o tipo para minúsculas para compatibilidade cross-platform.
    Sempre usa formato com sufixo de idioma (padrão: "pt").
    
    Args:
        tipo: Nome do tipo de contrato (ex: "NDA")
        clausulas: Lista de cláusulas a salvar
        idioma: Idioma do contrato ("pt" ou "en"). Se None, usa "pt" como padrão.
    """
    tipo_normalizado = tipo.lower()
    idioma_para_salvar = idioma if idioma else "pt"
    path = DB_DIR / f"{tipo_normalizado}_clausulas_{idioma_para_salvar}.json"
    path.write_text(
        json.dumps(clausulas, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

# ========= Sidebar - Informações =========
def sidebar_informacoes(tipo_nome: str):
    """
    Exibe botão de informação com guias sobre edição de prompts e estrutura JSON.
    """
    from analise.agent import AGENTES, DESCRICOES_AGENTES, RECOMENDACOES_POR_AGENTE
    
    with st.sidebar:
        with st.expander("ℹ️ Guia: Como editar instruções e regras", expanded=False):
            st.markdown("### 📝 Como Editar Instruções da IA")
            
            st.markdown("As instruções orientam a IA na análise de contratos. São personalizáveis por tipo de contrato (NDA, SPA, etc.) e por idioma.")
            
            st.markdown("**Passo a passo:**")
            st.markdown("1. Na seção **Configurações** da sidebar, clique em **'Editar prompt'**")
            st.markdown("2. No bloco de acesso, digite a **senha de administrador** e clique em **'Entrar como administrador'**")
            st.markdown("3. O editor abre com **abas para cada tipo de análise** (agent3, agent4)")
            st.markdown("4. Edite **Mensagem System** e **Mensagem User** conforme necessário")
            st.markdown("5. Clique em **'Salvar Todos'** para aplicar ou **'Fechar'** para sair sem salvar")
            
            st.markdown("**Tipos de análise editáveis:**")
            agentes_editaveis_guia = [a for a in AGENTES if a != "extrator"]
            for agent in agentes_editaveis_guia:
                st.markdown(f"- **{DESCRICOES_AGENTES.get(agent, agent)}**")
                rec = RECOMENDACOES_POR_AGENTE.get(agent, {})
                if rec.get("system"):
                    st.caption(f"  📌 System: {rec['system']}")
                if rec.get("user"):
                    st.caption(f"  📌 User: {rec['user']}")
            
            st.markdown("**Tipos de mensagem:**")
            st.markdown("- **Mensagem System**: Comportamento geral do agente")
            st.markdown("- **Mensagem User**: Template que recebe os dados do documento (variáveis obrigatórias devem ser mantidas)")
            
            st.markdown("**Importante:**")
            st.markdown("- Mantenha todas as variáveis obrigatórias no template User")
            st.markdown("- Use **'Reset Todos'** para restaurar as instruções padrão")
            
            st.markdown("---")
            
            st.markdown("### 📄 Como Gerenciar Regras de Conformidade")
            
            st.markdown("As regras definem o que a IA verifica no contrato (conformidade com cláusulas de referência).")
            
            st.markdown("**Adicionar nova regra:**")
            st.markdown("1. Em **Configurações**, clique em **'Adicionar cláusula'**")
            st.markdown("2. Preencha:")
            st.markdown("   - **Nome da cláusula** (obrigatório): Ex.: _Confidencialidade de dados_, _Prazo de vigência_")
            st.markdown("   - **Descrição** (obrigatório): O que a IA deve verificar no contrato — critério de conformidade")
            st.markdown("   - **Buscar em** (obrigatório): Palavras-chave para busca semântica. Ex.: _vigência_, _prazo_, _confidencialidade_")
            st.markdown("   - **Como corrigir** (opcional): Sugestão de redação para correção")
            st.markdown("   - **Cláusula ativa**: Marque para incluir na análise")
            st.markdown("3. Clique em **'Salvar Cláusula'** — a base de regras é atualizada automaticamente")
            
            st.markdown("**Editar ou excluir:**")
            st.markdown("- Use **✏️** para editar e **❌** para excluir cada regra na lista")
            st.markdown("- Confirme em **'Confirmar Exclusão'** ao excluir")
            
            st.markdown("**Atualização da base:**")
            st.markdown("- A base é atualizada automaticamente ao **adicionar**, **editar** ou **excluir** regras")
            st.markdown("- Use **'Atualizar Base de Regras'** ao trocar o **modelo de IA** ou o **idioma do contrato**")
            
            st.markdown("**Visualizar:**")
            st.markdown("- As regras aparecem na sidebar do tipo de contrato atual, com editar (✏️) e excluir (❌).")

# ========= Sidebar - Histórico de Análises =========
def sidebar_historico():
    """
    Exibe o histórico de análises realizadas na sessão atual.
    Permite visualizar resumo de análises anteriores.
    """
    _inicializar_historico()
    historico = _obter_historico()
    
    with st.sidebar:
        with st.expander(f"📊 Histórico de Análises ({len(historico)})", expanded=False):
            if not historico:
                st.caption("Nenhuma análise realizada nesta sessão.")
                st.caption("As análises aparecerão aqui após serem concluídas.")
            else:
                for i, h in enumerate(historico):
                    # Formatar timestamp
                    try:
                        dt = datetime.fromisoformat(h["timestamp"])
                        hora_formatada = dt.strftime("%H:%M")
                    except:
                        hora_formatada = "?"
                    
                    # Card visual para cada análise
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            # Nome do arquivo truncado
                            nome = h.get("nome_arquivo", "Arquivo")
                            if len(nome) > 25:
                                nome = nome[:22] + "..."
                            st.markdown(f"**{nome}**")
                            
                            # Detalhes
                            tipo = h.get("tipo_contrato", "")
                            violacoes = h.get("total_violacoes", 0)
                            conformidades = h.get("total_conformidades", 0)
                            tempo = h.get("tempo_total", 0)
                            
                            # Status com cores
                            if violacoes == 0:
                                status_icon = "✅"
                                status_text = "Conforme"
                            elif violacoes <= 2:
                                status_icon = "⚠️"
                                status_text = f"{violacoes} problema(s)"
                            else:
                                status_icon = "🔴"
                                status_text = f"{violacoes} problemas"
                            
                            st.caption(f"{status_icon} {status_text} | {tempo:.1f}s | {hora_formatada}")
                        
                        with col2:
                            # Botão para ver detalhes
                            if st.button("Ver", key=f"hist_ver_{h['id']}", help="Ver detalhes desta análise"):
                                st.session_state.historico_selecionado = h
                                st.rerun()
                        
                        st.divider()
                
                # Botão para limpar histórico
                if st.button("Limpar Histórico", key="btn_limpar_historico", type="secondary"):
                    _limpar_historico()
                    st.rerun()

# ========= Sidebar - Botões de Ação =========
def sidebar_botoes(tipo_nome: str):
    """
    Sidebar com botões de ação para gerenciamento de cláusulas.
    Usa o embedding do session_state para reindexação.
    
    Args:
        tipo_nome: Nome do tipo de contrato (NDA, TIPO 2, etc)
    """
    from analise.embeddings.clausulas import GerenciadorClausulasReferencia
    from analise.agent.escolha_modelo import GerenciadorEmbeddings
    
    # Garantir que embedding_selecionado exista no session_state
    if 'embedding_selecionado' not in st.session_state:
        st.session_state.embedding_selecionado = "openai-small"  # Padrão
    
    # Obter idioma do session_state (padrão: pt)
    idioma = st.session_state.get('idioma_contrato', 'pt')
    
    clausulas = carregar_clausulas(tipo_nome, idioma=idioma)
    adicionar_clausula = st.session_state.get(f"adicionar_clausula_{tipo_nome}", False)

    def _reindexar_clausulas(clausulas_lista: list, idioma_param: str = None) -> bool:
        """
        Reindexa as cláusulas no ChromaDB após alterações.
        
        Args:
            clausulas_lista: Lista de cláusulas para indexar
            idioma_param: Idioma explícito para indexação. Se None, usa o idioma atual do session_state.
        """
        # Pegar embedding do session_state
        embedding_id = st.session_state.get('embedding_selecionado')
        if not embedding_id:
            st.warning("Selecione um modelo de IA para atualizar a base.")
            return False
        
        try:
            embedding_config = GerenciadorEmbeddings.obter_embedding(embedding_id)
            if not embedding_config:
                st.error(f"Modelo de IA '{embedding_id}' não encontrado.")
                return False
            
            embedding_function = GerenciadorEmbeddings.criar_embedding_function(embedding_config)
            gerenciador = GerenciadorClausulasReferencia()
            
            # Usar idioma explícito se fornecido, senão obter do session_state
            idioma_indexacao = idioma_param if idioma_param else st.session_state.get('idioma_contrato', 'pt')
            
            total = gerenciador.indexar_clausulas(tipo_nome, clausulas_lista, embedding_function, idioma=idioma_indexacao)
            st.success(f"Base de regras atualizada com {total} regras (idioma: {idioma_indexacao}).")
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar base: {e}")
            return False

    with st.sidebar:
        st.subheader(f"Configurações {tipo_nome}")

        # Botão para adicionar nova cláusula (sempre disponível)
        if not adicionar_clausula:
            if st.button("Adicionar cláusula", key=f"btn_adicionar_clausula_{tipo_nome}"):
                st.session_state[f"adicionar_clausula_{tipo_nome}"] = True
                st.rerun()
        else:
            st.markdown("### Nova Cláusula")
            nome = st.text_input(
                "Nome da cláusula",
                key=f"novo_nome_{tipo_nome}",
                help="Identificador da regra na plataforma e nos relatórios. Ex.: Confidencialidade de dados, Prazo de vigência."
            )
            descricao = st.text_area(
                "Descrição",
                key=f"nova_desc_{tipo_nome}",
                help="O que a IA deve verificar no contrato — critério de conformidade. Ex.: Garante que dados confidenciais não podem ser divulgados a terceiros sem autorização."
            )
            buscar_em = st.text_input(
                "Buscar em (palavras-chave para similaridade)",
                key=f"novo_buscar_em_{tipo_nome}",
                help="Termos usados na busca semântica. Ex.: vigência, prazo, confidencialidade. Obrigatório para a análise."
            )
            como_corrigir = st.text_area(
                "Como corrigir",
                key=f"novo_como_corrigir_{tipo_nome}",
                help="Sugestão de redação para correção (opcional)."
            )
            ativa_nova = st.checkbox(
                "Cláusula ativa",
                value=True,
                key=f"novo_ativa_{tipo_nome}",
                help="Se desmarcada, esta regra não será usada na análise de similaridade."
            )
            
            cols_add = st.columns(2)
            with cols_add[0]:
                if st.button("Salvar Cláusula", key=f"btn_salvar_clausula_{tipo_nome}"):
                    if not nome.strip():
                        st.error("O nome da cláusula é obrigatório.")
                    elif not descricao.strip():
                        st.error("A descrição é obrigatória.")
                    elif not buscar_em.strip():
                        st.error("O campo 'Buscar em' é obrigatório para a análise de similaridade.")
                    else:
                        nova_clausula = {
                            "ativa": ativa_nova,
                            "titulo": nome.strip(),
                            "regra_spectra": descricao.strip(),
                            "buscar_em": buscar_em.strip(),
                        }
                        if como_corrigir.strip():
                            nova_clausula["como_corrigir"] = como_corrigir.strip()
                        
                        clausulas.append(nova_clausula)
                        salvar_clausulas(tipo_nome, clausulas, idioma=idioma)
                        _reindexar_clausulas(clausulas, idioma_param=idioma)
                        st.success(f"Cláusula '{nome}' adicionada com sucesso!")
                        st.session_state[f"adicionar_clausula_{tipo_nome}"] = False
                        st.rerun()
            with cols_add[1]:
                if st.button("Cancelar", key=f"btn_cancelar_clausula_{tipo_nome}"):
                    st.session_state[f"adicionar_clausula_{tipo_nome}"] = False
                    st.rerun()

        # Botão para forçar atualização da base de regras
        if st.button(
            "Atualizar Base de Regras",
            key=f"btn_reindexar_{tipo_nome}",
            help="Atualiza o banco de dados com as regras atuais. Use após adicionar, editar ou excluir regras; ao trocar o modelo de IA; ou para forçar a sincronização."
        ):
            clausulas_atuais = carregar_clausulas(tipo_nome, idioma=idioma)
            _reindexar_clausulas(clausulas_atuais, idioma_param=idioma)

        # Botão para editar prompts dos agentes
        if st.button(
            "Editar prompt",
            key=f"btn_editar_prompt_{tipo_nome}",
            help="Abre o editor de instruções da IA (Análise de Conformidade, Sugestão de Redação, etc.) para o tipo de contrato atual. Requer senha de administrador para salvar ou resetar."
        ):
            st.session_state[f"editar_prompt_{tipo_nome}"] = True
            st.rerun()


# ========= Sidebar - Lista de Cláusulas =========
def sidebar_lista_clausulas(tipo_nome: str):
    """
    Exibe a lista de cláusulas existentes na sidebar com botões de edição e exclusão.
    
    Args:
        tipo_nome: Nome do tipo de contrato (NDA, TIPO 2, etc)
    """
    from analise.embeddings.clausulas import GerenciadorClausulasReferencia
    from analise.agent.escolha_modelo import GerenciadorEmbeddings
    
    # Obter idioma do session_state (padrão: pt)
    idioma = st.session_state.get('idioma_contrato', 'pt')
    
    def _reindexar_clausulas_lista(clausulas_lista: list, idioma_param: str = None) -> bool:
        """
        Reindexa as cláusulas no ChromaDB após alterações.
        """
        embedding_id = st.session_state.get('embedding_selecionado')
        if not embedding_id:
            st.warning("Selecione um modelo de IA para atualizar a base.")
            return False
        
        try:
            embedding_config = GerenciadorEmbeddings.obter_embedding(embedding_id)
            if not embedding_config:
                st.error(f"Modelo de IA '{embedding_id}' não encontrado.")
                return False
            
            embedding_function = GerenciadorEmbeddings.criar_embedding_function(embedding_config)
            gerenciador = GerenciadorClausulasReferencia()
            
            idioma_indexacao = idioma_param if idioma_param else st.session_state.get('idioma_contrato', 'pt')
            
            total = gerenciador.indexar_clausulas(tipo_nome, clausulas_lista, embedding_function, idioma=idioma_indexacao)
            st.success(f"Base de regras atualizada com {total} regras (idioma: {idioma_indexacao}).")
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar base: {e}")
            return False
    
    with st.sidebar:
        clausulas = carregar_clausulas(tipo_nome, idioma=idioma)
        if clausulas:
            for i, c in enumerate(clausulas):
                # Verificar se esta cláusula está sendo editada
                editando_idx = st.session_state.get(f"editando_clausula_{tipo_nome}", None)
                excluindo_idx = st.session_state.get(f"excluindo_clausula_{tipo_nome}", None)
                
                # Se está editando esta cláusula, mostrar formulário de edição
                if editando_idx == i:
                    st.markdown("### ✏️ Editar Cláusula")
                    # Compatibilidade: titulo/nome, regra_spectra/descricao
                    nome_edit = st.text_input(
                        "Nome da cláusula",
                        value=c.get("titulo") or c.get("nome", ""),
                        key=f"edit_nome_{tipo_nome}_{i}",
                        help="Identificador da regra na plataforma e nos relatórios. Ex.: Confidencialidade de dados, Prazo de vigência."
                    )
                    descricao_edit = st.text_area(
                        "Descrição",
                        value=c.get("regra_spectra") or c.get("descricao", ""),
                        key=f"edit_desc_{tipo_nome}_{i}",
                        help="O que a IA deve verificar no contrato — critério de conformidade. Ex.: Garante que dados confidenciais não podem ser divulgados a terceiros sem autorização."
                    )
                    buscar_em_edit = st.text_input(
                        "Buscar em (palavras-chave para similaridade)",
                        value=c.get("buscar_em", ""),
                        key=f"edit_buscar_em_{tipo_nome}_{i}",
                        help="Termos usados na busca semântica. Ex.: vigência, prazo, confidencialidade."
                    )
                    como_corrigir_edit = st.text_area(
                        "Como corrigir",
                        value=c.get("como_corrigir", ""),
                        key=f"edit_como_corrigir_{tipo_nome}_{i}",
                        help="Sugestão de redação para correção (opcional)."
                    )
                    ativa_edit = st.checkbox(
                        "Cláusula ativa",
                        value=c.get("ativa", True),
                        key=f"edit_ativa_{tipo_nome}_{i}",
                        help="Se desmarcada, esta regra não será usada na análise de similaridade."
                    )
                    
                    cols_edit = st.columns(3)
                    with cols_edit[0]:
                        if st.button("Salvar", key=f"btn_salvar_edit_{tipo_nome}_{i}"):
                            if not nome_edit.strip():
                                st.error("O nome da cláusula é obrigatório.")
                            elif not descricao_edit.strip():
                                st.error("A descrição é obrigatória.")
                            elif not buscar_em_edit.strip():
                                st.error("O campo 'Buscar em' é obrigatório para a análise de similaridade.")
                            else:
                                clausula_editada = {
                                    "ativa": ativa_edit,
                                    "titulo": nome_edit.strip(),
                                    "regra_spectra": descricao_edit.strip(),
                                    "buscar_em": buscar_em_edit.strip(),
                                }
                                if como_corrigir_edit.strip():
                                    clausula_editada["como_corrigir"] = como_corrigir_edit.strip()
                                clausulas[i] = clausula_editada
                                salvar_clausulas(tipo_nome, clausulas, idioma=idioma)
                                _reindexar_clausulas_lista(clausulas, idioma_param=idioma)
                                st.success(f"Cláusula '{nome_edit}' atualizada com sucesso!")
                                st.session_state[f"editando_clausula_{tipo_nome}"] = None
                                st.rerun()
                    with cols_edit[1]:
                        if st.button("Cancelar", key=f"btn_cancelar_edit_{tipo_nome}_{i}"):
                            st.session_state[f"editando_clausula_{tipo_nome}"] = None
                            st.rerun()
                # Se está excluindo esta cláusula, mostrar confirmação
                elif excluindo_idx == i:
                    _nome_excl = c.get("titulo") or c.get("nome", "")
                    st.warning(f"⚠️ Excluir cláusula: **{_nome_excl}**?")
                    
                    cols_del = st.columns(2)
                    with cols_del[0]:
                        if st.button("Confirmar Exclusão", key=f"btn_confirmar_del_{tipo_nome}_{i}", type="primary"):
                                nome_clausula = clausulas[i].get("titulo") or clausulas[i].get("nome", "")
                                clausulas.pop(i)
                                salvar_clausulas(tipo_nome, clausulas, idioma=idioma)
                                _reindexar_clausulas_lista(clausulas, idioma_param=idioma)
                                st.success(f"Cláusula '{nome_clausula}' excluída com sucesso!")
                                st.session_state[f"excluindo_clausula_{tipo_nome}"] = None
                                st.rerun()
                    with cols_del[1]:
                        if st.button("Cancelar", key=f"btn_cancelar_del_{tipo_nome}_{i}"):
                            st.session_state[f"excluindo_clausula_{tipo_nome}"] = None
                            st.rerun()
                # Modo de visualização normal
                else:
                    _nome_display = c.get("titulo") or c.get("nome", "")
                    _desc_display = c.get("regra_spectra") or c.get("descricao", "")
                    
                    def _toggle_ativa_save(idx):
                        clausulas_atual = carregar_clausulas(tipo_nome, idioma=idioma)
                        if 0 <= idx < len(clausulas_atual):
                            clausulas_atual[idx]["ativa"] = not clausulas_atual[idx].get("ativa", True)
                            salvar_clausulas(tipo_nome, clausulas_atual, idioma=idioma)
                            _reindexar_clausulas_lista(clausulas_atual, idioma_param=idioma)
                        st.rerun()
                    
                    # Cabeçalho com botões de ação e checkbox Ativa
                    col_titulo, col_btn_edit, col_btn_del = st.columns([3, 1, 1])
                    with col_titulo:
                        st.markdown(f"**{i+1}. {_nome_display}**")
                    with col_btn_edit:
                        if st.button("✏️", key=f"btn_edit_{tipo_nome}_{i}", help="Editar cláusula"):
                            st.session_state[f"editando_clausula_{tipo_nome}"] = i
                            st.rerun()
                    with col_btn_del:
                        if st.button("❌", key=f"btn_del_{tipo_nome}_{i}", help="Excluir cláusula"):
                            st.session_state[f"excluindo_clausula_{tipo_nome}"] = i
                            st.rerun()
                    
                    st.checkbox(
                        "Ativa",
                        value=c.get("ativa", True),
                        key=f"ativa_{tipo_nome}_{i}",
                        help="Desmarque para desativar esta regra na análise de similaridade.",
                        on_change=lambda idx=i: _toggle_ativa_save(idx)
                    )
                    
                    st.markdown("**Nome da cláusula**")
                    st.caption(_nome_display or "—")
                    
                    st.markdown("**Descrição**")
                    st.caption(_desc_display or "—")
                    
                    _buscar_em = c.get("buscar_em", "")
                    st.markdown("**Buscar em (palavras-chave para similaridade)**")
                    st.caption(_buscar_em or "—")
                    
                    _como_corrigir = c.get("como_corrigir", "")
                    if _como_corrigir:
                        st.markdown("**Como corrigir**")
                        st.caption(_como_corrigir)
                    
                    st.markdown("---")
        else:
            st.caption("Nenhuma cláusula cadastrada.") 

# ========= Seleção de Modelo =========

from analise.agent.escolha_modelo import TipoModelo, GerenciadorModelos

def selecionar_modelo_ia() -> str:
    """
    Interface para seleção de modelo de IA.
    
    Returns:
        ID do modelo selecionado
    """
    
    # Inicializar session_state
    if 'modelo_selecionado' not in st.session_state:
        st.session_state.modelo_selecionado = "gpt-5-mini"  # Padrão
    if 'temperatura' not in st.session_state:
        st.session_state.temperatura = 0.2
    if 'threshold_similaridade' not in st.session_state:
        st.session_state.threshold_similaridade = 0.45  # Padrão
    
    # Obter todos os modelos disponíveis
    todos_modelos = []
    for provedor in TipoModelo:
        todos_modelos.extend(GerenciadorModelos.listar_por_provedor(provedor))
    
    if not todos_modelos:
        st.warning("Nenhum modelo disponível")
        return None
    
    # Criar opções para o selectbox
    opcoes = {m.id: f"{m.nome} ({m.provedor.value})" for m in todos_modelos}
    
    # Índice do modelo selecionado
    index = 0  # Fallback para o primeiro
    if st.session_state.modelo_selecionado in opcoes:
        index = list(opcoes.keys()).index(st.session_state.modelo_selecionado)
    
    # Selectbox
    modelo_id = st.selectbox(
        "Escolha o Modelo:",
        options=list(opcoes.keys()),
        format_func=lambda x: opcoes[x],
        index=index,
        key="select_modelo"
    )
    
    # Atualizar seleção
    if modelo_id:
        st.session_state.modelo_selecionado = modelo_id
    
    # Configurações avançadas
    with st.expander("Configurações Avançadas"):
        st.session_state.temperatura = st.slider(
            "Temperatura",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.temperatura,
            step=0.1,
            help="Controla a criatividade do modelo. 0 = mais conservador, 1 = mais criativo"
        )
        
        st.session_state.threshold_similaridade = st.slider(
            "Threshold de Similaridade",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.threshold_similaridade,
            step=0.05,
            help="Define o limite de similaridade para classificar como possível violação. Valores mais altos = menos violações detectadas, mais rigoroso"
        )
    
    return st.session_state.modelo_selecionado


# ========= Seleção de Embedding =========

from analise.agent.escolha_modelo import GerenciadorEmbeddings
from analise.agent.orquestrador import OrquestradorAnalise
from analise.agent.agent1_extrator_docx import (
    obter_estatisticas_cache_agent1,
    limpar_cache_agent1,
    CACHE_AVISO_TAMANHO_MB,
    CACHE_AVISO_QUANTIDADE,
)


def selecionar_embedding_ia() -> str:
    """
    Interface para seleção de modelo de embedding.
    
    Returns:
        ID do embedding selecionado (chave do dicionário, ex: "openai-small")
    """
    # Inicializar session_state
    if 'embedding_selecionado' not in st.session_state:
        st.session_state.embedding_selecionado = "openai-small"  # Padrão (chave do dicionário) 
    
    # Obter todos os embeddings disponíveis usando as chaves do dicionário
    embeddings_disponiveis = GerenciadorEmbeddings.MODELOS_DISPONIVEIS
    
    if not embeddings_disponiveis:
        st.warning("Nenhum embedding disponível")
        return None
    
    # Criar opções para o selectbox usando as chaves do dicionário
    opcoes = {
        chave: f"{config.nome} ({config.provedor.value})" 
        for chave, config in embeddings_disponiveis.items()
    }
    
    # Índice do embedding selecionado
    index = 0
    if st.session_state.embedding_selecionado in opcoes:
        index = list(opcoes.keys()).index(st.session_state.embedding_selecionado)
    
    # Selectbox
    embedding_id = st.selectbox(
        "Escolha o Modelo de Embedding:",
        options=list(opcoes.keys()),
        format_func=lambda x: opcoes[x],
        index=index,
        key="select_embedding"
    )
    
    # Atualizar seleção
    if embedding_id:
        st.session_state.embedding_selecionado = embedding_id
        
        # Mostrar info do embedding selecionado
        config = GerenciadorEmbeddings.obter_embedding(embedding_id)
        if config:
            st.caption(f"{config.descricao} | {config.dimensoes}D | {config.max_tokens:,} tokens")
    
    return st.session_state.embedding_selecionado


# ========= Download do Relatório =========

def _sanitizar_nome_arquivo(nome_base: str) -> str:
    """
    Sanitiza o nome para uso em caminhos de arquivo (evita erro no Word/COM com parênteses e caracteres especiais).
    Remove parênteses e caracteres problemáticos; espaços viram underscore; limita tamanho.
    """
    s = str(nome_base).strip()
    s = s.replace("(", "").replace(")", "")
    s = re.sub(r"[^\w\s\-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s[:80] if s else "documento"


def mostrar_resultado_analise(resultado, nome_arquivo: str, arquivo_original_bytes: bytes = None):
    """
    Mostra os resultados da análise e botões de download (relatório, problemas.docx, solucao.docx).

    Args:
        resultado: ResultadoAnalise do orquestrador
        nome_arquivo: Nome do arquivo original analisado
        arquivo_original_bytes: Bytes do DOCX original (para gerar DOC comparado)
    """
    from output.docx import gerar_relatorio_analise_docx, gerar_nome_relatorio_analise
    from datetime import datetime
    from pathlib import Path

    if resultado.sucesso:
        st.info(f"Tempo: {resultado.tempo_total:.2f}s | "
                f"{resultado.clausulas_analisadas}/{resultado.total_clausulas} cláusulas analisadas")

        # Relatório único (problema + diff + explicação)
        buffer = gerar_relatorio_analise_docx(
            resultado.violacoes,
            gerar_sugestoes_reescrita=resultado.gerar_sugestoes_reescrita
        )
        nome_output = gerar_nome_relatorio_analise(nome_arquivo)
        st.download_button(
            label=f"Baixar Relatório de Análise (DOCX) - {len(resultado.violacoes)} violações",
            data=buffer,
            file_name=nome_output,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_relatorio_analise"
        )

        # Comparação (problemas x solução): grava os 2 DOCX em output/docs, compara com Word (Revisar -> Comparar) e oferece download
        doc_problemas = getattr(resultado, "doc_problemas_bytes", None)
        doc_solucao = getattr(resultado, "doc_solucao_bytes", None)
        if doc_problemas is not None and doc_solucao is not None:
            # Lazy import: evita carregar comparar_docx (e pyuno no Linux) no startup do app
            if platform.system() != 'Windows':
                libreoffice_path = '/usr/lib/python3/dist-packages'
                if libreoffice_path not in sys.path:
                    sys.path.insert(0, libreoffice_path)
            from output.comparar_docx import comparar_docx, gerar_doc_comparado
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_base = Path(nome_arquivo).stem
            nome_base_safe = _sanitizar_nome_arquivo(str(nome_base))
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            output_dir = Path(__file__).resolve().parent.parent / "output" / "docs"
            output_dir.mkdir(parents=True, exist_ok=True)
            path_problemas = output_dir / f"problemas_{nome_base_safe}_{ts}.docx"
            path_solucao = output_dir / f"solucao_{nome_base_safe}_{ts}.docx"
            path_comparacao = output_dir / f"comparacao_{nome_base_safe}_{ts}.docx"
            if st.button("Comparar documentos (problemas x solução)", key="btn_comparar_doc"):
                with st.spinner("Salvando problemas e solução em output/docs e gerando comparação..."):
                    comparado_bytes = None
                    msg_sucesso = None
                    try:
                        path_problemas.write_bytes(doc_problemas)
                        path_solucao.write_bytes(doc_solucao)
                    except (PermissionError, OSError):
                        # Pasta output/docs em uso (ex.: OneDrive) ou sem permissão — gera só fallback em memória para download
                        fallback = gerar_doc_comparado(doc_problemas, doc_solucao)
                        if fallback:
                            comparado_bytes = fallback
                            msg_sucesso = (
                                "Não foi possível gravar em output/docs (pasta em uso ou sem permissão). "
                                "Foi gerado um documento com as seções 'Comparação: Problemas x Solução', "
                                "'1. Documento Problemas (original)' e '2. Documento Solução (revisado)'. Use o botão abaixo para baixar."
                            )
                        else:
                            st.error("Erro ao gerar o documento de comparação.")
                    if comparado_bytes is None:
                        try:
                            comparar_docx(str(path_problemas), str(path_solucao), str(path_comparacao))
                            comparado_bytes = path_comparacao.read_bytes()
                            msg_sucesso = (
                                "Documentos gravados em output/docs. Comparação gerada (track changes). "
                                "Use o botão abaixo para baixar."
                            )
                        except Exception as e:
                            # Fallback: documento com problemas + solução (sem track changes)
                            logging.exception("Erro ao comparar documentos (Word/LibreOffice); usando fallback.")
                            with st.expander("Detalhes do erro (para diagnóstico)", expanded=False):
                                st.code(traceback.format_exc(), language="text")
                                st.caption("Use estas informações para corrigir (ex.: caminho, Word/LibreOffice).")
                            fallback = gerar_doc_comparado(doc_problemas, doc_solucao)
                            if fallback:
                                comparado_bytes = fallback
                                msg_sucesso = (
                                    "Comparação com controle de alterações (track changes) não disponível; "
                                    "foi gerado um documento alternativo com as seções "
                                    "'Comparação: Problemas x Solução', '1. Documento Problemas (original)' e "
                                    "'2. Documento Solução (revisado)'. Use o botão abaixo para baixar."
                                )
                                try:
                                    path_comparacao.write_bytes(fallback)
                                except (PermissionError, OSError):
                                    st.warning(
                                        "O arquivo de comparação não pôde ser salvo em output/docs (pasta em uso ou sem permissão). "
                                        "Use o botão abaixo para baixar."
                                    )
                            else:
                                msg_sucesso = None
                    if comparado_bytes is not None:
                        st.session_state["comparacao_doc_bytes"] = comparado_bytes
                        st.session_state["comparacao_doc_nome"] = f"comparacao_{nome_base_safe}_{ts}.docx"
                        st.session_state["comparacao_doc_nome_base"] = nome_base
                        st.success(msg_sucesso)
                    else:
                        st.error(
                            "Erro ao comparar documentos. No Windows, verifique se o Word e o pywin32 estão instalados. "
                            "No Linux, verifique se o LibreOffice está instalado e em execução com o socket na porta 2002."
                        )
            if (st.session_state.get("comparacao_doc_bytes")
                    and st.session_state.get("comparacao_doc_nome_base") == nome_base):
                st.download_button(
                    label="Baixar comparação (DOCX)",
                    data=st.session_state["comparacao_doc_bytes"],
                    file_name=st.session_state.get("comparacao_doc_nome", f"comparacao_{nome_base_safe}_{ts}.docx"),
                    mime=mime,
                    key="dl_comparacao"
                )
        
        # Resumo simples
        if resultado.violacoes:
            st.warning(f"{len(resultado.violacoes)} cláusulas com anotações")
        if resultado.conformidades:
            st.info(f"{len(resultado.conformidades)} cláusulas OK")
        
        # Alerta se sugestões foram solicitadas mas faltam
        if resultado.gerar_sugestoes_reescrita and resultado.violacoes:
            violacoes_sem_sugestao = [
                v for v in resultado.violacoes 
                if not v.get('sugestao_reescrita') or 
                   (isinstance(v.get('sugestao_reescrita'), dict) and 
                    not v['sugestao_reescrita'].get('texto_reescrito'))
            ]
            if violacoes_sem_sugestao:
                st.warning(f"⚠️ {len(violacoes_sem_sugestao)} violação(ões) sem sugestão de reescrita gerada. Verifique os logs ou tente novamente.")
        
        # ========= DETALHAMENTO DAS VIOLAÇÕES =========
        if resultado.violacoes:
            st.subheader("Detalhamento das Violações")
            
            for i, violacao in enumerate(resultado.violacoes, 1):
                # Obter dados da violação (backend: regra, chunk, problema, sugestao_reescrita)
                regra = violacao.get("regra", {})
                chunk = violacao.get("chunk", {})
                clausula_violada = regra.get("titulo") if regra else violacao.get("clausula_violada", "Regra não identificada")
                localizacao = violacao.get("localizacao") or (chunk.get("titulo") if chunk else None) or violacao.get("titulo", "N/A")
                problema = violacao.get("problema", "")
                motivos = violacao.get("motivo", [])
                if problema and not motivos:
                    motivos = [problema]
                texto_trecho = chunk.get("texto", "")[:500] if chunk else ""
                
                # Fallback: se não tiver clausula_violada no novo formato, tentar pegar das clausulas_verificadas
                if clausula_violada == 'Regra não identificada':
                    clausulas_ref = violacao.get('clausulas_verificadas', [])
                    if clausulas_ref:
                        clausula_violada = clausulas_ref[0].get('nome', 'Regra não identificada')
                
                # Criar expander para cada violação
                with st.expander(f"⚠️ {i}. {clausula_violada}", expanded=False):
                    # Localização no documento
                    st.markdown(f"**Localização no documento:** {localizacao}")
                    
                    # Motivos
                    if motivos:
                        st.markdown("**Por que está em violação:**")
                        if isinstance(motivos, list):
                            for motivo in motivos:
                                st.markdown(f"- {motivo}")
                        else:
                            st.markdown(f"- {motivos}")
                    
                    # Análise original do Agent (fallback se não tiver motivos estruturados)
                    if not motivos and violacao.get('analise_agent1'):
                        st.markdown("**Análise:**")
                        analise_texto = violacao.get('analise_agent1', '')
                        # Limpar prefixos de classificação
                        analise_texto = analise_texto.replace("[VIOLAÇÃO]", "").strip()
                        analise_texto = analise_texto.replace("CLASSIFICAÇÃO: VIOLAÇÃO", "").strip()
                        st.text(analise_texto[:800] + "..." if len(analise_texto) > 800 else analise_texto)
                    
                    # Trechos do documento analisado
                    chunks_relacionados = violacao.get('chunks_relacionados', [])
                    
                    if texto_trecho:
                        # Mostrar indicador se há múltiplos trechos
                        if len(chunks_relacionados) > 1:
                            st.markdown(f"**Trechos do documento analisado:** ({len(chunks_relacionados)} cláusulas afetadas)")
                        else:
                            st.markdown("**Trecho do documento analisado:**")
                        
                        # Mostrar trecho principal
                        st.caption(texto_trecho + "..." if len(chunk.get('texto', '')) > 500 else texto_trecho)
                        
                        # Mostrar outros trechos relacionados (se houver mais de 1)
                        if len(chunks_relacionados) > 1:
                            chunks_adicionais = chunks_relacionados[1:]  # Pular o primeiro (já mostrado como principal)
                            with st.expander(f"Ver outros {len(chunks_adicionais)} trecho(s) relacionado(s)", expanded=False):
                                for idx, chunk_rel in enumerate(chunks_adicionais):
                                    texto_rel = chunk_rel.get('texto', '')[:400] if chunk_rel and chunk_rel.get('texto') else ''
                                    if texto_rel:
                                        titulo_chunk = chunk_rel.get('titulo', f'Cláusula {idx + 2}')
                                        st.markdown(f"**{titulo_chunk}:**")
                                        st.caption(texto_rel + "..." if len(chunk_rel.get('texto', '')) > 400 else texto_rel)
                                        # Adicionar separador apenas se não for o último item
                                        if idx < len(chunks_adicionais) - 1:
                                            st.markdown("---")
                    elif not texto_trecho and localizacao:
                        st.info(f"Trecho não localizado automaticamente. Verifique manualmente: {localizacao}")
                    
                    # Sugestão de reescrita (original vs. reescrito lado a lado)
                    sugestao = violacao.get("sugestao_reescrita")
                    if sugestao and isinstance(sugestao, dict):
                        st.markdown("---")
                        st.markdown("**Sugestão de reescrita**")
                        txt_orig = sugestao.get("texto_original", "")
                        txt_reesc = sugestao.get("texto_reescrito", "")
                        explicacao = sugestao.get("explicacao_mudancas", "")
                        col_orig, col_reesc = st.columns(2)
                        slug = "".join(c if c.isalnum() else "_" for c in nome_arquivo)[:40]
                        with col_orig:
                            st.markdown("*Original*")
                            st.text_area(
                                "Texto original",
                                value=txt_orig,
                                height=min(300, max(120, 80 + len(txt_orig) // 2)),
                                key=f"orig_{slug}_{i}",
                                disabled=True,
                                label_visibility="collapsed"
                            )
                        with col_reesc:
                            st.markdown("*Sugerido*")
                            st.text_area(
                                "Texto reescrito",
                                value=txt_reesc,
                                height=min(300, max(120, 80 + len(txt_reesc) // 2)),
                                key=f"reesc_{slug}_{i}",
                                disabled=True,
                                label_visibility="collapsed"
                            )
                        if explicacao:
                            st.markdown("**Explicação das mudanças:**")
                            st.caption(explicacao)
    else:
        st.error(f"❌ {resultado.mensagem}")


# ========= Função Genérica de Análise com Cache =========

# ========= Editor de Prompts dos Agentes =========

def render_editor_prompts(tipo_contrato: str, idioma: str = "pt"):
    """
    Renderiza o editor de prompts dos agentes para o tipo de contrato e idioma.
    Exibe abas por agente (agent3, agent4) com System e User.
    Extrator não é editável (formato técnico).
    Botões: Salvar Todos e Reset Todos (requerem auth admin), Fechar.
    """
    from analise.agent import (
        AGENTES,
        DESCRICOES_AGENTES,
        RECOMENDACOES_POR_AGENTE,
        carregar_prompt_tipo,
        salvar_prompt_tipo,
        validar_prompt_user,
        restaurar_todos_prompts_padrao,
    )
    from modulos.auth import esta_autenticado, autenticar, obter_senha_admin

    tipo_nome = tipo_contrato
    session_key_aberto = f"editar_prompt_{tipo_nome}"
    
    # Agentes editáveis (excluir extrator - formato técnico)
    AGENTES_EDITAVEIS = [a for a in AGENTES if a != "extrator"]

    # Inicializar conteúdo dos prompts na primeira abertura do editor
    for agent in AGENTES_EDITAVEIS:
        for parte in ["system", "user"]:
            key = f"prompt_edit_{parte}_{tipo_nome}_{agent}_{idioma}"
            if key not in st.session_state:
                st.session_state[key] = carregar_prompt_tipo(tipo_nome, agent, parte, idioma)

    st.subheader(f"📝 Editar Prompts dos Agentes — {tipo_nome}")
    st.caption("Altere as instruções (system) e o template (user) por agente. Salvar e Reset exigem senha de administrador.")

    # Bloco de autenticação de administrador (para Salvar/Reset)
    if obter_senha_admin():
        if not esta_autenticado():
            with st.expander("🔐 Acesso de administrador (para Salvar ou Reset)", expanded=True):
                senha_admin = st.text_input(
                    "Senha de administrador",
                    type="password",
                    key=f"input_senha_admin_prompts_{tipo_nome}",
                    help="Necessária para salvar ou resetar os prompts.",
                )
                if st.button("Entrar como administrador", key=f"btn_admin_prompts_{tipo_nome}"):
                    if senha_admin and autenticar(senha_admin):
                        st.success("Autenticado. Agora você pode Salvar ou Reset.")
                        st.rerun()
                    elif senha_admin:
                        st.error("Senha incorreta.")
                    else:
                        st.warning("Digite a senha.")
        else:
            st.caption("✅ Autenticado como administrador — você pode Salvar ou Reset.")

    tabs = st.tabs([DESCRICOES_AGENTES.get(agent, agent) for agent in AGENTES_EDITAVEIS])
    for idx, agent in enumerate(AGENTES_EDITAVEIS):
        with tabs[idx]:
            rec = RECOMENDACOES_POR_AGENTE.get(agent, {})
            if rec:
                with st.expander("📌 Recomendações: o que o prompt deve conter", expanded=False):
                    if rec.get("system"):
                        st.markdown("**Mensagem System:**")
                        st.caption(rec["system"])
                    if rec.get("user"):
                        st.markdown("**Mensagem User:**")
                        st.caption(rec["user"])
            key_sys = f"prompt_edit_system_{tipo_nome}_{agent}_{idioma}"
            key_user = f"prompt_edit_user_{tipo_nome}_{agent}_{idioma}"
            st.text_area(
                "Mensagem System",
                height=180,
                key=key_sys,
                help="Instruções gerais do agente.",
            )
            st.text_area(
                "Mensagem User",
                height=180,
                key=key_user,
                help="Template com variáveis que recebem os dados do documento.",
            )

    col_salvar, col_reset, col_fechar = st.columns([1, 1, 2])
    with col_salvar:
        if st.button("Salvar Todos", key=f"btn_salvar_prompts_{tipo_nome}", type="primary"):
            if not esta_autenticado():
                st.warning("Entre como administrador no bloco acima para poder salvar.")
            else:
                erros = []
                for agent in AGENTES_EDITAVEIS:
                    key_user = f"prompt_edit_user_{tipo_nome}_{agent}_{idioma}"
                    conteudo_user = st.session_state.get(key_user, "")
                    val = validar_prompt_user(conteudo_user, agent=agent)
                    if not val["valido"]:
                        vars_faltando = ", ".join(val['faltando'])
                        erros.append(f"**{agent}**: faltam variáveis obrigatórias: {vars_faltando}")
                if erros:
                    st.error("❌ Erro de validação. Corrija antes de salvar:")
                    for e in erros:
                        st.error(e)
                else:
                    # Aviso se agent3 System não menciona eh_violacao/chunk_index (pipeline depende disso)
                    key_sys_3 = f"prompt_edit_system_{tipo_nome}_agent3_{idioma}"
                    sys_agent3 = st.session_state.get(key_sys_3, "")
                    if sys_agent3 and ("eh_violacao" not in sys_agent3 or "chunk_index" not in sys_agent3):
                        st.warning(
                            "⚠️ O prompt System do **agent3** não menciona 'eh_violacao' ou 'chunk_index'. "
                            "O pipeline espera que a IA responda nesse formato; veja as recomendações na aba agent3."
                        )
                    for agent in AGENTES_EDITAVEIS:
                        key_sys = f"prompt_edit_system_{tipo_nome}_{agent}_{idioma}"
                        key_user = f"prompt_edit_user_{tipo_nome}_{agent}_{idioma}"
                        salvar_prompt_tipo(tipo_nome, agent, "system", st.session_state.get(key_sys, ""), idioma)
                        salvar_prompt_tipo(tipo_nome, agent, "user", st.session_state.get(key_user, ""), idioma)
                    carregar_prompt_tipo.cache_clear()
                    st.success("✅ Prompts salvos com sucesso.")
    with col_reset:
        if st.button(
            "Reset Todos",
            key=f"btn_reset_prompts_{tipo_nome}",
            help="Restaura todos os prompts (Verificador de Cláusulas e Redator) para o conteúdo padrão do tipo de contrato.",
        ):
            if not esta_autenticado():
                st.warning("Entre como administrador no bloco acima para poder resetar.")
            else:
                restaurar_todos_prompts_padrao(tipo_nome, idioma)
                carregar_prompt_tipo.cache_clear()
                for agent in AGENTES_EDITAVEIS:
                    for parte in ["system", "user"]:
                        key = f"prompt_edit_{parte}_{tipo_nome}_{agent}_{idioma}"
                        st.session_state[key] = carregar_prompt_tipo(tipo_nome, agent, parte, idioma)
                st.success("✅ Prompts restaurados ao padrão.")
                st.rerun()
    with col_fechar:
        if st.button("Fechar", key=f"btn_fechar_prompts_{tipo_nome}"):
            st.session_state[session_key_aberto] = False
            for agent in AGENTES_EDITAVEIS:
                for parte in ["system", "user"]:
                    key = f"prompt_edit_{parte}_{tipo_nome}_{agent}_{idioma}"
                    if key in st.session_state:
                        del st.session_state[key]
            st.rerun()


def _gerar_chave_cache_config(
    nome_arquivo: str,
    idioma: str,
    modelo_id: str,
    embedding_id: str,
    threshold: float,
    temperatura: float,
    gerar_sugestoes_reescrita: bool = False
) -> str:
    """
    Gera uma chave de cache única baseada em todas as configurações relevantes.
    
    Args:
        nome_arquivo: Nome do arquivo
        idioma: Idioma do contrato
        modelo_id: ID do modelo LLM
        embedding_id: ID do modelo de embedding
        threshold: Threshold de similaridade
        temperatura: Temperatura do modelo
        gerar_sugestoes_reescrita: Se deve gerar sugestões de reescrita
        
    Returns:
        Hash MD5 da configuração para usar como chave de cache
    """
    config_str = f"{nome_arquivo}|{idioma}|{modelo_id}|{embedding_id}|{threshold}|{temperatura}|{gerar_sugestoes_reescrita}"
    return hashlib.md5(config_str.encode('utf-8')).hexdigest()


def render_pagina_analise(
    tipo_contrato: str,
    titulo: str,
    label_upload: str,
    key_prefix: str
):
    """
    Renderiza uma página de análise completa com cache no session_state.
    Evita reprocessamento quando o usuário clica em download.
    O cache considera todas as configurações (arquivo, idioma, modelo, embedding, threshold, temperatura).
    
    Args:
        tipo_contrato: Tipo do contrato (NDA, SPA_COTAS, etc)
        titulo: Título da página
        label_upload: Label do campo de upload
        key_prefix: Prefixo para chaves do session_state (ex: "nda", "spa_cotas")
    """
    # Sidebar
    sidebar_informacoes(tipo_contrato)
    sidebar_botoes(tipo_contrato)
    sidebar_lista_clausulas(tipo_contrato)
    sidebar_historico()

    # Obter idioma primeiro (necessário para o editor de prompts)
    idioma = st.session_state.get('idioma_contrato', 'pt')
    
    # Se o usuário clicou em "Editar prompt", mostrar o editor e sair
    if st.session_state.get(f"editar_prompt_{tipo_contrato}"):
        render_editor_prompts(tipo_contrato, idioma)
        return

    st.title(titulo)
    
    # Botão voltar com limpeza de cache
    if st.button("← Voltar para seleção", key=f"btn_voltar_{key_prefix}"):
        # Limpar cache ao voltar
        _limpar_cache_analise(key_prefix)
        st.session_state.pagina = "home"
        st.rerun()
        
    modelo_id = selecionar_modelo_ia()
    embedding_id = selecionar_embedding_ia()

    # Cache do extrator de cláusulas: explicação, estatísticas, aviso e limpeza
    with st.expander("Cache do Extrator de Cláusulas", expanded=False):
        st.markdown(
            "O extrator de cláusulas processa o seu documento DOCX e extrai as cláusulas. Para não reprocessar o mesmo arquivo toda vez, "
            "o sistema guarda o resultado em um **cache em disco**: se você analisar de novo o **mesmo documento** "
            "(mesmo conteúdo), o resultado é reutilizado e a análise fica mais rápida, sem novas chamadas à API. "
            "O cache é identificado pelo conteúdo do arquivo (hash), não pelo nome."
        )
        stats = obter_estatisticas_cache_agent1()
        qtd = stats["quantidade"]
        tamanho_bytes = stats["tamanho_bytes"]
        if tamanho_bytes >= 1024 * 1024:
            tamanho_str = f"{tamanho_bytes / (1024 * 1024):.1f} MB"
        else:
            tamanho_str = f"{tamanho_bytes / 1024:.1f} KB"
        st.caption(f"{qtd} documentos em cache, {tamanho_str}.")
        if (
            tamanho_bytes > CACHE_AVISO_TAMANHO_MB * 1024 * 1024
            or qtd > CACHE_AVISO_QUANTIDADE
        ):
            st.warning(
                "O cache do Extrator de Cláusulas está grande e ocupa espaço em disco. "
                "Use o botão abaixo para limpar se não precisar reutilizar resultados antigos."
            )
        confirm_key = f"confirmar_limpar_cache_agent1_{key_prefix}"
        if st.session_state.get(confirm_key):
            st.markdown(
                "Tem certeza? Isso remove todos os resultados em cache. "
                "Documentos analisados novamente serão reprocessados."
            )
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("Sim, limpar", key=f"btn_limpar_confirm_{key_prefix}"):
                    removidos = limpar_cache_agent1()
                    if confirm_key in st.session_state:
                        del st.session_state[confirm_key]
                    st.success(f"Cache limpo: {removidos} documento(s) removido(s).")
                    st.rerun()
            with col_nao:
                if st.button("Cancelar", key=f"btn_limpar_cancel_{key_prefix}"):
                    if confirm_key in st.session_state:
                        del st.session_state[confirm_key]
                    st.rerun()
        else:
            if st.button(
                "Limpar cache do Extrator de Cláusulas",
                key=f"btn_limpar_cache_agent1_{key_prefix}",
            ):
                st.session_state[confirm_key] = True
                st.rerun()

    arquivo = upload_docx(label_upload, key=f"upload_{key_prefix}")
    threshold = st.session_state.get('threshold_similaridade', 0.45)
    temperatura = st.session_state.get('temperatura', 0.2)
    gerar_sugestoes_reescrita = True  # sempre ativo: sugestões de reescrita são geradas em toda análise

    # Inicializar session_state para cache
    cache_resultado = f"resultado_{key_prefix}"
    cache_nome = f"arquivo_{key_prefix}_nome"
    cache_bytes = f"arquivo_{key_prefix}_bytes"
    cache_config_key = f"config_key_{key_prefix}"
    
    if cache_resultado not in st.session_state:
        st.session_state[cache_resultado] = None
        st.session_state[cache_nome] = None
        st.session_state[cache_bytes] = None
        st.session_state[cache_config_key] = None

    # Só processa se arquivo foi enviado
    if arquivo is not None:
        nome_arquivo = arquivo.name
        
        # Ler arquivo apenas se necessário (evitar múltiplas leituras)
        # Se o arquivo já está em cache e não mudou, usar do cache
        if (st.session_state[cache_nome] == nome_arquivo and 
            st.session_state[cache_bytes] is not None):
            arquivo_bytes = st.session_state[cache_bytes]
        else:
            arquivo_bytes = arquivo.read()
            size_kb = len(arquivo_bytes) / 1024
            print(f"[Upload] Documento recebido: {nome_arquivo} ({size_kb:.1f} KB)")
        
        # Gerar chave de configuração atual (apenas uma vez)
        config_key_atual = _gerar_chave_cache_config(
            nome_arquivo, idioma, modelo_id, embedding_id, threshold, temperatura, gerar_sugestoes_reescrita
        )
        
        # Verificar se arquivo ou configurações mudaram
        arquivo_mudou = (st.session_state[cache_nome] != nome_arquivo)
        config_mudou = (st.session_state[cache_config_key] != config_key_atual)
        cache_invalido = (arquivo_mudou or config_mudou or st.session_state[cache_resultado] is None)
        
        # Se é um arquivo novo, configuração mudou ou não tem resultado em cache, mostrar botão de análise
        if cache_invalido:
            col1, col2 = st.columns([1, 4])
            with col1:
                analisar = st.button("Analisar", type="primary", key=f"btn_analisar_{key_prefix}")
            with col2:
                if arquivo_mudou and st.session_state[cache_resultado] is not None:
                    st.warning("Arquivo diferente detectado. Clique em 'Analisar' para processar.")
                elif config_mudou and st.session_state[cache_resultado] is not None:
                    st.warning("Configurações alteradas (idioma, modelo, threshold, etc). Clique em 'Analisar' para reprocessar.")
            
            if analisar:
                print(f"[Análise] Iniciando: {nome_arquivo} | tipo={tipo_contrato} | idioma={idioma}")
                # Callbacks para UI com progresso detalhado
                progress_bar = st.progress(0)
                status_text = st.empty()
                detail_text = st.empty()  # Novo: texto de detalhe (regra atual)
                log_container = st.expander("Detalhes Técnicos", expanded=True)
                with log_container:
                    log_placeholder = st.empty()
                logs = []
                erros_tecnicos = []  # Armazenar erros para exibição destacada
                
                def on_progress(msg: str, valor: float, detalhes: dict = None):
                    """Callback de progresso com suporte a detalhes."""
                    print(f"[Progresso] {valor*100:.0f}% | {msg}")
                    progress_bar.progress(valor)
                    status_text.text(msg)
                    # Mostrar detalhe da regra atual se disponível
                    if detalhes and detalhes.get("regra_atual"):
                        etapa = detalhes.get("etapa", "")
                        if etapa == "verificacao":
                            detail_text.caption(f"Analisando: {detalhes['regra_atual']}")
                        elif etapa == "reescrita":
                            detail_text.caption(f"Reescrevendo: {detalhes['regra_atual']}")
                    else:
                        detail_text.empty()
                
                def on_log(msg: str):
                    print(f"[Log] {msg}")
                    logs.append(msg)
                    # Detectar erros para destaque
                    if msg.startswith("[") and any(cat in msg for cat in [
                        "LIMITE DE REQUISIÇÕES", "AUTENTICAÇÃO", "TIMEOUT", 
                        "CONEXÃO", "RESPOSTA INVÁLIDA", "VALIDAÇÃO", "ERRO"
                    ]):
                        erros_tecnicos.append(msg)
                    log_placeholder.text("\n".join(logs))
                
                # Orquestrar análise
                orquestrador = OrquestradorAnalise()
                
                resultado = orquestrador.analisar_contrato(
                    arquivo_bytes=arquivo_bytes,
                    nome_arquivo=nome_arquivo,
                    tipo_contrato=tipo_contrato,
                    modelo_llm_id=modelo_id,
                    modelo_embedding_id=embedding_id,
                    idioma=idioma,
                    threshold_similaridade=threshold,
                    temperatura=temperatura,
                    gerar_sugestoes_reescrita=gerar_sugestoes_reescrita,
                    on_progress=on_progress,
                    on_log=on_log
                )
                print(f"[Análise] Concluída: {nome_arquivo} | sucesso={resultado.sucesso}")
                # Limpar UI de progresso
                progress_bar.empty()
                status_text.empty()
                detail_text.empty()
                
                # Exibir resumo de erros técnicos se houver
                if erros_tecnicos:
                    with st.expander(f"⚠️ Detalhes Técnicos - {len(erros_tecnicos)} erro(s) durante a análise", expanded=True):
                        st.warning("Algumas regras não puderam ser verificadas devido a erros. "
                                   "A análise continuou com as regras restantes.")
                        for erro in erros_tecnicos:
                            # Formatar erro para exibição
                            linhas = erro.split("\n")
                            if linhas:
                                # Primeira linha: categoria e regra
                                st.markdown(f"**{linhas[0]}**")
                                # Linhas seguintes: detalhes
                                for linha in linhas[1:]:
                                    if linha.strip():
                                        st.caption(linha)
                            st.divider()
                
                # Armazenar resultado no cache com a chave de configuração
                st.session_state[cache_resultado] = resultado
                st.session_state[cache_nome] = nome_arquivo
                st.session_state[cache_bytes] = arquivo_bytes
                st.session_state[cache_config_key] = config_key_atual
                st.session_state[f"erros_tecnicos_{key_prefix}"] = erros_tecnicos  # Salvar erros para exibição posterior
                
                # Salvar no histórico de análises se sucesso
                if resultado.sucesso:
                    _adicionar_ao_historico(
                        nome_arquivo=nome_arquivo,
                        tipo_contrato=tipo_contrato,
                        idioma=idioma,
                        resultado=resultado
                    )
                
                # Rerun para mostrar resultado sem reprocessar
                st.rerun()
        
        # Mostrar resultado se existir no cache E a configuração ainda for válida
        # Usar a mesma config_key_atual calculada acima (não recalcular)
        cache_valido = (
            st.session_state[cache_resultado] is not None and
            st.session_state[cache_config_key] == config_key_atual and
            st.session_state[cache_nome] == nome_arquivo
        )
        
        if cache_valido:
            # Exibir erros técnicos salvos, se houver
            erros_salvos = st.session_state.get(f"erros_tecnicos_{key_prefix}", [])
            if erros_salvos:
                with st.expander(f"⚠️ Detalhes Técnicos - {len(erros_salvos)} erro(s) durante a análise", expanded=False):
                    st.warning("Algumas regras não puderam ser verificadas devido a erros. "
                               "A análise continuou com as regras restantes.")
                    for erro in erros_salvos:
                        # Formatar erro para exibição
                        linhas = erro.split("\n")
                        if linhas:
                            # Primeira linha: categoria e regra
                            st.markdown(f"**{linhas[0]}**")
                            # Linhas seguintes: detalhes
                            for linha in linhas[1:]:
                                if linha.strip():
                                    st.caption(linha)
                        st.divider()
            
            mostrar_resultado_analise(
                st.session_state[cache_resultado],
                st.session_state[cache_nome],
                arquivo_original_bytes=st.session_state.get(cache_bytes),
            )
            
            # Botão para limpar cache e reprocessar
            if st.button("Nova Análise", help="Limpa o cache e permite processar novamente", key=f"btn_nova_{key_prefix}"):
                _limpar_cache_analise(key_prefix)
                st.rerun()


def _limpar_cache_analise(key_prefix: str):
    """Limpa o cache de análise para um tipo de contrato."""
    cache_resultado = f"resultado_{key_prefix}"
    cache_nome = f"arquivo_{key_prefix}_nome"
    cache_bytes = f"arquivo_{key_prefix}_bytes"
    cache_config_key = f"config_key_{key_prefix}"
    cache_erros = f"erros_tecnicos_{key_prefix}"
    
    if cache_resultado in st.session_state:
        del st.session_state[cache_resultado]
    if cache_nome in st.session_state:
        del st.session_state[cache_nome]
    if cache_bytes in st.session_state:
        del st.session_state[cache_bytes]
    if cache_config_key in st.session_state:
        del st.session_state[cache_config_key]
    if cache_erros in st.session_state:
        del st.session_state[cache_erros]
