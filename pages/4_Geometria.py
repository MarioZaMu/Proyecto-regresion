"""Página 4: superficie, curvas de nivel, trazas y secciones transversales."""
import numpy as np
import streamlit as st

from core.regresion import sumas
from interfaz import contexto, estilo, graficas

ctx = contexto.cargar()
contexto.cabecera("Geometría de la función de error")
contexto.tarjetas(ctx)
aj = ctx.ajuste
k = int(ctx.escala)
s = sumas(ctx.x, ctx.y)

c1, c2 = st.columns(2)
with c1:
    frac = estilo.persistente(st.select_slider, "Amplitud de la región (fracción de la variación total SST)", "geo_frac", 0.05,
                              options=[0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5], format_func=lambda v: f"{100 * v:g} %",
                              help="La región mostrada es {S ≤ S_mín + fracción·SST}.")
with c2:
    log = estilo.persistente(st.checkbox, "Usar log₁₀ S en la superficie", "geo_log", False)
da, db = graficas.region(ctx, frac)
st.caption(f"Región: a ∈ [{estilo.fmt(aj.a - da, 4)}, {estilo.fmt(aj.a + da, 4)}] {ctx.ua} · b ∈ [{estilo.fmt(aj.b - db, 4)}, {estilo.fmt(aj.b + db, 4)}] ms")

st.header("Superficie z = S(a, b)")
estilo.mostrar(graficas.superficie(ctx, frac, log), "sup")
estilo.pie("La superficie es un **paraboloide elíptico** abierto hacia arriba (porque $H$ es definida positiva): tiene un único punto más bajo, "
           "marcado en rojo, que corresponde a $(a^*, b^*)$. Su forma de **valle alargado** indica que $a$ y $b$ están fuertemente correlacionados: "
           "se puede cambiar $a$ y compensarlo con $b$ sin aumentar mucho el error. Arrastre para rotar.")

st.header("Curvas de nivel")
niveles = estilo.persistente(st.slider, "Número de curvas de nivel", "geo_niv", 14, min_value=6, max_value=30)
estilo.mostrar(graficas.contornos(ctx, frac, niveles), "cont")
estilo.pie("Cada curva une pares $(a,b)$ con el **mismo error** $S$ (escala logarítmica). Son **elipses concéntricas** alrededor de $(a^*, b^*)$ "
           "y se separan más a medida que nos alejamos, como corresponde a una función cuadrática. La inclinación y el alargamiento de las elipses "
           "reflejan el término cruzado $S_{ab} = 2\\sum x_i \\neq 0$. Las curvas más internas rodean la región de mínimo error.")

st.header("Trazas de la superficie")
estilo.mostrar(graficas.trazas(ctx, "b", frac), "tr_b")
estilo.pie("Cada curva es la intersección de la superficie con un plano $b = $ constante. **Todas son parábolas** en $a$ con la misma curvatura "
           "$S_{aa} = 2\\sum x_i^2$; solo cambian su altura y la posición del vértice. La de $b = b^*$ (azul) es la más baja pasando por el mínimo.")
estilo.mostrar(graficas.trazas(ctx, "a", frac), "tr_a")
estilo.pie("Planos $a = $ constante: parábolas en $b$ de curvatura $S_{bb} = 2n$, mucho menos pronunciada que la de $a$. Las parábolas "
           "de $a$ distinto de $a^*$ quedan **por encima** y desplazadas: no se puede reducir el error cambiando solo $b$ si $a$ es incorrecto.")

st.header("Secciones transversales")
fija = estilo.persistente(st.radio, "Variable que se fija", "geo_fija", "b", options=["b", "a"], horizontal=True)
if fija == "b":
    v = estilo.persistente(st.slider, "Valor fijo de b (ms)", f"geo_b_{k}", float(aj.b), min_value=float(aj.b - db), max_value=float(aj.b + db), step=float(db / 200), format="%.6g")
else:
    v = estilo.persistente(st.slider, f"Valor fijo de a ({ctx.ua})", f"geo_a_{k}", float(aj.a), min_value=float(aj.a - da), max_value=float(aj.a + da), step=float(da / 200), format="%.6g")
fig, opt, smin = graficas.seccion(ctx, fija, v, frac)
estilo.mostrar(fig, "sec")
otra = "a" if fija == "b" else "b"
estilo.pie(f"Con ${fija} = {estilo.fmt(v, 5)}$ fijo, $S$ es una parábola en ${otra}$ cuyo mínimo (rombo rojo) está en ${otra} = {estilo.fmt(opt, 6)}$ con "
           f"$S = {estilo.fmt(smin, 5)}$. Ese mínimo coincide con $S_{{\\min}} = {estilo.fmt(aj.s_min, 5)}$ **solo cuando** el valor fijo es el óptimo "
           f"(${fija}^* = {estilo.fmt(aj.b if fija == 'b' else aj.a, 6)}$); en otro caso es mayor. Esto muestra que $\\partial S/\\partial {otra} = 0$ "
           f"da el mejor valor de ${otra}$ *dado* ${fija}$, y que el mínimo global es la intersección de ambos óptimos condicionados.")

st.header("Cómo se identifica el mejor ajuste")
st.markdown(
    "Superficie, trazas, secciones y curvas de nivel cuentan la misma historia: $S(a,b)$ es una función cuadrática convexa con un **único valle** cuyo "
    "fondo está en $(a^*, b^*)$. En ese punto el plano tangente es horizontal ($\\nabla S = \\mathbf 0$: en las trazas, la pendiente es nula en el vértice) y las "
    "curvas de nivel se cierran sobre un punto. Cualquier otra recta queda en un nivel de error más alto."
)
