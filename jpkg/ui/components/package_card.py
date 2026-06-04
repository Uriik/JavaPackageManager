import streamlit as st
from typing import Callable, List

def render_package_card(package: dict, versions: List[str], on_install: Callable[[dict, str], None], card_key: str):
    """
    Renderiza um card premium contendo as informações do pacote do Maven Central,
    um seletor de versão e um botão de ação para instalação.
    """
    # Usar st.container(border=True) para criar o visual do card
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Título em negrito e destaque para o nome do artefato
            st.markdown(f"#### **{package['artifactId']}**")
            st.markdown(f"`{package['groupId']}`")
            
            # Se a IA sugeriu este pacote, exibir a justificativa inteligente
            if "reason" in package and package["reason"]:
                st.markdown(f"💡 *{package['reason']}*")
                
        with col2:
            if versions:
                # Caixa de seleção da versão (ordem das mais recentes no topo)
                selected_version = st.selectbox(
                    "Selecione a Versão",
                    options=versions,
                    key=f"select_ver_{card_key}",
                    label_visibility="collapsed"
                )
                
                # Botão de instalar estilizado como principal
                if st.button("Instalar", key=f"btn_install_{card_key}", type="primary", use_container_width=True):
                    on_install(package, selected_version)
            else:
                st.caption("Carregando versões...")
