"""Análisis adicionales: Opción A (sensibilidad), B (influencia de un dato) y C (modelo cuadrático)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from core.metricas import r_cuadrado, rmse
from core.regresion import ajustar, hessiano

Vector = np.ndarray


# ----------------------------------------------------------------- Opción B
def sin_punto(x: Vector, y: Vector, indice: int) -> dict:
    """Elimina el punto ``indice``, recalcula la regresión y compara con la original."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    base = ajustar(x, y)
    mascara = np.arange(len(x)) != indice
    nuevo = ajustar(x[mascara], y[mascara])
    n = len(x)
    s2 = base.s_min / (n - 2)
    d = np.array([base.a - nuevo.a, base.b - nuevo.b])
    cook = float(d @ (hessiano(x) / 2) @ d / (2 * s2)) if s2 > 0 else float("nan")
    e_nuevo = y[mascara] - (nuevo.a * x[mascara] + nuevo.b)
    return {
        "indice": indice, "base": base, "nuevo": nuevo,
        "delta_a": nuevo.a - base.a, "delta_b": nuevo.b - base.b,
        "delta_a_rel": (nuevo.a - base.a) / base.a if base.a else float("nan"),
        "rmse_nuevo": rmse(e_nuevo), "cook": cook,
        "x": x[mascara], "y": y[mascara],
    }


def influencia_todos(x: Vector, y: Vector) -> pd.DataFrame:
    """Para cada punto: parámetros al eliminarlo, cambio relativo y distancia de Cook (recalculada)."""
    filas = []
    base = ajustar(x, y)
    for i in range(len(x)):
        r = sin_punto(x, y, i)
        filas.append({
            "punto": i + 1, "x": float(x[i]), "y": float(y[i]),
            "a sin el punto": r["nuevo"].a, "b sin el punto": r["nuevo"].b,
            "Δa (%)": 100 * r["delta_a_rel"],
            "Δb": r["delta_b"],
            "RMSE sin el punto": r["rmse_nuevo"],
            "Cook": r["cook"],
        })
    df = pd.DataFrame(filas)
    return df


def mas_influyente(x: Vector, y: Vector) -> int:
    """Índice (0-based) del punto con mayor distancia de Cook."""
    return int(np.nanargmax(influencia_todos(x, y)["Cook"].to_numpy()))


# ----------------------------------------------------------------- Opción C
@dataclass(frozen=True)
class AjusteCuadratico:
    """y = c2 x² + c1 x + c0 ajustado por mínimos cuadrados."""

    c2: float
    c1: float
    c0: float
    s: float
    rmse: float
    r2: float
    r2_ajustado: float
    f: float
    p_f: float
    t_c2: float
    p_c2: float
    aporte_relativo: float  # |c2·x_max²| / |ŷ(x_max)|


def ajustar_cuadratico(x: Vector, y: Vector) -> AjusteCuadratico:
    """Ajuste cuadrático por ecuaciones normales 3×3 (con x normalizado para estabilidad)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    if n < 4:
        raise ValueError("El ajuste cuadrático requiere al menos 4 puntos.")
    xm = float(np.max(np.abs(x))) or 1.0
    u = x / xm
    A = np.column_stack([u * u, u, np.ones(n)])
    ata = A.T @ A
    cu = np.linalg.solve(ata, A.T @ y)
    c2, c1, c0 = cu[0] / xm ** 2, cu[1] / xm, cu[2]
    yhat = c2 * x * x + c1 * x + c0
    e = y - yhat
    s = float(np.sum(e * e))
    lin = ajustar(x, y)
    gl = n - 3
    s2 = s / gl if gl > 0 else float("nan")
    f = (lin.s_min - s) / s2 if s2 > 0 else float("nan")
    p_f = float(stats.f.sf(f, 1, gl)) if np.isfinite(f) else float("nan")
    cov = s2 * np.linalg.inv(ata)
    se_c2u = float(np.sqrt(cov[0, 0]))
    t_c2 = float(cu[0] / se_c2u) if se_c2u > 0 else float("nan")
    p_c2 = float(2 * stats.t.sf(abs(t_c2), gl)) if np.isfinite(t_c2) else float("nan")
    r2 = r_cuadrado(y, yhat)
    r2a = 1 - (1 - r2) * (n - 1) / gl if gl > 0 else float("nan")
    xmax = float(np.max(x))
    ymax = c2 * xmax ** 2 + c1 * xmax + c0
    aporte = abs(c2 * xmax ** 2) / abs(ymax) if ymax else float("nan")
    return AjusteCuadratico(float(c2), float(c1), float(c0), s, rmse(e), r2, float(r2a),
                            float(f), p_f, t_c2, p_c2, float(aporte))


def comparar_modelos(x: Vector, y: Vector) -> pd.DataFrame:
    """Tabla comparativa lineal vs. cuadrático (S, RMSE, R², R² ajustado)."""
    lin = ajustar(x, y)
    n = len(x)
    e = np.asarray(y, dtype=float) - (lin.a * np.asarray(x, dtype=float) + lin.b)
    r2 = r_cuadrado(y, np.asarray(y, dtype=float) - e)
    q = ajustar_cuadratico(x, y)
    return pd.DataFrame({
        "Modelo": ["Lineal  y = ax + b", "Cuadrático  y = ax² + bx + c"],
        "Parámetros": [2, 3],
        "S_mín": [lin.s_min, q.s],
        "RMSE": [rmse(e), q.rmse],
        "R²": [r2, q.r2],
        "R² ajustado": [1 - (1 - r2) * (n - 1) / (n - 2), q.r2_ajustado],
    })


# ----------------------------------------------------------------- Opción A
def sensibilidad(x: Vector, y: Vector, porcentaje: float = 1.0, ensayos: int = 500,
                 semilla: int = 42) -> pd.DataFrame:
    """Perturba cada yᵢ con ruido relativo ±``porcentaje``% y mide la variación de a*, b*.

    Se trata de un análisis *numérico de sensibilidad* (no altera los datos medidos).
    """
    rng = np.random.default_rng(semilla)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    base = ajustar(x, y)
    filas = []
    for _ in range(ensayos):
        yp = y * (1 + rng.uniform(-porcentaje, porcentaje, size=len(y)) / 100)
        f = ajustar(x, yp)
        filas.append((f.a, f.b))
    arr = np.array(filas)
    return pd.DataFrame({"a": arr[:, 0], "b": arr[:, 1],
                         "Δa (%)": 100 * (arr[:, 0] - base.a) / base.a,
                         "Δb": arr[:, 1] - base.b})
