"""
Orquestrador da análise de contratos.
Coordena todo o pipeline de análise.
"""
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
import traceback

from .agent1_extrator_docx import extrair_clausulas_docx
from .agent2_matcher import AgentMatcher
from .agent3_verificador import AgentVerificador
from .agent4_reescritor import AgentReescritor
from analise.embeddings.clausulas import GerenciadorClausulasReferencia
from .escolha_modelo import GerenciadorModelos, GerenciadorEmbeddings
from .exceptions import (
    GabrielBaseException,
    APIKeyError,
    APIConnectionError,
    APIRateLimitError,
    DocumentExtractionError,
    DocumentEmptyError,
    DatabaseNotIndexedError,
    DatabaseOutdatedError,
    DatabaseEmptyError,
    RuleVerificationError,
    RewriteError,
    ModelNotFoundError,
)


@dataclass
class ResultadoAnalise:
    """Resultado completo da análise de um contrato."""
    sucesso: bool
    mensagem: str
    
    # Dados do documento
    total_clausulas: int
    clausulas_analisadas: int
    
    # Resultados
    violacoes: List[Dict]          # Violações validadas e consolidadas
    conformidades: List[Dict]       # Conformidades
    
    # Metadados
    tempo_total: float
    modelo_llm_usado: str
    modelo_embedding_usado: str
    tipo_contrato: str
    
    # Novos campos para contexto e consolidação
    contexto_global: Dict = field(default_factory=dict)  # Contexto extraído pelo Agent0
    violacoes_invalidadas: List[Dict] = field(default_factory=list)  # Violações descartadas pelo Agent3
    resumo_consolidacao: str = ""  # Resumo da consolidação
    gerar_sugestoes_reescrita: bool = False  # Flag indicando se sugestões foram solicitadas
    # 3 DOCX para download (novo pipeline)
    doc_problemas_bytes: Optional[bytes] = None
    doc_solucao_bytes: Optional[bytes] = None
    doc_explicacao_bytes: Optional[bytes] = None


