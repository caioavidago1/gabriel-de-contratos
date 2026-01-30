"""
Agent 3: Verificador de Violações
Analisa regra + top 5 chunks do contrato.
analisar_regra_chunks(regra, top_5_chunks) -> eh_violacao, problema, chunk, regra.
Prompts carregados de prompts/<tipo>/agent3_system.txt e agent3_user.txt.
"""
from typing import Dict, List, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from analise.agent import carregar_prompt_tipo


class ResultadoVerificacaoRegra(BaseModel):
    """Saída estruturada do verificador para regra + top 5 chunks."""
    eh_violacao: bool = Field(description="True se algum dos trechos potencialmente infringe a regra Spectra.")
    problema: str = Field(description="Descrição objetiva do problema (vazio se eh_violacao=False).")
    chunk_index: int = Field(description="Índice do trecho que viola (1 a 5). 0 se nenhum.")


class AgentVerificador:
    """Analisa possíveis violações: regra Spectra + 5 trechos do contrato."""

    def __init__(self, llm, tipo_contrato: Optional[str] = None, idioma: str = "pt"):
        self.llm = llm
        self.tipo_contrato = tipo_contrato or "_defaults"
        self.idioma = idioma

    def _criar_prompt(self) -> ChatPromptTemplate:
        """Monta o prompt a partir dos arquivos em prompts/<tipo>/agent3_*.txt."""
        system_msg = carregar_prompt_tipo(self.tipo_contrato, "agent3", "system", self.idioma)
        user_msg = carregar_prompt_tipo(self.tipo_contrato, "agent3", "user", self.idioma)
        return ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", user_msg),
        ])

    def analisar_regra_chunks(
        self,
        regra: Dict,
        top_5_chunks: List[Dict],
    ) -> Dict[str, Any]:
        """
        Verifica se algum dos 5 trechos do contrato potencialmente infringe a regra Spectra.
        Saída: eh_violacao, problema, chunk (o que viola), regra.
        """
        if not top_5_chunks:
            return {
                "eh_violacao": False,
                "problema": "",
                "chunk": None,
                "regra": regra,
            }
        descricao_regra = regra.get("regra_spectra", "").strip()
        nome_regra = regra.get("titulo", "Regra")
        trechos_contrato = "\n\n---\n\n".join(
            f"Trecho {i+1} (título: {c.get('titulo', '')[:80]}):\n{c.get('texto', '')}"
            for i, c in enumerate(top_5_chunks)
        )
        prompt_regra = self._criar_prompt()
        chain = prompt_regra | self.llm.with_structured_output(
            ResultadoVerificacaoRegra, method="json_schema"
        )
        try:
            out = chain.invoke({
                "nome_regra": nome_regra,
                "descricao_regra": descricao_regra,
                "trechos_contrato": trechos_contrato,
            })
        except Exception:
            return {
                "eh_violacao": False,
                "problema": "",
                "chunk": None,
                "regra": regra,
            }
        idx = out.chunk_index
        chunk_que_viola = top_5_chunks[idx - 1] if 1 <= idx <= len(top_5_chunks) else None
        return {
            "eh_violacao": out.eh_violacao and chunk_que_viola is not None,
            "problema": out.problema or "",
            "chunk": chunk_que_viola,
            "regra": regra,
        }
