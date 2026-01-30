# 📄 Gabriel - Análise de Contratos

## Guia Completo de Instalação e Manutenção

---

## 📋 Índice

1. [O que é esta plataforma?](#o-que-é-esta-plataforma)
2. [Repositório e Servidor](#repositório-e-servidor)
3. [Pré-requisitos](#pré-requisitos)
4. [Instalação Passo a Passo](#instalação-passo-a-passo)
5. [Como Obter as Chaves de API](#como-obter-as-chaves-de-api)
6. [Configuração do Arquivo .env](#configuração-do-arquivo-env)
7. [Como Executar a Plataforma](#como-executar-a-plataforma)
8. [Como Usar a Plataforma](#como-usar-a-plataforma)
9. [Manutenção Básica](#manutenção-básica)
10. [Problemas Comuns e Soluções](#problemas-comuns-e-soluções)
11. [Estrutura Técnica (Para Referência)](#estrutura-técnica-para-referência)

---

## 🎯 O que é esta plataforma?

A plataforma **Gabriel** é um sistema automatizado que analisa contratos jurídicos (NDA, SPA, Regulamentos de Fundos, etc.) e identifica automaticamente se há violações em relação a cláusulas de referência pré-definidas.

### O que ela faz:

1. **Recebe** um arquivo Word (.docx) com um contrato
2. **Extrai** o texto do documento automaticamente
3. **Analisa** o contrato usando inteligência artificial
4. **Identifica** possíveis violações ou problemas
5. **Gera** um novo documento Word com anotações destacando os problemas encontrados

### Tipos de contratos suportados:

- **NDA** (Acordo de Confidencialidade)
- **SPAs** (Share Purchase Agreements) - vários tipos
- **Regulamentos de Fundos** (FIP, FIDC)
- **Contratos de Consultoria**
- **Contratos Sociais**
- **Acordos de Sócios**
- E outros...

---

## 🔗 Repositório e Servidor

### Repositório GitHub

O código-fonte desta plataforma está disponível no repositório:

**🔗 [https://github.com/caioavidago1/contratos](https://github.com/caioavidago1/contratos)**

Para clonar o repositório:

```bash
git clone https://github.com/caioavidago1/contratos.git
cd contratos
```

### Servidor de Produção

A aplicação está hospedada em um servidor Azure com as seguintes especificações:

#### Especificações do Servidor

- **Modelo**: B4ls V2
- **Processamento**: 4 vCPUs
- **Memória RAM**: 8 GB
- **Armazenamento**: SSD 128 GB
- **Região**: Sul do Brasil
- **Backup**: Política Standard, 1 instância, 128 GB, redundância LRS

#### Informações de Acesso

- **Hostname**: SPECTRA-APP
- **IP Público**: 4.203.89.177
- **Usuário**: spectrapp

#### Conectar ao Servidor

Para conectar ao servidor via SSH, você precisa do arquivo de chave privada:

**⚠️ IMPORTANTE**: Você precisa ter o arquivo `SPECTRA-APP_key.pem` no seu computador.

O arquivo deve estar localizado em:
```
C:\Users\SeuUsuario\OneDrive - Spectra\Documentos\Vm Linux SPECTRA-APP\SPECTRA-APP_key.pem
```

**Comando para conectar (Windows PowerShell ou Git Bash):**

```bash
ssh -i "C:\Users\SeuUsuario\OneDrive - Spectra\Documentos\Vm Linux SPECTRA-APP\SPECTRA-APP_key.pem" spectrapp@4.203.89.177
```

**Nota**: Ajuste o caminho do arquivo `.pem` conforme a localização no seu computador.

#### Executar a Aplicação no Servidor

Após conectar ao servidor via SSH, siga estes passos para iniciar a aplicação:

```bash
# 1. Navegue até o diretório da aplicação
cd ~/contratos  # ou o caminho onde o código está

# 2. Ative o ambiente virtual (se necessário)
source venv/bin/activate

# 3. Mate todos os processos Streamlit (incluindo órfãos)
pkill -f streamlit
pkill -f "python -m streamlit"  # Backup para processos antigos

# 4. Confirme que não há processos rodando (deve retornar vazio)
ps aux | grep streamlit

# 5. Limpe logs antigos (opcional, mas recomendado)
rm -f output.log nohup.out ~/.streamlit/logs/streamlit-server-*.log

# 6. Certifique-se que .streamlit/config.toml está atualizado
# (com as configurações necessárias)

# 7. Suba a aplicação em background
nohup streamlit run app.py > output.log 2>&1 &
disown

# 8. Verifique o status
ps aux | grep streamlit
tail -f output.log  # Ctrl+C para sair; acesse http://4.203.89.177:8501
```

#### Acessar a Aplicação

Após iniciar a aplicação, você pode acessá-la através do navegador:

**🌐 URL**: `http://4.203.89.177:8501`

#### Verificar Logs

Para verificar os logs da aplicação em tempo real:

```bash
tail -f output.log
```

Para ver as últimas 100 linhas:

```bash
tail -n 100 output.log
```

#### Parar a Aplicação

Para parar a aplicação:

```bash
pkill -f streamlit
```

Ou encontre o PID e mate o processo:

```bash
ps aux | grep streamlit
kill <PID>
```

---

## 📦 Pré-requisitos

Antes de começar, você precisa ter instalado:

### 1. Python 3.8 ou superior

**Como verificar se você tem Python instalado:**

1. Abra o **Prompt de Comando** (Windows)
2. Digite: `python --version` ou `python3 --version`
3. Pressione Enter

**Se aparecer um erro**, você precisa instalar Python:

- **Windows/Mac**: Baixe em [python.org](https://www.python.org/downloads/)
- Durante a instalação, **marque a opção "Add Python to PATH"**

**Como instalar Python no Windows:**

1. Acesse https://www.python.org/downloads/
2. Clique em "Download Python" (versão mais recente)
3. Execute o instalador baixado
4. **IMPORTANTE**: Na primeira tela, marque a opção **"Add Python to PATH"**
5. Clique em "Install Now"
6. Aguarde a instalação terminar
7. Feche e abra novamente o Prompt de Comando

### 2. Git (opcional, mas recomendado)

Se o código estiver em um repositório Git, você precisará do Git instalado:

- **Windows/Mac**: Baixe em [git-scm.com](https://git-scm.com/downloads)
- Instale com as opções padrão

### 3. Conta de e-mail para criar contas nos serviços de API

Você precisará criar contas em 3 serviços diferentes para obter as chaves de API (veja seção [Como Obter as Chaves de API](#como-obter-as-chaves-de-api)).

---

## 🚀 Instalação Passo a Passo

### Passo 1: Abrir o Prompt de Comando / Terminal

- **Windows**: Pressione `Windows + R`, digite `cmd` e pressione Enter
- **Mac**: Abra o aplicativo "Terminal" (procure por "Terminal" no Spotlight)
- **Linux**: Abra o Terminal

### Passo 2: Clonar ou Navegar até a pasta do projeto

**Opção A: Clonar do GitHub (recomendado para primeira instalação)**

```bash
git clone https://github.com/caioavidago1/contratos.git
cd contratos
```

**Opção B: Navegar até pasta local existente**

Digite o comando abaixo (ajuste o caminho conforme necessário):

```bash
cd "C:\Users\SeuUsuario\OneDrive - Spectra\Documentos\contratos"
```

**Dica**: Você pode copiar o caminho da pasta no Windows Explorer, clicar com botão direito na barra de endereço e selecionar "Copiar endereço como texto".

### Passo 3: Criar ambiente virtual Python

Um ambiente virtual é como uma "caixa isolada" onde as dependências do projeto ficam separadas de outros projetos Python.

**Windows:**
```bash
python -m venv venv
```

**Mac/Linux:**
```bash
python3 -m venv venv
```

Aguarde alguns segundos enquanto o ambiente é criado.

### Passo 4: Ativar o ambiente virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Como saber se funcionou?** Você verá `(venv)` no início da linha do prompt, assim:

```
(venv) C:\Users\...\contratos>
```

### Passo 5: Instalar as dependências

Com o ambiente virtual ativado, digite:

```bash
pip install -r requirements.txt
```

**Isso pode levar vários minutos** (5-15 minutos dependendo da sua internet). O sistema está baixando e instalando todas as bibliotecas necessárias.

**Se aparecer algum erro**, veja a seção [Problemas Comuns e Soluções](#problemas-comuns-e-soluções).

### Passo 6: Verificar se tudo foi instalado corretamente

Digite:

```bash
pip list
```

Você deve ver uma lista com muitas bibliotecas instaladas (streamlit, openai, chromadb, etc.).

---

## 🔑 Como Obter as Chaves de API

A plataforma precisa de **chaves de API** para funcionar. Essas chaves são como "senhas" que permitem o sistema acessar serviços de inteligência artificial.

Você precisa de **3 chaves obrigatórias** e **1 opcional**:

### ✅ Chaves Obrigatórias:

1. **OPENAI_API_KEY** - Para análise de texto e alguns embeddings
2. **ANTHROPIC_API_KEY** - Para análise de texto (Claude)
3. **LLAMA_CLOUD_API_KEY** - Para extrair texto de documentos Word

### ⚙️ Chave Opcional:

4. **VOYAGE_API_KEY** - Para embeddings avançados (pode usar OpenAI como alternativa)

---

### 🔵 Como Obter a OPENAI_API_KEY

**O que é:** Chave da OpenAI (criadora do ChatGPT) para usar modelos GPT e embeddings.

**Passo a passo:**

1. **Acesse**: https://platform.openai.com/
2. **Faça login** ou **crie uma conta**:
   - Clique em "Sign up" se não tiver conta
   - Use seu e-mail para criar a conta
   - Confirme o e-mail
3. **Adicione método de pagamento**:
   - Clique no seu perfil (canto superior direito)
   - Vá em "Billing" → "Payment methods"
   - Adicione um cartão de crédito
   - **Nota**: A OpenAI cobra por uso (pay-as-you-go). O uso desta plataforma pode gerar custos.
4. **Criar a chave de API**:
   - Clique no seu perfil → "API keys"
   - Clique em "Create new secret key"
   - Dê um nome (ex: "Gabriel Contratos")
   - **IMPORTANTE**: Copie a chave imediatamente! Ela começa com `sk-` e você não poderá vê-la novamente.
   - Cole em um arquivo de texto temporário para não perder
5. **Formato da chave**: `sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 🟣 Como Obter a ANTHROPIC_API_KEY

**O que é:** Chave da Anthropic (criadora do Claude) para usar modelos Claude.

**Passo a passo:**

1. **Acesse**: https://console.anthropic.com/
2. **Faça login** ou **crie uma conta**:
   - Clique em "Sign up" se não tiver conta
   - Use seu e-mail
   - Confirme o e-mail
3. **Adicione método de pagamento**:
   - Vá em "Billing" → "Payment methods"
   - Adicione um cartão de crédito
   - **Nota**: A Anthropic também cobra por uso.
4. **Criar a chave de API**:
   - Vá em "API Keys" no menu lateral
   - Clique em "Create Key"
   - Dê um nome (ex: "Gabriel Contratos")
   - **IMPORTANTE**: Copie a chave imediatamente! Ela começa com `sk-ant-` e você não poderá vê-la novamente.
   - Cole em um arquivo de texto temporário
5. **Formato da chave**: `sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 🟢 Como Obter a LLAMA_CLOUD_API_KEY

**O que é:** Chave do LlamaIndex para extrair texto de documentos Word (.docx).

**Passo a passo:**

1. **Acesse**: https://cloud.llamaindex.ai/
2. **Faça login** ou **crie uma conta**:
   - Clique em "Sign up" se não tiver conta
   - Use seu e-mail ou faça login com Google/GitHub
   - Confirme o e-mail se necessário
3. **Acessar API Keys**:
   - Após fazer login, você será redirecionado para o dashboard
   - No menu lateral, clique em "API Keys" ou procure por "Settings" → "API Keys"
4. **Criar a chave**:
   - Clique em "Create API Key" ou botão similar
   - Dê um nome (ex: "Gabriel Contratos")
   - **IMPORTANTE**: Copie a chave imediatamente! Ela começa com `llx-` e você não poderá vê-la novamente.
   - Cole em um arquivo de texto temporário
5. **Formato da chave**: `llx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 🟡 Como Obter a VOYAGE_API_KEY (Opcional)

**O que é:** Chave da Voyage AI para embeddings especializados. Se você não tiver esta chave, o sistema usará embeddings da OpenAI como alternativa.

**Passo a passo:**

1. **Acesse**: https://www.voyageai.com/
2. **Faça login** ou **crie uma conta**:
   - Clique em "Sign up" ou "Get Started"
   - Use seu e-mail
   - Confirme o e-mail
3. **Acessar API Keys**:
   - Após fazer login, vá em "Dashboard" ou "API Keys"
4. **Criar a chave**:
   - Clique em "Create API Key" ou botão similar
   - Dê um nome (ex: "Gabriel Contratos")
   - **IMPORTANTE**: Copie a chave imediatamente! Ela começa com `pa-` e você não poderá vê-la novamente.
   - Cole em um arquivo de texto temporário
5. **Formato da chave**: `pa-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Custos:**
- Voyage AI geralmente oferece créditos gratuitos para começar
- Verifique os preços no site

---

## ⚙️ Configuração do Arquivo .env

O arquivo `.env` é onde você coloca todas as chaves de API. Este arquivo **não deve ser compartilhado** ou enviado por e-mail, pois contém informações sensíveis.

### Passo 1: Criar o arquivo .env

Na pasta do projeto (`contratos`), crie um arquivo chamado exatamente `.env` (com o ponto no início).

**Como criar no Windows:**

1. Abra o Bloco de Notas
2. Vá em "Arquivo" → "Salvar como"
3. Na parte inferior, mude "Tipo" para "Todos os arquivos (*.*)"
4. Digite o nome: `.env` (com o ponto no início)
5. Salve na pasta do projeto


### Passo 2: Adicionar as chaves no arquivo .env

Abra o arquivo `.env` no Bloco de Notas (ou editor de texto) e adicione as seguintes linhas:

```env
# Chaves de API obrigatórias
OPENAI_API_KEY=sk-proj-sua-chave-aqui
ANTHROPIC_API_KEY=sk-ant-api03-sua-chave-aqui
LLAMA_CLOUD_API_KEY=llx-sua-chave-aqui

# Chave opcional (pode deixar vazio se não tiver)
VOYAGE_API_KEY=pa-sua-chave-aqui

# Autenticação (opcional): se definidas, exige login para acessar a app e/ou editar cláusulas
# APP_PASSWORD=senha_para_acessar_a_plataforma
# ADMIN_PASSWORD=senha_para_editar_clausulas_e_prompts
```

**IMPORTANTE:**

- Substitua `sua-chave-aqui` pelas chaves reais que você copiou
- **NÃO** adicione espaços antes ou depois do sinal de `=`
- **NÃO** adicione aspas (`"` ou `'`) ao redor das chaves
- Cada chave deve estar em uma linha separada
- As linhas que começam com `#` são comentários (ignorados)

**Exemplo de como deve ficar:**

```env
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
ANTHROPIC_API_KEY=sk-ant-api03-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
LLAMA_CLOUD_API_KEY=llx-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
VOYAGE_API_KEY=pa-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
```

### Passo 3: Salvar o arquivo

Salve o arquivo `.env` na pasta raiz do projeto (mesma pasta onde está o `app.py`).

### Passo 4: Verificar se o arquivo está correto

O arquivo `.env` deve estar na mesma pasta que:
- `app.py`
- `requirements.txt`
- `README.md`

**⚠️ SEGURANÇA:** O arquivo `.env` está no `.gitignore`, então ele não será enviado para o repositório Git. Isso é correto e seguro!

---

## ▶️ Como Executar a Plataforma

### Passo 1: Abrir o Prompt de Comando / Terminal

- **Windows**: `Windows + R`, digite `cmd`, Enter
- **Mac/Linux**: Abra o Terminal

### Passo 2: Navegar até a pasta do projeto

**Desenvolvimento Local:**
```bash
cd "C:\Users\SeuUsuario\OneDrive - Spectra\Documentos\contratos"
```

**Servidor de Produção:**
```bash
cd ~/contratos  # ou o caminho onde o código está no servidor
```

(Ajuste o caminho conforme necessário)

### Passo 3: Ativar o ambiente virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

Você deve ver `(venv)` no início da linha.

### Passo 4: Executar a plataforma

**Desenvolvimento Local (Windows/Mac/Linux):**

```bash
streamlit run app.py
```

**Servidor de Produção (Linux):**

Veja a seção [Executar a Aplicação no Servidor](#executar-a-aplicação-no-servidor) acima para instruções detalhadas de como rodar em background no servidor.

### Passo 5: Acessar no navegador

**Desenvolvimento Local:**

Após alguns segundos, você verá uma mensagem como:

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.1.100:8501
```

1. O navegador deve abrir automaticamente
2. Se não abrir, copie o endereço `http://localhost:8501` e cole no navegador
3. Você verá a tela inicial da plataforma

**Servidor de Produção:**

Acesse através do navegador:

```
http://4.203.89.177:8501
```

### Passo 6: Parar a plataforma

**Desenvolvimento Local:**

Para parar a plataforma, volte ao Prompt de Comando e pressione `Ctrl + C`.

**Servidor de Produção:**

```bash
pkill -f streamlit
```

---

## 💻 Como Usar a Plataforma

### Tela Inicial

Ao abrir a plataforma (após login, se `APP_PASSWORD` estiver configurado), você verá:

1. **Idioma do documento**: Português ou English (pt/en)
2. **Botões por tipo de contrato**, agrupados em:
   - Contratos Gerais (NDA, Consultoria/Side Letter)
   - SPAs (cotas, aquisição, desinvestimento)
   - Regulamentos de Fundos (FIP, FIDC)
   - Search Funds – Search Phase (Contrato social, Acordo de Sócios)
   - Search Funds – Acquisition Phase (Reg. FIP acquisition, Acordo de Cotistas)

### Processo de Análise

1. **Escolha o idioma** do documento (pt/en) na home
2. **Selecione o tipo de contrato** clicando no botão correspondente
3. **Faça upload do arquivo Word** (.docx) na página de análise
4. **Aguarde o processamento** (extração, busca, verificação e sugestões de reescrita)
5. **Visualize os resultados**: violações, conformidades, tempo e modelo usado
6. **Baixe os 3 documentos**:
   - **DOCX Problemas**: relatório com problemas identificados
   - **DOCX Solução**: parágrafos corrigidos/sugeridos
   - **DOCX Explicação**: comparação problemas x solução

### Sidebar (Barra Lateral)

Na barra lateral esquerda (em cada página de análise), você pode:

- **Gerenciar cláusulas de referência**: Adicionar, editar ou remover regras (requer `ADMIN_PASSWORD` se configurado)
- **Editar prompts**: Modificar prompts por tipo e idioma (extrator, agent3, agent4)
- **Selecionar modelo de IA**: Escolher modelo LLM e modelo de embedding
- **Atualizar Base de Regras**: Reindexar o ChromaDB quando alterar cláusulas de referência

---

## 🔧 Manutenção Básica

### Atualizar Dependências

Periodicamente, você pode precisar atualizar as bibliotecas do projeto:

1. Ative o ambiente virtual (veja [Como Executar](#como-executar-a-plataforma))
2. Execute:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

### Adicionar Novo Tipo de Contrato

Se precisar adicionar um novo tipo de contrato, consulte a seção técnica [Como Adicionar Novo Tipo de Contrato](#como-adicionar-novo-tipo-de-contrato) mais abaixo.

### Limpar Cache de Documentos Parseados

O cache de análise fica no session_state (Streamlit). Use o botão "Nova Análise" na página de análise para reprocessar.

### Backup do Banco de Dados

O banco de dados ChromaDB fica em `chroma_db/chroma.sqlite3`. Faça backup deste arquivo periodicamente se você tiver muitas cláusulas indexadas.

### Verificar Uso de API Keys

Monitore o uso das APIs nos dashboards:

- **OpenAI**: https://platform.openai.com/usage
- **Anthropic**: https://console.anthropic.com/settings/usage
- **LlamaIndex**: https://cloud.llamaindex.ai/ (verifique no dashboard)

---

## ❗ Problemas Comuns e Soluções

### Erro: "python não é reconhecido como comando"

**Causa**: Python não está instalado ou não está no PATH.

**Solução**:
1. Instale Python de [python.org](https://www.python.org/downloads/)
2. Durante a instalação, **marque "Add Python to PATH"**
3. Reinicie o Prompt de Comando

### Erro: "pip não é reconhecido como comando"

**Causa**: Python não está instalado corretamente.

**Solução**: Use `python -m pip` em vez de apenas `pip`:
```bash
python -m pip install -r requirements.txt
```

### Erro ao instalar dependências: "Failed to build"

**Causa**: Falta de ferramentas de compilação (comum no Windows).

**Solução**:
1. Instale o "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Ou use versões pré-compiladas:
   ```bash
   pip install --only-binary :all: -r requirements.txt
   ```

### Erro: "ModuleNotFoundError: No module named 'X'"

**Causa**: Dependência não instalada ou ambiente virtual não ativado.

**Solução**:
1. Certifique-se de que o ambiente virtual está ativado (veja `(venv)` no prompt)
2. Reinstale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Erro: "API key not found" ou "Invalid API key"

**Causa**: Chave de API não configurada ou incorreta no arquivo `.env`.

**Solução**:
1. Verifique se o arquivo `.env` existe na pasta raiz do projeto
2. Verifique se as chaves estão corretas (sem espaços, sem aspas)
3. Certifique-se de que copiou a chave completa
4. Reinicie a plataforma após alterar o `.env`

### Erro: "Can't patch loop of type uvloop"

**Causa**: Conflito técnico com o event loop (já tratado automaticamente).

**Solução**: Este erro geralmente é ignorado automaticamente. Se persistir, o sistema ainda deve funcionar.

### A plataforma não abre no navegador

**Causa**: Firewall ou porta já em uso.

**Solução**:
1. Verifique se a mensagem no terminal mostra uma URL
2. Copie a URL (ex: `http://localhost:8501`) e cole manualmente no navegador
3. Se não funcionar, tente fechar outros programas que possam estar usando a porta 8501

### Erro ao fazer upload: "File is not a valid .docx"

**Causa**: Arquivo corrompido ou formato incorreto.

**Solução**:
1. Certifique-se de que o arquivo é realmente um `.docx` (não `.doc` antigo)
2. Tente abrir o arquivo no Word e salvar novamente como `.docx`
3. Verifique se o arquivo não está corrompido

### Análise muito lenta

**Causa**: Documento muito grande ou modelo de IA lento.

**Solução**:
1. Documentos muito grandes (>100 páginas) podem demorar vários minutos
2. Tente usar um modelo mais rápido (ex: Claude Haiku em vez de Claude Opus)
3. Verifique sua conexão com a internet

### Erro: "Insufficient quota" ou "Rate limit exceeded"

**Causa**: Limite de uso da API atingido ou sem créditos.

**Solução**:
1. Verifique o saldo/créditos no dashboard da API correspondente
2. Adicione créditos ou aguarde o reset do limite (geralmente mensal)
3. Para OpenAI/Anthropic, verifique os limites no dashboard de billing

### ChromaDB desatualizado

**Causa**: Cláusulas de referência foram alteradas mas não reindexadas.

**Solução**:
1. Na sidebar da plataforma, clique em "Reindexar Vector Store"
2. Aguarde a reindexação terminar
3. Tente a análise novamente

---

## 🏗️ Estrutura Técnica (Para Referência)

Esta seção é para referência técnica. Você não precisa entender isso para usar a plataforma.

### Visão geral do código atual

- **Entrada**: Autenticação opcional (`APP_PASSWORD` no `.env`), seleção de **idioma** (pt/en) na home e **tipo de contrato**, upload de `.docx`.
- **Pipeline**: Orquestrador (`analise/agent/orquestrador.py`) coordena: **Agent 1** (extrator DOCX) → **Agent 2** (matcher ChromaDB) → **Agent 3** (verificador, em paralelo) → **Agent 4** (reescritor, em paralelo) → geração de **3 DOCX** (problemas, solução, explicação) em `output/docs/`.
- **Prompts**: Por tipo de contrato e idioma em `analise/agent/prompts/{tipo}/` (extrator, agent3, agent4; fallback em `_defaults/`).
- **Exceções**: `analise/agent/exceptions.py` (APIKeyError, DocumentEmptyError, DatabaseNotIndexedError, etc.) com mensagens amigáveis.
- **Config**: `config.toml` (Streamlit: tema, porta, upload size). Variáveis sensíveis no `.env` (API keys, `APP_PASSWORD`, `ADMIN_PASSWORD`).

### Diagrama: Fluxo do usuário

```mermaid
flowchart LR
    subgraph Entrada
        A[Login opcional] --> B[Home]
        B --> C[Idioma pt/en]
        C --> D[Tipo de contrato]
        D --> E[Upload .docx]
    end
    E --> F[Análise]
    F --> G[Resultado]
    G --> H[Download 3 DOCX]
```

### Diagrama: Arquitetura em camadas

```mermaid
flowchart TB
    subgraph UI["Interface (Streamlit)"]
        APP[app.py - Router]
        T1[t1_nda / t2_spa_cotas / ...]
        COMUM[comum.py - upload, sidebar, render_pagina_analise]
        AUTH[auth.py - APP_PASSWORD, ADMIN_PASSWORD]
        APP --> T1
        APP --> AUTH
        T1 --> COMUM
    end

    subgraph Analise["Análise (Multi-Agentes)"]
        ORQ[orquestrador.py]
        AG1[Agent 1 - Extrator DOCX]
        AG2[Agent 2 - Matcher]
        AG3[Agent 3 - Verificador]
        AG4[Agent 4 - Reescritor]
        ORQ --> AG1 --> AG2 --> AG3 --> AG4
    end

    subgraph Dados["Dados"]
        DB[(db/ - JSON cláusulas)]
        CHROMA[(ChromaDB)]
        EMB[embeddings/clausulas.py]
        DB --> EMB --> CHROMA
    end

    subgraph Saida["Saída"]
        DOCX[output/docx.py - problemas, solução]
        COMP[output/comparar_docx.py - explicacao]
        DOCX --> COMP
    end

    COMUM --> ORQ
    ORQ --> DB
    AG2 --> CHROMA
    AG4 --> DOCX
```

### Diagrama: Pipeline de agentes (sequência)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant O as Orquestrador
    participant A1 as Agent 1 Extrator
    participant A2 as Agent 2 Matcher
    participant A3 as Agent 3 Verificador
    participant A4 as Agent 4 Reescritor
    participant Out as output (3 DOCX)

    U->>O: .docx + tipo + idioma
    O->>A1: extrair_clausulas_docx()
    A1-->>O: cláusulas []
    O->>A2: match_regras_chunks(regras, chunks)
    A2-->>O: regra + top 5 chunks por regra
    par Verificação em paralelo
        O->>A3: analisar_regra_chunks(regra, top5)
        A3-->>O: eh_violacao, problema, chunk
    end
    O->>O: violacoes_validadas
    par Reescrita em paralelo
        O->>A4: reescrever_clausula(violacao)
        A4-->>O: sugestao_reescrita
    end
    O->>Out: gerar_problemas_docx, gerar_solucao_docx, gerar_doc_comparado
    Out-->>O: doc_problemas_bytes, doc_solucao_bytes, doc_explicacao_bytes
    O-->>U: ResultadoAnalise + downloads
```

### Estrutura de Diretórios

```
gabriel-de-contratos/
├── app.py                      # Entry point: auth, idioma, router de páginas
├── config.toml                 # Streamlit: tema, porta, maxUploadSize, etc.
├── requirements.txt            # Dependências Python
├── README.md                   # Esta documentação
├── .env                        # Chaves API, APP_PASSWORD, ADMIN_PASSWORD (NÃO compartilhar!)
│
├── modulos/                    # Interface por tipo de contrato
│   ├── auth.py                 # Autenticação app e admin (APP_PASSWORD, ADMIN_PASSWORD)
│   ├── comum.py                # upload, sidebar, render_pagina_analise, histórico, carregar_clausulas
│   ├── t1_nda.py               # NDA
│   ├── t2_spa_cotas.py         # SPA de cotas
│   ├── t3_spa_aquisicao.py     # SPA de aquisição
│   ├── t4_spa_desinvestimento.py
│   ├── t5_reg_fip.py
│   ├── t6_reg_fidc.py
│   ├── t7_consultoria.py
│   ├── t8_contrato_social_search.py
│   ├── t9_acordo_socios_search.py
│   ├── t10_reg_fip_acquisition.py
│   └── t11_acordo_cotistas_acquisition.py
│
├── analise/
│   ├── agent/                  # Sistema de agentes LLM
│   │   ├── orquestrador.py     # Orquestrador: pipeline completo e paralelização
│   │   ├── agent1_extrator_docx.py  # Extrai cláusulas do DOCX (LLM)
│   │   ├── agent2_matcher.py   # Matcher: regras + chunks (ChromaDB, top_k=5)
│   │   ├── agent3_verificador.py    # Verifica violação (regra + 5 chunks), paralelo
│   │   ├── agent4_reescritor.py     # Sugestão de reescrita por violação, paralelo
│   │   ├── escolha_modelo.py   # Gerenciador de modelos LLM e Embedding
│   │   ├── exceptions.py       # Exceções com user_message (APIKeyError, etc.)
│   │   ├── __init__.py         # Prompts: carregar_prompt_tipo, AGENTES, idioma
│   │   └── prompts/            # Por tipo e idioma (extrator, agent3, agent4)
│   │       ├── _defaults/      # Fallback
│   │       ├── nda/
│   │       └── ... (spa_cotas, reg_fip, etc.)
│   └── embeddings/
│       └── clausulas.py        # Indexação cláusulas de referência (JSON → ChromaDB)
│
├── output/
│   ├── docx.py                 # gerar_problemas_docx, gerar_solucao_docx
│   ├── comparar_docx.py        # gerar_doc_comparado (problemas + solução → explicacao)
│   └── docs/                   # DOCX gerados (problemas_*, solucao_*, explicacao_*)
│
├── db/                         # Cláusulas de referência por tipo e idioma
│   ├── nda_clausulas_pt.json
│   ├── nda_clausulas_en.json
│   └── {tipo}_clausulas_{pt|en}.json
│
└── chroma_db/                  # Vector store (ChromaDB)
    └── chroma.sqlite3
```

### Fluxo de Análise (detalhado)

1. **Autenticação**: Se `APP_PASSWORD` estiver no `.env`, exibe tela de login (`modulos/auth.py`).
2. **Home**: Usuário escolhe **idioma do documento** (pt/en) e **tipo de contrato**; ao clicar no tipo, vai para a página de análise.
3. **Upload**: Na página do tipo (ex.: `t1_nda`), upload do `.docx`; `comum.render_pagina_analise` chama o orquestrador.
4. **Orquestrador**:
   - Valida embedding e base de conhecimento (regras em `db/`, ChromaDB sincronizado).
   - **Agent 1**: Extrai cláusulas do DOCX (LLM + prompts por tipo/idioma).
   - **Agent 2**: Para cada regra ativa, busca no ChromaDB os chunks do documento com similaridade ≥ threshold; monta (regra, top 5 chunks).
   - **Agent 3**: Para cada (regra, top 5 chunks), verifica se há violação (LLM); execução **em paralelo** (ThreadPoolExecutor, até 4 workers).
   - **Agent 4**: Para cada violação validada, gera sugestão de reescrita (LLM); execução **em paralelo**.
   - **Output**: Gera 3 DOCX (problemas, solução, explicação via `comparar_docx`) e grava em `output/docs/`; retorna `ResultadoAnalise` com bytes dos DOCX para download na UI.
5. **Resultado**: Lista de violações/conformidades, tempo, modelo usado; download dos 3 DOCX; histórico das últimas análises na sessão.

### Configuração (config.toml)

O arquivo `config.toml` na raiz do projeto configura o Streamlit:

- **theme**: cores (primaryColor, backgroundColor, etc.)
- **server.port**: porta (padrão 8501)
- **server.maxUploadSize**: tamanho máximo de upload em MB (ex.: 5000)
- **server.maxMessageSize**: tamanho máximo de mensagem para widgets
- **browser.gatherUsageStats**: false para não enviar estatísticas

Variáveis sensíveis (API keys, senhas) ficam apenas no `.env`.

### Como Adicionar Novo Tipo de Contrato

#### Passo 1: Criar módulo em `modulos/`

```python
# modulos/t12_novo_tipo.py
from .comum import render_pagina_analise

def render():
    render_pagina_analise(
        tipo_contrato="NOVO_TIPO",           # Identificador único (MAIÚSCULAS)
        titulo="Análise - Novo Tipo",         # Título da página
        label_upload="Envie o arquivo...",    # Label do upload
        key_prefix="novo_tipo"                # Prefixo para session_state
    )
```

#### Passo 2: Criar arquivo de cláusulas em `db/`

```json
// db/novo_tipo_clausulas_pt.json (minúsculas, sufixo _pt ou _en)
[
  {
    "ativa": true,
    "titulo": "Nome da Cláusula",
    "regra_spectra": "O que esta cláusula deve verificar",
    "buscar_em": "Termos para busca semântica",
    "como_corrigir": "Sugestão de redação (opcional)"
  }
]
```

#### Passo 3: (Opcional) Criar prompts específicos

Os agentes **extrator**, **agent3** (Verificador) e **agent4** (Reescritor) usam prompts por tipo e idioma. Arquivos no formato `{agent}_{system|user}_{pt|en}.txt`.

```
analise/agent/prompts/novo_tipo/
├── extrator_system_pt.txt
├── extrator_user_pt.txt
├── agent3_system_pt.txt
├── agent3_user_pt.txt
├── agent4_system_pt.txt
└── agent4_user_pt.txt
```

Se não criar, usa os prompts de `_defaults/`.

#### Passo 4: Registrar em `app.py`

```python
# Import
from modulos.t12_novo_tipo import render as render_novo_tipo

# Adicionar botão na home (dentro do if apropriado)
if st.button("Novo Tipo de Contrato", use_container_width=True):
    st.session_state.tipo_documento = "NOVO_TIPO"
    st.session_state.pagina = "analise"
    st.rerun()

# Adicionar case no router
elif st.session_state.tipo_documento == "NOVO_TIPO":
    render_novo_tipo()
```

---

## 📞 Suporte

Se você encontrar problemas que não estão listados aqui:

1. Verifique os logs no terminal onde a plataforma está rodando
2. Verifique se todas as chaves de API estão corretas
3. Verifique se todas as dependências foram instaladas
4. Consulte a seção [Problemas Comuns e Soluções](#problemas-comuns-e-soluções)

Para questões técnicas mais complexas, consulte o histórico de commits.

---

## 📝 Notas Finais

- **Segurança**: Nunca compartilhe o arquivo `.env` ou as chaves de API
- **Backup**: Faça backup regular do arquivo `chroma_db/chroma.sqlite3` se você tiver muitas cláusulas indexadas
- **Custos**: Monitore o uso das APIs para controlar custos
- **Atualizações**: Mantenha as dependências atualizadas periodicamente

---

---

## 🔐 Segurança e Arquivos Importantes

### Arquivo de Chave SSH

Para acessar o servidor de produção, você precisa do arquivo de chave privada:

- **Arquivo**: `SPECTRA-APP_key.pem`
- **Localização esperada**: `C:\Users\SeuUsuario\OneDrive - Spectra\Documentos\Vm Linux SPECTRA-APP\SPECTRA-APP_key.pem`

**⚠️ IMPORTANTE**: 
- Este arquivo contém credenciais de acesso ao servidor
- **NÃO** compartilhe este arquivo
- **NÃO** faça commit deste arquivo no Git
- Mantenha este arquivo seguro e com permissões restritas (chmod 600 no Linux)

---

**Última atualização**: Janeiro 2026