class OrquestradorAnalise:
    """Orquestra: Agente 1 (docx → cláusulas) → Agente 2 (matcher) → Agente 3 (verificador) → Agente 4 (reescritor)."""

    def __init__(self):
        self.gerenciador_clausulas = GerenciadorClausulasReferencia()
    
    def analisar_contrato(
        self,
        arquivo_bytes: bytes,
        nome_arquivo: str,
        tipo_contrato: str,
        modelo_llm_id: str,
        modelo_embedding_id: str,
        idioma: str = "pt",
        threshold_similaridade: float = 0.45,
        temperatura: float = 0.2,
        gerar_sugestoes_reescrita: bool = False,
        on_progress: Optional[Callable[[str, float, Optional[Dict]], None]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> ResultadoAnalise:
        """
        Executa análise completa de um contrato.
        
        Args:
            arquivo_bytes: conteúdo do arquivo .docx
            nome_arquivo: nome do arquivo
            tipo_contrato: tipo (NDA, TIPO 2, etc)
            modelo_llm_id: ID do modelo LLM
            modelo_embedding_id: ID do modelo embedding
            idioma: "pt" para português, "en" para inglês
            threshold_similaridade: similaridade mínima (0–1) para incluir chunk no matcher. Padrão 0.45.
            gerar_sugestoes_reescrita: se True, gera sugestão de reescrita para cada violação
            on_progress: callback para atualizar progress bar (mensagem, porcentagem, detalhes opcionais)
            on_log: callback para logs
        
        Returns:
            ResultadoAnalise com todos os dados
        """
        tempo_inicio = time.time()
        
        try:
            # === ETAPA 1: Validar e Criar Embedding Function ===
            self._log(on_log, "Preparando sistema de análise...")
            self._progress(on_progress, "Preparando sistema de análise", 0.02)
            
            embedding_config = GerenciadorEmbeddings.obter_embedding(modelo_embedding_id)
            if not embedding_config:
                raise ModelNotFoundError(
                    f"Modelo de embedding '{modelo_embedding_id}' não encontrado",
                    user_message="Modelo de IA para embeddings não encontrado. Selecione outro modelo."
                )
            
            # Validar API key do embedding
            validacao_embedding = GerenciadorEmbeddings.validar_api_keys(embedding_config)
            if not validacao_embedding["valido"]:
                raise APIKeyError(
                    validacao_embedding["mensagem"],
                    user_message="Chave de API para embeddings inválida ou não configurada."
                )
            
            # Criar embedding function
            try:
                embedding_function = GerenciadorEmbeddings.criar_embedding_function(embedding_config)
            except Exception as e:
                raise APIConnectionError(
                    f"Erro ao criar embedding function: {e}",
                    user_message="Não foi possível conectar ao serviço de embeddings."
                )
            
            # === ETAPA 2: Carregar regras e validar base de conhecimento ===
            from modulos.comum import carregar_clausulas
            regras = carregar_clausulas(tipo_contrato, idioma=idioma)
            self._log(on_log, "Validando base de conhecimento...")
            self._progress(on_progress, "Validando base de conhecimento", 0.05)
            self._validar_base_conhecimento(tipo_contrato, idioma=idioma, regras=regras)
            
            # === ETAPA 3: Agente 1 – Extrator DOCX (lógica ia.py) ===
            self._log(on_log, "Extraindo cláusulas do documento...")
            self._progress(on_progress, "Extração de Cláusulas", 0.15)
            
            try:
                resultado_ag1 = extrair_clausulas_docx(
                    arquivo_bytes,
                    on_log=lambda msg: self._log(on_log, msg),
                    idioma=idioma,
                )
            except Exception as e:
                raise DocumentExtractionError(
                    f"Erro ao extrair cláusulas: {e}",
                    user_message="Erro ao extrair cláusulas do documento. Verifique se o arquivo está correto."
                )
            
            clausulas = resultado_ag1.get("clausulas", [])
            self._log(on_log, f"Encontradas {len(clausulas)} cláusulas")
            
            if not clausulas:
                raise DocumentEmptyError(
                    "Nenhuma cláusula encontrada no documento",
                    user_message="Não foi possível encontrar cláusulas no documento."
                )
            
            # Converter clausulas (index, texto) em chunks (id_clausula, titulo, texto) para Agente 2
            chunks = []
            for c in clausulas:
                idx = c.get("index", 0)
                texto = c.get("texto", "")
                titulo = (texto.split("\n")[0].strip() if texto else "") or f"Cláusula {idx}"
                if len(titulo) > 200:
                    titulo = titulo[:200].rsplit(" ", 1)[0] or titulo[:200]
                chunks.append({
                    "id_clausula": str(idx),
                    "titulo": titulo,
                    "texto": texto,
                })
            contexto_global = {}
            
            # === ETAPA 4: Agente 2 – Matcher (por regra, top 5 chunks) + Verificador ===
            regras_ativas = [r for r in regras if r.get("ativa", True)]
            total_regras = len(regras_ativas)
            self._log(on_log, f"Aplicando {total_regras} regras de conformidade")

            self._log(on_log, "Buscando trechos relevantes para análise...")
            self._progress(on_progress, "Busca e Comparação", 0.38)
            matcher = AgentMatcher(embedding_function, db_path=str(self.gerenciador_clausulas.db_path))
            match_resultado = matcher.match_regras_chunks(
                chunks, regras_ativas,
                threshold_similaridade=threshold_similaridade,
                top_k_max=5,
            )

            # === ETAPA 5: Verificador com Paralelização ===
            modelo_config = GerenciadorModelos.obter_modelo(modelo_llm_id)
            if not modelo_config:
                raise ModelNotFoundError(
                    f"Modelo LLM '{modelo_llm_id}' não encontrado",
                    user_message="Modelo de IA não encontrado. Selecione outro modelo."
                )
            validacao_llm = GerenciadorModelos.validar_api_keys(modelo_config)
            if not validacao_llm["valido"]:
                raise APIKeyError(
                    validacao_llm["mensagem"],
                    user_message="Chave de API do modelo LLM inválida ou não configurada."
                )
            llm = GerenciadorModelos.criar_llm(modelo_config, temperature=temperatura)
            agent_verificador = AgentVerificador(llm, tipo_contrato=tipo_contrato, idioma=idioma)

            self._log(on_log, f"Verificando {total_regras} regras em paralelo...")
            
            # Workers não chamam on_progress/on_log (evitar NoSessionContext). Atualizações na thread principal.
            def verificar_regra_worker(item: Dict, idx: int) -> Dict:
                """Worker para verificar uma regra em paralelo. Não usa Streamlit/callbacks."""
                regra = item["regra"]
                nome_regra = regra.get("titulo", "Regra")[:50]
                top_5 = item.get("top_5_chunks", [])
                try:
                    resultado = agent_verificador.analisar_regra_chunks(regra, top_5)
                    resultado["_nome_regra"] = nome_regra
                    return resultado
                except Exception as e:
                    erro_tipo = type(e).__name__
                    erro_msg = str(e)
                    erro_detalhado = self._formatar_erro_verificacao(erro_tipo, erro_msg, nome_regra)
                    return {
                        "eh_violacao": False,
                        "problema": "",
                        "chunk": None,
                        "regra": regra,
                        "_nome_regra": nome_regra,
                        "_erro_log": erro_detalhado,
                    }
            
            verificacoes = []
            regras_concluidas = [0]  # mutável para closure
            max_workers = min(4, total_regras) if total_regras > 0 else 1
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(verificar_regra_worker, item, i): i
                    for i, item in enumerate(match_resultado)
                }
                for future in as_completed(futures):
                    try:
                        resultado = future.result()
                        erro_log = resultado.pop("_erro_log", None)
                        if erro_log:
                            self._log(on_log, erro_log)
                        regras_concluidas[0] += 1
                        progresso = 0.55 + (regras_concluidas[0] / total_regras) * 0.25
                        nome_regra = resultado.pop("_nome_regra", "Regra")
                        self._progress(
                            on_progress,
                            f"Verificando regra {regras_concluidas[0]} de {total_regras}: {nome_regra}",
                            progresso,
                            {
                                "etapa": "verificacao",
                                "regra_atual": nome_regra,
                                "idx_regra": regras_concluidas[0],
                                "total_regras": total_regras,
                            },
                        )
                        verificacoes.append(resultado)
                    except Exception as e:
                        erro_tipo = type(e).__name__
                        erro_msg = str(e)
                        self._log(on_log, f"[ERRO CRÍTICO] Falha no worker de verificação")
                        self._log(on_log, f"  └─ Tipo: {erro_tipo}")
                        self._log(on_log, f"  └─ Detalhe: {erro_msg[:200]}")

            violacoes_validadas = [v for v in verificacoes if v.get("eh_violacao") and v.get("chunk")]
            conformidades_finais = [v for v in verificacoes if not v.get("eh_violacao")]
            violacoes_invalidadas = []
            resumo = ""
            self._log(on_log, f"Violações detectadas: {len(violacoes_validadas)}")

            # === ETAPA 6: Reescritor (paralelizado) ===
            if violacoes_validadas:
                self._log(on_log, "Preparando sugestões de redação...")
                self._progress(on_progress, "Sugestões de Redação", 0.85)
                agent4_reesc = AgentReescritor(llm, tipo_contrato=tipo_contrato, idioma=idioma)
                total_violacoes = len(violacoes_validadas)
                # Workers não chamam on_progress/on_log (evitar NoSessionContext).
                def reescrever_worker(idx: int, v: Dict) -> tuple:
                    """Worker para reescrever uma violação em paralelo. Não usa Streamlit/callbacks."""
                    nome_violacao = v.get("regra", {}).get("titulo", "")[:40]
                    try:
                        sugestao = agent4_reesc.reescrever_clausula(v, contexto_global)
                        return (idx, sugestao, None)
                    except Exception as e:
                        erro_tipo = type(e).__name__
                        erro_msg = str(e)
                        erro_detalhado = self._formatar_erro_reescrita(erro_tipo, erro_msg, nome_violacao, idx + 1)
                        return (idx, None, erro_detalhado)

                reescritas_concluidas = [0]
                max_workers_reescrita = min(4, total_violacoes) if total_violacoes > 0 else 1
                resultados_reescrita: Dict[int, Any] = {}
                with ThreadPoolExecutor(max_workers=max_workers_reescrita) as executor:
                    futures_reescrita = {
                        executor.submit(reescrever_worker, idx, v): idx
                        for idx, v in enumerate(violacoes_validadas)
                    }
                    for future in as_completed(futures_reescrita):
                        try:
                            idx, sugestao, erro_log = future.result()
                            if erro_log:
                                self._log(on_log, erro_log)
                            reescritas_concluidas[0] += 1
                            progresso = 0.85 + (reescritas_concluidas[0] / total_violacoes) * 0.05
                            nome_violacao = violacoes_validadas[idx].get("regra", {}).get("titulo", "")[:40]
                            self._progress(
                                on_progress,
                                f"Sugestão {reescritas_concluidas[0]} de {total_violacoes}: {nome_violacao}",
                                progresso,
                                {
                                    "etapa": "reescrita",
                                    "regra_atual": nome_violacao,
                                    "idx_regra": reescritas_concluidas[0],
                                    "total_regras": total_violacoes,
                                },
                            )
                            if not erro_log:
                                self._log(on_log, f"Sugestão {reescritas_concluidas[0]} de {total_violacoes} preparada")
                            resultados_reescrita[idx] = sugestao
                        except Exception as e:
                            erro_tipo = type(e).__name__
                            erro_msg = str(e)
                            self._log(on_log, f"[ERRO CRÍTICO] Falha no worker de reescrita")
                            self._log(on_log, f"  └─ Tipo: {erro_tipo}")
                            self._log(on_log, f"  └─ Detalhe: {erro_msg[:200]}")
                            idx = futures_reescrita[future]
                            resultados_reescrita[idx] = None

                for idx in range(total_violacoes):
                    violacoes_validadas[idx]["sugestao_reescrita"] = resultados_reescrita.get(idx)

            # === ETAPA 7: Gerar documentos ===
            self._progress(on_progress, "Finalizando Documentos", 0.92)
            from output.docx import gerar_problemas_docx, gerar_solucao_docx
            from output.comparar_docx import gerar_doc_comparado
            from pathlib import Path
            doc_problemas_bytes = gerar_problemas_docx(violacoes_validadas)
            doc_solucao_bytes = gerar_solucao_docx(violacoes_validadas)
            doc_explicacao_bytes = gerar_doc_comparado(doc_problemas_bytes, doc_solucao_bytes)
            from modulos.comum import limpar_docs_excedentes
            output_dir = Path("output") / "docs"
            output_dir.mkdir(parents=True, exist_ok=True)
            nome_base = Path(nome_arquivo).stem
            ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            (output_dir / f"problemas_{nome_base}_{ts}.docx").write_bytes(doc_problemas_bytes)
            (output_dir / f"solucao_{nome_base}_{ts}.docx").write_bytes(doc_solucao_bytes)
            if doc_explicacao_bytes:
                (output_dir / f"explicacao_{nome_base}_{ts}.docx").write_bytes(doc_explicacao_bytes)
            limpar_docs_excedentes(output_dir)

            # Finalizar
            self._progress(on_progress, "Finalizando", 0.98)
            tempo_total = time.time() - tempo_inicio
            self._progress(on_progress, "Concluído!", 1.0)
            self._log(on_log, f"Análise concluída em {tempo_total:.2f}s")
            self._log(on_log, f"Violações válidas: {len(violacoes_validadas)} | Conformidades: {len(conformidades_finais)}")

            return ResultadoAnalise(
                sucesso=True,
                mensagem="Análise concluída com sucesso",
                total_clausulas=len(chunks),
                clausulas_analisadas=len(chunks),
                violacoes=violacoes_validadas,
                conformidades=conformidades_finais,
                tempo_total=tempo_total,
                modelo_llm_usado=modelo_config.nome,
                modelo_embedding_usado=embedding_config.nome,
                tipo_contrato=tipo_contrato,
                contexto_global=contexto_global,
                violacoes_invalidadas=violacoes_invalidadas,
                resumo_consolidacao=resumo,
                gerar_sugestoes_reescrita=gerar_sugestoes_reescrita,
                doc_problemas_bytes=doc_problemas_bytes,
                doc_solucao_bytes=doc_solucao_bytes,
                doc_explicacao_bytes=doc_explicacao_bytes,
            )
        
        # Capturar exceções específicas
        except GabrielBaseException as e:
            self._log(on_log, f"ERRO: {e.message}")
            return self._erro(e.user_message)
        
        except Exception as e:
            self._log(on_log, f"ERRO inesperado: {str(e)}")
            # Tentar identificar tipo de erro comum
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                return self._erro("Limite de requisições atingido. Aguarde alguns minutos e tente novamente.")
            elif "api key" in error_str or "authentication" in error_str or "401" in error_str:
                return self._erro("Chave de API inválida ou não configurada.")
            elif "timeout" in error_str or "timed out" in error_str:
                return self._erro("O serviço de IA demorou para responder. Tente novamente.")
            elif "connection" in error_str or "network" in error_str:
                return self._erro("Não foi possível conectar ao serviço de IA. Verifique sua conexão.")
            else:
                return self._erro(f"Erro na análise: {str(e)}")
    
    def _validar_base_conhecimento(
        self, tipo_contrato: str, idioma: str = "pt", regras: Optional[List[Dict]] = None
    ) -> None:
        """
        Valida se a base de conhecimento está sincronizada.
        Lança exceção específica se não estiver.
        Se regras for passado, usa essa lista; caso contrário carrega do disco.
        """
        from modulos.comum import carregar_clausulas

        clausulas = regras if regras is not None else carregar_clausulas(tipo_contrato, idioma=idioma)

        if not clausulas:
            raise DatabaseEmptyError(
                f"Nenhuma cláusula encontrada para '{tipo_contrato}'",
                user_message=f"Nenhuma regra de conformidade encontrada para '{tipo_contrato}'."
            )
        
        status = self.gerenciador_clausulas.verificar_sincronizacao(
            tipo_contrato, 
            clausulas,
            idioma=idioma
        )
        
        if status == "nao_indexado":
            raise DatabaseNotIndexedError(
                f"Base não indexada para '{tipo_contrato}'",
                user_message="A base de regras não está indexada. Clique em 'Atualizar Base de Regras'."
            )
        
        if status == "desatualizado":
            raise DatabaseOutdatedError(
                f"Base desatualizada para '{tipo_contrato}'",
                user_message="A base de regras está desatualizada. Clique em 'Atualizar Base de Regras'."
            )
    
    @staticmethod
    def _erro(mensagem: str) -> ResultadoAnalise:
        """Cria resultado de erro."""
        return ResultadoAnalise(
            sucesso=False,
            mensagem=mensagem,
            total_clausulas=0,
            clausulas_analisadas=0,
            violacoes=[],
            conformidades=[],
            tempo_total=0.0,
            modelo_llm_usado="",
            modelo_embedding_usado="",
            tipo_contrato="",
            contexto_global={},
            violacoes_invalidadas=[],
            resumo_consolidacao=""
        )
    
    @staticmethod
    def _progress(callback: Optional[Callable], mensagem: str, valor: float, detalhes: Optional[Dict] = None):
        """Atualiza progress bar se callback existir. Suporta detalhes opcionais."""
        if callback:
            try:
                # Tentar chamar com 3 argumentos (novo formato)
                callback(mensagem, valor, detalhes)
            except TypeError:
                # Fallback para 2 argumentos (formato antigo)
                callback(mensagem, valor)
    
    @staticmethod
    def _log(callback: Optional[Callable], mensagem: str):
        """Adiciona log se callback existir."""
        if callback:
            callback(mensagem)
    
    @staticmethod
    def _formatar_erro_verificacao(erro_tipo: str, erro_msg: str, nome_regra: str) -> str:
        """
        Formata mensagem de erro de verificação de forma clara e informativa.
        Categoriza o erro e fornece contexto útil para debugging.
        """
        erro_lower = erro_msg.lower()
        
        # Categorizar o erro
        if "rate limit" in erro_lower or "429" in erro_lower:
            categoria = "LIMITE DE REQUISIÇÕES"
            sugestao = "Aguarde alguns segundos e tente novamente"
        elif "api key" in erro_lower or "authentication" in erro_lower or "401" in erro_lower:
            categoria = "AUTENTICAÇÃO"
            sugestao = "Verifique sua chave de API nas configurações"
        elif "timeout" in erro_lower or "timed out" in erro_lower:
            categoria = "TIMEOUT"
            sugestao = "O modelo demorou para responder, considere usar um modelo mais rápido"
        elif "connection" in erro_lower or "network" in erro_lower:
            categoria = "CONEXÃO"
            sugestao = "Verifique sua conexão com a internet"
        elif "json" in erro_lower or "parse" in erro_lower or "decode" in erro_lower:
            categoria = "RESPOSTA INVÁLIDA"
            sugestao = "O modelo retornou uma resposta mal formatada"
        elif "validation" in erro_lower or "pydantic" in erro_lower:
            categoria = "VALIDAÇÃO"
            sugestao = "O modelo não retornou os campos esperados"
        else:
            categoria = "ERRO GERAL"
            sugestao = "Erro inesperado durante a análise"
        
        # Truncar mensagem de erro para legibilidade
        erro_resumido = erro_msg[:150] + "..." if len(erro_msg) > 150 else erro_msg
        
        return (
            f"[{categoria}] Falha na regra: '{nome_regra}'\n"
            f"  └─ Tipo: {erro_tipo}\n"
            f"  └─ Causa: {erro_resumido}\n"
            f"  └─ Sugestão: {sugestao}"
        )
    
    @staticmethod
    def _formatar_erro_reescrita(erro_tipo: str, erro_msg: str, nome_violacao: str, idx: int) -> str:
        """
        Formata mensagem de erro de reescrita de forma clara e informativa.
        """
        erro_lower = erro_msg.lower()
        
        # Categorizar o erro
        if "rate limit" in erro_lower or "429" in erro_lower:
            categoria = "LIMITE DE REQUISIÇÕES"
            sugestao = "Aguarde alguns segundos"
        elif "timeout" in erro_lower or "timed out" in erro_lower:
            categoria = "TIMEOUT"
            sugestao = "O modelo demorou para gerar a sugestão"
        elif "json" in erro_lower or "parse" in erro_lower:
            categoria = "RESPOSTA INVÁLIDA"
            sugestao = "O modelo retornou resposta mal formatada"
        else:
            categoria = "ERRO GERAL"
            sugestao = "Erro ao gerar sugestão de reescrita"
        
        erro_resumido = erro_msg[:150] + "..." if len(erro_msg) > 150 else erro_msg
        
        return (
            f"[{categoria}] Falha na sugestão #{idx}: '{nome_violacao}'\n"
            f"  └─ Tipo: {erro_tipo}\n"
            f"  └─ Causa: {erro_resumido}\n"
            f"  └─ Sugestão: {sugestao}"
        )
