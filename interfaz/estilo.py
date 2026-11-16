"""Estilo visual común: paleta, plantilla Plotly, tarjetas y utilidades de formato."""
from __future__ import annotations

import re

import plotly.graph_objects as go
import streamlit as st

import config

# Paleta por tema (mismos tres colores semánticos + neutro)
PALETAS = {
    "claro": {
        "primario": config.COLOR_PRIMARIO, "secundario": config.COLOR_SECUNDARIO,
        "acento": config.COLOR_ACENTO, "neutro": config.COLOR_NEUTRO,
        "texto": "#1F2937", "grid": "rgba(107,114,128,0.22)", "fondo": "rgba(0,0,0,0)",
        "escala": [[0, "#EAF1FB"], [0.5, "#7FA8E3"], [1, "#1F5FBF"]],
    },
    "oscuro": {
        "primario": "#5B9BF0", "secundario": "#F2A03D", "acento": "#EF6B5B", "neutro": "#9CA3AF",
        "texto": "#E5E7EB", "grid": "rgba(156,163,175,0.25)", "fondo": "rgba(0,0,0,0)",
        "escala": [[0, "#14284A"], [0.5, "#2F63B0"], [1, "#9CC2F7"]],
    },
}


def tema_actual() -> str:
    """'claro' u 'oscuro' según el tema activo de Streamlit (claro si no se puede saber)."""
    try:
        return "oscuro" if st.context.theme.type == "dark" else "claro"
    except Exception:
        return "claro"


def paleta(tema: str | None = None) -> dict:
    """Paleta de colores para el tema indicado."""
    return PALETAS[tema or tema_actual()]


def aplicar(fig: go.Figure, titulo: str, xt: str, yt: str, tema: str | None = None,
            altura: int = 460, leyenda: bool = True) -> go.Figure:
    """Aplica el estilo Plotly común (título, ejes con unidades, leyenda, tipografía, cuadrícula)."""
    p = paleta(tema)
    fig.update_layout(
        title=dict(text=titulo, x=0.0, xanchor="left", font=dict(size=16, color=p["texto"])),
        template="plotly_white" if (tema or tema_actual()) == "claro" else "plotly_dark",
        paper_bgcolor=p["fondo"] if tema is None else ("white" if tema == "claro" else "#0E1117"),
        plot_bgcolor=p["fondo"] if tema is None else ("white" if tema == "claro" else "#0E1117"),
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=13, color=p["texto"]),
        height=altura, margin=dict(l=60, r=24, t=64, b=56),
        showlegend=leyenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=12)),
        colorway=[p["primario"], p["secundario"], p["acento"], p["neutro"]],
    )
    fig.update_xaxes(title_text=xt, gridcolor=p["grid"], zerolinecolor=p["grid"], linecolor=p["neutro"])
    fig.update_yaxes(title_text=yt, gridcolor=p["grid"], zerolinecolor=p["grid"], linecolor=p["neutro"])
    return fig


def mostrar(fig: go.Figure, clave: str | None = None) -> None:
    """Muestra una figura Plotly con el estilo del programa."""
    st.plotly_chart(fig, width="stretch", theme=None, key=clave,
                    config={"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}})


# ----------------------------------------------------------------- formato numérico
def fmt(v: float, cifras: int | None = None) -> str:
    """Formato con cifras significativas consistentes."""
    if v is None or v != v:
        return "—"
    return f"{v:.{cifras or config.CIFRAS}g}"


def latex_num(v: float, cifras: int | None = None) -> str:
    """Número en LaTeX (notación científica como ×10^k cuando corresponde)."""
    s = fmt(v, cifras)
    m = re.fullmatch(r"(-?[\d.]+)e([+-])(\d+)", s)
    if not m:
        return s
    mant, signo, exp = m.groups()
    return f"{mant}\\times 10^{{{'-' if signo == '-' else ''}{int(exp)}}}"


def matriz_latex(m, cifras: int = 6) -> str:
    """Matriz 2×2 en LaTeX."""
    return (r"\begin{pmatrix}" + f"{latex_num(m[0][0], cifras)} & {latex_num(m[0][1], cifras)} \\\\ "
            f"{latex_num(m[1][0], cifras)} & {latex_num(m[1][1], cifras)}" + r"\end{pmatrix}")


# ----------------------------------------------------------------- CSS y componentes
CSS = """
<style>
  .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px;}
  [data-testid="stMetricValue"] {font-size: 1.25rem; font-weight: 600;}
  [data-testid="stMetricValue"] > div, [data-testid="stMetricLabel"] p {white-space: normal !important; overflow: visible !important; text-overflow: clip !important; word-break: break-all;}
  [data-testid="stMetricLabel"] p {font-size: .82rem; opacity: .75;}
  h1 {font-size: 1.8rem !important; font-weight: 650 !important; letter-spacing: -.01em;}
  h2 {font-size: 1.3rem !important; font-weight: 600 !important; margin-top: 1.2rem;}
  h3 {font-size: 1.1rem !important; font-weight: 600 !important;}
  .encabezado {opacity: .72; font-size: .9rem; margin: -.4rem 0 1rem 0;}
  .pie-grafica {opacity: .85; font-size: .93rem; margin: -.2rem 0 1.4rem 0; line-height: 1.55;}
  .titulo-lateral {font-weight: 650; font-size: 1.05rem; line-height: 1.3; margin-bottom: .15rem;}
  .sub-lateral {opacity: .7; font-size: .8rem; margin-bottom: .6rem;}
</style>
"""


def inyectar_css() -> None:
    """Inserta el CSS global."""
    st.markdown(CSS, unsafe_allow_html=True)


def pie(texto: str) -> None:
    """Texto explicativo bajo una gráfica."""
    with st.container():
        st.markdown(texto)
        st.write("")


# ----------------------------------------------------------------- estado persistente
def persistente(widget, etiqueta: str, clave: str, defecto, **kw):
    """Crea un widget cuyo valor sobrevive al cambio de página.

    Streamlit borra el estado de un widget cuando deja de dibujarse; aquí el valor
    "canónico" vive en ``session_state[clave]`` y el widget solo lo refleja.
    """
    ss = st.session_state
    if clave not in ss:
        ss[clave] = defecto
    wk = f"w_{clave}"

    def _guardar() -> None:
        ss[clave] = ss[wk]

    if widget in (st.selectbox, st.radio):
        opciones = list(kw["options"])
        if ss[clave] not in opciones:
            ss[clave] = defecto
        kw["index"] = opciones.index(ss[clave])
    else:
        kw["value"] = ss[clave]
    widget(etiqueta, key=wk, on_change=_guardar, **kw)
    return ss[clave]
