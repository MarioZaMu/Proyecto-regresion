"""Página 3: ajuste, recta óptima y comparación con otras rectas."""
import pandas as pd
import streamlit as st

from core.regresion import error_cuadratico
from interfaz import contexto, estilo, graficas

ctx = contexto.cargar()
contexto.cabecera("Ajuste por mínimos cuadrados")
contexto.tarjetas(ctx)
aj = ctx.ajuste

st.header("Resultado")
st.latex(rf"a^* = {estilo.latex_num(aj.a)}\ \text{{{ctx.ua}}},\qquad b^* = {estilo.latex_num(aj.b)}\ \text{{ms}},\qquad "
         rf"S_{{\min}} = {estilo.latex_num(aj.s_min)}\ \text{{ms}}^2")
st.latex(rf"T(n) = {estilo.latex_num(aj.a)}\,x + ({estilo.latex_num(aj.b)})\qquad (x\ \text{{en}}\ {ctx.ux.split('(')[1].rstrip(')')})")

st.header("Comparación con otras rectas")
st.caption("Elija otras parejas $(a, b)$ con los controles deslizantes y compare su error $S$ con el mínimo.")
da, db = graficas.region(ctx, 0.02)
k = int(ctx.escala)
rectas, filas = [], [("Óptima (a*, b*)", aj.a, aj.b, aj.s_min)]
cols = st.columns(2)
for col, nombre, fa, fb in ((cols[0], "Recta A", 0.5, 0.0), (cols[1], "Recta B", -0.7, 0.8)):
    with col.container(border=True):
        st.markdown(f"**{nombre}**")
        a_ = estilo.persistente(st.slider, f"a de la {nombre.lower()} ({ctx.ua})", f"aj_{nombre}_a_{k}", float(aj.a + fa * da),
                                min_value=float(aj.a - da), max_value=float(aj.a + da), step=float(da / 200), format="%.6g")
        b_ = estilo.persistente(st.slider, f"b de la {nombre.lower()} (ms)", f"aj_{nombre}_b_{k}", float(aj.b + fb * db),
                                min_value=float(aj.b - db), max_value=float(aj.b + db), step=float(db / 200), format="%.6g")
        rectas.append((nombre, a_, b_))
        s_ = float(error_cuadratico(a_, b_, ctx.x, ctx.y))
        filas.append((nombre, a_, b_, s_))
        st.metric("S de esta recta", estilo.fmt(s_), delta=f"{s_ / aj.s_min:.4g} × S_mín", delta_color="off")
mostrar_res = estilo.persistente(st.checkbox, "Mostrar los residuos eᵢ de la recta óptima", "aj_res", False)
estilo.mostrar(graficas.ajuste(ctx, rectas, mostrar_res), "ajuste")
estilo.pie("La recta **azul** minimiza $S$: ninguna otra pareja $(a,b)$ obtiene un error menor. Las rectas discontinuas pueden "
           "parecer cercanas a los datos a simple vista, pero su $S$ (en la leyenda) es mayor, porque $S$ penaliza al cuadrado cada "
           "desviación vertical. Los segmentos rojos (si se activan) son los residuos $e_i$.")

st.dataframe(pd.DataFrame([{"Recta": n, f"a ({ctx.ua})": estilo.fmt(a), "b (ms)": estilo.fmt(b), "S (ms²)": estilo.fmt(s),
                            "S / S_mín": f"{s / aj.s_min:.4g}"} for n, a, b, s in filas]), hide_index=True, width="stretch")
mejores = all(f[3] >= aj.s_min for f in filas[1:])
st.success("Comprobación: todas las rectas elegidas tienen $S \\ge S_{\\min}$.") if mejores else st.error("Una recta elegida tiene S menor que S_mín: revisar.")

st.header("Análisis de la recta")
t = ctx.calidad
idx_max = int(abs(ctx.y - (aj.a * ctx.x + aj.b)).argmax())
st.markdown(
    f"- **Tendencia general:** con $R^2 = {t.r2:.6f}$ la recta reproduce la tendencia creciente de los datos prácticamente en todo el rango "
    f"(RMSE = {estilo.fmt(t.rmse)} ms, es decir, {estilo.fmt(100 * t.rmse / ctx.y.mean(), 3)} % del tiempo medio).\n"
    f"- **Mayor desviación:** el punto n.º {idx_max + 1} (x = {estilo.fmt(ctx.x[idx_max])}) con |e| = {estilo.fmt(t.max_abs_residuo)} ms.\n"
    f"- **Puntos influyentes:** consulte la página *Análisis adicional → Opción B* para saber si algún punto alejado condiciona la recta."
)
