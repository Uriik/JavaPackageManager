import json
import requests
from typing import List, Dict, Optional

try:
    from litellm import completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

class AIAssistant:
    def __init__(self, model: str = "ollama/qwen3", api_base: str = "http://localhost:11434"):
        """
        Inicializa o assistente de IA.
        Foca no uso local com Ollama através do LiteLLM.
        """
        self.model = model
        self.api_base = api_base
        self.available_models = []
        
    def is_available(self) -> bool:
        """
        Verifica se a biblioteca litellm está disponível e se o Ollama está rodando localmente.
        """
        if not LITELLM_AVAILABLE:
            return False
            
        try:
            # Tenta verificar as tags do Ollama para obter a lista de modelos instalados
            response = requests.get(f"{self.api_base}/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [m["name"] for m in data.get("models", [])]
                return True
            return False
        except Exception:
            return False

    def _get_active_model(self) -> str:
        """
        Retorna o modelo a ser usado no Ollama. Se o modelo configurado não estiver disponível,
        tenta selecionar automaticamente o melhor modelo de código ou de linguagem disponível localmente.
        """
        if not self.available_models:
            # Tenta atualizar a lista de modelos
            self.is_available()
            
        if not self.available_models:
            return self.model  # Fallback para o configurado
            
        # Remover o prefixo 'ollama/' para comparação limpa
        config_model_clean = self.model
        if self.model.startswith("ollama/"):
            config_model_clean = self.model[7:]
            
        # Se o modelo configurado estiver baixado no Ollama, usa ele
        if config_model_clean in self.available_models or self.model in self.available_models:
            return self.model
            
        # Se o modelo configurado não existir, tenta encontrar o melhor disponível
        # 1. Procurar por algum modelo 'qwen' ou 'coder'
        for m in self.available_models:
            if "qwen" in m.lower() or "coder" in m.lower():
                return f"ollama/{m}"
                
        # 2. Procurar por 'llama'
        for m in self.available_models:
            if "llama" in m.lower():
                return f"ollama/{m}"
                
        # 3. Procurar por 'gemma'
        for m in self.available_models:
            if "gemma" in m.lower():
                return f"ollama/{m}"
                
        # 4. Fallback para o primeiro modelo disponível
        return f"ollama/{self.available_models[0]}"

    def _parse_json_list(self, text: str) -> List[Dict]:
        """Tenta extrair uma lista em formato JSON da resposta da IA."""
        try:
            # Limpa possíveis blocos de código markdown (ex: ```json ... ```)
            clean_text = text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(clean_text)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "packages" in data:
                # Caso a IA retorne {"packages": [...]}
                return data["packages"]
            return []
        except Exception:
            # Fallback em caso de falha de parsing do JSON
            return []

    def suggest_packages(self, description: str) -> List[Dict]:
        """
        Sugere pacotes Maven com base na descrição das necessidades do usuário.
        Retorna: [{"groupId": "...", "artifactId": "...", "reason": "..."}]
        """
        if not self.is_available():
            return []
            
        prompt = f"""Você é um arquiteto especialista em ecossistema Java e Maven.
O usuário quer adicionar uma dependência no projeto com o seguinte objetivo:
"{description}"

Sugira entre 1 e 4 das melhores e mais populares bibliotecas Java (Maven) que resolvem isso.
Para cada biblioteca sugerida, informe exatamente o 'groupId', o 'artifactId' e a justificativa ('reason') em português de forma concisa.

Sua resposta DEVE ser estritamente no formato JSON abaixo, sem qualquer outro texto explicativo antes ou depois:
[
  {{
    "groupId": "nome.do.grupo",
    "artifactId": "nome-do-artefato",
    "reason": "Justificativa rápida de por que usar esta biblioteca"
  }}
]
"""
        try:
            response = completion(
                model=self._get_active_model(),
                messages=[{"role": "user", "content": prompt}],
                api_base=self.api_base,
                temperature=0.2
            )
            content = response.choices[0].message.content
            return self._parse_json_list(content)
        except Exception as e:
            print(f"Erro ao obter sugestões da IA: {str(e)}")
            return []

    def analyze_dependencies(self, deps: List[Dict]) -> str:
        """
        Analisa as dependências atuais e retorna um resumo com possíveis sugestões ou melhorias.
        """
        if not self.is_available():
            return ""
            
        deps_str = "\n".join([f"- {d['groupId']}:{d['artifactId']} (versão: {d.get('version', 'N/A')}, escopo: {d.get('scope', 'compile')})" for d in deps])
        
        prompt = f"""Como especialista em Java, analise as dependências atuais deste projeto e sugira melhorias:
{deps_str}

Responda em português, de forma concisa, abordando pontos como:
1. Versões desatualizadas ou vulneráveis (se souber).
2. Bibliotecas redundantes ou obsoletas.
3. Alternativas modernas recomendadas.
Limite a resposta a no máximo 15 linhas, formatada em tópicos (Markdown)."""
        
        try:
            response = completion(
                model=self._get_active_model(),
                messages=[{"role": "user", "content": prompt}],
                api_base=self.api_base,
                temperature=0.5
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro ao contatar o assistente de IA: {str(e)}"

    def explain_error(self, error_log: str) -> str:
        """
        Interpreta o log de erro do Maven e fornece uma explicação simples e passos para resolução.
        """
        if not self.is_available():
            return ""
            
        # Pega as últimas 50 linhas para não estourar o contexto do LLM local
        lines = error_log.splitlines()
        truncated_log = "\n".join(lines[-50:])
        
        prompt = f"""Um build do Maven falhou com o seguinte erro:
{truncated_log}

Explique em português, de forma amigável e direta:
1. O que causou o erro.
2. Como corrigir passo a passo.
Seja conciso e use formatação Markdown."""
        
        try:
            response = completion(
                model=self._get_active_model(),
                messages=[{"role": "user", "content": prompt}],
                api_base=self.api_base,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro ao contatar o assistente de IA para explicar erro: {str(e)}"
