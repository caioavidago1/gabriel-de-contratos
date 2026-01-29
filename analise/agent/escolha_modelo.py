"""
Gerenciadores de modelos LLM e Embeddings.
Centraliza configuração e criação de instâncias.
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


# ============ MODELOS LLM ============

class TipoModelo(Enum):
    """Tipos de modelos LLM disponíveis."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ModeloConfig:
    """Configuração de um modelo de IA."""
    id: str
    nome: str
    provedor: TipoModelo
    descricao: str
    max_tokens: int


class GerenciadorModelos:
    """Gerencia modelos de IA disponíveis."""
    
    MODELOS_DISPONIVEIS = {
        # OpenAI - Modelos 2026
        "gpt-5.1": ModeloConfig(
            id="gpt-5.1",
            nome="GPT-5.1",
            provedor=TipoModelo.OPENAI,
            descricao="Modelo mais avançado da OpenAI para 2026",
            max_tokens=128000
        ),
        "gpt-5-mini": ModeloConfig(
            id="gpt-5-mini",
            nome="GPT-5 Mini",
            provedor=TipoModelo.OPENAI,
            descricao="Versão compacta e econômica do GPT-5",
            max_tokens=128000
        ),
        
        # Anthropic - Modelos Claude 4.5 (2026)
        "claude-opus-4.5": ModeloConfig(
            id="claude-opus-4.5",
            nome="Claude Opus 4.5",
            provedor=TipoModelo.ANTHROPIC,
            descricao="Modelo mais poderoso da Anthropic",
            max_tokens=200000
        ),
        "claude-sonnet-4.5": ModeloConfig(
            id="claude-sonnet-4.5",
            nome="Claude Sonnet 4.5",
            provedor=TipoModelo.ANTHROPIC,
            descricao="Balanceamento ideal entre performance e custo",
            max_tokens=200000
        ),
        "claude-haiku-4.5": ModeloConfig(
            id="claude-haiku-4.5",
            nome="Claude Haiku 4.5",
            provedor=TipoModelo.ANTHROPIC,
            descricao="Mais rápido e econômico da família Claude",
            max_tokens=200000
        ),
    }
    
    @classmethod
    def obter_modelo(cls, id_modelo: str) -> Optional[ModeloConfig]:
        """Obtém configuração de um modelo específico."""
        return cls.MODELOS_DISPONIVEIS.get(id_modelo)
    
    @classmethod
    def criar_llm(cls, modelo_config: ModeloConfig, temperature: float = 0.2):
        """Cria instância do LLM configurado."""
        import os
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic
        
        if modelo_config.provedor == TipoModelo.OPENAI:
            return ChatOpenAI(
                model=modelo_config.id,
                temperature=temperature,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif modelo_config.provedor == TipoModelo.ANTHROPIC:
            return ChatAnthropic(
                model=modelo_config.id,
                temperature=temperature,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        
        raise ValueError(f"Provedor não suportado: {modelo_config.provedor}")

    @classmethod
    def listar_por_provedor(cls, provedor: TipoModelo) -> list[ModeloConfig]:
        """Lista todos os modelos de um provedor específico."""
        return [
            modelo for modelo in cls.MODELOS_DISPONIVEIS.values()
            if modelo.provedor == provedor
        ]
    
    @classmethod
    def validar_api_keys(cls, modelo_config: ModeloConfig) -> dict:
        """Valida se as API keys necessárias estão configuradas."""
        import os
        
        env_vars = {
            TipoModelo.OPENAI: "OPENAI_API_KEY",
            TipoModelo.ANTHROPIC: "ANTHROPIC_API_KEY"
        }
        
        var_name = env_vars.get(modelo_config.provedor)
        if not var_name:
            return {"valido": False, "mensagem": "Provedor não suportado"}
        
        if not os.getenv(var_name):
            return {"valido": False, "mensagem": f"{var_name} não configurada"}
        
        return {"valido": True, "mensagem": "API key configurada"}


# ============ MODELOS DE EMBEDDING ============

class TipoEmbedding(Enum):
    """Tipos de modelos de embedding disponíveis."""
    OPENAI = "openai"
    VOYAGE = "voyage"


@dataclass
class EmbeddingConfig:
    """Configuração de um modelo de embedding."""
    id: str
    nome: str
    provedor: TipoEmbedding
    descricao: str
    dimensoes: int
    max_tokens: int
    qualidade: str
    especializado_legal: bool = False
    suporta_portugues: bool = True


class GerenciadorEmbeddings:
    """Gerencia modelos de embedding disponíveis."""
    
    MODELOS_DISPONIVEIS = {
        # OpenAI
        "openai-small": EmbeddingConfig(
            id="text-embedding-3-small",
            nome="OpenAI Small",
            provedor=TipoEmbedding.OPENAI,
            descricao="Modelo econômico da OpenAI, ótimo custo-benefício",
            dimensoes=1536,
            max_tokens=8191,
            qualidade="alta",
            especializado_legal=False,
            suporta_portugues=True
        ),
        "openai-large": EmbeddingConfig(
            id="text-embedding-3-large",
            nome="OpenAI Large",
            provedor=TipoEmbedding.OPENAI,
            descricao="Melhor modelo generalista da OpenAI",
            dimensoes=3072,
            max_tokens=8191,
            qualidade="excelente",
            especializado_legal=False,
            suporta_portugues=True
        ),
        
        # Voyage AI - Série 4 (Janeiro 2026)
        "voyage-4": EmbeddingConfig(
            id="voyage-4",
            nome="Voyage 4",
            provedor=TipoEmbedding.VOYAGE,
            descricao="Generalista de última geração (Jan 2026)",
            dimensoes=1024,
            max_tokens=32000,
            qualidade="excelente",
            especializado_legal=False,
            suporta_portugues=True
        ),
        "voyage-4-large": EmbeddingConfig(
            id="voyage-4-large",
            nome="Voyage 4 Large",
            provedor=TipoEmbedding.VOYAGE,
            descricao="Máxima precisão de recuperação",
            dimensoes=1536,
            max_tokens=32000,
            qualidade="excelente",
            especializado_legal=False,
            suporta_portugues=True
        ),
        "voyage-4-lite": EmbeddingConfig(
            id="voyage-4-lite",
            nome="Voyage 4 Lite",
            provedor=TipoEmbedding.VOYAGE,
            descricao="Otimizado para latência e custo",
            dimensoes=512,
            max_tokens=32000,
            qualidade="alta",
            especializado_legal=False,
            suporta_portugues=True
        ),
        
        # Legado - ainda disponível
        "voyage-law-2": EmbeddingConfig(
            id="voyage-law-2",
            nome="Voyage Law 2",
            provedor=TipoEmbedding.VOYAGE,
            descricao="Especializado em textos jurídicos",
            dimensoes=1024,
            max_tokens=16000,
            qualidade="excelente",
            especializado_legal=True,
            suporta_portugues=True
        ),
    }
    
    @classmethod
    def obter_embedding(cls, id_embedding: str) -> Optional[EmbeddingConfig]:
        """Obtém configuração de um modelo de embedding específico."""
        return cls.MODELOS_DISPONIVEIS.get(id_embedding)
    
    @classmethod
    def criar_embedding_function(cls, embedding_config: EmbeddingConfig):
        """Cria função de embedding configurada para ChromaDB."""
        import os
        from chromadb.utils import embedding_functions
        
        if embedding_config.provedor == TipoEmbedding.OPENAI:
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name=embedding_config.id
            )
        
        elif embedding_config.provedor == TipoEmbedding.VOYAGE:
            from voyageai import Client as VoyageClient
            
            class VoyageEmbeddingFunction:
                def __init__(self, api_key: str, model_name: str):
                    self.client = VoyageClient(api_key=api_key)
                    self.model_name = model_name
                
                def __call__(self, input: list[str]) -> list[list[float]]:
                    result = self.client.embed(
                        texts=input,
                        model=self.model_name,
                        input_type="document"
                    )
                    return result.embeddings
            
            return VoyageEmbeddingFunction(
                api_key=os.getenv("VOYAGE_API_KEY"),
                model_name=embedding_config.id
            )
        
        raise ValueError(f"Provedor não suportado: {embedding_config.provedor}")
    
    @classmethod
    def listar_por_provedor(cls, provedor: TipoEmbedding) -> list[EmbeddingConfig]:
        """Lista todos os embeddings de um provedor específico."""
        return [
            modelo for modelo in cls.MODELOS_DISPONIVEIS.values()
            if modelo.provedor == provedor
        ]
    
    @classmethod
    def validar_api_keys(cls, embedding_config: EmbeddingConfig) -> dict:
        """Valida se as API keys necessárias estão configuradas."""
        import os
        
        env_vars = {
            TipoEmbedding.OPENAI: "OPENAI_API_KEY",
            TipoEmbedding.VOYAGE: "VOYAGE_API_KEY"
        }
        
        var_name = env_vars.get(embedding_config.provedor)
        if not var_name:
            return {"valido": False, "mensagem": "Provedor não suportado"}
        
        if not os.getenv(var_name):
            return {"valido": False, "mensagem": f"{var_name} não configurada"}
        
        return {"valido": True, "mensagem": "API key configurada"}
