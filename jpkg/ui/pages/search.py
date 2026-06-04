import streamlit as st
from jpkg.ui.components.package_card import render_package_card

st.markdown('<div class="main-title">🔍 Buscar Pacotes</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Pesquise bibliotecas no Maven Central ou obtenha recomendações inteligentes do Assistente de IA</div>', unsafe_allow_html=True)

if not st.session_state.env_project["valid"]:
    st.warning("Carregue um projeto Maven válido na página inicial antes de gerenciar dependências.")
else:
    pom_manager = st.session_state.pom_manager
    maven_api = st.session_state.maven_api
    maven_runner = st.session_state.maven_runner
    ai_assistant = st.session_state.ai_assistant

    # Função de callback ao clicar em Instalar
    def install_package(package: dict, version: str):
        st.info(f"Iniciando instalação de `{package['groupId']}:{package['artifactId']}:{version}`...")
        
        # 1. Fazer backup antes de qualquer alteração
        backup_path = pom_manager.backup()
        st.caption(f"Backup do pom.xml criado em: `{os.path.basename(backup_path)}`")
        
        # 2. Adicionar no pom.xml
        try:
            pom_manager.add_dependency(package["groupId"], package["artifactId"], version)
            pom_manager.save()
            st.success("Dependência adicionada ao pom.xml! Iniciando download...")
            
            # 3. Rodar mvn compile para baixar a dependência
            st.session_state.build_logs = []
            def log_callback(line):
                st.session_state.build_logs.append(line)
                
            with st.spinner("Baixando pacote e validando o build com o Maven..."):
                res = maven_runner.compile(callback=log_callback)
                
            if res["success"]:
                st.success(f"Pacote `{package['artifactId']}` instalado com sucesso! 🎉")
            else:
                st.error("Falha ao compilar o projeto após adicionar a dependência.")
                st.info(f"**Erro:** {res['error_msg']}")
                
                # Explicar erro usando IA se disponível
                if ai_assistant.is_available():
                    with st.spinner("Analisando erro de build com a IA..."):
                        analysis = ai_assistant.explain_error(res["output"])
                        st.markdown("### 🤖 Análise da IA sobre a Falha:")
                        st.info(analysis)
                
                # Oferecer Rollback automático
                if st.button("Restaurar pom.xml anterior (Desfazer)", key=f"rollback_{package['artifactId']}_{version}"):
                    # Sobrescrever pom.xml com o backup
                    import shutil
                    shutil.copy2(backup_path, pom_manager.pom_path)
                    # Recarregar
                    st.session_state.pom_manager = PomManager(pom_manager.pom_path)
                    st.warning("Alteração desfeita. pom.xml restaurado com sucesso.")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Erro inesperado durante a instalação: {str(e)}")

    # Criar abas para Busca Tradicional vs IA
    tab_search, tab_ai = st.tabs(["🔍 Busca Maven Central", "🤖 Sugestões de IA (Ollama)"])
    
    with tab_search:
        col_search, col_btn = st.columns([4, 1])
        with col_search:
            search_query = st.text_input("Nome da biblioteca, grupo ou funcionalidade", placeholder="ex: jackson-databind ou org.json", label_visibility="collapsed")
        with col_btn:
            btn_search = st.button("Pesquisar", use_container_width=True, type="primary")
            
        if btn_search or search_query:
            if not search_query.strip():
                st.warning("Insira um termo de busca.")
            else:
                with st.spinner("Buscando no Maven Central..."):
                    results = maven_api.search(search_query)
                    
                if not results:
                    st.warning("Nenhum pacote encontrado para o termo especificado.")
                else:
                    st.markdown(f"**Resultados encontrados ({len(results)}):**")
                    for i, pkg in enumerate(results):
                        # Obter versões assincronamente ou sob demanda
                        versions = maven_api.get_versions(pkg["groupId"], pkg["artifactId"])
                        render_package_card(pkg, versions, install_package, f"search_{i}")
                        
    with tab_ai:
        if not ai_assistant.is_available():
            st.info("O Assistente de IA local está offline. Inicie o Ollama com o modelo `qwen3` para usar este recurso.")
        else:
            st.markdown("### Pergunte à IA qual biblioteca usar no seu projeto")
            ai_query = st.text_input("O que você deseja que a biblioteca faça?", placeholder="ex: fazer requisições HTTP assíncronas de forma simples", label_visibility="collapsed")
            btn_ai = st.button("Obter Recomendações", type="primary")
            
            if btn_ai and ai_query:
                with st.spinner("IA consultando sugestões no ecossistema Java..."):
                    suggestions = ai_assistant.suggest_packages(ai_query)
                    
                if not suggestions:
                    st.warning("A IA não conseguiu gerar sugestões válidas. Tente detalhar melhor o seu pedido.")
                else:
                    st.markdown("**Sugestões da IA para o seu projeto:**")
                    for i, pkg in enumerate(suggestions):
                        # Buscar versões dinamicamente no Maven Central usando a sugestão da IA
                        versions = maven_api.get_versions(pkg["groupId"], pkg["artifactId"])
                        render_package_card(pkg, versions, install_package, f"ai_{i}")
