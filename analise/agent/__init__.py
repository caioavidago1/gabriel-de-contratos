import functools
from pathlib import Path
from typing import Dict, List, Optional

PROMPTS_DIR = Path(__file__).parent / "prompts"
DEFAULTS_DIR = PROMPTS_DIR / "_defaults"

# Agentes em uso: extrator (docx → cláusulas), agent3 (verificador), agent4 (reescritor)
AGENTES = ["extrator", "agent3", "agent4"]

VARIAVEIS_POR_AGENTE = {
    "extrator": ["{text}"],
    "agent3": ["{nome_regra}", "{descricao_regra}", "{trechos_contrato}"],
    "agent4": ["{titulo}", "{texto_original}", "{regra_violada}", "{motivo}", "{contexto_global}"]
}

DESCRICOES_AGENTES = {
    "extrator": "Extrator de Cláusulas",
    "agent3": "Verificador de Cláusulas",
    "agent4": "Redator"
}

# Recomendações: o que cada prompt deve conter para o fluxo não quebrar (variáveis + formato de saída)
RECOMENDACOES_POR_AGENTE = {
    "agent3": {
        "system": (
            "Obrigatório para o pipeline: o System deve instruir a IA a responder com "
            "eh_violacao (true/false), problema (descrição objetiva; vazio se conformidade) e "
            "chunk_index (1 a 5 = qual trecho viola; 0 = nenhum). "
            "A saída é parseada como JSON estruturado (não remova esses conceitos)."
        ),
        "user": "Variáveis obrigatórias: {nome_regra}, {descricao_regra}, {trechos_contrato}.",
    },
    "agent4": {
        "system": (
            "Recomendado manter no System: instrução para responder com os rótulos exatos "
            "'TEXTO REESCRITO:' e 'EXPLICAÇÃO DAS MUDANÇAS:' (ou em EN: 'REWRITTEN TEXT:', 'EXPLANATION OF CHANGES:'). "
            "O código extrai o texto reescrito e a explicação por esses rótulos."
        ),
        "user": "Variáveis obrigatórias: {titulo}, {texto_original}, {regra_violada}, {motivo}, {contexto_global}.",
    },
}


@functools.lru_cache(maxsize=None)
def carregar_prompt_tipo(tipo_contrato: str, agent: str, parte: str, idioma: str = "pt") -> str:
    """
    Carrega prompt customizado por tipo de contrato e idioma.
    Se não existir customizado, retorna o default.
    
    Args:
        tipo_contrato: "NDA", "TIPO 2", "_defaults", etc
        agent: "extrator", "agent3" ou "agent4"
        parte: "system" ou "user"
        idioma: "pt" ou "en" (padrão: "pt")
    
    Returns:
        Conteúdo do prompt
    """
    tipo_normalizado = tipo_contrato.lower().replace(" ", "_")
    
    # Tentar carregar customizado com idioma específico
    nome_arquivo_idioma = f"{agent}_{parte}_{idioma}.txt"
    custom_path_idioma = PROMPTS_DIR / tipo_normalizado / nome_arquivo_idioma
    if custom_path_idioma.exists():
        return custom_path_idioma.read_text(encoding="utf-8")
    
    # Tentar carregar customizado sem sufixo de idioma (fallback legado)
    nome_arquivo = f"{agent}_{parte}.txt"
    custom_path = PROMPTS_DIR / tipo_normalizado / nome_arquivo
    if custom_path.exists():
        return custom_path.read_text(encoding="utf-8")
    
    # Fallback para default com idioma
    default_path_idioma = DEFAULTS_DIR / nome_arquivo_idioma
    if default_path_idioma.exists():
        return default_path_idioma.read_text(encoding="utf-8")
    
    # Fallback para default sem sufixo de idioma (compatibilidade)
    default_path = DEFAULTS_DIR / nome_arquivo
    if default_path.exists():
        return default_path.read_text(encoding="utf-8")
    
    return ""


