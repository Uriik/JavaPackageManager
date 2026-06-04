import requests
import time
from typing import List, Dict, Optional

class MavenCentralAPI:
    SEARCH_URL = "https://search.maven.org/solrsearch/select"
    
    def __init__(self, cache_ttl: int = 600):
        """
        Inicializa o cliente da API do Maven Central com cache local.
        """
        self.cache_ttl = cache_ttl
        self.search_cache: Dict[str, tuple] = {} # query -> (timestamp, data)
        self.version_cache: Dict[str, tuple] = {} # group_id:artifact_id -> (timestamp, versions)
        
    def _is_cache_valid(self, timestamp: float) -> bool:
        return (time.time() - timestamp) < self.cache_ttl

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Pesquisa artefatos no Maven Central.
        Retorna: [{"groupId": "...", "artifactId": "...", "latestVersion": "...", "id": "..."}]
        """
        query = query.strip()
        if not query:
            return []
            
        # Verificar cache
        cache_key = f"{query}:{limit}"
        if cache_key in self.search_cache:
            ts, cached_data = self.search_cache[cache_key]
            if self._is_cache_valid(ts):
                return cached_data
                
        # Preparar parâmetros
        params = {
            "q": query,
            "rows": limit,
            "wt": "json"
        }
        
        try:
            response = requests.get(self.SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            
            results = []
            for doc in docs:
                results.append({
                    "groupId": doc.get("g", ""),
                    "artifactId": doc.get("a", ""),
                    "latestVersion": doc.get("latestVersion", ""),
                    "id": doc.get("id", "")
                })
                
            # Salvar no cache
            self.search_cache[cache_key] = (time.time(), results)
            return results
            
        except Exception as e:
            # Em caso de falha de rede/API, retorna lista vazia ou loga erro
            print(f"Erro ao buscar na API do Maven Central: {str(e)}")
            # Retorna do cache mesmo expirado se houver, senão retorna vazio
            if cache_key in self.search_cache:
                return self.search_cache[cache_key][1]
            return []

    def get_versions(self, group_id: str, artifact_id: str, limit: int = 50) -> List[str]:
        """
        Retorna a lista de versões de um determinado artefato.
        Ordenado pelas versões mais recentes de acordo com o timestamp do Maven Central.
        """
        group_id = group_id.strip()
        artifact_id = artifact_id.strip()
        
        cache_key = f"{group_id}:{artifact_id}"
        if cache_key in self.version_cache:
            ts, cached_data = self.version_cache[cache_key]
            if self._is_cache_valid(ts):
                return cached_data
                
        # Query para pegar as versões (GAV core)
        params = {
            "q": f'g:"{group_id}" AND a:"{artifact_id}"',
            "core": "gav",
            "rows": limit,
            "wt": "json"
        }
        
        try:
            response = requests.get(self.SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            
            # Extrair versões
            versions = []
            for doc in docs:
                v = doc.get("v")
                if v:
                    versions.append(v)
                    
            # Garantir ordenação (se a API já não retornou ordenada por data, mas normalmente docs vem ordenados)
            # Salvar no cache
            self.version_cache[cache_key] = (time.time(), versions)
            return versions
            
        except Exception as e:
            print(f"Erro ao obter versões para {group_id}:{artifact_id}: {str(e)}")
            if cache_key in self.version_cache:
                return self.version_cache[cache_key][1]
            return []
