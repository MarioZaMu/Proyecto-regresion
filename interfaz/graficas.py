"""Constructores de figuras Plotly (todas con el mismo estilo). Devuelven ``go.Figure``."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from core import extras, metricas
from core.regresion import error_cuadratico, sumas
from interfaz import estilo
from interfaz.contexto import Ctx


# ----------------------------------------------------------------- utilidades
def region(ctx: Ctx, fraccion: float = 0.05) -> tuple[float, float]:
    """Semiamplitudes (δa, δb) de la región {S ≤ S_mín + fracción·SST} (elipse de nivel).

    Para el paraboloide S = S_mín + δθᵀ (H/2) δθ, las semiamplitudes de la elipse son
    δa = √(L·n/D),  δb = √(L·Σx²/D),  con D = nΣx² − (Σx)² y L = fracción·SST.
    """
    s = sumas(ctx.x, ctx.y)
    d = s.n * s.sxx - s.sx ** 2
    nivel = fraccion * ctx.sst
    return float(np.sqrt(nivel * s.n / d)), float(np.sqrt(nivel * s.sxx / d))


def _recta_x(ctx: Ctx) -> np.ndarray:
    return np.linspace(0, 1.05 * ctx.x.max(), 60)


def _bruto(tema: str | None):
    return estilo.paleta(tema)


# ----------------------------------------------------------------- páginas 1 y 3
def dispersion(ctx: Ctx, tema: str | None = None) -> go.Figure:
    """Diagrama de dispersión (x, y)."""
    p = _bruto(tema)
    fig = go.Figure(go.Scatter(x=ctx.x, y=ctx.y, mode="markers", name="Mediciones (mediana)",
                               marker=dict(size=9, color=p["primario"], line=dict(width=1, color="white"))))
    return estilo.aplicar(fig, "Diagrama de dispersión: tiempo de búsqueda lineal vs. tamaño de entrada",
                          ctx.ux, ctx.uy, tema)


def ajuste(ctx: Ctx, rectas: list[tuple[str, float, float]] | None = None, residuos: bool = False,
           tema: str | None = None) -> go.Figure:
    """Datos + recta óptima + rectas alternativas (cada una con su S en la leyenda)."""
    p = _bruto(tema)
    fx = _recta_x(ctx)
    a, b = ctx.ajuste.a, ctx.ajuste.b
    fig = go.Figure(go.Scatter(x=ctx.x, y=ctx.y, mode="markers", name="Datos",
                               marker=dict(size=9, color=p["neutro"], line=dict(width=1, color="white"))))
    if residuos:
        xs, ys = [], []
        for xi, yi in zip(ctx.x, ctx.y):
            xs += [xi, xi, None]
            ys += [yi, a * xi + b, None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name="Residuos eᵢ",
                                 line=dict(color=p["acento"], width=1.5), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=fx, y=a * fx + b, mode="lines", line=dict(color=p["primario"], width=3),
                             name=f"Óptima (a*, b*): S = {estilo.fmt(ctx.ajuste.s_min, 4)}"))
    colores = [p["secundario"], p["acento"], p["neutro"]]
    for i, (nombre, aa, bb) in enumerate(rectas or []):
        s = float(error_cuadratico(aa, bb, ctx.x, ctx.y))
        fig.add_trace(go.Scatter(x=fx, y=aa * fx + bb, mode="lines",
                                 line=dict(color=colores[i % 3], width=2, dash="dash"),
                                 name=f"{nombre}: S = {estilo.fmt(s, 4)}"))
    fig = estilo.aplicar(fig, "Datos observados y rectas de ajuste", ctx.ux, ctx.uy, tema)
    fig.update_xaxes(rangemode="tozero")
    return fig


# ----------------------------------------------------------------- página 4
def _malla(ctx: Ctx, fraccion: float, m: int = 70):
    da, db = region(ctx, fraccion)
    av = np.linspace(ctx.ajuste.a - da, ctx.ajuste.a + da, m)
    bv = np.linspace(ctx.ajuste.b - db, ctx.ajuste.b + db, m)
    A, B = np.meshgrid(av, bv)
    return av, bv, error_cuadratico(A, B, ctx.x, ctx.y)


def superficie(ctx: Ctx, fraccion: float = 0.05, log: bool = False, tema: str | None = None) -> go.Figure:
    """Superficie 3D z = S(a, b) con el mínimo marcado."""
    p = _bruto(tema)
    av, bv, Z = _malla(ctx, fraccion)
    zf = (lambda z: np.log10(z)) if log else (lambda z: z)
    fig = go.Figure(go.Surface(x=av, y=bv, z=zf(Z), colorscale=p["escala"], opacity=0.92,
                               name="S(a, b)", showscale=True,
                               colorbar=dict(title="log₁₀ S (ms²)" if log else "S (ms²)", len=0.7),
                               contours=dict(z=dict(show=True, usecolormap=True, project_z=False))))
    fig.add_trace(go.Scatter3d(x=[ctx.ajuste.a], y=[ctx.ajuste.b], z=[zf(ctx.ajuste.s_min)], mode="markers",
                               name="Mínimo (a*, b*)", marker=dict(size=7, color=p["acento"], symbol="diamond")))
    fig = estilo.aplicar(fig, "Superficie de error S(a, b)", "", "", tema, altura=620)
    fig.update_layout(scene=dict(
        xaxis_title=f"a ({ctx.ua})", yaxis_title="b (ms)",
        zaxis_title="log₁₀ S (ms²)" if log else "S (ms²)",
        aspectmode="manual", aspectratio=dict(x=1.1, y=1.1, z=0.75),
        camera=dict(eye=dict(x=1.7, y=-1.7, z=0.8))), margin=dict(l=0, r=0, t=64, b=0))
    return fig


def contornos(ctx: Ctx, fraccion: float = 0.05, niveles: int = 14, tema: str | None = None) -> go.Figure:
    """Curvas de nivel de S en escala log₁₀ con el mínimo (a*, b*) señalado."""
    p = _bruto(tema)
    av, bv, Z = _malla(ctx, fraccion, 160)
    L = np.log10(Z)
    paso = (L.max() - L.min()) / niveles
    fig = go.Figure(go.Contour(
        x=av, y=bv, z=L, colorscale=p["escala"], ncontours=niveles, name="S(a, b)",
        contours=dict(coloring="lines", showlabels=True, labelfont=dict(size=10), start=L.min() + paso, end=L.max(), size=paso),
        line=dict(width=1.6), colorbar=dict(title="log₁₀ S (ms²)", len=0.8)))
    fig.add_trace(go.Scatter(x=[ctx.ajuste.a], y=[ctx.ajuste.b], mode="markers+text", name="Mínimo (a*, b*)",
                             marker=dict(size=11, color=p["acento"], symbol="x", line=dict(width=2, color=p["acento"])),
                             text=["(a*, b*)"], textposition="top right"))
    fig = estilo.aplicar(fig, "Curvas de nivel de S(a, b)", f"a ({ctx.ua})", "b (ms)", tema, altura=520)
    return fig


def _valores_fijos(centro: float, semi: float, k: int = 5) -> np.ndarray:
    return centro + semi * np.linspace(-1, 1, k)


def trazas(ctx: Ctx, fija: str, fraccion: float = 0.05, tema: str | None = None) -> go.Figure:
    """Trazas de la superficie: cortes con planos b = const (fija='b') o a = const (fija='a')."""
    p = _bruto(tema)
    s = sumas(ctx.x, ctx.y)
    da, db = region(ctx, fraccion)
    a0, b0 = ctx.ajuste.a, ctx.ajuste.b
    colores = [p["neutro"], p["secundario"], p["primario"], p["secundario"], p["neutro"]]
    fig = go.Figure()
    if fija == "b":
        av = np.linspace(a0 - da, a0 + da, 200)
        for k, bk in enumerate(_valores_fijos(b0, db * 0.8)):
            nombre = "b = b*" if k == 2 else f"b = {estilo.fmt(bk, 4)}"
            fig.add_trace(go.Scatter(x=av, y=error_cuadratico(av, bk, ctx.x, ctx.y), mode="lines", name=nombre,
                                     line=dict(color=colores[k], width=3 if k == 2 else 1.8)))
        return estilo.aplicar(fig, "Trazas de S(a, b) con b constante", f"a ({ctx.ua})", "S (ms²)", tema)
    bv = np.linspace(b0 - db, b0 + db, 200)
    for k, ak in enumerate(_valores_fijos(a0, da * 0.8)):
        nombre = "a = a*" if k == 2 else f"a = {estilo.fmt(ak, 4)}"
        fig.add_trace(go.Scatter(x=bv, y=error_cuadratico(ak, bv, ctx.x, ctx.y), mode="lines", name=nombre,
                                 line=dict(color=colores[k], width=3 if k == 2 else 1.8)))
    return estilo.aplicar(fig, "Trazas de S(a, b) con a constante", "b (ms)", "S (ms²)", tema)


def seccion(ctx: Ctx, fija: str, valor: float, fraccion: float = 0.05, tema: str | None = None) -> tuple[go.Figure, float, float]:
    """Sección transversal con una variable fija; devuelve (figura, parámetro óptimo de la sección, S mínima)."""
    p = _bruto(tema)
    s = sumas(ctx.x, ctx.y)
    da, db = region(ctx, fraccion)
    a0, b0 = ctx.ajuste.a, ctx.ajuste.b
    fig = go.Figure()
    if fija == "b":
        v = np.linspace(a0 - da, a0 + da, 300)
        S = error_cuadratico(v, valor, ctx.x, ctx.y)
        opt = (s.sxy - valor * s.sx) / s.sxx              # ∂S/∂a = 0 con b fijo
        smin = float(error_cuadratico(opt, valor, ctx.x, ctx.y))
        fig.add_trace(go.Scatter(x=v, y=S, mode="lines", name=f"S(a, b = {estilo.fmt(valor, 4)})",
                                 line=dict(color=p["primario"], width=3)))
        fig.add_trace(go.Scatter(x=[opt], y=[smin], mode="markers", name="Mínimo de la sección",
                                 marker=dict(size=10, color=p["acento"], symbol="diamond")))
        fig.add_vline(x=a0, line=dict(color=p["neutro"], dash="dot"), annotation_text="a*")
        return estilo.aplicar(fig, "Sección transversal con b fijo", f"a ({ctx.ua})", "S (ms²)", tema), float(opt), smin
    v = np.linspace(b0 - db, b0 + db, 300)
    S = error_cuadratico(valor, v, ctx.x, ctx.y)
    opt = (s.sy - valor * s.sx) / s.n                     # ∂S/∂b = 0 con a fijo
    smin = float(error_cuadratico(valor, opt, ctx.x, ctx.y))
    fig.add_trace(go.Scatter(x=v, y=S, mode="lines", name=f"S(a = {estilo.fmt(valor, 4)}, b)",
                             line=dict(color=p["primario"], width=3)))
    fig.add_trace(go.Scatter(x=[opt], y=[smin], mode="markers", name="Mínimo de la sección",
                             marker=dict(size=10, color=p["acento"], symbol="diamond")))
    fig.add_vline(x=b0, line=dict(color=p["neutro"], dash="dot"), annotation_text="b*")
    return estilo.aplicar(fig, "Sección transversal con a fijo", "b (ms)", "S (ms²)", tema), float(opt), smin


# ----------------------------------------------------------------- página 7
def residuos(ctx: Ctx, tema: str | None = None) -> go.Figure:
    """Residuos eᵢ en función de xᵢ con banda ±2s y atípicos resaltados."""
    p = _bruto(tema)
    t = metricas.tabla_puntos(ctx.ajuste.a, ctx.ajuste.b, ctx.x, ctx.y)
    s = ctx.calidad.desv_residuos
    fig = go.Figure()
    fig.add_hrect(y0=-2 * s, y1=2 * s, fillcolor=p["neutro"], opacity=0.12, line_width=0,
                  annotation_text="±2s", annotation_position="top left")
    fig.add_hline(y=0, line=dict(color=p["neutro"], width=1.5))
    normal = t[~t["atipico"]]
    fig.add_trace(go.Scatter(x=normal["x"], y=normal["residuo"], mode="markers+lines", name="Residuo eᵢ",
                             marker=dict(size=9, color=p["primario"]), line=dict(color=p["primario"], width=1, dash="dot")))
    if t["atipico"].any():
        at = t[t["atipico"]]
        fig.add_trace(go.Scatter(x=at["x"], y=at["residuo"], mode="markers", name="Atípico (|t| > 2)",
                                 marker=dict(size=12, color=p["acento"], symbol="diamond")))
    return estilo.aplicar(fig, "Residuos eᵢ en función de xᵢ", ctx.ux, "eᵢ = yᵢ − (a*xᵢ + b*)  (ms)", tema)


def histograma(ctx: Ctx, bins: int = 8, tema: str | None = None) -> go.Figure:
    """Histograma de residuos."""
    p = _bruto(tema)
    e = metricas.residuos(ctx.ajuste.a, ctx.ajuste.b, ctx.x, ctx.y)
    fig = go.Figure(go.Histogram(x=e, nbinsx=bins, name="Residuos", marker=dict(color=p["primario"], line=dict(width=1, color="white"))))
    fig.add_vline(x=0, line=dict(color=p["acento"], dash="dash"), annotation_text="e = 0")
    return estilo.aplicar(fig, "Histograma de residuos", "eᵢ (ms)", "Frecuencia (n.º de puntos)", tema, leyenda=False)


# ----------------------------------------------------------------- página 8
def influencia(ctx: Ctx, indice: int, tema: str | None = None) -> go.Figure:
    """Recta original vs. recta sin el punto eliminado."""
    p = _bruto(tema)
    r = extras.sin_punto(ctx.x, ctx.y, indice)
    fx = _recta_x(ctx)
    fig = go.Figure(go.Scatter(x=ctx.x, y=ctx.y, mode="markers", name="Datos",
                               marker=dict(size=9, color=p["neutro"], line=dict(width=1, color="white"))))
    fig.add_trace(go.Scatter(x=[ctx.x[indice]], y=[ctx.y[indice]], mode="markers", name=f"Punto eliminado (n.º {indice + 1})",
                             marker=dict(size=14, color=p["acento"], symbol="circle-open", line=dict(width=3))))
    fig.add_trace(go.Scatter(x=fx, y=ctx.ajuste.a * fx + ctx.ajuste.b, mode="lines", name="Con todos los puntos",
                             line=dict(color=p["primario"], width=3)))
    fig.add_trace(go.Scatter(x=fx, y=r["nuevo"].a * fx + r["nuevo"].b, mode="lines", name="Sin ese punto",
                             line=dict(color=p["secundario"], width=2.5, dash="dash")))
    fig = estilo.aplicar(fig, "Influencia de un dato: recta con y sin el punto", ctx.ux, ctx.uy, tema)
    fig.update_xaxes(rangemode="tozero")
    return fig


def cook(ctx: Ctx, tema: str | None = None) -> go.Figure:
    """Distancia de Cook por punto (el de mayor influencia resaltado)."""
    p = _bruto(tema)
    df = extras.influencia_todos(ctx.x, ctx.y)
    imax = int(np.nanargmax(df["Cook"].to_numpy()))
    colores = [p["acento"] if i == imax else p["primario"] for i in range(len(df))]
    fig = go.Figure(go.Bar(x=df["punto"], y=df["Cook"], marker_color=colores, name="Distancia de Cook"))
    fig.add_hline(y=4 / len(df), line=dict(color=p["neutro"], dash="dash"), annotation_text="4/n (referencia)")
    return estilo.aplicar(fig, "Influencia de cada punto (distancia de Cook)", "Punto n.º", "Dₖ (adimensional)", tema, leyenda=False)


def cuadratico(ctx: Ctx, tema: str | None = None) -> go.Figure:
    """Datos + recta + parábola."""
    p = _bruto(tema)
    q = extras.ajustar_cuadratico(ctx.x, ctx.y)
    fx = np.linspace(0, 1.05 * ctx.x.max(), 200)
    fig = go.Figure(go.Scatter(x=ctx.x, y=ctx.y, mode="markers", name="Datos",
                               marker=dict(size=9, color=p["neutro"], line=dict(width=1, color="white"))))
    fig.add_trace(go.Scatter(x=fx, y=ctx.ajuste.a * fx + ctx.ajuste.b, mode="lines", name="Lineal  y = ax + b",
                             line=dict(color=p["primario"], width=3)))
    fig.add_trace(go.Scatter(x=fx, y=q.c2 * fx ** 2 + q.c1 * fx + q.c0, mode="lines", name="Cuadrático  y = ax² + bx + c",
                             line=dict(color=p["secundario"], width=2.5, dash="dash")))
    fig = estilo.aplicar(fig, "Modelo lineal vs. modelo cuadrático", ctx.ux, ctx.uy, tema)
    fig.update_xaxes(rangemode="tozero")
    return fig


def residuos_comparados(ctx: Ctx, tema: str | None = None) -> go.Figure:
    """Residuos de ambos modelos en función de x."""
    p = _bruto(tema)
    q = extras.ajustar_cuadratico(ctx.x, ctx.y)
    e1 = metricas.residuos(ctx.ajuste.a, ctx.ajuste.b, ctx.x, ctx.y)
    e2 = ctx.y - (q.c2 * ctx.x ** 2 + q.c1 * ctx.x + q.c0)
    fig = go.Figure()
    fig.add_hline(y=0, line=dict(color=p["neutro"], width=1.5))
    fig.add_trace(go.Scatter(x=ctx.x, y=e1, mode="markers+lines", name="Lineal",
                             marker=dict(color=p["primario"], size=8), line=dict(width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=ctx.x, y=e2, mode="markers+lines", name="Cuadrático",
                             marker=dict(color=p["secundario"], size=8, symbol="square"), line=dict(width=1, dash="dot")))
    return estilo.aplicar(fig, "Residuos de ambos modelos", ctx.ux, "eᵢ (ms)", tema)


def sensibilidad(ctx: Ctx, df, tema: str | None = None) -> go.Figure:
    """Nube de (a, b) obtenidos al perturbar los datos."""
    p = _bruto(tema)
    fig = go.Figure(go.Scatter(x=df["a"], y=df["b"], mode="markers", name="Ajustes con datos perturbados",
                               marker=dict(size=5, color=p["primario"], opacity=0.5)))
    fig.add_trace(go.Scatter(x=[ctx.ajuste.a], y=[ctx.ajuste.b], mode="markers", name="(a*, b*) original",
                             marker=dict(size=12, color=p["acento"], symbol="x")))
    return estilo.aplicar(fig, "Sensibilidad de (a*, b*) ante pequeñas perturbaciones", f"a ({ctx.ua})", "b (ms)", tema)


def todas(ctx: Ctx) -> dict[str, go.Figure]:
    """Todas las figuras (tema claro, valores por defecto) para exportar."""
    t = "claro"
    figs = {
        "01_dispersion": dispersion(ctx, t),
        "02_ajuste": ajuste(ctx, None, True, t),
        "03_superficie": superficie(ctx, 0.05, False, t),
        "04_curvas_de_nivel": contornos(ctx, 0.05, 14, t),
        "05_trazas_b_constante": trazas(ctx, "b", 0.05, t),
        "06_trazas_a_constante": trazas(ctx, "a", 0.05, t),
        "07_residuos": residuos(ctx, t),
        "08_histograma_residuos": histograma(ctx, 8, t),
    }
    i = extras.mas_influyente(ctx.x, ctx.y)
    figs["09_influencia_punto_max"] = influencia(ctx, i, t)
    figs["10_cook"] = cook(ctx, t)
    if len(ctx.x) >= 4:
        figs["11_modelo_cuadratico"] = cuadratico(ctx, t)
        figs["12_residuos_comparados"] = residuos_comparados(ctx, t)
    return figs
