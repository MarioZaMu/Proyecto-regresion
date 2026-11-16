"""Página 1: datos, ficha técnica, dispersión y justificación de la linealidad."""
import pandas as pd
import streamlit as st

from core import datos as dat
from core import regresion
from interfaz import contexto, estilo, graficas

# Escala de x (se guarda fuera del widget para que persista entre páginas)
st.session_state.setdefault("escala_activa", True)
ctx = contexto.cargar()
contexto.cabecera("Datos del experimento")
contexto.tarjetas(ctx)

# ------------------------------------------------------------------ problema y ficha
st.header("Problema elegido")
st.markdown(
    "**Tiempo de ejecución de una búsqueda lineal en función del tamaño de la entrada.** "
    "Se mide cuánto tarda un `for` propio en recorrer una lista de $n$ enteros buscando un elemento que **no está** "
    "(peor caso: se hacen exactamente $n$ comparaciones)."
)
st.markdown(
    r"""
| Variable | Símbolo | Descripción | Unidades |
|---|---|---|---|
| Independiente | $x = n$ | Tamaño de la entrada | elementos (o $10^5$ elementos si se escala) |
| Dependiente | $y = T$ | Tiempo de ejecución (mediana de 5 mediciones) | ms |
"""
)
meta = ctx.meta
exp = meta.get("experimento", {})
with st.expander("Ficha técnica del experimento (metadata.json)", expanded=True):
    if ctx.usuario:
        st.info("Se están usando datos cargados desde un archivo CSV por el usuario.")
    filas = [
        ("Origen", meta.get("origen", "—")), ("Fecha y hora", meta.get("fecha_hora", "—")),
        ("Python", meta.get("python", "—")), ("Sistema operativo", meta.get("sistema_operativo", "—")),
        ("Procesador", meta.get("procesador", "—")), ("RAM (GB)", meta.get("ram_gb", "—")),
        ("Descripción", exp.get("descripcion", "—")), ("Algoritmo", exp.get("algoritmo", "—")),
        ("Calentamiento (descartadas)", exp.get("calentamiento", "—")), ("Repeticiones por n", exp.get("repeticiones", "—")),
        ("Estadístico guardado", exp.get("estadistico", "—")), ("Cronómetro", exp.get("cronometro", "—")),
    ]
    st.dataframe(pd.DataFrame(filas, columns=["Campo", "Valor"]).astype(str), hide_index=True, width="stretch")

# ------------------------------------------------------------------ escala
st.header("Escala de x")
estilo.persistente(st.checkbox, "Escalar x a unidades de 10⁵ elementos (recomendado)", "escala_activa", True,
                   help="Evita números enormes en Σx², en el Hessiano y en la superficie S(a, b).")
if ctx.escala:
    st.markdown(
        r"""**Conversión usada.** $x' = \dfrac{n}{10^{5}}$, de modo que $n = 10^{5}\,x'$.  
Si se ajusta $T = a'\,x' + b'$, entonces $T = a'\dfrac{n}{10^5} + b'$, es decir  
$$a_{\text{original}} = \frac{a'}{10^{5}}\ \ \text{(ms/elemento)},\qquad b_{\text{original}} = b'\ \ \text{(ms)} .$$
$S_{\min}$, RMSE y $R^2$ **no cambian** con la escala; solo cambian $a^*$ y las entradas del Hessiano."""
    )
else:
    st.markdown("Se usan los valores originales de $n$ (elementos). Las sumas como $\\sum x^2$ llegan a ~$10^{13}$.")

# ------------------------------------------------------------------ tabla
st.header("Tabla de datos")
tabla = pd.DataFrame({"n (elementos)": ctx.x_raw.astype(int)})
if ctx.escala:
    tabla["x = n/10⁵ (×10⁵ elementos)"] = ctx.x
tabla["y = T (ms)"] = ctx.y
st.dataframe(tabla, hide_index=True, width="stretch",
             column_config={"n (elementos)": st.column_config.NumberColumn(format="%d"),
                            "y = T (ms)": st.column_config.NumberColumn(format="%.4f")})
