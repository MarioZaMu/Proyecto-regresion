"""Página 9: exportación de figuras (PNG) y resumen (PDF / Markdown)."""
import streamlit as st

import config
from interfaz import contexto, estilo, exportar, graficas

ctx = contexto.cargar()
contexto.cabecera("Exportar resultados")
contexto.tarjetas(ctx)


def _num(t: str):
    try:
        return float(str(t).strip().replace(",", ".")) if str(t).strip() else None
    except ValueError:
        return None


ss = st.session_state
manual = (_num(ss.get("man_a", "")), _num(ss.get("man_b", "")), _num(ss.get("man_s", "")))
textos = {k: ss.get(k, "") for k in exportar.CLAVES_TEXTO}
st.caption("El resumen incluye los valores manuales de la página *Comparación* y los textos de *Calidad y residuos* que haya escrito.")

st.header("Resumen de resultados")
md = exportar.resumen_markdown(ctx, manual, textos)
c = st.columns(2)
c[0].download_button("Descargar resumen (Markdown)", md.encode("utf-8"), "resumen_resultados.md", "text/markdown", width="stretch")
with st.expander("Vista previa del resumen"):
    st.markdown(md)

st.header("Figuras en PNG")
st.caption("Se generan con fondo blanco y valores por defecto (tema claro). Requiere `kaleido` y Chrome/Chromium instalado.")
if st.button("Generar figuras y PDF", type="primary"):
    figs = graficas.todas(ctx)
    with st.spinner("Renderizando figuras (la superficie 3D puede tardar unos segundos)…"):
        zbytes, fallos = exportar.zip_figuras(figs)
        ss["zip_figuras"] = zbytes
        ss["fallos_export"] = fallos
        imgs = {}
        for nombre in ("02_ajuste", "04_curvas_de_nivel", "07_residuos"):
            try:
                imgs[nombre] = exportar.figura_png(figs[nombre])
            except Exception:  # noqa: BLE001
                pass
        try:
            ss["pdf_resumen"] = exportar.resumen_pdf(ctx, manual, textos, imgs)
        except Exception as e:  # noqa: BLE001
            ss["pdf_resumen"] = None
            fallos.append(f"PDF: {e}")
if ss.get("fallos_export"):
    st.warning("Algunos elementos no se pudieron generar:\n\n" + "\n".join(f"- {f}" for f in ss["fallos_export"]))
if ss.get("zip_figuras"):
    st.success("Figuras generadas.")
    d = st.columns(2)
    d[0].download_button("Descargar todas las figuras (ZIP de PNG)", ss["zip_figuras"], "figuras.zip", "application/zip", width="stretch")
    if ss.get("pdf_resumen"):
        d[1].download_button("Descargar resumen (PDF)", ss["pdf_resumen"], "resumen_resultados.pdf", "application/pdf", width="stretch")
