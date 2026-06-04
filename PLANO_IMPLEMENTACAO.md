# 🚀 Plano de Implementação: Java Package Manager (jpkg)

> Plano passo a passo para construir uma ferramenta tipo NuGet para Java/Maven com interface Streamlit e IA opcional via LLM open source.

---

## 📌 DECISÕES TÉCNICAS DEFINIDAS

| Item | Decisão | Justificativa |
|------|---------|---------------|
| Build Tool | **Maven** (apenas) | Foco no MVP, Gradle fica para v2 |
| UI | **Streamlit** | Rápido de desenvolver, web-based |
| XML Parsing | **lxml** | Preserva formatação do pom.xml |
| Maven Exec | **subprocess** | Simples e confiável |
| LLM | **Ollama + LiteLLM** | Local, open source, flexível |
| Modelo IA | **Qwen3** (recomendado) | Melhor para coding open-source |
| CLI | **Click** | Padrão de mercado |

---

## 🤖 ARQUITETURA DE IA (LLM Open Source)

### Por que Ollama + LiteLLM?

```
┌─────────────────┐
│   Streamlit UI  │
└────────┬────────┘
         │
┌────────▼────────┐
│    LiteLLM      │  ← Interface unificada
│  (abstração)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼─────┐
│ Ollama│ │ OpenAI │  ← Pode trocar facilmente
│(local)│ │(cloud) │
└───────┘ └────────┘
```

**Vantagens:**
- Roda 100% local (privacidade)
- Pode trocar para cloud se quiser
- Mesmo código funciona com qualquer modelo

**Exemplo de código:**
```python
from litellm import completion

response = completion(
    model="ollama/qwen3",  # Local!
    messages=[{
        "role": "user",
        "content": "Sugira pacotes Maven para fazer requisições HTTP"
    }],
    api_base="http://localhost:11434"
)
print(response.choices[0].message.content)
```

---

## 📅 FASES DE IMPLEMENTAÇÃO

### 🏗️ FASE 0: SETUP INICIAL (30 min)

**Passo 0.1 — Estrutura de pastas**
```bash
mkdir -p jpkg/{core,ui,ui/pages,ui/components,tests}
cd jpkg
```

**Passo 0.2 — Ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

**Passo 0.3 — Dependências (requirements.txt)**
```txt
streamlit>=1.40.0
lxml>=5.0.0
requests>=2.32.0
click>=8.1.0
pydantic>=2.0.0
litellm>=1.50.0      # IA opcional
ollama>=0.3.0        # IA opcional
```

```bash
pip install -r requirements.txt
```

**✅ Checkpoint:** Estrutura criada e dependências instaladas

---

### 🔍 FASE 1: DETECÇÃO DE AMBIENTE (2-3h)

**Objetivo:** Detectar Java, Maven e validar projeto

**Passo 1.1 — core/environment.py**

Funções a implementar:
```python
def detect_java() -> dict:
    """Detecta Java instalado e versão"""
    # 1. Tentar JAVA_HOME
    # 2. Executar 'java -version'
    # 3. Retornar: {found, version, path, error}

def detect_maven() -> dict:
    """Detecta Maven instalado"""
    # 1. Tentar M2_HOME / MAVEN_HOME
    # 2. Executar 'mvn -version'
    # 3. Retornar: {found, version, path, error}

def validate_project(project_path: str) -> dict:
    """Valida se há pom.xml válido"""
    # 1. Verificar se pom.xml existe
    # 2. Validar XML
    # 3. Retornar: {valid, pom_path, error}
```

**Passo 1.2 — Testes manuais**
```bash
python -c "from core.environment import detect_java; print(detect_java())"
python -c "from core.environment import detect_maven; print(detect_maven())"
```

**✅ Checkpoint:** Sistema detecta Java/Maven e valida projeto

**⚠️ Edge cases a tratar:**
- Java instalado mas JAVA_HOME não configurado
- Múltiplas versões de JDK
- Maven em PATH mas não em M2_HOME
- Windows vs Unix paths

---

### 📄 FASE 2: MANIPULAÇÃO DE POM.XML (3-4h)

**Objetivo:** Ler, adicionar, remover e atualizar dependências

**Passo 2.1 — core/pom_manager.py**