st.caption(f"{len(ctx.x)} puntos · T mínimo {estilo.fmt(ctx.y.min(), 4)} ms · T máximo {estilo.fmt(ctx.y.max(), 4)} ms")

# ------------------------------------------------------------------ dispersión
st.header("Diagrama de dispersión")
estilo.mostrar(graficas.dispersion(ctx), "disp")
estilo.pie("Los puntos siguen una **trayectoria aproximadamente recta** que crece con $n$: al duplicar el tamaño de la entrada el tiempo "
           "se duplica, sin curvatura apreciable a simple vista. Esto hace razonable proponer $y = ax + b$. "
           "Las pequeñas desviaciones respecto a una recta perfecta se estudian con los residuos (página *Calidad y residuos*).")

st.subheader("¿Por qué esperar una relación lineal? (O(n))")
st.markdown(
    r"""Una búsqueda lineal inspecciona cada elemento una vez; en el peor caso (elemento ausente) realiza exactamente $n$ comparaciones, 
por lo que su complejidad es $O(n)$ y su tiempo se modela como
$$T(n) \approx a\,n + b,$$
donde $a$ es el **costo por elemento** (una iteración del bucle: comparar, avanzar el índice) y $b$ el **costo fijo de arranque** 
(llamada a la función, lectura del cronómetro). El **ruido** de las mediciones viene del sistema real: planificador del SO, 
memoria caché de la CPU, recolector de basura, otros procesos y variaciones de frecuencia del procesador."""
)

# ------------------------------------------------------------------ interpretación
st.header("Interpretación de a* y b*")
a_ns = ctx.a_ns_por_elemento
b = ctx.ajuste.b
t_fin = ctx.ajuste.a * ctx.x.max() + b
st.markdown(
    f"- **a\\* = {estilo.fmt(ctx.ajuste.a)} {ctx.ua}** equivale a **{estilo.fmt(a_ns, 4)} ns por elemento**: "
    f"cada elemento adicional de la lista añade en promedio ese tiempo a la búsqueda.\n"
    f"- **b\\* = {estilo.fmt(b)} ms** es el sobrecosto fijo estimado (valor de $T$ extrapolado a $n = 0$). "
    + ("Es **negativo**, lo cual no tiene sentido físico literal: es una extrapolación fuera del rango medido (nunca se midió $n$ cercano a 0) "
       "combinada con el ruido; su magnitud es pequeña frente a $T$ en el extremo del rango "
       f"({estilo.fmt(abs(b) / t_fin * 100, 3)} % de {estilo.fmt(t_fin, 4)} ms)."
       if b < 0 else
       f"Representa el {estilo.fmt(abs(b) / t_fin * 100, 3)} % del tiempo total en el mayor tamaño medido ({estilo.fmt(t_fin, 4)} ms), "
       "es decir, el costo de arranque es despreciable frente al costo por elemento.")
)

# ------------------------------------------------------------------ carga de datos
with st.expander("Usar otro conjunto de datos (opcional)"):
    st.caption("Suba un CSV con columnas `x` e `y`. Se valida: mínimo 3 puntos y x no todos iguales.")
    archivo = st.file_uploader("Archivo CSV", type="csv")
    if archivo is not None:
        try:
            nuevo = pd.read_csv(archivo)
            if not {"x", "y"} <= set(nuevo.columns):
                raise ValueError("El CSV debe tener las columnas `x` e `y`.")
            nuevo = nuevo[["x", "y"]].apply(pd.to_numeric, errors="coerce").astype(float)
            problemas = regresion.validar(nuevo["x"].to_numpy(), nuevo["y"].to_numpy())
            if problemas:
                for p in problemas:
                    st.error(p)
            else:
                st.session_state["df_usuario"] = nuevo
                st.success("Datos cargados. Todas las páginas usan ahora este conjunto.")
                st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"No se pudo leer el archivo: {e}")
    if st.session_state.get("df_usuario") is not None and st.button("Volver a los datos medidos"):
        st.session_state.pop("df_usuario", None)
        st.rerun()
