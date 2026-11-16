# Regresión lineal y optimización con funciones de varias variables

Proyecto de **Cálculo Multivariable** (UCC, 2026-B). Problema real elegido: **tiempo de ejecución de una búsqueda lineal
en función del tamaño de la entrada**, modelo `T = a·n + b` (O(n)).

## Instalación

```bash
pip install -r requirements.txt
```

Python 3.11+. Para exportar figuras PNG se necesita `kaleido` y **Google Chrome/Chromium** instalado.

## Cómo ejecutar

1. **Medir los datos reales** (en su computador):

   ```bash
   python datos/medir.py
   ```

   > **Antes de medir:** cierre otros programas (navegador, juegos, descargas) y **conecte el equipo a la corriente**
   > (el modo ahorro de energía cambia la frecuencia del procesador y mete ruido). Tarda unos segundos.

   Genera `datos/datos.csv` (x, y), `datos/mediciones_detalle.csv` (mín., máx., desv. estándar) y `datos/metadata.json`.
   Los tiempos salen del cronómetro tal cual (`time.perf_counter_ns`); nunca se simulan ni se editan.
   Por defecto el origen queda como `"estudiante"`. Los datos incluidos en este repositorio se generaron en el entorno de
   desarrollo con `--origen entorno_dev` y la app muestra el aviso **«DATOS DE PRUEBA»** hasta que usted vuelva a correr `medir.py`.

2. **Abrir la aplicación:**

   ```bash
   streamlit run app.py
   ```

3. **Pruebas:**

   ```bash
   python -m pytest
   ```

## Estructura

| Ruta | Contenido |
|---|---|
| `datos/medir.py` | Benchmark real (búsqueda lineal propia, 15 tamaños, 2 calentamientos + 5 mediciones, mediana) |
| `core/regresion.py` | Ajuste **desde cero** (fórmulas normales), S(a,b), gradiente, Hessiano, autovalores, criterio det H > 0 y S_aa > 0 |
| `core/verificacion.py` | Comparación con `numpy.polyfit` y `scipy.stats.linregress` (tabla de la sección 9 del enunciado) |
| `core/metricas.py` | Residuos, RMSE, R², atípicos, apalancamiento, distancia de Cook, diagnóstico de patrón |
| `core/extras.py` | Opción B (influencia), Opción C (cuadrático) y Opción A (sensibilidad) |
| `interfaz/` | Estilo Plotly común, contexto, gráficas, exportación |
| `app.py`, `pages/` | Aplicación Streamlit con 9 páginas |
| `config.py` | Curso, universidad y nombre del estudiante (editable) |
| `tests/` | Pruebas con pytest |

## Páginas

Datos · Modelo y fórmulas · Ajuste · Geometría · Hessiano · Comparación · Calidad y residuos · Análisis adicional · Exportar.

- En *Datos* puede **escalar x a unidades de 10⁵ elementos** (activado por defecto); la conversión se muestra explícitamente.
- En *Comparación* escriba su resultado **hecho a mano** (a, b, S_mín) en los campos editables.
- En *Calidad y residuos* hay espacios de texto para su interpretación; se incluyen en el resumen exportado.
- *Exportar* genera un ZIP de PNG y un resumen en Markdown y PDF.

> El desarrollo analítico (derivadas parciales, sistema normal, solución y Hessiano) debe hacerse **a mano en papel**;
> la app solo lo verifica y lo visualiza.
