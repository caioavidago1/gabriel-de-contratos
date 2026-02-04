"""
Gerenciadores de modelos LLM e de embeddings da plataforma.
Centraliza configuração, listagem e criação de instâncias (LangChain, ChromaDB).
Provedores: OpenAI, Anthropic (LLM); OpenAI (embeddings).
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from .exceptions import APIKeyError, APIConnectionError, ModelNotFoundError, EmbeddingError


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
        
        # Anthropic - Modelos Claude 4.5 (IDs oficiais: hífen 4-5, não ponto 4.5)
        "claude-opus-4-5": ModeloConfig(
            id="claude-opus-4-5",
            nome="Claude Opus 4.5",
            provedor=TipoModelo.ANTHROPIC,
            descricao="Modelo mais poderoso da Anthropic",
            max_tokens=200000
        ),
        "claude-sonnet-4-5": ModeloConfig(
            id="claude-sonnet-4-5",
            nome="Claude Sonnet 4.5",
            provedor=TipoModelo.ANTHROPIC,
            descricao="Balanceamento ideal entre performance e custo",
            max_tokens=200000
        ),
        "claude-haiku-4-5": ModeloConfig(
            id="claude-haiku-4-5",
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
        
        try:
            if modelo_config.provedor == TipoModelo.OPENAI:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise APIKeyError(
                        "OPENAI_API_KEY não configurada",
                        user_message="Chave de API da OpenAI não configurada."
                    )
                return ChatOpenAI(
                    model=modelo_config.id,
                    temperature=temperature,
                    api_key=api_key
                )
            elif modelo_config.provedor == TipoModelo.ANTHROPIC:
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise APIKeyError(
                        "ANTHROPIC_API_KEY não configurada",
                        user_message="Chave de API da Anthropic não configurada."
                    )
                return ChatAnthropic(
                    model=modelo_config.id,
                    temperature=temperature,
                    api_key=api_key
                )
            
            raise ModelNotFoundError(
                f"Provedor não suportado: {modelo_config.provedor}",
                user_message="Provedor de IA não suportado."
            )
        except (APIKeyError, ModelNotFoundError):
            raise
        except Exception as e:
            raise APIConnectionError(
                f"Erro ao criar LLM: {e}",
                user_message="Erro ao conectar com o serviço de IA."
            )

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
        
        try:
            if embedding_config.provedor == TipoEmbedding.OPENAI:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise APIKeyError(
                        "OPENAI_API_KEY não configurada",
                        user_message="Chave de API da OpenAI não configurada para embeddings."
                    )
                return embedding_functions.OpenAIEmbeddingFunction(
                    api_key=api_key,
                    model_name=embedding_config.id
                )
            
            raise ModelNotFoundError(
                f"Provedor de embedding não suportado: {embedding_config.provedor}",
                user_message="Provedor de embeddings não suportado."
            )
        except (APIKeyError, ModelNotFoundError):
            raise
        except Exception as e:
            raise EmbeddingError(
                f"Erro ao criar função de embedding: {e}",
                user_message="Erro ao inicializar serviço de embeddings."
            )
    
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
            TipoEmbedding.OPENAI: "OPENAI_API_KEY"
        }
        
        var_name = env_vars.get(embedding_config.provedor)
        if not var_name:
            return {"valido": False, "mensagem": "Provedor não suportado"}
        
        if not os.getenv(var_name):
            return {"valido": False, "mensagem": f"{var_name} não configurada"}
        
        return {"valido": True, "mensagem": "API key configurada"}
