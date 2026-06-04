import os
import sys
import subprocess
import click
from jpkg.core.environment import validate_project

@click.group()
def cli():
    """jpkg - Gerenciador Visual de Dependências Java/Maven."""
    pass

@cli.command()
@click.option("--project", "-p", default=".", help="Caminho do projeto Java/Maven (deve conter um pom.xml)")
@click.option("--port", default=8501, help="Porta onde o servidor Streamlit irá rodar")
def open(project, port):
    """Abre a interface visual do jpkg no seu navegador."""
    # Resolver o caminho absoluto do projeto
    abs_project_path = os.path.abspath(project)
    
    # Validar se o projeto possui pom.xml válido
    click.echo(f"Validando projeto em: {abs_project_path}...")
    validation = validate_project(abs_project_path)
    
    if not validation["valid"]:
        click.secho(f"Erro: {validation['error']}", fg="red")
        click.echo("Por favor, aponte para um diretório válido que contenha um arquivo pom.xml.")
        sys.exit(1)
        
    click.secho("Projeto validado com sucesso!", fg="green")
    
    # Definir a variável de ambiente para que o app.py possa consumir
    os.environ["JPKG_PROJECT_PATH"] = abs_project_path
    
    # Resolver o caminho do app.py (deve estar na mesma pasta de main.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_py_path = os.path.join(current_dir, "app.py")
    
    if not os.path.exists(app_py_path):
        click.secho(f"Erro: Arquivo {app_py_path} não encontrado.", fg="red")
        sys.exit(1)
        
    click.echo(f"Iniciando o servidor visual jpkg na porta {port}...")
    
    # Executar o streamlit
    # No Windows/Python virtualenv, é mais seguro chamar o streamlit executável da mesma pasta Scripts do Python atual
    streamlit_exe = "streamlit"
    python_dir = os.path.dirname(sys.executable)
    local_streamlit = os.path.join(python_dir, "streamlit.exe" if os.name == "nt" else "streamlit")
    if os.path.exists(local_streamlit):
        streamlit_exe = local_streamlit
        
    cmd = [
        streamlit_exe,
        "run",
        app_py_path,
        "--server.port",
        str(port),
        "--server.headless",
        "false" # Abre automaticamente o navegador
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        click.echo("\nServidor finalizado pelo usuário. Até logo!")
    except Exception as e:
        click.secho(f"Erro ao iniciar o Streamlit: {str(e)}", fg="red")
        sys.exit(1)

if __name__ == "__main__":
    cli()
