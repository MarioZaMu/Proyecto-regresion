"""Exportación: figuras PNG (ZIP) y resumen de resultados en Markdown y PDF."""
from __future__ import annotations

import io
import zipfile
from datetime import datetime

import numpy as np

import config
from core import extras, metricas, regresion, verificacion
from interfaz import estilo
from interfaz.contexto import Ctx

CLAVES_TEXTO = {
    "txt_centrado": "¿Los residuos están centrados alrededor de cero?",
    "txt_patron": "¿Presentan alguna tendencia o patrón?",
    "txt_dispersion": "¿Aumenta o disminuye su dispersión con x?",
    "txt_atipicos": "¿Existen valores atípicos?",
    "txt_sistematica": "¿Hay regiones con desviación sistemática?",
    "txt_rmse_r2": "Interpretación de RMSE y R² para estos datos",
}


def figura_png(fig, ancho: int = 1100, alto: int | None = None) -> bytes:
    """Renderiza una figura a PNG con kaleido (requiere Chrome/Chromium instalado)."""
    return fig.to_image(format="png", width=ancho, height=alto or int(fig.layout.height or 480), scale=2)


def zip_figuras(figs: dict) -> tuple[bytes, list[str]]:
    """Empaqueta todas las figuras en un ZIP; devuelve (bytes, lista de fallos)."""
    buf = io.BytesIO()
    fallos: list[str] = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, fig in figs.items():
            try:
                z.writestr(f"{nombre}.png", figura_png(fig))
            except Exception as e:  # noqa: BLE001
                fallos.append(f"{nombre}: {e}")
    return buf.getvalue(), fallos


def _datos_resumen(ctx: Ctx, manual: tuple, textos: dict) -> dict:
    comp = verificacion.comparar(ctx.x, ctx.y, manual)
    diag = metricas.diagnostico(ctx.ajuste.a, ctx.ajuste.b, ctx.x, ctx.y)
    infl = extras.mas_influyente(ctx.x, ctx.y)
    r_infl = extras.sin_punto(ctx.x, ctx.y, infl)
    q = extras.ajustar_cuadratico(ctx.x, ctx.y) if len(ctx.x) >= 4 else None
    return dict(comp=comp, diag=diag, infl=infl, r_infl=r_infl, q=q)


