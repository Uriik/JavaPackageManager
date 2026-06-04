# ☕ jpkg — Java Package Manager

**jpkg** é um gerenciador de pacotes visual e de linha de comando inovador para projetos Java baseados em **Maven**, inspirado no NuGet do ecossistema .NET. Ele fornece uma interface moderna e bonita via **Streamlit** que permite buscar, adicionar, atualizar e remover dependências com facilidade, além de contar com suporte a **IA local (Ollama)** para recomendações e análises.

---

## 🎨 Interface Visual (Streamlit)

A interface do `jpkg` foi desenvolvida com foco em estética moderna, oferecendo:
* **Tema Escuro Nativo:** Layout elegante e confortável com acentos visuais.
* **Barra Lateral de Configurações:** Permite selecionar dinamicamente o modelo ativo no seu Ollama local (como `gemma4:latest`, `llama3.1:8b`, etc.) e exibe informações do projeto atual.
* **Status do Ambiente:** Indicadores de integridade do Java JDK, CLI do Maven, arquivo `pom.xml` e status da conexão com a IA.
* **Console de Logs Integrado:** Exibe o output das compilações e downloads do Maven em tempo real.

---

## 🚀 Funcionalidades Principais

1. **Manipulação de `pom.xml` Limpa:** Utiliza o parser `lxml` para ler e salvar modificações no seu `pom.xml`, garantindo a preservação absoluta de comentários, espaços em branco e recuo original.
2. **Integração Maven Central:** Realiza pesquisas de pacotes e busca todas as versões disponíveis em tempo real com um sistema de cache local para evitar requisições repetidas.
3. **Maven Runner em Tempo Real:** Executa tarefas do Maven (`clean compile`, `clean install`, etc.) em subprocessos de forma assíncrona, capturando os logs linha por linha.
4. **Assistente de IA Local (Ollama + LiteLLM):**
   * **Busca Inteligente:** Recomenda bibliotecas com base em descrições em linguagem natural (ex: *"preciso fazer requisições HTTP"*).
   * **Revisão de Arquitetura:** Analisa a lista de dependências instaladas e sugere alternativas modernas, upgrades ou substituições.
   * **Diagnóstico de Erros:** Interpreta logs de erro de compilação do Maven e explica em português simples o que falhou e como corrigir.

---

## 💻 Requisitos do Sistema

* **Python:** >= 3.8 (Recomendado 3.13)
* **Java:** JDK instalado e configurado no ambiente
* **Maven:** CLI global instalada ou um wrapper local (`mvnw` / `mvnw.cmd`) na pasta do projeto Java
* **Ollama (Opcional):** Para as funções de IA local

---

## 🛠️ Como Instalar e Rodar

### 1. Clonar e Instalar o jpkg
Na pasta do repositório, instale no modo editável:
```bash
pip install -e .
```
Isso disponibilizará o comando global `jpkg` no seu terminal.

### 2. Iniciar a Interface
Aponte o comando para o diretório de qualquer projeto Java que possua um arquivo `pom.xml`:
```bash
jpkg open --project /caminho/do/seu/projeto/java
```
A interface Streamlit abrirá automaticamente no navegador em: **[http://localhost:8501](http://localhost:8501)**

### 3. Configurar a IA Local (Opcional)
Se você tiver o Ollama rodando, o `jpkg` detectará os modelos instalados automaticamente.
1. Instale o [Ollama](https://ollama.com/).
2. Baixe um modelo compatível (como `gemma4` ou `llama3.1`):
   ```bash
   ollama pull gemma4
   ```
3. Na barra lateral da interface do `jpkg`, selecione o modelo desejado no campo **🤖 Modelo Ollama**.

---

## 📁 Estrutura de Pastas do Projeto

```text
JavaPackageManager/
├── jpkg/                     # Código fonte principal do pacote python
│   ├── core/                 # Lógica de detecção, parsing de XML e execução do Maven
│   │   ├── environment.py    # Detecção de SDKs (Java, Maven, pom.xml)
│   │   ├── pom_manager.py    # CRUD de dependências pom.xml com lxml
│   │   ├── maven_runner.py   # Execução subprocess de mvn
│   │   ├── maven_api.py      # Conector API do Maven Central
│   │   └── ai_assistant.py   # Integração LiteLLM/Ollama
│   ├── ui/                   # Interface visual Streamlit
│   │   ├── components/       # Componentes visuais (cards de pacotes)
│   │   └── pages/            # Abas da interface (home, search, dependencies, logs)
│   ├── app.py                # Inicialização e roteamento do Streamlit
│   ├── main.py               # Entry point CLI (Click)
│   └── tests/                # Testes unitários com pytest
├── setup.py                  # Script setuptools de empacotamento
└── README.md                 # Esta documentação do repositório
```
