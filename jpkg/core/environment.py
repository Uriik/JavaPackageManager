import os
import subprocess
import re
from xml.etree import ElementTree

def detect_java() -> dict:
    """
    Detecta o Java instalado e sua versão.
    Verifica a variável JAVA_HOME e executa 'java -version'.
    """
    result = {
        "found": False,
        "version": "",
        "path": "",
        "error": ""
    }
    
    # 1. Tentar obter pelo JAVA_HOME
    java_home = os.environ.get("JAVA_HOME", "")
    if java_home:
        java_exe = os.path.join(java_home, "bin", "java.exe" if os.name == "nt" else "java")
        if os.path.exists(java_exe):
            result["path"] = java_exe
            
    # 2. Executar 'java -version'
    try:
        # Se achou pelo JAVA_HOME, executa direto dele, senão tenta do PATH global
        cmd = result["path"] if result["path"] else "java"
        process = subprocess.run(
            [cmd, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        
        # O java -version imprime no stderr
        output = process.stderr + process.stdout
        
        # Regex para capturar a versão (ex: version "17.0.2" ou version "1.8.0_291")
        match = re.search(r'version "([^"]+)"', output)
        if match:
            result["found"] = True
            result["version"] = match.group(1)
            if not result["path"]:
                result["path"] = "java (PATH)"
        else:
            result["error"] = "Não foi possível extrair a versão do output do comando java."
    except Exception as e:
        result["error"] = f"Erro ao executar java -version: {str(e)}"
        
    return result

def detect_maven(project_path: str = ".") -> dict:
    """
    Detecta o Maven instalado.
    Verifica primeiro wrappers locais (mvnw/mvnw.cmd) no projeto, depois MAVEN_HOME/M2_HOME e PATH global.
    """
    result = {
        "found": False,
        "version": "",
        "path": "",
        "error": ""
    }
    
    # 1. Tentar wrapper local no projeto
    if project_path:
        wrapper_cmd = "mvnw.cmd" if os.name == "nt" else "./mvnw"
        wrapper_path = os.path.join(os.path.abspath(project_path), wrapper_cmd)
        if os.path.exists(wrapper_path):
            result["path"] = wrapper_path
            
    # 2. Tentar variáveis de ambiente MAVEN_HOME ou M2_HOME
    if not result["path"]:
        maven_home = os.environ.get("MAVEN_HOME") or os.environ.get("M2_HOME")
        if maven_home:
            mvn_exe = os.path.join(maven_home, "bin", "mvn.cmd" if os.name == "nt" else "mvn")
            if os.path.exists(mvn_exe):
                result["path"] = mvn_exe
                
    # 3. Executar o comando do Maven para pegar a versão
    try:
        cmd = result["path"] if result["path"] else ("mvn.cmd" if os.name == "nt" else "mvn")
        process = subprocess.run(
            [cmd, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True if os.name == "nt" else False, # Necessário no Windows para rodar .cmd/.bat sem caminho absoluto direto
            timeout=10
        )
        
        output = process.stdout + process.stderr
        
        # Regex para capturar a versão (ex: Apache Maven 3.9.6)
        match = re.search(r'Apache Maven ([^\s\(\)]+)', output)
        if match:
            result["found"] = True
            result["version"] = match.group(1)
            if not result["path"]:
                result["path"] = "mvn (PATH)"
        else:
            result["error"] = "Não foi possível extrair a versão do output do comando mvn."
    except Exception as e:
        result["error"] = f"Erro ao executar mvn -version: {str(e)}"
        
    return result

def validate_project(project_path: str) -> dict:
    """
    Valida se o caminho do projeto é válido e contém um pom.xml estruturalmente correto.
    """
    result = {
        "valid": False,
        "pom_path": "",
        "error": ""
    }
    
    abs_path = os.path.abspath(project_path)
    pom_path = os.path.join(abs_path, "pom.xml")
    
    if not os.path.exists(pom_path):
        result["error"] = f"Arquivo pom.xml não encontrado no diretório: {abs_path}"
        return result
        
    result["pom_path"] = pom_path
    
    try:
        # Parsing rápido usando ElementTree padrão apenas para validar sintaxe
        ElementTree.parse(pom_path)
        result["valid"] = True
    except Exception as e:
        result["error"] = f"O arquivo pom.xml está malformado ou inválido: {str(e)}"
        
    return result
