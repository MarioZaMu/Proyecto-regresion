"""Página 7: residuos y calidad del ajuste."""
import numpy as np
import pandas as pd
import streamlit as st

from core import metricas
from interfaz import contexto, estilo, graficas

ctx = contexto.cargar()
contexto.cabecera("Calidad del ajuste y residuos")
contexto.tarjetas(ctx)
aj, cal = ctx.ajuste, ctx.calidad
dg = metricas.diagnostico(aj.a, aj.b, ctx.x, ctx.y)
tab = metricas.tabla_puntos(aj.a, aj.b, ctx.x, ctx.y)

st.header("Residuos eᵢ en función de xᵢ")
estilo.mostrar(graficas.residuos(ctx), "res")
estilo.pie("Cada punto es la distancia vertical entre el dato y la recta ($e_i = y_i - (a^*x_i + b^*)$). La banda gris marca $\\pm 2s$, con $s$ la desviación "
           "estándar de los residuos; los rombos rojos serían atípicos (residuo estudentizado $|t_i| > 2$).")

st.header("Histograma de residuos")
bins = estilo.persistente(st.slider, "Número de barras", "res_bins", 8, min_value=4, max_value=20)
estilo.mostrar(graficas.histograma(ctx, bins), "hist")
estilo.pie("Muestra cómo se reparten los errores. Con pocos puntos ($n = %d$) el histograma es solo orientativo; interesa si está aproximadamente "
           "centrado en 0 y si es razonablemente simétrico." % len(ctx.x))

st.header("Medidas cuantitativas")
c = st.columns(2)
with c[0]:
    st.latex(r"\mathrm{RMSE} = \sqrt{\frac{1}{n}\sum e_i^2} = " + estilo.latex_num(cal.rmse) + r"\ \text{ms}")
    st.markdown(f"El **RMSE** es el error típico de predicción, en las mismas unidades que $T$: la recta se equivoca en promedio unos **{estilo.fmt(cal.rmse, 3)} ms**, "
                f"es decir, {estilo.fmt(100 * cal.rmse / ctx.y.mean(), 3)} % del tiempo medio ({estilo.fmt(ctx.y.mean(), 4)} ms) y "
                f"{estilo.fmt(100 * cal.rmse / ctx.y.max(), 3)} % del máximo medido ({estilo.fmt(ctx.y.max(), 4)} ms). "
                f"Para el propósito del modelo (estimar cuánto tarda una búsqueda para un $n$ dado) es un error pequeño.")
with c[1]:
    st.latex(r"R^2 = 1 - \frac{\sum (y_i-\hat y_i)^2}{\sum (y_i-\bar y)^2} = " + f"{cal.r2:.6f}")
    st.markdown(f"**$R^2$** indica que la recta explica el **{100 * cal.r2:.4f} %** de la variabilidad de $T$ en los datos ({estilo.fmt(ctx.sst, 5)} ms² de variación total, "
                f"de los que solo {estilo.fmt(aj.s_min, 3)} ms² quedan sin explicar). Un $R^2$ tan alto es **esperable** aquí, porque $T$ depende casi solo de $n$ "
                "y el rango de $n$ es amplio (15 veces), pero **no prueba** que el modelo sea lineal: por eso se revisan los residuos.")

st.header("Diagnóstico automático de los residuos")
cen = abs(cal.media_residuos) < 1e-6 * max(cal.max_abs_residuo, 1e-12) + 1e-9
cur = dg["corr_curvatura"]
medias = dg["medias_tercios"]
sist = (medias[0] * medias[2] > 0) and (medias[1] * medias[0] < 0) and abs(cur) > 0.5
n_at = int(tab["atipico"].sum())
st.dataframe(pd.DataFrame([
    ("Media de los residuos", f"{estilo.fmt(cal.media_residuos, 3)} ms", "≈ 0 (siempre, por construcción con intercepto)"),
    ("Correlación e ↔ x", f"{estilo.fmt(cal.corr_residuo_x, 3)}", "≈ 0 también por construcción (Σ xᵢeᵢ = 0)"),
    ("Correlación e ↔ (x − x̄)²  (curvatura)", f"{cur:.3f}", "|r| grande ⇒ patrón curvo (U o ∩)"),
    ("Correlación |e| ↔ x  (dispersión)", f"{dg['corr_abs_x']:.3f}", "> 0 ⇒ la dispersión crece con x"),
    ("Cambios de signo (ordenados por x)", f"{dg['cambios_signo']} (esperados ≈ {dg['cambios_esperados']:.1f})", "pocos cambios ⇒ rachas largas de un mismo signo"),
    ("Media de e por tercios de x", " · ".join(estilo.fmt(m, 3) for m in medias) + " ms", "signos opuestos entre tercios ⇒ desviación sistemática"),
    ("Atípicos (|t| > 2)", str(n_at), ""),
], columns=["Indicador", "Valor", "Cómo leerlo"]), hide_index=True, width="stretch")
msgs = []
msgs.append("Los residuos están centrados en cero (garantizado por el método)." if cen else "Los residuos no están centrados: revisar.")
msgs.append(f"Patrón curvo: {'**posible** (correlación con la curvatura = %.2f)' % cur if abs(cur) > 0.5 else 'no evidente (%.2f)' % cur}.")
msgs.append(f"Dispersión: {'tiende a **crecer** con x' if dg['corr_abs_x'] > 0.5 else 'tiende a decrecer con x' if dg['corr_abs_x'] < -0.5 else 'sin tendencia clara respecto a x'} (r = {dg['corr_abs_x']:.2f}).")
msgs.append(f"Atípicos: {n_at} punto(s) con |t| > 2." if n_at else "Atípicos: ninguno según el criterio |t| > 2.")
msgs.append("Desviación sistemática: **sí hay indicios** (tercios con signos alternados y curvatura marcada)." if sist else "Desviación sistemática: no se detecta un patrón fuerte por regiones.")
st.markdown("\n".join(f"- {m}" for m in msgs))
st.caption("Este diagnóstico es una ayuda automática; la interpretación final es la que usted escribe abajo.")

st.header("Interpretación (espacios para redactar)")
st.caption("Sugerencia: relacione cada observación con causas reales del ruido en la medición: planificador del sistema operativo, memoria caché de la CPU, "
           "recolector de basura de Python, otros procesos en ejecución y cambios de frecuencia del procesador (turbo / ahorro de energía).")
from interfaz.exportar import CLAVES_TEXTO  # noqa: E402

for clave, titulo in CLAVES_TEXTO.items():
    estilo.persistente(st.text_area, titulo, clave, "", height=90, placeholder="Escriba aquí su interpretación…")
