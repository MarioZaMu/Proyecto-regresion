"""Página 8: análisis adicional (Opciones B, C y A)."""
import numpy as np
import pandas as pd
import streamlit as st

from core import extras
from interfaz import contexto, estilo, graficas

ctx = contexto.cargar()
contexto.cabecera("Análisis adicional")
contexto.tarjetas(ctx)
aj = ctx.ajuste
tb, tc, ta = st.tabs(["Opción B · Influencia de un dato", "Opción C · Modelo cuadrático", "Opción A · Sensibilidad"])

# ---------------------------------------------------------------- B
with tb:
    infl = extras.influencia_todos(ctx.x, ctx.y)
    imax = int(np.nanargmax(infl["Cook"].to_numpy()))
    etiquetas = [f"n.º {i + 1} · x = {estilo.fmt(ctx.x[i], 4)}" + ("  ★ más influyente" if i == imax else "") for i in range(len(ctx.x))]
    sel = estilo.persistente(st.selectbox, "Punto a eliminar temporalmente", f"b_punto_{len(ctx.x)}_{int(ctx.escala)}", etiquetas[imax], options=etiquetas)
    i = etiquetas.index(sel)
    r = extras.sin_punto(ctx.x, ctx.y, i)
    st.success(f"Punto de **mayor influencia** (distancia de Cook, recalculada eliminando cada punto): **n.º {imax + 1}** (x = {estilo.fmt(ctx.x[imax], 4)}), "
               f"resaltado en rojo en el gráfico de barras.", icon=":material/star:")
    c = st.columns(4)
    for col, (n_, v, d) in zip(c, [
        ("a sin el punto", estilo.fmt(r["nuevo"].a), f"{100 * r['delta_a_rel']:+.4f} %"),
        ("b sin el punto", estilo.fmt(r["nuevo"].b), f"{r['delta_b']:+.4g} ms"),
        ("RMSE sin el punto", estilo.fmt(r["rmse_nuevo"]), f"{r['rmse_nuevo'] - ctx.calidad.rmse:+.3g} ms"),
        ("Distancia de Cook", estilo.fmt(r["cook"]), "referencia 4/n = " + estilo.fmt(4 / len(ctx.x), 3))]):
        with col.container(border=True):
            st.metric(n_, v, d, delta_color="off")
    estilo.mostrar(graficas.influencia(ctx, i), "infl")
    estilo.pie(f"Se ajustó de nuevo la recta sin el punto n.º {i + 1} (círculo rojo). La pendiente cambia {100 * r['delta_a_rel']:+.4f} %: "
               + ("el cambio es **muy pequeño**, la recta casi no se mueve." if abs(r["delta_a_rel"]) < 0.01 else
                  "el cambio es **apreciable**: este punto influye en el ajuste.")
               + " Los puntos de los extremos de $x$ tienen más **apalancamiento** (leverage), pero solo son realmente influyentes si además se alejan de la recta.")
    estilo.mostrar(graficas.cook(ctx), "cook")
    estilo.pie("La distancia de Cook combina apalancamiento y tamaño del residuo. Valores por encima de $4/n$ merecen revisión; "
               f"aquí el máximo es {estilo.fmt(infl['Cook'].max(), 3)} " + ("(supera" if infl["Cook"].max() > 4 / len(ctx.x) else "(no supera") + " la referencia).")
    tabla = infl.copy()
    tabla.insert(0, "", ["★" if k == imax else "" for k in range(len(tabla))])
    for col in tabla.columns[3:]:
        tabla[col] = [estilo.fmt(v, 5) for v in tabla[col]]
    st.dataframe(tabla, hide_index=True, width="stretch")

