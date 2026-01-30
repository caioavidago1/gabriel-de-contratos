"""
Exceções customizadas para o sistema Gabriel.
Cada exceção possui uma mensagem técnica (para logs) e uma mensagem user-friendly (para UI).
"""


class GabrielBaseException(Exception):
    """Exceção base com mensagem user-friendly."""
    user_message: str = "Ocorreu um erro inesperado. Tente novamente."
    
    def __init__(self, message: str = None, user_message: str = None):
        self.message = message or self.__class__.__name__
        if user_message:
            self.user_message = user_message
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


# === Erros de API e Conexão ===

class APIKeyError(GabrielBaseException):
    """Chave de API inválida ou não configurada."""
    user_message = "Chave de API inválida ou não configurada. Verifique suas configurações."


class APIConnectionError(GabrielBaseException):
    """Erro de conexão com serviço externo (OpenAI, etc)."""
    user_message = "Não foi possível conectar ao serviço de IA. Verifique sua conexão."


class APIRateLimitError(GabrielBaseException):
    """Limite de requisições da API atingido."""
    user_message = "Limite de requisições atingido. Aguarde alguns minutos e tente novamente."


class APITimeoutError(GabrielBaseException):
    """Timeout na chamada da API."""
    user_message = "O serviço de IA demorou para responder. Tente novamente."


# === Erros de Documento ===

class DocumentExtractionError(GabrielBaseException):
    """Erro ao extrair cláusulas do documento DOCX."""
    user_message = "Erro ao extrair cláusulas do documento. Verifique se o arquivo está correto."


class DocumentFormatError(GabrielBaseException):
    """Formato de documento inválido ou corrompido."""
    user_message = "O documento está em formato inválido ou corrompido."


class DocumentEmptyError(GabrielBaseException):
    """Documento sem cláusulas extraíveis."""
    user_message = "Não foi possível encontrar cláusulas no documento."


# === Erros de Base de Conhecimento ===

class DatabaseNotIndexedError(GabrielBaseException):
    """Base de conhecimento não indexada."""
    user_message = "A base de regras não está indexada. Clique em 'Atualizar Base de Regras'."


class DatabaseOutdatedError(GabrielBaseException):
    """Base de conhecimento desatualizada."""
    user_message = "A base de regras está desatualizada. Clique em 'Atualizar Base de Regras'."


class DatabaseEmptyError(GabrielBaseException):
    """Nenhuma cláusula/regra encontrada."""
    user_message = "Nenhuma regra de conformidade encontrada para este tipo de contrato."


# === Erros de Verificação ===

class RuleVerificationError(GabrielBaseException):
    """Erro ao verificar uma regra específica."""
    user_message = "Erro ao verificar regra de conformidade."
    
    def __init__(self, message: str = None, rule_name: str = None):
        self.rule_name = rule_name
        if rule_name:
            user_msg = f"Erro ao verificar a regra '{rule_name}'."
        else:
            user_msg = self.user_message
        super().__init__(message, user_msg)


class RewriteError(GabrielBaseException):
    """Erro ao gerar sugestão de reescrita."""
    user_message = "Erro ao gerar sugestão de reescrita para a cláusula."


# === Erros de Modelo ===

class ModelNotFoundError(GabrielBaseException):
    """Modelo LLM ou embedding não encontrado."""
    user_message = "Modelo de IA não encontrado. Selecione outro modelo."


class EmbeddingError(GabrielBaseException):
    """Erro ao gerar embeddings."""
    user_message = "Erro ao processar texto para análise."
