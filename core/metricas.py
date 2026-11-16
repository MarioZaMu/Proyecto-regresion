"""Residuos, métricas de calidad, atípicos e influencia de cada punto."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

Vector = np.ndarray


def predicciones(a: float, b: float, x: Vector) -> Vector:
    """ŷᵢ = a xᵢ + b."""
    return a * np.asarray(x, dtype=float) + b


def residuos(a: float, b: float, x: Vector, y: Vector) -> Vector:
    """eᵢ = yᵢ − (a xᵢ + b)."""
    return np.asarray(y, dtype=float) - predicciones(a, b, x)


def rmse(e: Vector) -> float:
    """Raíz del error cuadrático medio: √( (1/n) Σ eᵢ² )."""
    e = np.asarray(e, dtype=float)
    return float(np.sqrt(np.mean(e * e)))


def r_cuadrado(y: Vector, y_pred: Vector) -> float:
    """R² = 1 − Σ(yᵢ − ŷᵢ)² / Σ(yᵢ − ȳ)²."""
    y = np.asarray(y, dtype=float)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


@dataclass(frozen=True)
class Calidad:
    """Resumen de calidad del ajuste."""

    rmse: float
    r2: float
    media_residuos: float
    desv_residuos: float
    max_abs_residuo: float
    corr_residuo_x: float
    corr_absresiduo_x: float


def calidad(a: float, b: float, x: Vector, y: Vector) -> Calidad:
    """Calcula RMSE, R² y estadísticos de los residuos (centrado, tendencia, dispersión)."""
    x = np.asarray(x, dtype=float)
    e = residuos(a, b, x, y)
    corr = lambda u, v: float(np.corrcoef(u, v)[0, 1]) if np.std(u) > 0 and np.std(v) > 0 else 0.0  # noqa: E731
    return Calidad(rmse(e), r_cuadrado(y, predicciones(a, b, x)), float(np.mean(e)),
                   float(np.std(e, ddof=2)) if len(e) > 2 else float("nan"), float(np.max(np.abs(e))),
                   corr(x, e), corr(x, np.abs(e)))


def tabla_puntos(a: float, b: float, x: Vector, y: Vector, umbral: float = 2.0) -> pd.DataFrame:
    """Tabla por punto: residuo, apalancamiento, residuo estudentizado, distancia de Cook y atípico.

    * Apalancamiento hᵢ = 1/n + (xᵢ − x̄)² / Σ(xⱼ − x̄)²
    * Residuo estudentizado tᵢ = eᵢ / (s √(1 − hᵢ)),  s² = S_mín/(n − 2)
    * Distancia de Cook Dᵢ = eᵢ² hᵢ / (2 s² (1 − hᵢ)²)
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    e = residuos(a, b, x, y)
    sxx = float(np.sum((x - x.mean()) ** 2))
    h = 1.0 / n + (x - x.mean()) ** 2 / sxx
    s2 = float(np.sum(e * e)) / (n - 2) if n > 2 else float("nan")
    s = np.sqrt(s2) if s2 > 0 else np.nan
    with np.errstate(divide="ignore", invalid="ignore"):
        t = e / (s * np.sqrt(1 - h))
        cook = e ** 2 * h / (2 * s2 * (1 - h) ** 2)
    return pd.DataFrame({
        "x": x, "y": y, "y_pred": predicciones(a, b, x), "residuo": e,
        "apalancamiento": h, "residuo_estudentizado": t, "cook": cook,
        "atipico": np.abs(t) > umbral,
    })


def diagnostico(a: float, b: float, x: Vector, y: Vector) -> dict:
    """Indicadores de patrón en los residuos.

    Con intercepto, Σeᵢ = 0 y Σxᵢeᵢ = 0 *por construcción*; por eso un patrón solo puede
    aparecer como curvatura (``corr_curvatura``), rachas de un mismo signo, cambios de
    dispersión (``corr_abs_x``) o diferencias entre regiones (``medias_tercios``).
    """
    x = np.asarray(x, dtype=float)
    e = residuos(a, b, x, y)
    u = (x - x.mean()) ** 2
    corr = lambda p, q: float(np.corrcoef(p, q)[0, 1]) if np.std(p) > 0 and np.std(q) > 0 else 0.0  # noqa: E731
    orden = np.argsort(x)
    e_ord = e[orden]
    signos = np.sign(e_ord)
    cambios = int(np.sum(signos[1:] * signos[:-1] < 0))
    tercios = [float(np.mean(t)) for t in np.array_split(e_ord, 3)]
    return {
        "corr_curvatura": corr(e, u), "corr_abs_x": corr(np.abs(e), x),
        "cambios_signo": cambios, "cambios_esperados": (len(e) - 1) / 2,
        "medias_tercios": tercios,
    }