```python
class PomManager:
    def __init__(self, pom_path: str):
        """Carrega pom.xml preservando formatação"""

    def get_dependencies(self) -> list[dict]:
        """Lista dependências atuais
        Retorna: [{groupId, artifactId, version, scope}]"""

    def add_dependency(self, group_id, artifact_id, version, scope="compile"):
        """Adiciona nova dependência"""

    def remove_dependency(self, group_id, artifact_id):
        """Remove dependência existente"""

    def update_version(self, group_id, artifact_id, new_version):
        """Atualiza versão (upgrade/downgrade)"""

    def backup(self) -> str:
        """Cria backup antes de mudanças"""

    def save(self):
        """Salva mudanças preservando formatação"""
```

**Passo 2.2 — Estratégia de preservação de formatação**
```python
# Usar lxml com parser que mantém:
from lxml import etree
parser = etree.XMLParser(remove_blank_text=False)
tree = etree.parse(pom_path, parser)
# Detectar namespace Maven automaticamente
```

**Passo 2.3 — Testes**
```python
# tests/test_pom_manager.py
def test_add_dependency():
    # Criar pom.xml temporário
    # Adicionar dependência
    # Verificar que foi adicionada
    # Verificar formatação preservada

def test_remove_dependency():
    # ...

def test_update_version():
    # ...
```

**✅ Checkpoint:** CRUD de dependências funciona preservando formatação

**⚠️ Edge cases a tratar:**
- Dependência em `<dependencyManagement>`
- Versão definida em `<properties>` (ex: `${spring.version}`)
- Namespaces XML
- Comentários no pom.xml
- Multi-module (parent pom)

---

### ⚙️ FASE 3: INTEGRAÇÃO MAVEN (2-3h)

**Objetivo:** Executar comandos Maven e capturar resultados

**Passo 3.1 — core/maven_runner.py**

```python
class MavenRunner:
    def __init__(self, project_path: str, maven_path: str = "mvn"):
        """Inicializa runner"""

    def run(self, goals: list[str], timeout=300) -> dict:
        """Executa comando Maven
        Retorna: {success, stdout, stderr, return_code}"""

    def install(self) -> dict:
        """mvn install"""

    def compile(self) -> dict:
        """mvn compile"""

    def dependency_tree(self) -> dict:
        """mvn dependency:tree"""

    def clean(self) -> dict:
        """mvn clean"""
```

**Passo 3.2 — Captura de output em tempo real**
```python
import subprocess

def run_with_streaming(cmd, callback):
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    for line in process.stdout:
        callback(line)  # Atualiza UI em tempo real
    process.wait()
    return process.returncode
```

**Passo 3.3 — Parser de erros**
```python
def parse_maven_error(output: str) -> dict:
    """Identifica erros comuns e sugere soluções"""
    errors = {
        "Could not resolve dependencies": "Verifique groupId/artifactId/version",
        "Unsupported major.minor": "Versão Java incompatível - verifique JAVA_HOME",
        "Could not transfer": "Erro de rede - verifique conexão/proxy",
        # ...
    }
```

**✅ Checkpoint:** Executa Maven e captura logs/erros

---

### 🔎 FASE 4: BUSCA MAVEN CENTRAL (2h)

**Objetivo:** Buscar pacotes na API do Maven Central

**Passo 4.1 — core/maven_api.py**

```python
import requests

class MavenCentralAPI:
    BASE_URL = "https://central.sonatype.com/api/v1/search"

    def search(self, query: str, limit=20) -> list[dict]:
        """Busca pacotes
        Retorna: [{groupId, artifactId, latestVersion, ...}]"""

    def get_versions(self, group_id, artifact_id) -> list[str]:
        """Lista todas versões disponíveis"""

    def get_package_info(self, group_id, artifact_id) -> dict:
        """Detalhes do pacote"""
```

**Passo 4.2 — Cache local**
```python
from functools import lru_cache
import json, time

class SearchCache:
    def __init__(self, ttl=3600):  # 1 hora
        self.cache = {}

    def get(self, key):
        # Verifica TTL
        # Retorna se válido

    def set(self, key, value):
        # Armazena com timestamp
```

**✅ Checkpoint:** Busca funcionando com cache

**⚠️ Edge cases:**
- Rate limiting da API
- Timeout de rede
- Resultados vazios
- Caracteres especiais na busca

---

### 🤖 FASE 5: INTEGRAÇÃO IA - LLM (2-3h) [OPCIONAL]

**Objetivo:** Sugestões inteligentes de pacotes via LLM local

