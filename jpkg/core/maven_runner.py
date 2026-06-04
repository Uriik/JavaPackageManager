import os
import subprocess
import threading
from typing import Callable, Optional, List, Dict

class MavenRunner:
    def __init__(self, project_path: str, maven_path: Optional[str] = None):
        """
        Inicializa o Maven Runner.
        Se maven_path não for informado, tenta buscar o mvnw (wrapper) local ou do PATH.
        """
        self.project_path = os.path.abspath(project_path)
        self.maven_path = maven_path
        
        if not self.maven_path:
            # 1. Tentar wrapper local
            wrapper_cmd = "mvnw.cmd" if os.name == "nt" else "./mvnw"
            wrapper_full = os.path.join(self.project_path, wrapper_cmd)
            if os.path.exists(wrapper_full):
                self.maven_path = wrapper_full
            else:
                # 2. Cair para o comando global do PATH
                self.maven_path = "mvn.cmd" if os.name == "nt" else "mvn"

    def run(self, goals: List[str], callback: Optional[Callable[[str], None]] = None, timeout: int = 300) -> Dict:
        """
        Executa comandos Maven de forma síncrona com callback para streaming do output.
        Retorna dicionário com os detalhes do resultado.
        """
        # Preparar o comando
        cmd = [self.maven_path] + goals
        
        result = {
            "success": False,
            "output": "",
            "return_code": -1,
            "error_msg": "",
            "suggestion": ""
        }
        
        try:
            # Usar shell=True no Windows se estiver executando comando do PATH sem caminho completo
            use_shell = os.name == "nt" and not os.path.isabs(self.maven_path)
            
            process = subprocess.Popen(
                cmd,
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                shell=use_shell
            )
            
            output_lines = []
            
            # Ler saída em tempo real
            for line in process.stdout:
                output_lines.append(line)
                if callback:
                    callback(line)
                    
            process.wait(timeout=timeout)
            
            result["return_code"] = process.returncode
            result["success"] = (process.returncode == 0)
            result["output"] = "".join(output_lines)
            
            if not result["success"]:
                # Realizar o parse do erro para sugerir soluções
                parse_results = self.parse_errors(result["output"])
                result["error_msg"] = parse_results["error_msg"]
                result["suggestion"] = parse_results["suggestion"]
                
        except subprocess.TimeoutExpired:
            process.kill()
            result["error_msg"] = "Tempo limite de execução do Maven expirou."
            result["suggestion"] = "Tente rodar novamente ou verifique se há processos travados."
        except Exception as e:
            result["error_msg"] = f"Falha ao executar o comando Maven: {str(e)}"
            result["suggestion"] = "Verifique se o Maven está instalado no sistema ou no PATH do ambiente virtual."
            
        return result

    def clean(self, callback: Optional[Callable[[str], None]] = None) -> Dict:
        return self.run(["clean"], callback)

    def compile(self, callback: Optional[Callable[[str], None]] = None) -> Dict:
        return self.run(["compile"], callback)

    def install(self, callback: Optional[Callable[[str], None]] = None) -> Dict:
        return self.run(["clean", "install", "-DskipTests"], callback)

    def dependency_tree(self, callback: Optional[Callable[[str], None]] = None) -> Dict:
        """Executa dependency:tree para extrair a árvore de dependências."""
        return self.run(["dependency:tree"], callback)

    def parse_errors(self, output: str) -> Dict[str, str]:
        """
        Analisa os logs de build do Maven para identificar falhas comuns e sugerir correções.
        """
        res = {
            "error_msg": "Falha na compilação/build do Maven.",
            "suggestion": "Verifique o log de saída para identificar o problema."
        }
        
        # Procurar por linhas de erro no output
        error_lines = []
        for line in output.splitlines():
            if "[ERROR]" in line:
                error_lines.append(line)
                
        if not error_lines:
            return res
            
        res["error_msg"] = "\n".join(error_lines[:3]) # Mostra os primeiros 3 erros
        
        # Padrões comuns
        full_error_text = "\n".join(error_lines)
        
        if "Could not resolve dependencies" in full_error_text or "Failed to collect dependencies" in full_error_text:
            res["suggestion"] = "Não foi possível baixar alguma dependência. Verifique se o groupId, artifactId ou a versão estão corretos no seu pom.xml."
        elif "Unsupported major.minor" in full_error_text or "class file has wrong version" in full_error_text:
            res["suggestion"] = "Incompatibilidade da versão do Java. O projeto requer uma versão mais atual do JDK que a ativa no ambiente."
        elif "Could not transfer artifact" in full_error_text or "Transfer failed for" in full_error_text:
            res["suggestion"] = "Erro de conexão de rede ou problema com os repositórios Maven Central/locais. Verifique sua conexão ou se é necessário configurar proxy."
        elif "Compilation failure" in full_error_text or "compiler error" in full_error_text:
            res["suggestion"] = "Erro de sintaxe no código Java. Abra seu editor e corrija os erros de código apontados acima."
            
        return res
