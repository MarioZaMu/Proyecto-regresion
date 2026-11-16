"""Comparación entre método analítico (manual), código propio y bibliotecas de Python."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from core.regresion import ajustar, error_cuadratico

Vector = np.ndarray


def ajuste_polyfit(x: Vector, y: Vector) -> tuple[float, float]:
    """Ajuste con ``numpy.polyfit`` de grado 1 → (a, b)."""
    a, b = np.polyfit(x, y, 1)
    return float(a), float(b)


def ajuste_linregress(x: Vector, y: Vector) -> tuple[float, float]:
    """Ajuste con ``scipy.stats.linregress`` → (a, b)."""
    r = stats.linregress(x, y)
    return float(r.slope), float(r.intercept)


def comparar(x: Vector, y: Vector, manual: tuple[float | None, float | None, float | None] | None = None) -> dict:
    """Compara los métodos y devuelve tablas.

    ``manual`` = (a_man, b_man, S_man) escritos por el estudiante (cada uno puede ser ``None``).
    La columna "Biblioteca" usa ``numpy.polyfit`` y ``scipy.stats.linregress`` (se reportan ambos
    y, en la tabla principal, ``linregress``; S_mín se evalúa con la definición de S).
    """
    propio = ajustar(x, y)
    a_np, b_np = ajuste_polyfit(x, y)
    a_sp, b_sp = ajuste_linregress(x, y)
    s_np = float(error_cuadratico(a_np, b_np, x, y))
    s_sp = float(error_cuadratico(a_sp, b_sp, x, y))

    filas = {"a": [propio.a, a_sp], "b": [propio.b, b_sp], "S_mín": [propio.s_min, s_sp]}
    man = {"a": None, "b": None, "S_mín": None}
    if manual is not None:
        man = {"a": manual[0], "b": manual[1], "S_mín": manual[2]}

    tabla_filas = []
    for nombre in ("a", "b", "S_mín"):
        propio_v, lib_v = filas[nombre]
        valores = [v for v in (man[nombre], propio_v, lib_v) if v is not None and np.isfinite(v)]
        dif = max(valores) - min(valores)
        tabla_filas.append({
            "Parámetro": nombre,
            "Analítico (manual)": man[nombre] if man[nombre] is not None else np.nan,
            "Código propio": propio_v,
            "Biblioteca (linregress)": lib_v,
            "Diferencia máxima": dif,
        })
    tabla = pd.DataFrame(tabla_filas)

    detalle = pd.DataFrame({
        "Método": ["Código propio (fórmulas normales)", "numpy.polyfit", "scipy.stats.linregress"],
        "a": [propio.a, a_np, a_sp],
        "b": [propio.b, b_np, b_sp],
        "S_mín": [propio.s_min, s_np, s_sp],
    })
    return {"tabla": tabla, "detalle": detalle, "propio": propio,
            "numpy": (a_np, b_np, s_np), "scipy": (a_sp, b_sp, s_sp)}