**Passo 5.1 — Setup Ollama**
```bash
# Instalar Ollama
curl https://ollama.ai/install.sh | sh

# Baixar modelo Qwen3
ollama pull qwen3

# Testar
ollama run qwen3 "Olá"
```

**Passo 5.2 — core/ai_assistant.py**

```python
from litellm import completion

class AIAssistant:
    def __init__(self, model="ollama/qwen3", api_base="http://localhost:11434"):
        self.model = model
        self.api_base = api_base

    def suggest_packages(self, description: str) -> list[dict]:
        """Sugere pacotes baseado em descrição
        Ex: 'fazer requisições HTTP' → [okhttp, httpclient]"""
        prompt = f"""Você é um especialista em Java/Maven.
        Sugira pacotes Maven para: {description}
        Responda APENAS em JSON: [{{"groupId":"", "artifactId":"", "reason":""}}]"""

        response = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            api_base=self.api_base
        )
        return self._parse_json(response)

    def analyze_dependencies(self, deps: list) -> str:
        """Analisa dependências e sugere melhorias"""

    def explain_error(self, error_log: str) -> str:
        """Explica erro de build em linguagem simples"""

    def is_available(self) -> bool:
        """Verifica se Ollama está rodando"""
```

**Passo 5.3 — Tratamento de falhas**
```python
# IA é OPCIONAL - app funciona sem ela
def safe_ai_call(func):
    try:
        if not assistant.is_available():
            return None  # Desabilita features de IA
        return func()
    except Exception:
        return None  # Falha graciosamente
```

**✅ Checkpoint:** IA sugere pacotes (com fallback se indisponível)

---

### 🎨 FASE 6: INTERFACE STREAMLIT (4-5h)

**Objetivo:** UI completa e visual tipo NuGet

**Passo 6.1 — app.py (entrada principal)**
```python
import streamlit as st

st.set_page_config(
    page_title="jpkg - Java Package Manager",
    page_icon="☕",
    layout="wide"
)

# Sidebar com navegação
# Detecção de ambiente no início
# Estado da sessão (st.session_state)
```

**Passo 6.2 — ui/pages/home.py**
```
┌──────────────────────────────────┐
│  ☕ jpkg - Java Package Manager   │
├──────────────────────────────────┤
│  📊 Status do Projeto             │
│  • Java: 17.0.2 ✅                │
│  • Maven: 3.9.6 ✅                │
│  • Dependências: 12               │
│  • Projeto: meu-projeto           │
└──────────────────────────────────┘
```

**Passo 6.3 — ui/pages/search.py**
```
┌──────────────────────────────────┐
│  🔍 [spring boot______] [Buscar] │
├──────────────────────────────────┤
│  💡 IA: Quer fazer web? Tente... │  ← Sugestão IA
├──────────────────────────────────┤
│  ┌────────────────────────────┐  │
│  │ spring-boot-starter-web    │  │
│  │ org.springframework.boot   │  │
│  │ v3.2.0 ▼   [Instalar]      │  │  ← Card de pacote
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │ spring-boot-starter-data   │  │
│  │ ...                        │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

**Passo 6.4 — ui/pages/dependencies.py**
```
┌──────────────────────────────────┐
│  📦 Dependências Atuais          │
├──────────────────────────────────┤
│ Pacote          Versão   Ações   │
│ junit           4.13.2   ⬆️ ⬇️ 🗑️ │  ← upgrade/downgrade/remove
│ spring-core     6.1.0    ⬆️ ⬇️ 🗑️ │
│ lombok          1.18.30  ⬆️ ⬇️ 🗑️ │
└──────────────────────────────────┘
```

**Passo 6.5 — ui/pages/logs.py**
```
┌──────────────────────────────────┐
│  📜 Logs de Build                │
├──────────────────────────────────┤
│ [INFO] Building project...       │
│ [INFO] Downloading dependency... │
│ [SUCCESS] Build completed ✅      │
└──────────────────────────────────┘
```

**Passo 6.6 — ui/components/package_card.py**
```python
def render_package_card(package: dict, on_install):
    """Renderiza card de pacote com botão instalar"""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(package["artifactId"])
            st.caption(package["groupId"])
        with col2:
            version = st.selectbox("Versão", package["versions"])
            if st.button("Instalar", key=package["id"]):
                on_install(package, version)
