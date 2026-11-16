"""Punto de entrada de la aplicación Streamlit.  Ejecutar:  streamlit run app.py"""
import streamlit as st

import config
from interfaz import estilo

st.set_page_config(page_title=config.TITULO_CORTO, page_icon=":material/show_chart:", layout="wide",
                   initial_sidebar_state="expanded")
estilo.inyectar_css()

PAGINAS = [
    st.Page("pages/1_Datos.py", title="Datos", icon=":material/table_chart:", default=True),
    st.Page("pages/2_Modelo.py", title="Modelo y fórmulas", icon=":material/function:"),
    st.Page("pages/3_Ajuste.py", title="Ajuste", icon=":material/show_chart:"),
    st.Page("pages/4_Geometria.py", title="Geometría", icon=":material/3d_rotation:"),
    st.Page("pages/5_Hessiano.py", title="Hessiano", icon=":material/grid_on:"),
    st.Page("pages/6_Comparacion.py", title="Comparación", icon=":material/compare_arrows:"),
    st.Page("pages/7_Calidad.py", title="Calidad y residuos", icon=":material/analytics:"),
    st.Page("pages/8_Adicional.py", title="Análisis adicional", icon=":material/science:"),
    st.Page("pages/9_Exportar.py", title="Exportar", icon=":material/download:"),
]

with st.sidebar:
    st.markdown(f'<div class="titulo-lateral">{config.TITULO_PROYECTO}</div>'
                f'<div class="sub-lateral">{config.CURSO} · {config.PERIODO}<br/>{config.UNIVERSIDAD}<br/>{config.ESTUDIANTE}</div>',
                unsafe_allow_html=True)
    st.divider()
    for pagina in PAGINAS:
        st.page_link(pagina)
    st.divider()
    esc = st.session_state.get("escala_activa", True)
    st.caption("Escala de x: " + ("10⁵ elementos" if esc else "elementos (sin escalar)")
               + "  \nSe cambia en la página *Datos*.")

st.navigation(PAGINAS, position="hidden").run()
