import streamlit as st
import os

st.markdown('<div class="main-title">☕ jpkg — Java Package Manager</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Visão geral do ambiente de desenvolvimento e do projeto Java</div>', unsafe_allow_html=True)

# 1. Painel de status em colunas
col1, col2, col3, col4 = st.columns(4)

with col1:
    java = st.session_state.env_java
    if java["found"]:
        st.metric("Java SDK", f"JDK {java['version']}", "Disponível", delta_color="normal")
        st.markdown('<span class="status-badge badge-ok">✓ Java OK</span>', unsafe_allow_html=True)
    else:
        st.metric("Java SDK", "Não encontrado", "Erro", delta_color="inverse")
        st.markdown('<span class="status-badge badge-error">✗ Java Ausente</span>', unsafe_allow_html=True)

with col2:
    maven = st.session_state.env_maven
    if maven["found"]:
        st.metric("Maven CLI", f"v{maven['version']}", "Disponível", delta_color="normal")
        st.markdown('<span class="status-badge badge-ok">✓ Maven OK</span>', unsafe_allow_html=True)
    else:
        st.metric("Maven CLI", "Não encontrado", "Erro", delta_color="inverse")
        st.markdown('<span class="status-badge badge-error">✗ Maven Ausente</span>', unsafe_allow_html=True)

with col3:
    project = st.session_state.env_project
    if project["valid"]:
        st.metric("pom.xml", "Válido", "Projeto Java", delta_color="normal")
        st.markdown('<span class="status-badge badge-ok">✓ pom.xml OK</span>', unsafe_allow_html=True)
    else:
        st.metric("pom.xml", "Inválido", "Erro", delta_color="inverse")
        st.markdown('<span class="status-badge badge-error">✗ pom.xml Inválido</span>', unsafe_allow_html=True)

with col4:
    ai = st.session_state.ai_assistant
    if ai.is_available():
        st.metric("Assistente de IA", ai.model.split("/")[-1], "Ollama Local", delta_color="normal")
        st.markdown('<span class="status-badge badge-ok">✓ IA Ativa</span>', unsafe_allow_html=True)
    else:
        st.metric("Assistente de IA", "Offline", "Sem IA", delta_color="off")
        st.markdown('<span class="status-badge badge-error">✗ IA Indisponível</span>', unsafe_allow_html=True)

st.divider()

# 2. Informações detalhadas do projeto
if st.session_state.env_project["valid"]:
    pom_manager = st.session_state.pom_manager
    project_info = pom_manager.get_project_info()
    deps = pom_manager.get_dependencies()
    
    st.markdown("### 📋 Informações do Projeto")
    
    with st.container(border=True):
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.markdown(f"**Group ID:** `{project_info['groupId']}`")
            st.markdown(f"**Artifact ID:** `{project_info['artifactId']}`")
            st.markdown(f"**Versão:** `{project_info['version']}`")
        with p_col2:
            st.markdown(f"**Caminho do pom.xml:** `{st.session_state.env_project['pom_path']}`")
            st.markdown(f"**Total de Dependências Diretas:** `{len(deps)}`")
            
    # Bloco de ações rápidas
    st.markdown("### ⚡ Ações Rápidas")
    
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button("🔧 Compilar Projeto (mvn compile)", use_container_width=True):
            with st.spinner("Compilando projeto Maven..."):
                runner = st.session_state.maven_runner
                # Limpar logs anteriores
                st.session_state.build_logs = []
                
                def log_callback(line):
                    st.session_state.build_logs.append(line)
                    
                res = runner.compile(callback=log_callback)
                if res["success"]:
                    st.success("Compilação concluída com sucesso! ✅")
                else:
                    st.error(f"Falha na compilação. {res['error_msg']}")
                    if res["suggestion"]:
                        st.info(f"💡 Sugestão: {res['suggestion']}")
            # Redirecionar para logs
            st.info("Consulte os logs detalhados na aba 'Logs de Build'.")
            
    with act_col2:
        if st.button("📦 Instalar Projeto (mvn install)", use_container_width=True):
            with st.spinner("Executando mvn clean install..."):
                runner = st.session_state.maven_runner
                st.session_state.build_logs = []
                
                def log_callback(line):
                    st.session_state.build_logs.append(line)
                    
                res = runner.install(callback=log_callback)
                if res["success"]:
                    st.success("Projeto empacotado e instalado com sucesso! ✅")
                else:
                    st.error(f"Falha no build. {res['error_msg']}")
                    if res["suggestion"]:
                        st.info(f"💡 Sugestão: {res['suggestion']}")
            st.info("Consulte os logs detalhados na aba 'Logs de Build'.")

else:
    # Exibir detalhes do erro do projeto
    st.error("O projeto atual não pôde ser validado como um projeto Maven.")
    st.info(f"**Detalhes da falha:** {st.session_state.env_project['error']}")
    st.warning("Certifique-se de que a pasta aponta para um projeto Java que contém um arquivo `pom.xml` válido.")
