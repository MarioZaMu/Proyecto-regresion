"""Página 6: comparación analítico (manual) / código propio / biblioteca."""
import pandas as pd
import streamlit as st

from core import verificacion
from interfaz import contexto, estilo

ctx = contexto.cargar()
contexto.cabecera("Comparación de métodos")
contexto.tarjetas(ctx)

st.header("Su resultado analítico (hecho a mano)")
st.caption(f"Escriba los valores obtenidos en papel, en las unidades activas: a en {ctx.ua}, b en ms, S en ms² "
           f"(x en {ctx.ux}). Admite notación científica, p. ej. 2.5e-5.")
c = st.columns(3)
txt = {}
with c[0]:
    txt["a"] = estilo.persistente(st.text_input, "a (manual)", "man_a", "", placeholder="p. ej. 2.6325")
with c[1]:
    txt["b"] = estilo.persistente(st.text_input, "b (manual)", "man_b", "", placeholder="p. ej. 0.0123")
with c[2]:
    txt["S"] = estilo.persistente(st.text_input, "S_mín (manual)", "man_s", "", placeholder="p. ej. 0.512")


def parsear(t: str):
    t = t.strip().replace(",", ".")
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return "error"


vals = {k: parsear(v) for k, v in txt.items()}
for k, v in vals.items():
    if v == "error":
        st.error(f"El valor manual de {k} no es un número válido.")
        vals[k] = None
manual = (vals["a"], vals["b"], vals["S"])
if all(v is None for v in manual):
    st.info("Aún no ha ingresado su resultado manual: la columna «Analítico (manual)» aparece vacía y la diferencia máxima compara solo código propio y biblioteca.")

r = verificacion.comparar(ctx.x, ctx.y, manual)
st.header("Tabla comparativa")
tabla = r["tabla"].copy()
for col in tabla.columns[1:]:
    tabla[col] = [estilo.fmt(v) if col != "Diferencia máxima" else estilo.fmt(v, 3) for v in tabla[col]]
tabla.columns = ["Parámetro", "Analítico (manual)", "Código propio", "Biblioteca de Python", "Diferencia máxima"]
tabla["Parámetro"] = ["a", "b", "S_mín"]
st.dataframe(tabla, hide_index=True, width="stretch")
st.caption("«Biblioteca de Python» = `scipy.stats.linregress`; S_mín de la biblioteca se evalúa con la definición de S usando sus a y b.")

with st.expander("Detalle por método (incluye numpy.polyfit)", expanded=True):
    det = r["detalle"].copy()
    for col in ("a", "b", "S_mín"):
        det[col] = [estilo.fmt(v, 10) for v in det[col]]
    st.dataframe(det, hide_index=True, width="stretch")

st.header("Análisis de las diferencias")
d = r["tabla"]
dmax_rel = max(float(d.loc[i, "Diferencia máxima"] / abs(d.loc[i, "Código propio"])) for i in range(3) if d.loc[i, "Código propio"] != 0)
st.markdown(
    f"- Entre **código propio** y **bibliotecas** la diferencia relativa máxima es **{estilo.fmt(dmax_rel, 3)}**, del orden del épsilon de máquina "
    "de `float64` (~2.2·10⁻¹⁶): los tres métodos resuelven el mismo problema y solo difieren por **redondeo de punto flotante** "
    "(`polyfit` usa descomposición QR / mínimos cuadrados con SVD; `linregress` usa covarianzas; el código propio usa las fórmulas normales).\n"
    "- Si su valor **manual** difiere más (p. ej. en la 4.ª o 5.ª cifra), la causa suele ser el **redondeo** de las sumatorias al hacer las cuentas a mano, "
    "o usar unidades distintas a las activas. Una diferencia grande indica un error algebraico o de transcripción.\n"
    "- $S_{\\min}$ es especialmente sensible: resulta de restar cantidades casi iguales, así que su diferencia relativa es mayor que la de $a$ y $b$."
)
