import streamlit as st
import os
from jpkg.core.pom_manager import PomManager

st.markdown('<div class="main-title">📦 Dependências Instaladas</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Gerencie as dependências diretas configuradas no seu arquivo pom.xml</div>', unsafe_allow_html=True)

if not st.session_state.env_project["valid"]:
    st.warning("Carregue um projeto Maven válido na página inicial antes de gerenciar dependências.")
else:
    pom_manager = st.session_state.pom_manager
    maven_api = st.session_state.maven_api
    maven_runner = st.session_state.maven_runner
    ai_assistant = st.session_state.ai_assistant
    
    # Obter dependências atuais
    dependencies = pom_manager.get_dependencies()

    # Função para remover dependência
    def delete_dependency(group_id: str, artifact_id: str):
        st.info(f"Removendo `{group_id}:{artifact_id}`...")
        backup_path = pom_manager.backup()
        
        try:
            success = pom_manager.remove_dependency(group_id, artifact_id)
            if success:
                pom_manager.save()
                st.success("Dependência removida do pom.xml! Sincronizando com o Maven...")
                
                st.session_state.build_logs = []
                def log_callback(line):
                    st.session_state.build_logs.append(line)
                    
                with st.spinner("Atualizando repositório local..."):
                    res = maven_runner.compile(callback=log_callback)
                    
                if res["success"]:
                    st.success("Projeto sincronizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Falha ao compilar após a remoção. Restaurando backup...")
                    import shutil
                    shutil.copy2(backup_path, pom_manager.pom_path)
                    st.session_state.pom_manager = PomManager(pom_manager.pom_path)
                    st.rerun()
            else:
                st.error("Não foi possível localizar a dependência para remoção.")
        except Exception as e:
            st.error(f"Erro ao remover dependência: {str(e)}")

    # Função para atualizar versão de dependência
    def change_version(group_id: str, artifact_id: str, new_version: str):
        st.info(f"Atualizando `{group_id}:{artifact_id}` para `{new_version}`...")
        backup_path = pom_manager.backup()
        
        try:
            success = pom_manager.update_version(group_id, artifact_id, new_version)
            if success:
                pom_manager.save()
                st.success("Versão atualizada no pom.xml! Validando build...")
                
                st.session_state.build_logs = []
                def log_callback(line):
                    st.session_state.build_logs.append(line)
                    
                with st.spinner("Rodando mvn compile..."):
                    res = maven_runner.compile(callback=log_callback)
                    
                if res["success"]:
                    st.success("Versão atualizada com sucesso! 🎉")
                    st.rerun()
                else:
                    st.error("Nova versão causou falha de compilação. Restaurando versão anterior...")
                    import shutil
                    shutil.copy2(backup_path, pom_manager.pom_path)
                    st.session_state.pom_manager = PomManager(pom_manager.pom_path)
                    st.rerun()
        except Exception as e:
            st.error(f"Erro ao alterar versão: {str(e)}")

    # IA análise de dependências
    if ai_assistant.is_available() and dependencies:
        if st.button("🤖 Analisar Projeto com IA (Revisão de Arquitetura)", use_container_width=True):
            with st.spinner("Analisando conjunto de dependências com Ollama local..."):
                analysis = ai_assistant.analyze_dependencies(dependencies)
                st.markdown("### 🤖 Recomendações e Análise da IA:")
                st.info(analysis)
        st.divider()

    if not dependencies:
        st.info("Nenhuma dependência direta encontrada no seu arquivo pom.xml.")
    else:
        st.markdown(f"**Dependências Diretas ({len(dependencies)}):**")
        
        for i, dep in enumerate(dependencies):
            with st.container(border=True):
                col_name, col_ver, col_scope, col_act = st.columns([3, 2, 1, 1])
                
                with col_name:
                    st.markdown(f"##### **{dep['artifactId']}**")
                    st.caption(f"Grupo: `{dep['groupId']}`")
                    
                with col_ver:
                    # Obter todas as versões disponíveis para permitir upgrade/downgrade
                    versions = maven_api.get_versions(dep["groupId"], dep["artifactId"])
                    current_ver = dep["version"]
                    
                    if current_ver:
                        # Identificar se há atualização disponível
                        latest_ver = versions[0] if versions else current_ver
                        if latest_ver != current_ver:
                            st.caption(f"Atualização disponível: `{latest_ver}` ⬆️")
                        else:
                            st.caption("Última versão instalada ✅")
                            
                        # Selectbox pré-selecionado na versão atual
                        if current_ver not in versions:
                            versions = [current_ver] + versions
                            
                        selected_ver = st.selectbox(
                            "Versão Atual",
                            options=versions,
                            index=versions.index(current_ver),
                            key=f"dep_ver_{i}",
                            label_visibility="collapsed"
                        )
                        
                        if selected_ver != current_ver:
                            if st.button("Atualizar", key=f"up_btn_{i}", type="secondary", use_container_width=True):
                                change_version(dep["groupId"], dep["artifactId"], selected_ver)
                    else:
                        st.caption("Versão gerenciada pelo Parent/Properties ℹ️")
                        
                with col_scope:
                    st.markdown(f"**Escopo**")
                    st.caption(dep["scope"])
                    
                with col_act:
                    st.markdown("**Remover**")
                    if st.button("🗑️", key=f"del_btn_{i}", type="secondary", use_container_width=True):
                        delete_dependency(dep["groupId"], dep["artifactId"])
