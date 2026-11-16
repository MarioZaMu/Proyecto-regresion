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
        "texto": "#1E1B4B", "grid": "rgba(100,116,139,0.22)", "fondo": "rgba(0,0,0,0)",
        "escala": [[0, "#06B6D4"], [0.5, "#6366F1"], [1, "#EC4899"]],
    },
    "oscuro": {
        "primario": "#818CF8", "secundario": "#FB923C", "acento": "#F472B6", "neutro": "#94A3B8",
        "texto": "#E2E8F0", "grid": "rgba(148,163,184,0.25)", "fondo": "rgba(0,0,0,0)",
        "escala": [[0, "#22D3EE"], [0.5, "#818CF8"], [1, "#F472B6"]],
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
        paper_bgcolor=p["fondo"] if tema is None else ("white" if tema == "claro" else "#0B1020"),
        plot_bgcolor=p["fondo"] if tema is None else ("white" if tema == "claro" else "#0B1020"),
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
  :root {--c1:#4F46E5; --c2:#06B6D4; --c3:#EC4899; --c4:#F97316;}
  @keyframes subir {from {opacity:0; transform:translateY(16px);} to {opacity:1; transform:none;}}
  @keyframes aparecer {from {opacity:0;} to {opacity:1;}}
  @keyframes brillo {from {background-position:0% 50%;} to {background-position:200% 50%;}}
  @keyframes pulso {0%,100% {box-shadow:0 0 0 0 rgba(236,72,153,0);} 50% {box-shadow:0 0 0 7px rgba(236,72,153,.16);}}

  .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px;}
  [data-testid="stMainBlockContainer"] {animation: subir .55s cubic-bezier(.2,.7,.2,1) both;}

  /* Títulos con degradado animado */
  h1 {font-size: 2rem !important; font-weight: 750 !important; letter-spacing: -.02em;
      background: linear-gradient(90deg, var(--c1), var(--c2), var(--c3), var(--c1)); background-size: 200% auto;
      -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; animation: brillo 7s linear infinite;}
  h2 {font-size: 1.3rem !important; font-weight: 650 !important; margin-top: 1.4rem; padding-left: .7rem;
      border-left: 4px solid var(--c1); border-image: linear-gradient(var(--c1), var(--c3)) 1;}
  h3 {font-size: 1.1rem !important; font-weight: 600 !important;}
  .encabezado {opacity: .78; font-size: .9rem; margin: -.4rem 0 1rem 0; padding-bottom: .7rem; position: relative;}
  .encabezado::after {content:""; position:absolute; left:0; bottom:0; height:3px; width:100%; border-radius:3px;
      background: linear-gradient(90deg, var(--c1), var(--c2), var(--c3), var(--c4), var(--c1)); background-size: 300% auto; animation: brillo 8s linear infinite;}

  /* Tarjetas de métricas */
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] [data-testid="stMetric"]) {
      border: 1px solid rgba(99,102,241,.35) !important; border-top: 4px solid var(--c1) !important; border-radius: 14px !important;
      background: linear-gradient(160deg, rgba(99,102,241,.13), rgba(6,182,212,.07) 60%, rgba(236,72,153,.06));
      transition: transform .28s cubic-bezier(.2,.7,.2,1), box-shadow .28s, border-color .28s; animation: subir .6s cubic-bezier(.2,.7,.2,1) both;}
  [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] [data-testid="stMetric"]):hover {
      transform: translateY(-5px) scale(1.015); box-shadow: 0 14px 28px -10px rgba(79,70,229,.55); border-color: var(--c3) !important;}
  [data-testid="stColumn"]:nth-child(2) > div > div > div > [data-testid="stVerticalBlock"] {animation-delay: .07s;}
  [data-testid="stColumn"]:nth-child(3) [data-testid="stVerticalBlock"] {animation-delay: .14s;}
  [data-testid="stColumn"]:nth-child(4) [data-testid="stVerticalBlock"] {animation-delay: .21s;}
  [data-testid="stColumn"]:nth-child(5) [data-testid="stVerticalBlock"] {animation-delay: .28s;}
  [data-testid="stMetricValue"] {font-size: 1.3rem; font-weight: 700;}
  [data-testid="stMetricValue"] > div {background: linear-gradient(90deg, var(--c1), var(--c3)); -webkit-background-clip: text; background-clip: text;
      -webkit-text-fill-color: transparent; white-space: normal !important; overflow: visible !important; text-overflow: clip !important; word-break: break-all;}
  [data-testid="stMetricLabel"] p {font-size: .82rem; opacity: .8; white-space: normal !important; overflow: visible !important; text-overflow: clip !important;}

  /* Gráficas, tablas y avisos */
  [data-testid="stPlotlyChart"] {animation: aparecer .9s ease both; border-radius: 14px;}
  [data-testid="stDataFrame"] {border-radius: 12px; overflow: hidden; animation: aparecer .7s ease both;}
  [data-testid="stAlert"] {border-radius: 12px; animation: subir .5s ease both;}
  [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {animation: subir .5s ease both, pulso 2.6s ease-in-out 1s infinite;}
  [data-testid="stExpander"] {border-radius: 12px; transition: box-shadow .25s;}
  [data-testid="stExpander"]:hover {box-shadow: 0 6px 18px -8px rgba(79,70,229,.45);}
  .stTabs [data-baseweb="tab"] {transition: color .2s, transform .2s;}
  .stTabs [data-baseweb="tab"]:hover {transform: translateY(-2px);}
  .stTabs [data-baseweb="tab-highlight"] {background: linear-gradient(90deg, var(--c1), var(--c3)) !important; height: 3px;}

  /* Botones */
  .stButton > button, .stDownloadButton > button {border-radius: 12px; font-weight: 600; transition: transform .2s, box-shadow .2s;}
  .stButton > button[kind="primary"] {background: linear-gradient(90deg, var(--c1), var(--c3)); border: 0; color: white;}
  .stButton > button:hover, .stDownloadButton > button:hover {transform: translateY(-3px); box-shadow: 0 10px 20px -8px rgba(79,70,229,.6);}

  /* Barra lateral */
  [data-testid="stSidebar"] {background-image: linear-gradient(180deg, rgba(79,70,229,.14), rgba(6,182,212,.06) 55%, rgba(236,72,153,.10));}
  [data-testid="stPageLink-NavLink"] {border-radius: 10px; transition: transform .2s, background .2s;}
  [data-testid="stPageLink-NavLink"]:hover {transform: translateX(6px); background: rgba(99,102,241,.18);}
  [data-testid="stPageLink-NavLink"][aria-current="page"] {background: linear-gradient(90deg, rgba(79,70,229,.32), rgba(236,72,153,.18)); box-shadow: inset 3px 0 0 var(--c3);}
  .titulo-lateral {font-weight: 750; font-size: 1.05rem; line-height: 1.3; margin-bottom: .15rem;
      background: linear-gradient(90deg, var(--c1), var(--c2), var(--c3)); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;}
  .sub-lateral {opacity: .75; font-size: .8rem; margin-bottom: .6rem;}
  .pie-grafica {opacity: .9; font-size: .93rem; line-height: 1.55;}

  @media (prefers-reduced-motion: reduce) {* {animation: none !important; transition: none !important;}}
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
