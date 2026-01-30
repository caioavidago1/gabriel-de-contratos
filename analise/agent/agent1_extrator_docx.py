"""
Agente 1: Extrator de cláusulas a partir de DOCX.
Recebe o .docx (bytes), analisa cru como ia.py (lógica validada), retorna JSON com cláusulas.
Cache por hash do documento: mesmo DOCX reutiliza resultado sem reprocessar.
"""
import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Optional, Callable

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import docx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from analise.agent import carregar_prompt_tipo

load_dotenv()

# Diretório de cache apenas do Agente 1 (hash do docx → resultado)
_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache" / "agent1"


class ExtractedClause(BaseModel):
    """Saída estruturada do LLM para uma cláusula."""
    is_last_clause: bool = Field(
        description="True se esta for a ÚLTIMA cláusula do documento inteiro."
    )
    clause_full_text: str = Field(
        description="O texto COMPLETO da cláusula extraída (incluindo título, caput, parágrafos, incisos)."
    )
    end_quote: str = Field(
        description="As ultimas 10-15 palavras exatas onde esta cláusula termina no texto original, para que o sistema possa cortar o texto corretamente."
    )


def _criar_prompt_extrator(idioma: str = "pt") -> ChatPromptTemplate:
    """Monta o prompt do extrator a partir dos arquivos em prompts/_defaults."""
    system_msg = carregar_prompt_tipo("_defaults", "extrator", "system", idioma)
    user_msg = carregar_prompt_tipo("_defaults", "extrator", "user", idioma)
    return ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", user_msg),
    ])


def extract_text_from_docx_bytes(docx_bytes: bytes) -> str:
    """Extrai texto do DOCX a partir de bytes."""
    doc = docx.Document(BytesIO(docx_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def _hash_docx(docx_bytes: bytes) -> str:
    """Chave de cache: hash SHA256 do conteúdo do documento."""
    return hashlib.sha256(docx_bytes).hexdigest()


def _cache_path(cache_key: str) -> Path:
    """Caminho do arquivo de cache para a chave."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{cache_key}.json"


def extrair_clausulas_docx(
    docx_bytes: bytes,
    on_log: Optional[Callable[[str], None]] = None,
    max_clausulas: int = 200,
    chunk_size: int = 15000,
    idioma: str = "pt",
) -> Dict:
    """
    Agente 1: recebe .docx (bytes), extrai cláusulas com a lógica validada (ia.py).
    Retorna {"clausulas": [{"index": 1, "texto": "..."}, ...]}.
    Usa cache por hash do documento: mesmo arquivo retorna resultado em cache sem reprocessar.
    """
    log = on_log or (lambda _: None)
    cache_key = _hash_docx(docx_bytes)
    path = _cache_path(cache_key)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            clausulas = data.get("clausulas", [])
            if clausulas:
                log(f"Cache do Agente 1: documento já processado ({len(clausulas)} cláusulas).")
                return {"clausulas": clausulas}
            # cache vazio ou estrutura inesperada: reprocessar
        except Exception as e:
            log(f"Cache inválido, reprocessando: {e}")

    full_text = extract_text_from_docx_bytes(docx_bytes)
    remaining = full_text
    clauses = []

    log(f"Texto total: {len(full_text)} caracteres.")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt_extrator = _criar_prompt_extrator(idioma)
    chain = prompt_extrator | llm.with_structured_output(ExtractedClause, method="json_schema")

    for i in range(max_clausulas):
        if len(remaining.strip()) < 50:
            break
        # Log a cada 5 cláusulas para não poluir (1, 5, 10, 15, ...)
        if (i + 1) == 1 or (i + 1) % 5 == 0:
            log(f"Processando cláusula {i+1}...")
        chunk = remaining[:chunk_size]
        try:
            result = chain.invoke({"text": chunk})
        except Exception as e:
            log(f"Erro LLM: {e}")
            break
        clauses.append({"index": i + 1, "texto": result.clause_full_text})

        end_pos = remaining.find(result.end_quote)
        if end_pos == -1:
            log("Não encontrei a frase final no texto. Tentando recuperação...")
            end_pos = remaining.find(result.clause_full_text[-20:])
            if end_pos == -1:
                log("Falha total no corte. Abortando.")
                break
        cut_index = end_pos + len(result.end_quote)
        remaining = remaining[cut_index:].strip()
        if result.is_last_clause or not remaining:
            log("Fim do documento detectado.")
            break

    resultado = {"clausulas": clauses}
    try:
        _cache_path(cache_key).write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log(f"Não foi possível gravar cache: {e}")
    return resultado