def resumen_markdown(ctx: Ctx, manual: tuple, textos: dict[str, str]) -> str:
    """Resumen de resultados en Markdown."""
    d = _datos_resumen(ctx, manual, textos)
    aj, cal, cl = ctx.ajuste, ctx.calidad, ctx.clasif
    f = estilo.fmt
    origen = ctx.meta.get("origen", "")
    L = [f"# {config.TITULO_PROYECTO}", "",
         f"**Curso:** {config.CURSO} · **Universidad:** {config.UNIVERSIDAD} · **Estudiante:** {config.ESTUDIANTE}",
         f"**Fecha de generación:** {datetime.now():%Y-%m-%d %H:%M}", ""]
    if origen == "entorno_dev":
        L += ["> **DATOS DE PRUEBA** del entorno de desarrollo: ejecutar `datos/medir.py` en el equipo del estudiante.", ""]
    L += ["## 1. Problema", "Tiempo de ejecución de una búsqueda lineal (peor caso) en función del tamaño de la entrada. "
          "Modelo `T = a·n + b` con n = tamaño (elementos) y T = tiempo (ms).",
          f"Unidades de x en este resumen: **{ctx.ux}**. Número de puntos: **{len(ctx.x)}**.", "",
          "## 2. Resultados del ajuste", "",
          "| Magnitud | Valor | Unidades |", "|---|---|---|",
          f"| a* | {f(aj.a)} | {ctx.ua} |", f"| b* | {f(aj.b)} | ms |", f"| S_mín | {f(aj.s_min)} | ms² |",
          f"| RMSE | {f(cal.rmse)} | ms |", f"| R² | {cal.r2:.6f} | — |",
          f"| a* en ns/elemento | {f(ctx.a_ns_por_elemento)} | ns/elemento |", "",
          "## 3. Hessiano", "",
          f"H = [[{f(cl.hessiano[0, 0])}, {f(cl.hessiano[0, 1])}], [{f(cl.hessiano[1, 0])}, {f(cl.hessiano[1, 1])}]]",
          f"- det H = {f(cl.det)} > 0 y S_aa = {f(cl.s_aa)} > 0",
          f"- Autovalores: λ₁ = {f(cl.autovalores[0])}, λ₂ = {f(cl.autovalores[1])}",
          f"- Conclusión: **{cl.tipo}** (S es convexa: mínimo global).", "",
          "## 4. Comparación de métodos", "", "| Parámetro | Analítico (manual) | Código propio | Biblioteca (linregress) | Diferencia máxima |",
          "|---|---|---|---|---|"]
    for _, r in d["comp"]["tabla"].iterrows():
        L.append(f"| {r['Parámetro']} | {f(r['Analítico (manual)'])} | {f(r['Código propio'])} | "
                 f"{f(r['Biblioteca (linregress)'])} | {f(r['Diferencia máxima'], 3)} |")
    dg = d["diag"]
    L += ["", "## 5. Residuos", "",
          f"- Media de residuos: {f(cal.media_residuos, 3)} ms; desviación: {f(cal.desv_residuos)} ms; máx |e|: {f(cal.max_abs_residuo)} ms",
          f"- Correlación e–(x−x̄)² (curvatura): {dg['corr_curvatura']:.3f}; correlación |e|–x: {dg['corr_abs_x']:.3f}",
          f"- Cambios de signo: {dg['cambios_signo']} (esperados ≈ {dg['cambios_esperados']:.1f})",
          f"- Media de residuos por tercios de x: {', '.join(f(v, 3) for v in dg['medias_tercios'])} ms", ""]
    for k, titulo in CLAVES_TEXTO.items():
        t = (textos.get(k) or "").strip()
        if t:
            L += [f"**{titulo}** {t}", ""]
    ri = d["r_infl"]
    L += ["## 6. Análisis adicional", "",
          f"**Opción B.** Punto más influyente (distancia de Cook): n.º {d['infl'] + 1} (x = {f(ctx.x[d['infl']])}). "
          f"Al eliminarlo: a = {f(ri['nuevo'].a)} (Δ = {100 * ri['delta_a_rel']:.3f} %), b = {f(ri['nuevo'].b)}.", ""]
    q = d["q"]
    if q is not None:
        L += [f"**Opción C.** Modelo cuadrático: c₂ = {f(q.c2)}, c₁ = {f(q.c1)}, c₀ = {f(q.c0)}; "
              f"S = {f(q.s)} (lineal: {f(aj.s_min)}); R² ajustado = {q.r2_ajustado:.6f}; "
              f"p(F) = {f(q.p_f, 3)}; aporte relativo del término cuadrático en x máx = {100 * q.aporte_relativo:.3f} %.", ""]
    L += ["---", "*El desarrollo analítico (derivadas parciales, sistema normal, Hessiano) se realizó manualmente en papel.*"]
    return "\n".join(L)