def salvar_prompt_tipo(tipo_contrato: str, agent: str, parte: str, conteudo: str, idioma: str = "pt") -> bool:
    """
    Salva prompt customizado para um tipo de contrato e idioma.
    
    Args:
        tipo_contrato: "NDA", "TIPO 2", "_defaults", etc
        agent: "extrator", "agent3" ou "agent4"
        parte: "system" ou "user"
        conteudo: Conteúdo do prompt
        idioma: "pt" ou "en" (padrão: "pt")
    
    Returns:
        True se salvou com sucesso
    """
    nome_arquivo = f"{agent}_{parte}_{idioma}.txt"
    tipo_normalizado = tipo_contrato.lower().replace(" ", "_")
    
    # Criar diretório do tipo se não existir
    tipo_dir = PROMPTS_DIR / tipo_normalizado
    tipo_dir.mkdir(exist_ok=True, parents=True)
    
    # Salvar arquivo
    path = tipo_dir / nome_arquivo
    path.write_text(conteudo, encoding="utf-8")
    return True


def validar_prompt_user(conteudo: str, agent: str = None) -> Dict:
    """
    Valida se o prompt user contém todas as variáveis obrigatórias.
    
    Args:
        conteudo: Conteúdo do prompt a validar
        agent: Nome do agente (extrator, agent3, agent4). Se None, usa variáveis legadas.
    
    Returns:
        {"valido": True/False, "faltando": [...]}
    """
    # Determinar variáveis a validar
    if agent and agent in VARIAVEIS_POR_AGENTE:
        variaveis = VARIAVEIS_POR_AGENTE[agent]
    else:
        variaveis = []
    
    faltando = []
    for var in variaveis:
        if var not in conteudo:
            faltando.append(var)
    
    return {
        "valido": len(faltando) == 0,
        "faltando": faltando
    }


def restaurar_prompt_padrao(tipo_contrato: str, agent: str, parte: str, idioma: str = "pt") -> str:
    """
    Restaura prompt do arquivo _defaults para o tipo de contrato e idioma.
    
    Args:
        tipo_contrato: "NDA", "TIPO 2", "_defaults", etc
        agent: "extrator", "agent3" ou "agent4"
        parte: "system" ou "user"
        idioma: "pt" ou "en" (padrão: "pt")
    
    Returns:
        Conteúdo do prompt padrão restaurado
    """
    nome_arquivo = f"{agent}_{parte}_{idioma}.txt"
    tipo_normalizado = tipo_contrato.lower().replace(" ", "_")
    
    default_path = DEFAULTS_DIR / nome_arquivo
    if not default_path.exists():
        # Fallback para arquivo sem sufixo de idioma (compatibilidade)
        nome_arquivo_legado = f"{agent}_{parte}.txt"
        default_path = DEFAULTS_DIR / nome_arquivo_legado
        if not default_path.exists():
            return ""
    
    conteudo_padrao = default_path.read_text(encoding="utf-8")
    
    # Salvar no diretório do tipo
    tipo_dir = PROMPTS_DIR / tipo_normalizado
    tipo_dir.mkdir(exist_ok=True, parents=True)
    custom_path = tipo_dir / nome_arquivo
    custom_path.write_text(conteudo_padrao, encoding="utf-8")
    
    return conteudo_padrao


def restaurar_todos_prompts_padrao(tipo_contrato: str, idioma: str = "pt") -> bool:
    """
    Restaura todos os prompts padrão para um tipo de contrato e idioma.
    
    Args:
        tipo_contrato: "NDA", "TIPO 2", etc
        idioma: "pt" ou "en" (padrão: "pt")
    
    Returns:
        True se restaurou com sucesso
    """
    for agent in AGENTES:
        for parte in ["system", "user"]:
            restaurar_prompt_padrao(tipo_contrato, agent, parte, idioma)
    return True
