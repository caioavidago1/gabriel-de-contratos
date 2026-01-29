"""
Agent 3: Verificador de Violações
Analisa regra + top 5 chunks do contrato.
analisar_regra_chunks(regra, top_5_chunks) -> eh_violacao, problema, chunk, regra.

Nota: Este agente usa prompts inline. Os arquivos prompts/agent1_* (Verificador)
existem para a UI/edição; uma refatoração futura pode carregá-los via
carregar_prompt_tipo(tipo, "agent1", "system"|"user").
"""
from typing import Dict, List, Any
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class ResultadoVerificacaoRegra(BaseModel):
    """Saída estruturada do verificador para regra + top 5 chunks."""
    eh_violacao: bool = Field(description="True se algum dos trechos potencialmente infringe a regra Spectra.")
    problema: str = Field(description="Descrição objetiva do problema (vazio se eh_violacao=False).")
    chunk_index: int = Field(description="Índice do trecho que viola (1 a 5). 0 se nenhum.")


class AgentVerificador:
    """Analisa possíveis violações: regra Spectra + 5 trechos do contrato."""

    def __init__(self, llm):
        self.llm = llm

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
        regra_spectra = regra.get("regra_spectra", "").strip()
        titulo_regra = regra.get("titulo", "Regra")
        chunks_texto = "\n\n---\n\n".join(
            f"Trecho {i+1} (título: {c.get('titulo', '')[:80]}):\n{c.get('texto', '')}"
            for i, c in enumerate(top_5_chunks)
        )
        prompt_regra = ChatPromptTemplate.from_messages([
            ("system",
             "Você é um especialista em análise de contratos. Dada uma REGRA SPECTRA e 5 trechos de contrato, "
             "decida se ALGUM dos trechos potencialmente INFringe a regra. Seja objetivo: só marque violação se "
             "o trecho claramente contrariar a regra. Responda com eh_violacao (true/false), problema (descrição breve) "
             "e chunk_index (1 a 5; qual trecho viola; 0 se nenhum)."),
            ("human",
             "REGRA SPECTRA ({titulo_regra}):\n{regra_spectra}\n\n"
             "TRECHOS DO CONTRATO:\n{chunks_texto}\n\n"
             "Algum trecho infringe a regra? Responda no formato estruturado.")
        ])
        chain = prompt_regra | self.llm.with_structured_output(
            ResultadoVerificacaoRegra, method="json_schema"
        )
        try:
            out = chain.invoke({
                "titulo_regra": titulo_regra,
                "regra_spectra": regra_spectra,
                "chunks_texto": chunks_texto,
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
