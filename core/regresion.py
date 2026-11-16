"""Ajuste lineal y = a x + b DESDE CERO, con las fórmulas del cálculo multivariable.

No se usa ninguna función de regresión incorporada. Se implementa:

* S(a, b) = Σ (yᵢ − a xᵢ − b)²
* ∇S = ( −2 Σ xᵢ(yᵢ − a xᵢ − b),  −2 Σ (yᵢ − a xᵢ − b) )
* Sistema normal  a Σx² + b Σx = Σxy ;  a Σx + b n = Σy
* a* = (nΣxy − ΣxΣy)/(nΣx² − (Σx)²),  b* = (Σy − a*Σx)/n
* H = [[2Σx², 2Σx], [2Σx, 2n]]  (constante, pues S es cuadrática)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

Vector = np.ndarray


@dataclass(frozen=True)
class Sumas:
    """Sumatorias que intervienen en el sistema normal."""

    n: int
    sx: float
    sy: float
    sxx: float
    sxy: float
    syy: float


@dataclass(frozen=True)
class Ajuste:
    """Resultado del ajuste por mínimos cuadrados."""

    a: float
    b: float
    s_min: float
    sumas: Sumas


@dataclass(frozen=True)
class ClasificacionCritico:
    """Resultado del criterio del Hessiano (criterio de las segundas derivadas)."""

    hessiano: np.ndarray
    det: float
    s_aa: float
    autovalores: tuple[float, float]
    tipo: str  # "mínimo local (estricto)", "máximo local", "punto silla", "no concluyente"


def validar(x: Vector, y: Vector) -> list[str]:
    """Devuelve la lista de problemas encontrados en los datos (vacía si son válidos)."""
    errores: list[str] = []
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape or x.ndim != 1:
        errores.append("x e y deben ser vectores de la misma longitud.")
        return errores
    if x.size < 3:
        errores.append(f"Se necesitan al menos 3 puntos (hay {x.size}).")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        errores.append("Los datos contienen valores no numéricos (NaN o infinito).")
    elif x.size >= 1 and np.ptp(x) == 0:
        errores.append("Todos los valores de x son iguales: no existe una recta única (el Hessiano sería singular).")
    return errores


def exigir_validos(x: Vector, y: Vector) -> None:
    """Lanza ``ValueError`` con un mensaje claro si los datos no son válidos."""
    errores = validar(x, y)
    if errores:
        raise ValueError(" ".join(errores))


def sumas(x: Vector, y: Vector) -> Sumas:
    """Calcula n, Σx, Σy, Σx², Σxy, Σy²."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return Sumas(len(x), float(np.sum(x)), float(np.sum(y)), float(np.sum(x * x)),
                 float(np.sum(x * y)), float(np.sum(y * y)))


def error_cuadratico(a, b, x: Vector, y: Vector):
    """S(a, b) = Σ (yᵢ − a xᵢ − b)². Admite ``a`` y ``b`` escalares o mallas (broadcast)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    r = y - a_arr[..., None] * x - b_arr[..., None]
    return np.sum(r * r, axis=-1)


def gradiente(a: float, b: float, x: Vector, y: Vector) -> Vector:
    """∇S(a, b) = (∂S/∂a, ∂S/∂b) analítico."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    e = y - a * x - b
    return np.array([-2.0 * np.sum(x * e), -2.0 * np.sum(e)])


def hessiano(x: Vector) -> np.ndarray:
    """Hessiano analítico H = [[2Σx², 2Σx], [2Σx, 2n]] (no depende de a, b ni de y)."""
    x = np.asarray(x, dtype=float)
    return np.array([[2.0 * np.sum(x * x), 2.0 * np.sum(x)],
                     [2.0 * np.sum(x), 2.0 * len(x)]])


def ajustar(x: Vector, y: Vector) -> Ajuste:
    """Mínimos cuadrados con las fórmulas del sistema normal (a*, b*, S_mín)."""
    exigir_validos(x, y)
    s = sumas(x, y)
    denom = s.n * s.sxx - s.sx ** 2
    a = (s.n * s.sxy - s.sx * s.sy) / denom
    b = (s.sy - a * s.sx) / s.n
    return Ajuste(float(a), float(b), float(error_cuadratico(a, b, x, y)), s)


def autovalores_2x2(h: np.ndarray) -> tuple[float, float]:
    """Autovalores de una matriz simétrica 2×2: λ = tr/2 ± √((tr/2)² − det)."""
    tr = h[0, 0] + h[1, 1]
    det = h[0, 0] * h[1, 1] - h[0, 1] * h[1, 0]
    disc = max((tr / 2) ** 2 - det, 0.0)
    r = np.sqrt(disc)
    return float(tr / 2 - r), float(tr / 2 + r)


