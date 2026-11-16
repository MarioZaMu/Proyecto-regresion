"""Carga de datos y metadatos del experimento."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_DATOS = RAIZ / "datos"
ESCALA_X = 1e5  # unidad escalada: 10^5 elementos


def cargar_csv(ruta: Path | str | None = None) -> pd.DataFrame:
    """Lee ``datos.csv`` (columnas ``x`` e ``y``) y devuelve un DataFrame."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / "datos.csv"
    df = pd.read_csv(ruta)
    faltan = {"x", "y"} - set(df.columns)
    if faltan:
        raise ValueError(f"Al archivo le faltan las columnas: {', '.join(sorted(faltan))}.")
    return df[["x", "y"]].astype(float)


def cargar_metadata(ruta: Path | str | None = None) -> dict:
    """Lee ``metadata.json``; devuelve un dict vacío si no existe."""
    ruta = Path(ruta) if ruta else CARPETA_DATOS / "metadata.json"
    if not ruta.exists():
        return {}
    return json.loads(ruta.read_text(encoding="utf-8"))


def es_datos_de_prueba(meta: dict) -> bool:
    """Verdadero mientras ``origen`` sea ``entorno_dev``."""
    return meta.get("origen") == "entorno_dev"


def escalar(x: np.ndarray, activo: bool) -> np.ndarray:
    """Convierte n (elementos) a unidades de 10^5 elementos si ``activo``."""
    return np.asarray(x, dtype=float) / ESCALA_X if activo else np.asarray(x, dtype=float)