```

**✅ Checkpoint:** UI completa e funcional

---

### 🖥️ FASE 7: CLI ENTRY POINT (1h)

**Objetivo:** Comando `jpkg` que abre a UI

**Passo 7.1 — main.py**
```python
import click
import subprocess
import os

@click.group()
def cli():
    """jpkg - Java Package Manager visual"""
    pass

@cli.command()
@click.option("--project", default=".", help="Caminho do projeto")
@click.option("--port", default=8501, help="Porta do servidor")
def open(project, port):
    """Abre a interface visual"""
    os.environ["JPKG_PROJECT"] = os.path.abspath(project)
    subprocess.run([
        "streamlit", "run", "app.py",
        "--server.port", str(port)
    ])

if __name__ == "__main__":
    cli()
```

**Passo 7.2 — setup.py (para instalar globalmente)**
```python
from setuptools import setup, find_packages

setup(
    name="jpkg",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[...],
    entry_points={
        "console_scripts": ["jpkg=main:cli"]
    }
)
```

**Passo 7.3 — Instalação**
```bash
pip install -e .
# Agora pode usar de qualquer lugar:
jpkg open
```

**✅ Checkpoint:** Comando `jpkg open` funciona

---

### 🧪 FASE 8: TESTES E POLIMENTO (2-3h)

**Passo 8.1 — Testes unitários**
```bash
pip install pytest
pytest tests/
```

**Passo 8.2 — Testes de integração**
- Criar projeto Maven de teste
- Adicionar dependência via UI
- Verificar pom.xml
- Build do projeto

**Passo 8.3 — Documentação**
- README.md com instruções
- Screenshots
- Exemplos de uso

---

## 📊 RESUMO DA TIMELINE

| Fase | Descrição | Tempo | Prioridade |
|------|-----------|-------|------------|
| 0 | Setup inicial | 30min | 🔴 Crítico |
| 1 | Detecção ambiente | 2-3h | 🔴 Crítico |
| 2 | Manipulação POM | 3-4h | 🔴 Crítico |
| 3 | Integração Maven | 2-3h | 🔴 Crítico |
| 4 | Busca Maven Central | 2h | 🟡 Alto |
| 5 | IA (LLM) | 2-3h | 🟢 Opcional |
| 6 | Interface Streamlit | 4-5h | 🔴 Crítico |
| 7 | CLI entry point | 1h | 🟡 Alto |
| 8 | Testes | 2-3h | 🟡 Alto |
| **TOTAL** | **MVP completo** | **18-24h** | |

**Sem IA: ~16-21h | Com IA: ~18-24h**

---

## 🎯 ORDEM DE EXECUÇÃO RECOMENDADA

```
1. FASE 0 (Setup)
   ↓
2. FASE 1 (Detecção) ← Fundação
   ↓
3. FASE 2 (POM) ← Coração do sistema
   ↓
4. FASE 4 (Busca) ← Pode fazer antes da UI
   ↓
5. FASE 3 (Maven) ← Executar comandos
   ↓
6. FASE 6 (UI) ← Juntar tudo
   ↓
7. FASE 7 (CLI) ← Entry point
   ↓
8. FASE 5 (IA) ← Adicionar inteligência [opcional]
   ↓
9. FASE 8 (Testes) ← Validação final
```

---

## ⚡ ESTRATÉGIA "WALKING SKELETON"

Para ter algo funcionando RÁPIDO, sugiro fazer um fluxo mínimo end-to-end primeiro:

**Sprint 1 (4-5h) - Esqueleto funcional:**
1. Detectar Maven (versão simplificada)
2. Ler dependências do pom.xml
3. UI Streamlit básica mostrando dependências
4. Comando jpkg open

**Sprint 2 (4-5h) - Funcionalidade core:**
1. Buscar Maven Central
2. Adicionar dependência
3. Executar mvn install

**Sprint 3 (4-5h) - Completar:**
1. Remover/atualizar versões
2. Logs em tempo real
3. Tratamento de erros

**Sprint 4 (opcional) - IA:**
1. Integrar Ollama/LiteLLM
2. Sugestões inteligentes

---

## 🚦 PRÓXIMA DECISÃO

**Por onde quer começar?**

**Opção A:** Walking Skeleton (algo funcionando rápido)
**Opção B:** Fase por fase em ordem (mais estruturado)
**Opção C:** Componente específico primeiro (ex: só POM manager)

Me diga e começamos a codar! 🚀
