import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def testar_chave_anthropic():
    """Testa se a chave da API da Anthropic está funcionando"""
    
    # Obtém a chave do ambiente
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Verifica se a chave existe
    if not api_key:
        print("❌ ERRO: ANTHROPIC_API_KEY não encontrada no arquivo .env")
        return False
    
    # Verifica o formato básico da chave
    if not api_key.startswith("sk-ant-"):
        print("❌ ERRO: Formato de chave inválido (deve começar com 'sk-ant-')")
        return False
    
    print("✓ Chave encontrada no .env")
    print(f"✓ Formato correto (começa com: {api_key[:10]}...)")
    
    # Testa a chave fazendo uma chamada mínima à API
    try:
        client = Anthropic(api_key=api_key)
        
        # Usa o modelo mais barato para o teste
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Olá"}
            ]
        )
        
        print("✅ SUCESSO: Chave da API está válida e funcionando!")
        print(f"   Resposta: {message.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao testar a chave: {str(e)}")
        return False

if __name__ == "__main__":
    testar_chave_anthropic()