def resumen_pdf(ctx: Ctx, manual: tuple, textos: dict[str, str], imagenes: dict[str, bytes]) -> bytes:
    """Resumen en PDF (ReportLab) con tablas y las figuras principales."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.platypus import Paragraph as _Paragraph

    mapa = str.maketrans({"Δ": "var. ", "≈": "~", "₂": "2", "₁": "1", "₀": "0", "−": "-", "≤": "<=", "·": "·"})

    def Paragraph(texto, estilo):  # noqa: N802 - fuentes estándar del PDF no incluyen estos símbolos
        return _Paragraph(texto.translate(mapa), estilo)

    d = _datos_resumen(ctx, manual, textos)
    aj, cal, cl = ctx.ajuste, ctx.calidad, ctx.clasif
    f = estilo.fmt
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=17, leading=21, textColor=colors.HexColor(config.COLOR_PRIMARIO))
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12.5, textColor=colors.HexColor("#1F2937"))
    cuerpo = ParagraphStyle("c", parent=ss["BodyText"], fontSize=9.5, leading=13)

    def tabla(filas, anchos=None):
        t = Table(filas, colWidths=anchos, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(config.COLOR_PRIMARIO)), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9CA3AF")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        return t

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title=config.TITULO_PROYECTO, author=config.ESTUDIANTE)
    S = [Paragraph(config.TITULO_PROYECTO, h1),
         Paragraph(f"{config.CURSO} · {config.UNIVERSIDAD} · {config.ESTUDIANTE}<br/>Generado: {datetime.now():%Y-%m-%d %H:%M}", cuerpo)]
    if ctx.meta.get("origen") == "entorno_dev":
        S += [Spacer(1, 6), Paragraph("<b>DATOS DE PRUEBA</b> del entorno de desarrollo: ejecutar datos/medir.py en el equipo del estudiante.",
                                      ParagraphStyle("w", parent=cuerpo, textColor=colors.HexColor(config.COLOR_ACENTO)))]
    S += [Paragraph("1. Resultados del ajuste", h2),
          Paragraph(f"Modelo T = a·n + b. Unidades de x: {ctx.ux}. Puntos: {len(ctx.x)}.", cuerpo),
          tabla([["Magnitud", "Valor", "Unidades"], ["a*", f(aj.a), ctx.ua], ["b*", f(aj.b), "ms"], ["S_mín", f(aj.s_min), "ms²"],
                 ["RMSE", f(cal.rmse), "ms"], ["R²", f"{cal.r2:.6f}", "—"], ["a* (ns/elemento)", f(ctx.a_ns_por_elemento), "ns/elemento"]],
                [5 * cm, 5 * cm, 5 * cm]),
          Paragraph("2. Hessiano", h2),
          Paragraph(f"H = [[{f(cl.hessiano[0, 0])}, {f(cl.hessiano[0, 1])}], [{f(cl.hessiano[1, 0])}, {f(cl.hessiano[1, 1])}]]<br/>"
                    f"det H = {f(cl.det)} &gt; 0, S_aa = {f(cl.s_aa)} &gt; 0; autovalores {f(cl.autovalores[0])} y {f(cl.autovalores[1])}.<br/>"
                    f"Conclusión: <b>{cl.tipo}</b> (S convexa: mínimo global).", cuerpo),
          Paragraph("3. Comparación de métodos", h2)]
    filas = [["Parámetro", "Analítico (manual)", "Código propio", "Biblioteca", "Dif. máxima"]]
    for _, r in d["comp"]["tabla"].iterrows():
        filas.append([r["Parámetro"], f(r["Analítico (manual)"]), f(r["Código propio"]), f(r["Biblioteca (linregress)"]), f(r["Diferencia máxima"], 3)])
    S.append(tabla(filas, [3 * cm, 3.6 * cm, 3.6 * cm, 3.6 * cm, 3.2 * cm]))
    dg = d["diag"]
    S += [Paragraph("4. Residuos", h2),
          Paragraph(f"Media {f(cal.media_residuos, 3)} ms · desv. {f(cal.desv_residuos)} ms · máx |e| {f(cal.max_abs_residuo)} ms · "
                    f"corr. de curvatura {dg['corr_curvatura']:.3f} · cambios de signo {dg['cambios_signo']} (esperados ≈ {dg['cambios_esperados']:.1f}).", cuerpo)]
    for k, titulo in CLAVES_TEXTO.items():
        t = (textos.get(k) or "").strip()
        if t:
            S.append(Paragraph(f"<b>{titulo}</b> {t.replace(chr(10), '<br/>')}", cuerpo))
    ri = d["r_infl"]
    S += [Paragraph("5. Análisis adicional", h2),
          Paragraph(f"<b>Opción B.</b> Punto más influyente: n.º {d['infl'] + 1}. Al eliminarlo a = {f(ri['nuevo'].a)} "
                    f"(Δ = {100 * ri['delta_a_rel']:.3f} %), b = {f(ri['nuevo'].b)}.", cuerpo)]
    if d["q"] is not None:
        q = d["q"]
        S.append(Paragraph(f"<b>Opción C.</b> Cuadrático: c₂ = {f(q.c2)}; S = {f(q.s)} (lineal {f(aj.s_min)}); "
                           f"p(F) = {f(q.p_f, 3)}; aporte del término cuadrático = {100 * q.aporte_relativo:.3f} %.".replace("₂", "2"), cuerpo))
    for nombre, png in imagenes.items():
        S += [Spacer(1, 8), Image(io.BytesIO(png), width=16 * cm, height=16 * cm * 0.45, kind="proportional")]
    S.append(Paragraph("<i>El desarrollo analítico se realizó manualmente en papel.</i>", cuerpo))
    doc.build(S)
    return buf.getvalue()
