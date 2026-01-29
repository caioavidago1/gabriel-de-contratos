"""
Agent 2: Matcher – para cada regra ativa, obtém chunks do contrato com similaridade >= threshold.
"""
import uuid
from typing import List, Dict, Any

import chromadb
from pathlib import Path


class AgentMatcher:
    """Para cada regra ativa, busca chunks do contrato com similaridade >= threshold (cosine)."""

    def __init__(self, embedding_function, db_path: str = "./chroma_db"):
        self.embedding_function = embedding_function
        self.db_path = Path(db_path)
        self.client = chromadb.PersistentClient(path=str(self.db_path))

    def match_regras_chunks(
        self,
        chunks: List[Dict],
        regras_ativas: List[Dict],
        threshold_similaridade: float = 0.45,
        top_k_max: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Para cada regra ativa, retorna até top_k_max chunks cuja similaridade com buscar_em
        seja >= threshold_similaridade (cosine; 0 a 1).

        Args:
            chunks: Lista de chunks do Agente 1 (id_clausula, titulo, texto).
            regras_ativas: Lista de regras com buscar_em, regra_spectra, como_corrigir, ativa.
            threshold_similaridade: Mínimo de similaridade (0–1) para incluir um chunk. Padrão 0.45.
            top_k_max: Máximo de chunks por regra (padrão 5).

        Returns:
            Lista de {regra, top_5_chunks} para cada regra ativa (chunks que passaram no threshold).
        """
        if not chunks or not regras_ativas:
            return []

        chunk_texts = [
            f"{c.get('titulo', '')}\n\n{c.get('texto', '')}".strip() or c.get("texto", "")
            for c in chunks
        ]
        chunk_ids = [f"c_{i}" for i in range(len(chunks))]

        coll_name = f"temp_contract_{uuid.uuid4().hex[:12]}"
        try:
            collection = self.client.create_collection(
                name=coll_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
            collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                metadatas=[{"idx": i} for i in range(len(chunks))],
            )
        except Exception:
            try:
                self.client.delete_collection(coll_name)
            except Exception:
                pass
            raise

        resultado = []
        try:
            n_candidatos = min(50, len(chunks))
            for regra in regras_ativas:
                buscar_em = regra.get("buscar_em", "").strip()
                if not buscar_em:
                    resultado.append({"regra": regra, "top_5_chunks": []})
                    continue
                res = collection.query(
                    query_texts=[buscar_em],
                    n_results=n_candidatos,
                    include=["distances"],
                )
                if not res or not res.get("ids") or not res["ids"][0]:
                    resultado.append({"regra": regra, "top_5_chunks": []})
                    continue
                ids_retornados = res["ids"][0]
                distances = res.get("distances", [[]])[0]
                # Cosine distance: similarity = 1 - distance. Incluir só similarity >= threshold.
                top_chunks = []
                for j, cid in enumerate(ids_retornados):
                    if len(top_chunks) >= top_k_max:
                        break
                    dist = distances[j] if j < len(distances) else 1.0
                    similarity = 1.0 - float(dist)
                    if similarity < threshold_similaridade:
                        continue
                    if cid.startswith("c_") and cid[2:].isdigit():
                        idx = int(cid[2:])
                        if 0 <= idx < len(chunks):
                            top_chunks.append(chunks[idx])
                resultado.append({"regra": regra, "top_5_chunks": top_chunks})
        finally:
            try:
                self.client.delete_collection(coll_name)
            except Exception:
                pass

        return resultado
