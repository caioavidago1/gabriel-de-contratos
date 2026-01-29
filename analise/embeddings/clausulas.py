"""
Gerenciamento da base de conhecimento de cláusulas.
Responsável APENAS por indexar as regras do JSON no ChromaDB.
"""
import chromadb
from pathlib import Path
from typing import List, Dict, Optional, Literal
import json
import hashlib


class GerenciadorClausulasReferencia:
    """Gerencia indexação das cláusulas de referência (regras do JSON)."""
    
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.db_path))
    
    @staticmethod
    def calcular_hash_clausulas(clausulas: List[dict]) -> str:
        """Calcula hash único das cláusulas para detectar mudanças."""
        clausulas_str = json.dumps(clausulas, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(clausulas_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _obter_nome_collection(tipo_contrato: str, idioma: str = "pt") -> str:
        """Gera o nome da collection incluindo o idioma."""
        tipo_normalizado = tipo_contrato.lower().replace(' ', '_')
        return f"{tipo_normalizado}_clausulas_{idioma}"
    
    def obter_versao_indexada(self, tipo_contrato: str, idioma: str = "pt") -> Optional[str]:
        """Obtém o hash da versão atualmente indexada no ChromaDB."""
        collection_name = self._obter_nome_collection(tipo_contrato, idioma)
        try:
            collection = self.client.get_collection(name=collection_name)
            return collection.metadata.get('hash_clausulas')
        except:
            return None
    
    def verificar_sincronizacao(
        self, 
        tipo_contrato: str, 
        clausulas_json: List[dict],
        idioma: str = "pt"
    ) -> Literal["sincronizado", "desatualizado", "nao_indexado"]:
        """Verifica se o ChromaDB está sincronizado com o JSON."""
        if not clausulas_json:
            return "nao_indexado"
        
        hash_atual = self.calcular_hash_clausulas(clausulas_json)
        hash_indexado = self.obter_versao_indexada(tipo_contrato, idioma=idioma)
        
        if hash_indexado is None:
            return "nao_indexado"
        if hash_atual == hash_indexado:
            return "sincronizado"
        return "desatualizado"
    
    def _preparar_texto_clausula(self, clausula: dict) -> str:
        """
        Texto para embedding da regra.
        """
        buscar_em = clausula.get("buscar_em", "").strip()
        return buscar_em
       
    
    def indexar_clausulas(
        self, 
        tipo_contrato: str, 
        clausulas: List[dict],
        embedding_function,
        idioma: str = "pt"
    ) -> int:
        """Indexa cláusulas de referência no ChromaDB. Apenas regras com ativa=True são indexadas."""
        if not clausulas:
            return 0
        
        # Filtrar apenas cláusulas ativas
        clausulas_ativas = [c for c in clausulas if c.get("ativa", True)]
        if not clausulas_ativas:
            return 0
        
        hash_versao = self.calcular_hash_clausulas(clausulas)
        collection_name = self._obter_nome_collection(tipo_contrato, idioma)
        
        # Recriar collection
        try:
            self.client.delete_collection(name=collection_name)
        except:
            pass
        
        collection = self.client.create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={
                "tipo_contrato": tipo_contrato,
                "idioma": idioma,
                "hash_clausulas": hash_versao,
                "total_clausulas": len(clausulas_ativas)
            }
        )
        
        # Preparar dados (índice refere-se à posição na lista de ativas)
        ids = []
        documents = []
        metadatas = []
        nome_display = lambda c: c.get("titulo") or c.get("nome", "")
        desc_display = lambda c: (c.get("regra_spectra") or c.get("descricao", ""))[:200]

        for i, clausula in enumerate(clausulas_ativas):
            ids.append(f"{tipo_contrato}_{i}")
            documents.append(self._preparar_texto_clausula(clausula))
            metadatas.append({
                "nome": nome_display(clausula),
                "descricao": desc_display(clausula),
                "buscar_em": clausula.get("buscar_em", ""),
                "ativa": clausula.get("ativa", True),
                "tipo_contrato": tipo_contrato,
                "indice": i
            })
        
        # Indexar
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(clausulas_ativas)
    
    def obter_estatisticas(self, tipo_contrato: str, clausulas_json: List[dict], idioma: str = "pt") -> Dict:
        """Obtém estatísticas com status de sincronização."""
        collection_name = self._obter_nome_collection(tipo_contrato, idioma)
        status = self.verificar_sincronizacao(tipo_contrato, clausulas_json, idioma=idioma)
        
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()
            return {
                "tipo_contrato": tipo_contrato,
                "idioma": idioma,
                "total_clausulas_json": len(clausulas_json),
                "total_clausulas_indexadas": count,
                "status": status,
                "indexado": True
            }
        except:
            return {
                "tipo_contrato": tipo_contrato,
                "idioma": idioma,
                "total_clausulas_json": len(clausulas_json),
                "total_clausulas_indexadas": 0,
                "status": status,
                "indexado": False
            }
