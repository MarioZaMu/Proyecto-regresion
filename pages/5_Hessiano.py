"""Página 5: Hessiano, autovalores y verificación numérica."""
import numpy as np
import pandas as pd
import streamlit as st

from core import regresion
from interfaz import contexto, estilo

ctx = contexto.cargar()
contexto.cabecera("Hessiano y naturaleza del punto crítico")
contexto.tarjetas(ctx)
aj, cl = ctx.ajuste, ctx.clasif

st.header("Matriz hessiana")
st.latex("H = " + estilo.matriz_latex(cl.hessiano) + r"= \begin{pmatrix} 2\sum x_i^2 & 2\sum x_i \\ 2\sum x_i & 2n \end{pmatrix}")
c = st.columns(4)
for col, (n_, v) in zip(c, [("S_aa = 2Σx²", cl.s_aa), ("S_ab = 2Σx", cl.hessiano[0, 1]), ("S_bb = 2n", cl.hessiano[1, 1]), ("det H", cl.det)]):
    with col.container(border=True):
        st.metric(n_, estilo.fmt(v))

st.header("Criterio de las segundas derivadas")
cond = [("det H > 0", cl.det > 0), ("S_aa > 0", cl.s_aa > 0)]
for txt, ok in cond:
    st.markdown(f"{':green[✔]' if ok else ':red[✘]'} {txt}")
st.success(f"**Conclusión: {cl.tipo}.** $\\det H = {estilo.latex_num(cl.det)} > 0$ y $S_{{aa}} = {estilo.latex_num(cl.s_aa)} > 0$.")

st.header("Autovalores")
ev_num = np.linalg.eigvalsh(cl.hessiano)
t = pd.DataFrame({"": ["λ₁ (menor)", "λ₂ (mayor)"], "Fórmula cerrada": [estilo.fmt(v, 8) for v in cl.autovalores],
                  "numpy.linalg.eigvalsh": [estilo.fmt(v, 8) for v in ev_num]})
st.dataframe(t, hide_index=True, width="stretch")
cond_num = cl.autovalores[1] / cl.autovalores[0]
st.markdown(f"Ambos autovalores son **positivos** ⇒ $H$ es definida positiva. Número de condición $\\lambda_2/\\lambda_1 = {estilo.fmt(cond_num, 4)}$: "
            f"{'las elipses de nivel son muy alargadas (valle estrecho): a y b están fuertemente correlacionados.' if cond_num > 50 else 'las elipses de nivel son moderadamente alargadas.'}")
pd_ok = bool(np.all(ev_num > 0))
try:
    np.linalg.cholesky(cl.hessiano)
    chol = True
except np.linalg.LinAlgError:
    chol = False
st.caption(f"Comprobaciones adicionales: autovalores > 0: {pd_ok} · factorización de Cholesky existe: {chol} · menores principales (S_aa, det H) > 0: {cl.s_aa > 0 and cl.det > 0}.")

st.header("Verificación numérica (diferencias finitas)")
factor = estilo.persistente(st.select_slider, "Tamaño del paso (fracción de la escala de los datos)", "hes_paso", 1e-2,
                            options=[1e-1, 1e-2, 1e-3, 1e-4], format_func=lambda v: f"{v:g}")
ha, hb = regresion.pasos_por_defecto(ctx.x, ctx.y, factor)
hn = regresion.hessiano_numerico(ctx.x, ctx.y, aj.a, aj.b, ha, hb)
st.caption(f"Pasos usados: h_a = {estilo.fmt(ha, 4)}, h_b = {estilo.fmt(hb, 4)}. Como S es cuadrática, las diferencias centrales son exactas salvo redondeo.")
filas = []
for nombre, (i, j) in {"S_aa": (0, 0), "S_ab": (0, 1), "S_bb": (1, 1)}.items():
    an, nu = cl.hessiano[i, j], hn[i, j]
    filas.append({"Elemento": nombre, "Analítico": estilo.fmt(an, 8), "Numérico": estilo.fmt(nu, 8),
                  "Error absoluto": estilo.fmt(abs(an - nu), 3), "Error relativo": estilo.fmt(abs(an - nu) / abs(an), 3)})
st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
err = float(np.max(np.abs(hn - cl.hessiano) / np.abs(cl.hessiano)))
if err < 1e-4:
    st.success(f"Error relativo máximo: {estilo.fmt(err, 3)} → el Hessiano analítico queda verificado.")
else:
    st.warning(f"Error relativo máximo: {estilo.fmt(err, 3)} → pruebe con otro paso.")

st.subheader("Gradiente en el punto crítico")
g_an = regresion.gradiente(aj.a, aj.b, ctx.x, ctx.y)
g_nu = regresion.gradiente_numerico(ctx.x, ctx.y, aj.a, aj.b, ha, hb)
esc = np.array([np.sum(np.abs(ctx.x * ctx.y)), np.sum(np.abs(ctx.y))])
st.dataframe(pd.DataFrame({"Componente": ["∂S/∂a", "∂S/∂b"], "Analítico": [estilo.fmt(v, 4) for v in g_an],
                           "Numérico": [estilo.fmt(v, 4) for v in g_nu], "Relativo a la escala de las sumas": [estilo.fmt(abs(v) / s, 3) for v, s in zip(g_an, esc)]}),
             hide_index=True, width="stretch")
st.caption("Ambas componentes son cero salvo errores de redondeo del orden de la precisión de máquina (~10⁻¹⁶ relativo).")

st.subheader("Convexidad")
cv = regresion.verificar_convexidad(ctx.x, ctx.y, aj)
st.markdown(f"Se probó $S(t p + (1-t)q) \\le t S(p) + (1-t) S(q)$ en {cv['pares']} pares aleatorios $(p, q)$ con $t \\in [0,1]$: "
            f"**se cumplió en {cv['cumplen']} de {cv['pares']}**. Como $H$ es definida positiva y constante, $S$ es convexa en todo $\\mathbb{{R}}^2$ y el mínimo es global.")
