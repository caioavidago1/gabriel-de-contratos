"""
Agent 4: Reescritor de Cláusulas Problemáticas
Sugere uma versão reescrita da cláusula que corrige a violação, alinhada às preferências da Spectra.
"""
from typing import Dict, List, Optional
import re
from langchain_core.prompts import ChatPromptTemplate
from analise.agent import carregar_prompt_tipo


class AgentReescritor:
    """Reescreve cláusulas problemáticas conforme preferências da base de conhecimento."""

    def __init__(self, llm, tipo_contrato: Optional[str] = None, idioma: str = "pt"):
        self.llm = llm
        self.tipo_contrato = tipo_contrato
        self.idioma = idioma
        self.prompt = self._criar_prompt()

    def _criar_prompt(self):
        # Sempre carregar prompts de arquivos .txt
        # Se nenhum tipo foi informado, usar os defaults em `prompts/_defaults`
        tipo = self.tipo_contrato or "_defaults"
        system_msg = carregar_prompt_tipo(tipo, "agent4", "system", self.idioma)
        user_msg = carregar_prompt_tipo(tipo, "agent4", "user", self.idioma)

        return ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("user", user_msg)
        ])

    def reescrever_clausula(
        self,
        violacao: Dict,
        contexto_global: Dict
    ) -> Dict:
        """
        Gera sugestão de reescrita para uma cláusula problemática.

        Args:
            violacao: Violação validada (com chunk, clausula_violada, motivo, etc.)
            contexto_global: Contexto extraído pelo Agent0

        Returns:
            {"texto_original": str, "texto_reescrito": str, "explicacao_mudancas": str}
        """
        chunk = violacao.get("chunk", {})
        texto_original = chunk.get("texto", "")
        titulo = chunk.get("titulo", violacao.get("localizacao", "Cláusula"))

        regra = violacao.get("regra", {})
        regra_violada = (
            regra.get("titulo") or regra.get("regra_spectra", "")
            if regra
            else violacao.get("clausula_violada", "Regra não identificada")
        )
        problema = violacao.get("problema", "").strip()
        como_corrigir = (regra.get("como_corrigir", "") if regra else "").strip()
        motivos = violacao.get("motivo", [])
        motivo_texto = "\n".join(f"- {m}" for m in motivos) if isinstance(motivos, list) else str(motivos)
        if problema:
            motivo_texto = problema if not motivo_texto else f"{problema}\n{motivo_texto}"
        if not motivo_texto and violacao.get("analise_agent1"):
            motivo_texto = violacao["analise_agent1"][:800]
        if como_corrigir:
            motivo_texto = f"{motivo_texto}\n\nComo corrigir (orientação Spectra): {como_corrigir}"

        contexto_texto = self._formatar_contexto(contexto_global or {})

        mensagens = self.prompt.format_messages(
            titulo=titulo,
            texto_original=texto_original,
            regra_violada=regra_violada,
            motivo=motivo_texto,
            contexto_global=contexto_texto or "Nenhum contexto adicional."
        )

        # Evitar NoSessionContext em workers (ThreadPoolExecutor); desabilitar callbacks.
        resposta = self.llm.invoke(mensagens, config={"callbacks": []})
        parsed = self._parsear_resposta(resposta.content, texto_original)

        return {
            "texto_original": texto_original,
            "texto_reescrito": parsed.get("texto_reescrito", ""),
            "explicacao_mudancas": parsed.get("explicacao_mudancas", "")
        }

    def _formatar_contexto(self, contexto: Dict) -> str:
        partes = []
        if contexto.get("definicoes"):
            partes.append("Definições: " + "; ".join(f"{k}: {v[:80]}..." if len(str(v)) > 80 else f"{k}: {v}" for k, v in list(contexto["definicoes"].items())[:5]))
        if contexto.get("excecoes_confidencialidade"):
            partes.append("Exceções: " + str(contexto["excecoes_confidencialidade"])[:200])
        if contexto.get("prazo_vigencia"):
            partes.append("Prazo: " + str(contexto["prazo_vigencia"]))
        if contexto.get("lei_foro"):
            partes.append("Lei/Foro: " + str(contexto["lei_foro"]))
        return "\n".join(partes) if partes else ""

    def _parsear_resposta(self, resposta: str, texto_original_fallback: str) -> Dict:
        """Extrai TEXTO REESCRITO e EXPLICAÇÃO DAS MUDANÇAS da resposta do LLM."""
        texto_reescrito = ""
        explicacao_mudancas = ""

        # Marcações em PT/EN
        for label_reescrito, label_explicacao in [
            ("TEXTO REESCRITO:", "EXPLICAÇÃO DAS MUDANÇAS:"),
            ("TEXTO REESCRITO", "EXPLICAÇÃO DAS MUDANÇAS"),
            ("REWRITTEN TEXT:", "EXPLANATION OF CHANGES:"),
        ]:
            idx_reescrito = resposta.find(label_reescrito)
            idx_explicacao = resposta.find(label_explicacao)
            if idx_reescrito != -1:
                inicio_reescrito = idx_reescrito + len(label_reescrito)
                fim_reescrito = idx_explicacao if idx_explicacao > idx_reescrito else len(resposta)
                texto_reescrito = resposta[inicio_reescrito:fim_reescrito].strip()
            if idx_explicacao != -1:
                inicio_explicacao = idx_explicacao + len(label_explicacao)
                explicacao_mudancas = resposta[inicio_explicacao:].strip()
                # Remover código/JSON residual
                if "```" in explicacao_mudancas:
                    explicacao_mudancas = explicacao_mudancas.split("```")[0].strip()
            if texto_reescrito or explicacao_mudancas:
                break

        if not texto_reescrito and len(resposta) > 50:
            # Fallback: primeiro bloco de texto como reescrita
            blocos = re.split(r"\n\s*\n", resposta.strip(), maxsplit=1)
            texto_reescrito = blocos[0].strip() if blocos else texto_original_fallback

        return {
            "texto_reescrito": texto_reescrito or texto_original_fallback,
            "explicacao_mudancas": explicacao_mudancas or "Alterações não detalhadas."
        }
