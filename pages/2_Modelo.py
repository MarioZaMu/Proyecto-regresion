"""Página 2: modelo y derivación (solo referencia)."""
import streamlit as st

from interfaz import contexto, estilo

ctx = contexto.cargar()
contexto.cabecera("Modelo y fórmulas")
contexto.tarjetas(ctx)
st.info("Esta página es **solo de referencia**. El desarrollo analítico exigido en el enunciado (derivadas parciales, "
        "sistema normal, solución y Hessiano) lo realiza el estudiante **manualmente en papel**; aquí se muestra el resultado esperado "
        "para contrastarlo.", icon=":material/edit_note:")

st.header("1. Modelo y función de error")
st.markdown(r"""Modelo: $y = ax + b$. Con datos $(x_i, y_i)$, $i = 1,\dots,n$, el valor predicho es $\hat y_i = a x_i + b$ y el residuo $e_i = y_i - (ax_i + b)$.""")
st.latex(r"S(a,b) = \sum_{i=1}^{n} (y_i - a x_i - b)^2")

st.header("2. Derivadas parciales")
st.latex(r"\frac{\partial S}{\partial a} = \sum_{i=1}^{n} 2\,(y_i - a x_i - b)(-x_i) = -2\sum_{i=1}^{n} x_i\,(y_i - a x_i - b)")
st.latex(r"\frac{\partial S}{\partial b} = \sum_{i=1}^{n} 2\,(y_i - a x_i - b)(-1) = -2\sum_{i=1}^{n} (y_i - a x_i - b)")

st.header("3. Punto crítico  ∇S = 0  y sistema normal")
st.latex(r"\nabla S(a,b) = \left(\frac{\partial S}{\partial a},\frac{\partial S}{\partial b}\right) = (0,0)")
st.markdown("Dividiendo entre $-2$ y distribuyendo las sumas se obtiene el **sistema normal**:")
st.latex(r"""\begin{cases} a\sum x_i^2 + b\sum x_i = \sum x_i y_i \\[2pt] a\sum x_i + n\,b = \sum y_i \end{cases}""")

st.header("4. Solución")
st.markdown(r"Con $D = n\sum x_i^2 - \left(\sum x_i\right)^2$ (por Cramer o eliminando $b$):")
st.latex(r"a^* = \frac{n\sum x_i y_i - \sum x_i \sum y_i}{n\sum x_i^2 - \left(\sum x_i\right)^2},\qquad "
         r"b^* = \frac{\sum y_i - a^*\sum x_i}{n} = \frac{\sum x_i^2\sum y_i - \sum x_i\sum x_i y_i}{D}")
st.markdown(r"Además, como en el óptimo $\sum e_i = 0$ y $\sum x_i e_i = 0$:")
st.latex(r"S_{\min} = \sum e_i y_i = \sum y_i^2 - a^*\sum x_i y_i - b^*\sum y_i")

st.header("5. Hessiano y criterio de las segundas derivadas")
st.latex(r"S_{aa} = 2\sum x_i^2,\qquad S_{bb} = 2n,\qquad S_{ab} = S_{ba} = 2\sum x_i")
st.latex(r"H = \begin{pmatrix} 2\sum x_i^2 & 2\sum x_i \\ 2\sum x_i & 2n \end{pmatrix},\qquad "
         r"\det H = 4\left[n\sum x_i^2 - \left(\sum x_i\right)^2\right] = 4n\sum (x_i-\bar x)^2")
st.markdown(r"""Por la desigualdad de Cauchy–Schwarz, $\det H > 0$ siempre que los $x_i$ **no sean todos iguales**; además $S_{aa} = 2\sum x_i^2 > 0$.  
Por el criterio de las segundas derivadas, $(a^*, b^*)$ es un **mínimo local estricto**. Como $H$ es constante (no depende de $a$, $b$) y definida positiva en todo $\mathbb R^2$, $S$ es **convexa** y el mínimo es **global y único**.""")

st.header("6. Sumatorias con los datos actuales (para contrastar su cálculo manual)")
s = ctx.ajuste.sumas
st.caption(f"Unidades de x: {ctx.ux}. Si cambia la escala en la página *Datos*, estas sumas cambian.")
c = st.columns(3)
for col, (n_, v) in zip(c * 2, [("n", s.n), ("Σx", s.sx), ("Σy", s.sy), ("Σx²", s.sxx), ("Σxy", s.sxy), ("Σy²", s.syy)]):
    col.metric(n_, estilo.fmt(v, 8))
den = s.n * s.sxx - s.sx ** 2
st.latex(rf"D = {estilo.latex_num(den, 8)},\quad a^* = \frac{{{estilo.latex_num(s.n * s.sxy - s.sx * s.sy, 8)}}}{{{estilo.latex_num(den, 8)}}} = {estilo.latex_num(ctx.ajuste.a, 8)},\quad b^* = {estilo.latex_num(ctx.ajuste.b, 8)}")
