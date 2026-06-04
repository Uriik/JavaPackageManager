import streamlit as st
import os
import sys

# Garante que a pasta jpkg esteja no path do python para que os imports relativos funcionem
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jpkg.core.environment import detect_java, detect_maven, validate_project
from jpkg.core.pom_manager import PomManager
from jpkg.core.maven_runner import MavenRunner
from jpkg.core.maven_api import MavenCentralAPI
from jpkg.core.ai_assistant import AIAssistant

# Page config
st.set_page_config(
    page_title="jpkg - Java Package Manager",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injetar CSS customizado para aparência premium
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Titulo principal */
    .main-title {
        background: linear-gradient(135deg, #FF5E3A 0%, #FF2A6D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #888888;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Card de dependência premium */
    .dependency-card {
        border-radius: 12px;
        border: 1px solid #303030;
        background-color: #1a1a1a;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    
    .dependency-card:hover {
        transform: translateY(-2px);
        border-color: #FF2A6D;
        box-shadow: 0 4px 20px rgba(255, 42, 109, 0.15);
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .badge-ok {
        background-color: rgba(46, 204, 113, 0.15);
        color: #2ecc71;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }
    
    .badge-error {
        background-color: rgba(231, 76, 60, 0.15);
        color: #e74c3c;
        border: 1px solid rgba(231, 76, 60, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Pegar o caminho do projeto da variável de ambiente ou do diretório atual
if "project_path" not in st.session_state:
    st.session_state.project_path = os.environ.get("JPKG_PROJECT_PATH", os.path.abspath("."))

# Inicializar os objetos do Core se não estiverem no session_state
if "env_java" not in st.session_state:
    st.session_state.env_java = detect_java()
if "env_maven" not in st.session_state:
    st.session_state.env_maven = detect_maven(st.session_state.project_path)
if "env_project" not in st.session_state:
    st.session_state.env_project = validate_project(st.session_state.project_path)

if "pom_manager" not in st.session_state and st.session_state.env_project["valid"]:
    st.session_state.pom_manager = PomManager(st.session_state.env_project["pom_path"])
    
if "maven_runner" not in st.session_state:
    st.session_state.maven_runner = MavenRunner(st.session_state.project_path)
if "maven_api" not in st.session_state:
    st.session_state.maven_api = MavenCentralAPI()
if "ai_assistant" not in st.session_state:
    st.session_state.ai_assistant = AIAssistant()

# Detectar os modelos instalados no Ollama
if "ai_assistant" in st.session_state and not hasattr(st.session_state.ai_assistant, "available_models"):
    st.session_state.ai_assistant = AIAssistant()

if "available_models" not in st.session_state:
    st.session_state.available_models = []
    if st.session_state.ai_assistant.is_available():
        st.session_state.available_models = getattr(st.session_state.ai_assistant, "available_models", [])

# Desenhar a barra lateral (Sidebar) com as configurações de modelo de IA
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    if st.session_state.env_project["valid"]:
        project_info = st.session_state.pom_manager.get_project_info()
        st.caption(f"Projeto: **{project_info['artifactId']}**")
        st.caption(f"Grupo: `{project_info['groupId']}`")
        st.caption(f"Caminho: `{os.path.basename(st.session_state.project_path)}`")
    
    st.divider()
    
    # Seletor de modelo IA
    if st.session_state.available_models:
        models_list = st.session_state.available_models
        
        # Tentar achar o melhor default na inicialização
        if "selected_model" not in st.session_state:
            # Se tiver Gemma, prefere gemma4 por ter funcionado melhor e não estourar RAM
            gemma_models = [m for m in models_list if "gemma" in m.lower()]
            if gemma_models:
                st.session_state.selected_model = f"ollama/{gemma_models[0]}"
            else:
                st.session_state.selected_model = f"ollama/{models_list[0]}"
                
        clean_selected = st.session_state.selected_model.replace("ollama/", "")
        if clean_selected not in models_list:
            models_list = [clean_selected] + models_list
            
        selected = st.selectbox(
            "🤖 Modelo Ollama",
            options=models_list,
            index=models_list.index(clean_selected) if clean_selected in models_list else 0
        )
        st.session_state.selected_model = f"ollama/{selected}"
        st.session_state.ai_assistant.model = st.session_state.selected_model
    else:
        st.caption("🤖 Assistente de IA Offline")

# Logs globais de build na interface
if "build_logs" not in st.session_state:
    st.session_state.build_logs = []

# Resolver o caminho das páginas dinamicamente
current_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = os.path.join(current_dir, "ui", "pages")

home_page = st.Page(os.path.join(pages_dir, "home.py"), title="Visão Geral", icon="📊", default=True)
search_page = st.Page(os.path.join(pages_dir, "search.py"), title="Buscar Pacotes", icon="🔍")
deps_page = st.Page(os.path.join(pages_dir, "dependencies.py"), title="Dependências", icon="📦")
logs_page = st.Page(os.path.join(pages_dir, "logs.py"), title="Logs de Build", icon="📜")

pg = st.navigation({
    "Navegação": [home_page, search_page, deps_page, logs_page]
})

pg.run()
