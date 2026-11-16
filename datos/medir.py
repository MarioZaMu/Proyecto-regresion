"""Benchmark real: tiempo de una búsqueda lineal en función del tamaño de la entrada.

Uso:  python datos/medir.py

Los tiempos salen del cronómetro (``time.perf_counter_ns``) tal cual: nunca se
simulan, suavizan ni editan. Se genera:

* ``datos/datos.csv``              columnas ``x`` (n elementos) y ``y`` (mediana, ms)
* ``datos/mediciones_detalle.csv`` mínimo, máximo, desviación estándar, etc.
* ``datos/metadata.json``          ficha técnica del experimento
"""
from __future__ import annotations

import argparse
import csv
import json
import platform
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
TAMANOS = [100_000 * k for k in range(1, 16)]  # 100 000 ... 1 500 000
CALENTAMIENTO = 2
REPETICIONES = 5


def busqueda_lineal(lista: list[int], objetivo: int) -> int:
    """Búsqueda lineal propia (sin ``in`` ni funciones de búsqueda incorporadas).

    Devuelve el índice de ``objetivo`` o ``-1`` si no está (peor caso: recorre todo).
    """
    for i in range(len(lista)):
        if lista[i] == objetivo:
            return i
    return -1


def medir_una_vez(lista: list[int], objetivo: int) -> float:
    """Ejecuta la búsqueda una vez y devuelve el tiempo en milisegundos."""
    t0 = time.perf_counter_ns()
    busqueda_lineal(lista, objetivo)
    t1 = time.perf_counter_ns()
    return (t1 - t0) / 1e6


def info_sistema() -> dict[str, str | float]:
    """Datos del equipo: SO, procesador y RAM."""
    ram_gb: float | None = None
    try:
        import psutil

        ram_gb = round(psutil.virtual_memory().total / 1024**3, 2)
    except Exception:  # psutil opcional
        pass
    return {
        "python": sys.version.split()[0],
        "sistema_operativo": f"{platform.system()} {platform.release()} ({platform.version()})",
        "procesador": platform.processor() or platform.machine(),
        "ram_gb": ram_gb if ram_gb is not None else "desconocida",
    }


def barra(i: int, total: int, n: int) -> None:
    """Barra de progreso en consola."""
    ancho = 30
    lleno = int(ancho * i / total)
    print(f"\r[{'#' * lleno}{'.' * (ancho - lleno)}] {i}/{total}  n = {n:>9,}", end="", flush=True)


def main(origen: str) -> None:
    print("=" * 62)
    print(" Medición: búsqueda lineal (peor caso, elemento ausente)")
    print(" Cierre otros programas y conecte el equipo a la corriente.")
    print("=" * 62)
    inicio = datetime.now()
    filas_datos: list[tuple[int, float]] = []
    filas_detalle: list[dict[str, float | int]] = []

    for idx, n in enumerate(TAMANOS, start=1):
        lista = list(range(n))
        objetivo = -1  # NO está en la lista → recorre los n elementos
        for _ in range(CALENTAMIENTO):
            busqueda_lineal(lista, objetivo)  # descartadas
        tiempos = [medir_una_vez(lista, objetivo) for _ in range(REPETICIONES)]
        mediana = statistics.median(tiempos)
        filas_datos.append((n, mediana))
        filas_detalle.append({
            "x": n,
            "mediana_ms": mediana,
            "min_ms": min(tiempos),
            "max_ms": max(tiempos),
            "desv_std_ms": statistics.stdev(tiempos),
            **{f"t{k + 1}_ms": t for k, t in enumerate(tiempos)},
        })
        barra(idx, len(TAMANOS), n)
        del lista
    print()

    with open(CARPETA / "datos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y"])
        w.writerows(filas_datos)

    with open(CARPETA / "mediciones_detalle.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_detalle[0].keys()))
        w.writeheader()
        w.writerows(filas_detalle)

    meta = {
        "origen": origen,
        "fecha_hora": inicio.isoformat(timespec="seconds"),
        **info_sistema(),
        "experimento": {
            "descripcion": "Tiempo de ejecución de una búsqueda lineal propia en función del tamaño de la entrada.",
            "algoritmo": "for sobre list(range(n)) buscando un elemento ausente (-1): peor caso, n comparaciones.",
            "x": "n = tamaño de la entrada (elementos)",
            "y": "tiempo de ejecución (ms)",
            "tamanos": [TAMANOS[0], TAMANOS[-1], TAMANOS[1] - TAMANOS[0]],
            "calentamiento": CALENTAMIENTO,
            "repeticiones": REPETICIONES,
            "estadistico": "mediana de las repeticiones",
            "cronometro": "time.perf_counter_ns()",
        },
    }
    with open(CARPETA / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("\nResumen")
    print("-" * 62)
    print(f"{'n':>12} {'mediana (ms)':>14} {'min':>10} {'max':>10} {'desv':>9}")
    for d in filas_detalle:
        print(f"{d['x']:>12,} {d['mediana_ms']:>14.3f} {d['min_ms']:>10.3f} {d['max_ms']:>10.3f} {d['desv_std_ms']:>9.3f}")
    print("-" * 62)
    print(f"Origen: {origen}  |  Duración: {(datetime.now() - inicio).total_seconds():.1f} s")
    print(f"Archivos en: {CARPETA}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Mide el tiempo de una búsqueda lineal.")
    ap.add_argument("--origen", default="estudiante", choices=["estudiante", "entorno_dev"],
                    help="'entorno_dev' marca los datos como de prueba (la app mostrará un aviso).")
    main(ap.parse_args().origen)
