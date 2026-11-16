"""Contexto de la aplicación: datos activos, escala de x, ajuste y métricas."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

import config
from core import datos as dat
from core import metricas, regresion
from interfaz import estilo


@dataclass
class Ctx:
    """Todo lo que necesitan las páginas, calculado una sola vez por ejecución."""

    df: pd.DataFrame
    meta: dict
    escala: bool
    x: np.ndarray            # x en las unidades activas
    y: np.ndarray            # tiempo en ms
    x_raw: np.ndarray        # n en elementos
    ajuste: regresion.Ajuste
    calidad: metricas.Calidad
    clasif: regresion.ClasificacionCritico
    ux: str
    uy: str
    ua: str
    ub: str
    usuario: bool            # datos subidos por el usuario

    @property
    def etiqueta_x(self) -> str:
        return f"{self.ux}"

    @property
    def a_ns_por_elemento(self) -> float:
        """Pendiente convertida a ns por elemento."""
        a_raw = self.ajuste.a / (dat.ESCALA_X if self.escala else 1.0)
        return a_raw * 1e6

    @property
    def sst(self) -> float:
        return float(np.sum((self.y - self.y.mean()) ** 2))


def datos_activos() -> tuple[pd.DataFrame, dict, bool]:
    """Datos de ``datos/datos.csv`` o los subidos por el usuario."""
    df_u = st.session_state.get("df_usuario")
    if df_u is not None:
        return df_u, {"origen": "usuario", "experimento": {"descripcion": "Datos cargados desde un archivo CSV por el usuario."}}, True
    try:
        return dat.cargar_csv(), dat.cargar_metadata(), False
    except FileNotFoundError:
        st.error("No se encontró `datos/datos.csv`. Ejecute primero `python datos/medir.py`.")
        st.stop()
    except ValueError as e:
        st.error(str(e))
        st.stop()


def cargar() -> Ctx:
    """Construye el contexto; detiene la página con un mensaje claro si los datos no son válidos."""
    df, meta, usuario = datos_activos()
    escala = bool(st.session_state.get("escala_activa", True))
    x_raw = df["x"].to_numpy(dtype=float)
    y = df["y"].to_numpy(dtype=float)
    x = dat.escalar(x_raw, escala)
    errores = regresion.validar(x, y)
    if errores:
        for e in errores:
            st.error(e)
        if usuario and st.button("Restablecer datos medidos"):
            st.session_state.pop("df_usuario", None)
            st.rerun()
        st.stop()
    aj = regresion.ajustar(x, y)
    return Ctx(
        df=df, meta=meta, escala=escala, x=x, y=y, x_raw=x_raw, ajuste=aj,
        calidad=metricas.calidad(aj.a, aj.b, x, y), clasif=regresion.clasificar(x),
        ux="n (×10⁵ elementos)" if escala else "n (elementos)", uy="T (ms)",
        ua="ms por 10⁵ elementos" if escala else "ms por elemento", ub="ms", usuario=usuario,
    )


def cabecera(titulo: str, subtitulo: str | None = None) -> None:
    """Título de página, línea institucional y aviso de datos de prueba."""
    st.title(titulo)
    st.markdown(f'<div class="encabezado">{config.CURSO} · {config.UNIVERSIDAD} · {config.ESTUDIANTE}</div>',
                unsafe_allow_html=True)
    meta = dat.cargar_metadata() if st.session_state.get("df_usuario") is None else {}
    if dat.es_datos_de_prueba(meta):
        st.warning("**DATOS DE PRUEBA**, ejecutar `datos/medir.py` en el equipo del estudiante "
                   "(origen: entorno de desarrollo).", icon=":material/warning:")
    if subtitulo:
        st.caption(subtitulo)


def tarjetas(ctx: Ctx) -> None:
    """Métricas clave: a*, b*, S_mín, RMSE y R²."""
    c = st.columns(5)
    vals = [
        ("a*", estilo.fmt(ctx.ajuste.a), ctx.ua),
        ("b*", estilo.fmt(ctx.ajuste.b), ctx.ub),
        ("S_mín", estilo.fmt(ctx.ajuste.s_min), "ms²"),
        ("RMSE", estilo.fmt(ctx.calidad.rmse), "ms"),
        ("R²", f"{ctx.calidad.r2:.6f}", ""),
    ]
    for col, (nombre, v, u) in zip(c, vals):
        with col.container(border=True):
            st.metric(nombre, v, help=f"Unidades: {u}" if u else "Adimensional")
            st.caption(u or "adimensional")
