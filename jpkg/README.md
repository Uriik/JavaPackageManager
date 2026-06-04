# ☕ jpkg — Java Package Manager

jpkg (Java Package Manager) é uma ferramenta visual e de linha de comando inovadora (tipo NuGet) para gerenciar dependências de projetos Java configurados com **Maven**. 

Ela oferece uma interface web rica, construída com **Streamlit**, capaz de pesquisar pacotes no Maven Central, atualizar versões, remover pacotes com segurança mantendo a formatação original do seu `pom.xml`, rodar comandos Maven em tempo real com streaming de logs e oferecer sugestões inteligentes e suporte a erros usando **IA local (Ollama + LiteLLM)**.

---

## ✨ Funcionalidades

- **Detecção Automática:** Identifica o JDK instalado, a CLI do Maven (ou wrappers locais `./mvnw`) e valida o projeto.
- **Parsing de XML com Formatação:** Usa o parser `lxml` para ler e salvar modificações no seu `pom.xml` preservando rigorosamente a indentação, os comentários e a ordem dos elementos.
- **Pesquisa Maven Central:** Integração direta com a API do Maven Central para buscar pacotes e listar todas as versões disponíveis com cache inteligente de requisições.
- **Execução do Maven com Logs Streaming:** Roda metas (`mvn compile`, `mvn clean install`, etc.) em segundo plano e exibe o output do terminal linha a linha na interface de logs.
- **Assistente de IA Local (Opcional):**
  - Sugere pacotes Maven a partir de solicitações em linguagem natural.
  - Analisa o conjunto de dependências instaladas para sugerir melhorias de arquitetura.
  - Traduz e explica falhas de compilação em português simples com passos para correção.
- **CLI Click:** Ponto de entrada amigável pelo comando global `jpkg open`.

---

## 🚀 Instalação e Uso

### Prerrequisitos
- Python >= 3.8 (Recomendado 3.13)
- Java JDK instalado
- Maven instalado (ou wrapper `mvnw` no seu projeto Java)

### Passo 1: Instalação do jpkg

Instale o pacote localmente no modo editável:
```bash
# Na pasta raiz do repositório
pip install -e .
```

### Passo 2: Execução do Servidor Visual

Para gerenciar um projeto Java, aponte o comando `jpkg` para a pasta do projeto (onde está o `pom.xml`):
```bash
jpkg open --project /caminho/do/seu/projeto/java
```
O navegador abrirá automaticamente no endereço: [http://localhost:8501](http://localhost:8501)

### Passo 3: Ativando Inteligência Artificial (Opcional)

1. Baixe e instale o [Ollama](https://ollama.com/) no seu sistema.
2. Puxe o modelo recomendado `qwen3` ou similar:
   ```bash
   ollama pull qwen3
   ```
3. O `jpkg` detectará o Ollama ativo de forma totalmente transparente e ativará as sugestões automáticas nas abas de busca e dependências.
