import streamlit as st

st.markdown('<div class="main-title">📜 Logs de Build</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Console de logs do Maven em tempo real</div>', unsafe_allow_html=True)

if not st.session_state.build_logs:
    st.info("Nenhum comando Maven foi executado ou gerou logs nesta sessão.")
else:
    # Botão para limpar console
    if st.button("Limpar Histórico de Logs"):
        st.session_state.build_logs = []
        st.rerun()
        
    # Agrupar logs em string única e renderizar
    logs_text = "".join(st.session_state.build_logs)
    
    st.markdown("### 🖥️ Saída do Terminal:")
    st.code(logs_text, language="bash")
