from pathlib import Path
from typing import Dict, List, Optional

PROMPTS_DIR = Path(__file__).parent / "prompts"
DEFAULTS_DIR = PROMPTS_DIR / "_defaults"

# Agentes em uso (Verificador + Reescritor; extrator docx não usa prompts daqui)
AGENTES = ["agent1", "agent4"]

VARIAVEIS_POR_AGENTE = {
    "agent1": ["{titulo}", "{texto}", "{clausulas_referencia}"],
    "agent4": ["{titulo}", "{texto_original}", "{regra_violada}", "{motivo}", "{contexto_global}"]
}

DESCRICOES_AGENTES = {
    "agent1": "Verificador - Analisa possíveis violações (regra + chunks)",
    "agent4": "Reescritor - Sugere reescrita de cláusulas problemáticas"
}


def carregar_prompt_tipo(tipo_contrato: str, agent: str, parte: str) -> str:
    """
    Carrega prompt customizado por tipo de contrato.
    Se não existir customizado, retorna o default.
    
    Args:
        tipo_contrato: "NDA", "TIPO 2", etc
        agent: "agent1" ou "agent4"
        parte: "system" ou "user"
    
    Returns:
        Conteúdo do prompt
    """
    nome_arquivo = f"{agent}_{parte}.txt"
    tipo_normalizado = tipo_contrato.lower().replace(" ", "_")
    
    # Tentar carregar customizado
    custom_path = PROMPTS_DIR / tipo_normalizado / nome_arquivo
    if custom_path.exists():
        return custom_path.read_text(encoding="utf-8")
    
    # Fallback para default
    default_path = DEFAULTS_DIR / nome_arquivo
    if default_path.exists():
        return default_path.read_text(encoding="utf-8")
    
    return ""


def salvar_prompt_tipo(tipo_contrato: str, agent: str, parte: str, conteudo: str) -> bool:
    """
    Salva prompt customizado para um tipo de contrato.
    
    Args:
        tipo_contrato: "NDA", "TIPO 2", etc
        agent: "agent1" ou "agent4"
        parte: "system" ou "user"
        conteudo: Conteúdo do prompt
    
    Returns:
        True se salvou com sucesso
    """
    nome_arquivo = f"{agent}_{parte}.txt"
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
        agent: Nome do agente (agent1, agent4). Se None, usa variáveis legadas.
    
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


def restaurar_prompt_padrao(tipo_contrato: str, agent: str, parte: str) -> str:
    """
    Restaura prompt do arquivo _defaults para o tipo de contrato.
    
    Args:
        tipo_contrato: "NDA", "TIPO 2", etc
        agent: "agent1" ou "agent4"
        parte: "system" ou "user"
    
    Returns:
        Conteúdo do prompt padrão restaurado
    """
    nome_arquivo = f"{agent}_{parte}.txt"
    tipo_normalizado = tipo_contrato.lower().replace(" ", "_")
    
    default_path = DEFAULTS_DIR / nome_arquivo
    if not default_path.exists():
        return ""
    
    conteudo_padrao = default_path.read_text(encoding="utf-8")
    
    # Salvar no diretório do tipo
    tipo_dir = PROMPTS_DIR / tipo_normalizado
    tipo_dir.mkdir(exist_ok=True, parents=True)
    custom_path = tipo_dir / nome_arquivo
    custom_path.write_text(conteudo_padrao, encoding="utf-8")
    
    return conteudo_padrao


def restaurar_todos_prompts_padrao(tipo_contrato: str) -> bool:
    """
    Restaura todos os prompts padrão para um tipo de contrato.
    
    Args:
        tipo_contrato: "NDA", "TIPO 2", etc
    
    Returns:
        True se restaurou com sucesso
    """
    for agent in AGENTES:
        for parte in ["system", "user"]:
            restaurar_prompt_padrao(tipo_contrato, agent, parte)
    return True