def clasificar(x: Vector) -> ClasificacionCritico:
    """Criterio del Hessiano: det H > 0 y S_aa > 0  ⇒  mínimo local estricto."""
    h = hessiano(x)
    det = float(h[0, 0] * h[1, 1] - h[0, 1] ** 2)
    s_aa = float(h[0, 0])
    if det > 0 and s_aa > 0:
        tipo = "mínimo local (estricto)"
    elif det > 0 and s_aa < 0:
        tipo = "máximo local"
    elif det < 0:
        tipo = "punto silla"
    else:
        tipo = "no concluyente"
    return ClasificacionCritico(h, det, s_aa, autovalores_2x2(h), tipo)


def hessiano_numerico(x: Vector, y: Vector, a: float, b: float,
                      ha: float, hb: float) -> np.ndarray:
    """Hessiano por diferencias finitas centrales de S (para verificar el analítico)."""
    s = lambda aa, bb: float(error_cuadratico(aa, bb, x, y))  # noqa: E731
    s0 = s(a, b)
    saa = (s(a + ha, b) - 2 * s0 + s(a - ha, b)) / ha ** 2
    sbb = (s(a, b + hb) - 2 * s0 + s(a, b - hb)) / hb ** 2
    sab = (s(a + ha, b + hb) - s(a + ha, b - hb) - s(a - ha, b + hb) + s(a - ha, b - hb)) / (4 * ha * hb)
    return np.array([[saa, sab], [sab, sbb]])


def gradiente_numerico(x: Vector, y: Vector, a: float, b: float, ha: float, hb: float) -> Vector:
    """∇S por diferencias finitas centrales."""
    s = lambda aa, bb: float(error_cuadratico(aa, bb, x, y))  # noqa: E731
    return np.array([(s(a + ha, b) - s(a - ha, b)) / (2 * ha),
                     (s(a, b + hb) - s(a, b - hb)) / (2 * hb)])


def pasos_por_defecto(x: Vector, y: Vector, factor: float = 1e-2) -> tuple[float, float]:
    """Pasos h_a, h_b adaptados a la escala de los datos."""
    sx = float(np.std(x)) or 1.0
    sy = float(np.std(y)) or 1.0
    return factor * sy / sx, factor * sy


def verificar_convexidad(x: Vector, y: Vector, ajuste: Ajuste, pares: int = 500,
                         semilla: int = 0) -> dict[str, float]:
    """Prueba numérica de convexidad: S(tp+(1−t)q) ≤ tS(p)+(1−t)S(q) en pares aleatorios."""
    rng = np.random.default_rng(semilla)
    ha, hb = pasos_por_defecto(x, y, 1.0)
    p = np.column_stack([ajuste.a + ha * rng.normal(size=pares) * 5, ajuste.b + hb * rng.normal(size=pares) * 5])
    q = np.column_stack([ajuste.a + ha * rng.normal(size=pares) * 5, ajuste.b + hb * rng.normal(size=pares) * 5])
    t = rng.uniform(size=pares)
    m = t[:, None] * p + (1 - t[:, None]) * q
    sm = error_cuadratico(m[:, 0], m[:, 1], x, y)
    sp = error_cuadratico(p[:, 0], p[:, 1], x, y)
    sq = error_cuadratico(q[:, 0], q[:, 1], x, y)
    holgura = t * sp + (1 - t) * sq - sm  # debe ser ≥ 0
    escala = np.maximum(np.abs(t * sp + (1 - t) * sq), 1e-300)
    cumplen = int(np.sum(holgura >= -1e-9 * escala))
    return {"pares": pares, "cumplen": cumplen, "holgura_min": float(np.min(holgura))}


def descenso_gradiente(x: Vector, y: Vector, inicio: tuple[float, float], pasos: int = 40) -> np.ndarray:
    """Descenso por gradiente con búsqueda de línea exacta (S es cuadrática).

    En cada paso θ ← θ − α∇S con α = (∇Sᵀ∇S)/(∇Sᵀ H ∇S). Devuelve la ruta (pasos+1, 2).
    Sirve para *visualizar* cómo se llega al mínimo; el ajuste real usa las fórmulas normales.
    """
    h = hessiano(x)
    th = np.array(inicio, dtype=float)
    ruta = [th.copy()]
    for _ in range(pasos):
        g = gradiente(th[0], th[1], x, y)
        gg = float(g @ g)
        if gg == 0.0:
            break
        th = th - (gg / float(g @ h @ g)) * g
        ruta.append(th.copy())
    return np.array(ruta)