# ---------------------------------------------------------------- C
with tc:
    if len(ctx.x) < 4:
        st.warning("El modelo cuadrático necesita al menos 4 puntos.")
    else:
        q = extras.ajustar_cuadratico(ctx.x, ctx.y)
        st.latex(rf"y = a x^2 + b x + c:\quad a = {estilo.latex_num(q.c2)},\ b = {estilo.latex_num(q.c1)},\ c = {estilo.latex_num(q.c0)}")
        comp = extras.comparar_modelos(ctx.x, ctx.y)
        tabla = comp.copy()
        for col in ("S_mín", "RMSE"):
            tabla[col] = [estilo.fmt(v) for v in tabla[col]]
        tabla["R²"] = [f"{v:.8f}" for v in comp["R²"]]
        tabla["R² ajustado"] = [f"{v:.8f}" for v in comp["R² ajustado"]]
        st.dataframe(tabla, hide_index=True, width="stretch")
        estilo.mostrar(graficas.cuadratico(ctx), "cuad")
        estilo.pie("Ambas curvas son casi indistinguibles en el rango medido: la parábola solo se separa de la recta de forma imperceptible.")
        estilo.mostrar(graficas.residuos_comparados(ctx), "rescomp")
        estilo.pie("Si los residuos del modelo cuadrático fueran claramente menores y sin patrón, el término $x^2$ estaría capturando una curvatura real.")
        c = st.columns(3)
        with c[0].container(border=True):
            st.metric("Reducción de S", f"{100 * (1 - q.s / aj.s_min):.3f} %")
        with c[1].container(border=True):
            st.metric("p del término x² (t)", estilo.fmt(q.p_c2, 3))
        with c[2].container(border=True):
            st.metric("Aporte del término x² en x máx", f"{100 * q.aporte_relativo:.3f} %")
        signif = q.p_f < 0.05
        st.markdown(
            "**Discusión.** Si el algoritmo es $O(n)$, el coeficiente cuadrático debería ser **casi cero**. "
            f"Se obtuvo $a_2 = {estilo.fmt(q.c2, 4)}$; en el extremo del rango, el término $a_2 x^2$ aporta solo el **{100 * q.aporte_relativo:.3f} %** del tiempo predicho. "
            f"La prueba F parcial da $p = {estilo.fmt(q.p_f, 3)}$: el término cuadrático "
            + ("**es estadísticamente significativo**, pero su efecto práctico es mínimo (un modelo con más parámetros siempre reduce $S$ y con pocos puntos y ruido de sistema "
               "—efectos de caché, frecuencia de la CPU— puede captar una ligera curvatura). " if signif else
               "**no es estadísticamente significativo** al 5 %: el modelo más complejo no aporta una mejora real. ")
            + f"El $R^2$ ajustado pasa de {comp['R² ajustado'][0]:.6f} a {comp['R² ajustado'][1]:.6f}. "
            "Conclusión: el modelo lineal es suficiente para representar el comportamiento $O(n)$ y la parábola no cambia de forma importante la representación de los datos."
        )

# ---------------------------------------------------------------- A
with ta:
    st.caption("Se perturban todos los tiempos con ruido relativo uniforme ±p % y se recalcula el ajuste muchas veces (semilla fija; los datos medidos no se modifican).")
    c = st.columns(2)
    with c[0]:
        p = estilo.persistente(st.slider, "Perturbación relativa máxima p (%)", "sens_p", 1.0, min_value=0.1, max_value=10.0, step=0.1)
    with c[1]:
        m = estilo.persistente(st.slider, "Número de ensayos", "sens_m", 500, min_value=50, max_value=3000, step=50)
    sd = extras.sensibilidad(ctx.x, ctx.y, p, m)
    c = st.columns(3)
    with c[0].container(border=True):
        st.metric("Desv. estándar de a*", estilo.fmt(sd["a"].std()), f"{100 * sd['a'].std() / abs(aj.a):.3f} % de a*", delta_color="off")
    with c[1].container(border=True):
        st.metric("Desv. estándar de b*", estilo.fmt(sd["b"].std()), "ms", delta_color="off")
    with c[2].container(border=True):
        st.metric("Rango de Δa", f"[{sd['Δa (%)'].min():.3f}, {sd['Δa (%)'].max():.3f}] %")
    estilo.mostrar(graficas.sensibilidad(ctx, sd), "sens")
    estilo.pie(f"Con perturbaciones de hasta ±{p:g} % en cada dato, la pendiente varía en torno a {100 * sd['a'].std() / abs(aj.a):.3f} % (desv. estándar). "
               "La nube es alargada porque $a$ y $b$ están correlacionados (valle de $S$). El modelo es **poco sensible** a pequeñas modificaciones, "
               "porque se promedia el ruido sobre muchos puntos; $b$, en cambio, es relativamente más incierto porque se extrapola hasta $n=0$.")
