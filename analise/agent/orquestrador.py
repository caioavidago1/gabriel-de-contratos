"""
Orquestrador da análise de contratos.
Coordena todo o pipeline de análise.
"""
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
import time

from .agent1_extrator_docx import extrair_clausulas_docx
from .agent2_matcher import AgentMatcher
from .agent3_verificador import AgentVerificador
from .agent4_reescritor import AgentReescritor
from analise.embeddings.clausulas import GerenciadorClausulasReferencia
from .escolha_modelo import GerenciadorModelos, GerenciadorEmbeddings


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
        on_progress: Optional[Callable[[str, float], None]] = None,
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
            on_progress: callback para atualizar progress bar (mensagem, porcentagem)
            on_log: callback para logs
        
        Returns:
            ResultadoAnalise com todos os dados
        """
        tempo_inicio = time.time()
        
        try:
            # === ETAPA 1: Validar e Criar Embedding Function ===
            self._log(on_log, "Configurando modelo de embedding...")
            self._progress(on_progress, "Configurando embedding", 0.02)
            
            embedding_config = GerenciadorEmbeddings.obter_embedding(modelo_embedding_id)
            if not embedding_config:
                return self._erro(f"Modelo de embedding '{modelo_embedding_id}' não encontrado")
            
            # Validar API key do embedding
            validacao_embedding = GerenciadorEmbeddings.validar_api_keys(embedding_config)
            if not validacao_embedding["valido"]:
                return self._erro(validacao_embedding["mensagem"])
            
            # Criar embedding function
            embedding_function = GerenciadorEmbeddings.criar_embedding_function(embedding_config)
            
            # === ETAPA 2: Validar Base de Conhecimento ===
            self._log(on_log, "Validando base de conhecimento...")
            self._progress(on_progress, "Validando base de conhecimento", 0.05)
            
            validacao = self._validar_base_conhecimento(tipo_contrato, idioma=idioma)
            if not validacao["ok"]:
                return self._erro(validacao["mensagem"])
            
            # === ETAPA 3: Agente 1 – Extrator DOCX (lógica ia.py) ===
            self._log(on_log, f"Agente 1: extraindo cláusulas de {nome_arquivo}...")
            self._progress(on_progress, "Agente 1 – Extração", 0.15)
            
            resultado_ag1 = extrair_clausulas_docx(
                arquivo_bytes,
                on_log=lambda msg: self._log(on_log, msg),
            )
            clausulas = resultado_ag1.get("clausulas", [])
            self._log(on_log, f"Encontradas {len(clausulas)} cláusulas")
            
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
            from modulos.comum import carregar_clausulas
            regras = carregar_clausulas(tipo_contrato, idioma=idioma)
            regras_ativas = [r for r in regras if r.get("ativa", True)]
            self._log(on_log, f"{len(regras_ativas)} regras ativas")

            self._log(on_log, f"Agente 2: Matcher (threshold={threshold_similaridade}) + Verificador...")
            self._progress(on_progress, "Agente 2 – Matcher", 0.38)
            matcher = AgentMatcher(embedding_function, db_path=str(self.gerenciador_clausulas.db_path))
            match_resultado = matcher.match_regras_chunks(
                chunks, regras_ativas,
                threshold_similaridade=threshold_similaridade,
                top_k_max=5,
            )

            # === ETAPA 6: Verificador (regra + chunks acima do threshold → eh_violacao, problema, chunk) ===
            modelo_config = GerenciadorModelos.obter_modelo(modelo_llm_id)
            if not modelo_config:
                return self._erro(f"Modelo LLM '{modelo_llm_id}' não encontrado")
            validacao_llm = GerenciadorModelos.validar_api_keys(modelo_config)
            if not validacao_llm["valido"]:
                return self._erro(validacao_llm["mensagem"])
            llm = GerenciadorModelos.criar_llm(modelo_config, temperature=temperatura)
            agent_verificador = AgentVerificador(llm)

            self._log(on_log, "Verificador: analisando regra + 5 chunks...")
            self._progress(on_progress, "Verificador", 0.55)
            verificacoes = []
            for item in match_resultado:
                regra = item["regra"]
                top_5 = item.get("top_5_chunks", [])
                try:
                    res = agent_verificador.analisar_regra_chunks(regra, top_5)
                    verificacoes.append(res)
                except Exception as e:
                    self._log(on_log, f"Aviso: falha ao verificar regra '{regra.get('titulo', '')}': {e}")
                    verificacoes.append({"eh_violacao": False, "problema": "", "chunk": None, "regra": regra})

            violacoes_validadas = [v for v in verificacoes if v.get("eh_violacao") and v.get("chunk")]
            conformidades_finais = [v for v in verificacoes if not v.get("eh_violacao")]
            violacoes_invalidadas = []
            resumo = ""
            self._log(on_log, f"Violações detectadas: {len(violacoes_validadas)}")

            # Reescritor (violação → sugestao_reescrita): sempre ativo quando há violações
            if violacoes_validadas:
                self._log(on_log, "Reescritor: gerando sugestões para violações...")
                self._progress(on_progress, "Reescritor", 0.85)
                agent4_reesc = AgentReescritor(llm, tipo_contrato=tipo_contrato, idioma=idioma)
                for idx, v in enumerate(violacoes_validadas):
                    try:
                        sugestao = agent4_reesc.reescrever_clausula(v, contexto_global)
                        v["sugestao_reescrita"] = sugestao
                        self._log(on_log, f"Sugestão {idx + 1}/{len(violacoes_validadas)} gerada")
                    except Exception as e:
                        self._log(on_log, f"Aviso: falha ao reescrever violação {idx + 1}: {e}")
                        v["sugestao_reescrita"] = None

            # === ETAPA 8: Gerar problemas, solução e explicacao = Compare(problemas, solução) ===
            self._progress(on_progress, "Gerando DOCX", 0.92)
            from output.docx import gerar_problemas_docx, gerar_solucao_docx
            from output.comparar_docx import gerar_doc_comparado
            from pathlib import Path
            doc_problemas_bytes = gerar_problemas_docx(violacoes_validadas)
            doc_solucao_bytes = gerar_solucao_docx(violacoes_validadas)
            doc_explicacao_bytes = gerar_doc_comparado(doc_problemas_bytes, doc_solucao_bytes)
            output_dir = Path("output") / "docs"
            output_dir.mkdir(parents=True, exist_ok=True)
            nome_base = Path(nome_arquivo).stem
            ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            (output_dir / f"problemas_{nome_base}_{ts}.docx").write_bytes(doc_problemas_bytes)
            (output_dir / f"solucao_{nome_base}_{ts}.docx").write_bytes(doc_solucao_bytes)
            if doc_explicacao_bytes:
                (output_dir / f"explicacao_{nome_base}_{ts}.docx").write_bytes(doc_explicacao_bytes)

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
            
        except Exception as e:
            self._log(on_log, f"ERRO: {str(e)}")
            return self._erro(f"Erro na análise: {str(e)}")
    
    def _validar_base_conhecimento(self, tipo_contrato: str, idioma: str = "pt") -> Dict:
        """Valida se a base de conhecimento está sincronizada."""
        from modulos.comum import carregar_clausulas
        
        clausulas = carregar_clausulas(tipo_contrato, idioma=idioma)
        
        if not clausulas:
            return {
                "ok": False,
                "mensagem": f"Nenhuma cláusula encontrada para '{tipo_contrato}'"
            }
        
        status = self.gerenciador_clausulas.verificar_sincronizacao(
            tipo_contrato, 
            clausulas,
            idioma=idioma
        )
        
        if status == "nao_indexado":
            return {
                "ok": False,
                "mensagem": "Base de conhecimento não indexada. Indexe as cláusulas primeiro."
            }
        
        if status == "desatualizado":
            return {
                "ok": False,
                "mensagem": "Base de conhecimento desatualizada. Reindexe as cláusulas."
            }
        
        return {"ok": True, "mensagem": "Base de conhecimento válida"}
    
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
    def _progress(callback: Optional[Callable], mensagem: str, valor: float):
        """Atualiza progress bar se callback existir."""
        if callback:
            callback(mensagem, valor)
    
    @staticmethod
    def _log(callback: Optional[Callable], mensagem: str):
        """Adiciona log se callback existir."""
        if callback:
            callback(mensagem)
