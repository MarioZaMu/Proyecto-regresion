"""Genera la presentación (PPTX) con los datos y figuras ACTUALES del proyecto.

Uso (desde la raíz del proyecto):   python presentacion/generar_pptx.py
Salida: presentacion/Presentacion_Regresion_Lineal.pptx

Si vuelve a correr ``datos/medir.py`` basta con ejecutar este script otra vez: todos los
números y gráficas se recalculan.  Requiere ``python-pptx`` y ``kaleido`` (+ Chrome).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

import config  # noqa: E402
from core import datos, extras, metricas, regresion, verificacion  # noqa: E402
from interfaz import estilo, graficas  # noqa: E402
from interfaz.contexto import Ctx  # noqa: E402

IMG = Path(__file__).resolve().parent / "img"
SALIDA = Path(__file__).resolve().parent / "Presentacion_Regresion_Lineal.pptx"

# ----------------------------------------------------------------- paleta
BG = RGBColor(0x0B, 0x10, 0x20)
CARD = RGBColor(0x15, 0x1A, 0x33)
TXT = RGBColor(0xF1, 0xF5, 0xF9)
SUB = RGBColor(0x94, 0xA3, 0xB8)
INDIGO = RGBColor(0x81, 0x8C, 0xF8)
CIAN = RGBColor(0x22, 0xD3, 0xEE)
ROSA = RGBColor(0xF4, 0x72, 0xB6)
NARANJA = RGBColor(0xFB, 0x92, 0x3C)
FUENTE = "Segoe UI"
FUENTE_MATE = "Cambria Math"

PERSONAS = {
    "N": "Nicoll López",
    "J": "Juan Jurado",
    "B": "Brayan Guerrero",
    "M": "Mario Zambrano",
}
COLOR_PERSONA = {"N": CIAN, "J": INDIGO, "B": NARANJA, "M": ROSA}


# ----------------------------------------------------------------- datos
def construir_ctx() -> Ctx:
    df = datos.cargar_csv()
    x = datos.escalar(df["x"].to_numpy(), True)
    y = df["y"].to_numpy()
    aj = regresion.ajustar(x, y)
    return Ctx(df, datos.cargar_metadata(), True, x, y, df["x"].to_numpy(), aj, metricas.calidad(aj.a, aj.b, x, y),
               regresion.clasificar(x), "n (×10⁵ elementos)", "T (ms)", "ms por 10⁵ elementos", "ms", False)


def figura_a_png(fig, nombre: str, ancho: int, alto: int) -> Path:
    fig.update_layout(title_text="", margin=dict(l=70, r=30, t=30, b=60), width=ancho, height=alto,
                      paper_bgcolor="#0B1020", plot_bgcolor="#0B1020")
    ruta = IMG / f"{nombre}.png"
    ruta.write_bytes(fig.to_image(format="png", width=ancho, height=alto, scale=2))
    return ruta


def generar_figuras(ctx: Ctx) -> dict[str, Path]:
    IMG.mkdir(parents=True, exist_ok=True)
    t = "oscuro"
    f = {}
    f["dispersion"] = figura_a_png(graficas.dispersion(ctx, t), "dispersion", 1000, 560)
    f["ajuste"] = figura_a_png(graficas.ajuste(ctx, None, True, t), "ajuste", 1000, 560)
    sup = graficas.superficie(ctx, 0.05, False, t)
    sup.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    f["superficie"] = figura_a_png(sup, "superficie", 1000, 620)
    f["contornos"] = figura_a_png(graficas.contornos(ctx, 0.05, 14, t), "contornos", 1000, 600)
    f["trazas_b"] = figura_a_png(graficas.trazas(ctx, "b", 0.05, t), "trazas_b", 700, 420)
    f["trazas_a"] = figura_a_png(graficas.trazas(ctx, "a", 0.05, t), "trazas_a", 700, 420)
    f["residuos"] = figura_a_png(graficas.residuos(ctx, t), "residuos", 900, 520)
    f["histograma"] = figura_a_png(graficas.histograma(ctx, 8, t), "histograma", 700, 520)
    i = extras.mas_influyente(ctx.x, ctx.y)
    f["influencia"] = figura_a_png(graficas.influencia(ctx, i, t), "influencia", 900, 520)
    f["cuadratico"] = figura_a_png(graficas.cuadratico(ctx, t), "cuadratico", 900, 520)
    return f


# ----------------------------------------------------------------- helpers de diseño
def nueva(prs: Presentation, quien: str | None = None, nota: str = ""):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    # franja degradada superior
    barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.09))
    barra.line.fill.background()
    barra.fill.gradient()
    barra.fill.gradient_angle = 0
    barra.fill.gradient_stops[0].color.rgb = INDIGO
    barra.fill.gradient_stops[1].color.rgb = ROSA
    # orbes decorativos
    for cx, cy, d, col in ((11.6, -1.0, 3.4, INDIGO), (-1.2, 6.2, 3.0, CIAN)):
        o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx), Inches(cy), Inches(d), Inches(d))
        o.line.fill.background()
        o.fill.solid()
        o.fill.fore_color.rgb = col
        _transparencia(o, 9)
    if quien:
        chip(s, prs, PERSONAS[quien], COLOR_PERSONA[quien])
    if nota:
        s.notes_slide.notes_text_frame.text = nota
    return s


def _transparencia(shape, porcentaje_opaco: int) -> None:
    """Fija la opacidad (0-100) del relleno sólido de una forma."""
    from lxml import etree

    sf = shape.fill._xPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill")
    clr = sf[0]
    alpha = etree.SubElement(clr, "{http://schemas.openxmlformats.org/drawingml/2006/main}alpha")
    alpha.set("val", str(porcentaje_opaco * 1000))


def texto(s, x, y, w, h, contenido, tam=18, color=TXT, negrita=False, fuente=FUENTE, alinea=PP_ALIGN.LEFT,
          ancla=MSO_ANCHOR.TOP, interlineado=1.1):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = ancla
    tf.margin_left = tf.margin_right = Inches(0.05)
    lineas = contenido if isinstance(contenido, list) else [contenido]
    for k, ln in enumerate(lineas):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.alignment = alinea
        p.line_spacing = interlineado
        partes = ln if isinstance(ln, list) else [(ln, {})]
        for t, op in partes:
            r = p.add_run()
            r.text = t
            r.font.name = op.get("fuente", fuente)
            r.font.size = Pt(op.get("tam", tam))
            r.font.bold = op.get("negrita", negrita)
            r.font.color.rgb = op.get("color", color)
    return tb


def titulo(s, t, sub=None):
    texto(s, 0.7, 0.45, 11.2, 0.8, t, tam=34, negrita=True)
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.78), Inches(1.28), Inches(1.4), Inches(0.06))
    ln.line.fill.background()
    ln.fill.gradient()
    ln.fill.gradient_stops[0].color.rgb = CIAN
    ln.fill.gradient_stops[1].color.rgb = ROSA
    if sub:
        texto(s, 0.7, 1.4, 11.5, 0.5, sub, tam=16, color=SUB)


def tarjeta(s, x, y, w, h, color=INDIGO, radio=0.08):
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    c.adjustments[0] = radio
    c.fill.solid()
    c.fill.fore_color.rgb = CARD
    c.line.color.rgb = color
    c.line.width = Pt(1.25)
    c.shadow.inherit = False
    return c


def chip(s, prs, nombre, color):
    w = 2.55
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, prs.slide_width - Inches(w + 0.45), Inches(0.42), Inches(w), Inches(0.42))
    c.adjustments[0] = 0.5
    c.fill.solid()
    c.fill.fore_color.rgb = color
    c.line.fill.background()
    tf = c.text_frame
    tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = f"Presenta · {nombre}"
    r.font.name = FUENTE
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = BG
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def metrica(s, x, y, w, etiqueta, valor, unidad="", color=INDIGO):
    tarjeta(s, x, y, w, 1.35, color)
    texto(s, x + 0.1, y + 0.08, w - 0.2, 0.35, etiqueta, tam=13, color=SUB)
    texto(s, x + 0.1, y + 0.42, w - 0.2, 0.55, valor, tam=26, negrita=True, color=color)
    texto(s, x + 0.1, y + 0.97, w - 0.2, 0.3, unidad, tam=11, color=SUB)


def imagen(s, ruta, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(str(ruta), Inches(x), Inches(y), **kw)


def vinetas(s, x, y, w, items, tam=17, color=TXT, sep=0.62):
    for k, it in enumerate(items):
        pto = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y + k * sep + 0.1), Inches(0.14), Inches(0.14))
        pto.line.fill.background()
        pto.fill.solid()
        pto.fill.fore_color.rgb = [CIAN, INDIGO, ROSA, NARANJA][k % 4]
        texto(s, x + 0.3, y + k * sep, w - 0.3, sep, it, tam=tam, color=color)


# ----------------------------------------------------------------- construcción
def construir(ctx: Ctx, fig: dict[str, Path]) -> Presentation:
    aj, cal, cl = ctx.ajuste, ctx.calidad, ctx.clasif
    f = estilo.fmt
    s_ = aj.sumas
    comp = verificacion.comparar(ctx.x, ctx.y)
    tabla = comp["tabla"]
    t = metricas.tabla_puntos(aj.a, aj.b, ctx.x, ctx.y)
    dg = metricas.diagnostico(aj.a, aj.b, ctx.x, ctx.y)
    imax = extras.mas_influyente(ctx.x, ctx.y)
    ri = extras.sin_punto(ctx.x, ctx.y, imax)
    q = extras.ajustar_cuadratico(ctx.x, ctx.y)
    n_at = int(t["atipico"].sum())
    a_ns = ctx.a_ns_por_elemento
    cond = cl.autovalores[1] / cl.autovalores[0]

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 1 · Portada -------------------------------------------------------------
    s = nueva(prs, None, "Nicoll abre: saludo, título y quiénes somos.")
    for cx, cy, d, col in ((7.2, 0.4, 6.4, INDIGO), (9.8, 3.2, 4.4, ROSA), (6.0, 4.4, 3.2, CIAN)):
        o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx), Inches(cy), Inches(d), Inches(d))
        o.line.fill.background()
        o.fill.solid()
        o.fill.fore_color.rgb = col
        _transparencia(o, 22)
    texto(s, 0.8, 0.9, 8, 0.5, "CÁLCULO MULTIVARIABLE  ·  " + config.PERIODO, tam=15, color=CIAN, negrita=True)
    texto(s, 0.8, 1.5, 8.6, 2.6, ["Regresión lineal", "y optimización con", "funciones de varias variables"], tam=44, negrita=True, interlineado=1.0)
    texto(s, 0.8, 4.3, 9.6, 0.8, "¿Cuánto tarda una búsqueda lineal cuando crece la entrada?  T(n) ≈ a·n + b", tam=16, color=SUB)
    y0 = 5.45
    for k, (cl_, nm) in enumerate(COLOR_PERSONA.items()):
        pass
    for k, (clave, nombre) in enumerate(PERSONAS.items()):
        col = COLOR_PERSONA[clave]
        px = 0.8 + (k % 2) * 3.4
        py = y0 + (k // 2) * 0.5
        d = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(px), Inches(py + 0.1), Inches(0.16), Inches(0.16))
        d.line.fill.background()
        d.fill.solid()
        d.fill.fore_color.rgb = col
        texto(s, px + 0.25, py, 3.1, 0.4, nombre, tam=16)
    texto(s, 0.8, 6.85, 9, 0.4, f"{config.UNIVERSIDAD}", tam=13, color=SUB)

    # 2 · Pregunta central ------------------------------------------------------
    s = nueva(prs, "N", "Presentar la pregunta central del enunciado y los tres pilares: analítico, geométrico y computacional. El computador verifica, no sustituye.")
    titulo(s, "La pregunta central")
    tarjeta(s, 0.8, 1.75, 11.7, 1.35, ROSA)
    texto(s, 1.05, 1.85, 11.2, 1.2, "¿Cómo se puede utilizar el Cálculo Multivariable para determinar y analizar el modelo lineal que mejor representa un conjunto de datos?",
          tam=22, negrita=True, ancla=MSO_ANCHOR.MIDDLE)
    pilares = [("Análisis analítico", "Derivadas parciales, ∇S = 0, sistema normal y Hessiano, hechos a mano.", CIAN),
               ("Interpretación geométrica", "Superficie S(a,b), curvas de nivel, trazas y secciones.", INDIGO),
               ("Análisis computacional", "Código propio + bibliotecas para verificar y analizar los datos.", NARANJA)]
    for k, (a_, b_, c_) in enumerate(pilares):
        x0 = 0.8 + k * 3.95
        tarjeta(s, x0, 3.55, 3.75, 2.6, c_)
        texto(s, x0 + 0.2, 3.7, 3.35, 0.6, a_, tam=20, negrita=True, color=c_)
        texto(s, x0 + 0.2, 4.4, 3.35, 1.7, b_, tam=16, color=TXT)
    texto(s, 0.8, 6.5, 11.7, 0.5, "El computador no sustituye el desarrollo matemático: lo verifica y lo visualiza.", tam=15, color=SUB)

    # 3 · Problema real -----------------------------------------------------------
    s = nueva(prs, "N", "Explicar el problema real: búsqueda lineal O(n), peor caso con elemento ausente, y por qué es lineal. Variables y unidades.")
    titulo(s, "El problema real: búsqueda lineal", "Tiempo de ejecución en función del tamaño de la entrada")
    tarjeta(s, 0.8, 2.1, 6.0, 4.5, CIAN)
    texto(s, 1.05, 2.25, 5.5, 0.5, "Por qué esperamos una recta", tam=20, negrita=True, color=CIAN)
    vinetas(s, 1.05, 2.9, 5.5, ["Recorre la lista elemento por elemento: O(n).",
                                "Peor caso: el elemento NO está → n comparaciones.",
                                "T(n) ≈ a·n + b",
                                "a = costo por elemento · b = costo fijo de arranque"], tam=16, sep=0.88)
    tarjeta(s, 7.1, 2.1, 5.45, 2.1, INDIGO)
    texto(s, 7.35, 2.2, 5.0, 0.4, "Variables y unidades", tam=18, negrita=True, color=INDIGO)
    texto(s, 7.35, 2.7, 5.0, 1.4, [[("x = n", {"negrita": True, "color": CIAN}), ("  tamaño de la entrada (elementos)", {})],
                                   [("y = T", {"negrita": True, "color": ROSA}), ("  tiempo de ejecución (ms)", {})],
                                   [("Escala: ", {"color": SUB}), ("x' = n / 10⁵  (evita números enormes)", {"color": SUB})]], tam=16, interlineado=1.3)
    tarjeta(s, 7.1, 4.45, 5.45, 2.15, ROSA)
    texto(s, 7.35, 4.55, 5.0, 0.4, "Ruido real del sistema", tam=18, negrita=True, color=ROSA)
    texto(s, 7.35, 5.05, 5.0, 1.5, "Planificador del SO · memoria caché de la CPU · recolector de basura · otros procesos · frecuencia del procesador.", tam=15)

    # 4 · Datos ------------------------------------------------------------------
    s = nueva(prs, "N", "Datos medidos con time.perf_counter_ns: 15 tamaños, 2 calentamientos descartados y 5 mediciones; se guarda la mediana. La nube es casi una recta.")
    titulo(s, "Los datos: 15 mediciones reales")
    imagen(s, fig["dispersion"], 0.7, 1.65, w=7.6)
    meta = ctx.meta
    exp = meta.get("experimento", {})
    tarjeta(s, 8.6, 1.75, 4.0, 4.9, CIAN)
    texto(s, 8.85, 1.85, 3.6, 0.4, "Ficha técnica", tam=18, negrita=True, color=CIAN)
    texto(s, 8.85, 2.4, 3.6, 4.2, [f"n = 100 000 … 1 500 000", f"{exp.get('calentamiento', 2)} calentamientos descartados",
                                   f"{exp.get('repeticiones', 5)} mediciones por n → mediana", "Cronómetro: perf_counter_ns",
                                   f"Python {meta.get('python', '')}", f"{meta.get('sistema_operativo', '').split(' (')[0]} · RAM {meta.get('ram_gb', '')} GB",
                                   "Tiempos sin simular ni editar"], tam=14, interlineado=1.45)

    # 5 · Modelo y S -------------------------------------------------------------------
    s = nueva(prs, "J", "Juan: planteamos y = ax + b. Cada dato tiene un residuo e_i. Como unos son positivos y otros negativos, sumamos los cuadrados: S(a,b). Ahora el problema es de dos variables.")
    titulo(s, "Del problema al cálculo multivariable")
    tarjeta(s, 0.8, 1.8, 5.6, 1.5, INDIGO)
    texto(s, 1.0, 1.9, 5.2, 1.3, [[("Modelo   ", {"color": SUB, "tam": 14}), ("y = a x + b", {"fuente": FUENTE_MATE, "tam": 26, "negrita": True})],
                                  [("Residuo   ", {"color": SUB, "tam": 14}), ("eᵢ = yᵢ − (a xᵢ + b)", {"fuente": FUENTE_MATE, "tam": 20})]], interlineado=1.3)
    tarjeta(s, 0.8, 3.55, 11.7, 1.6, ROSA)
    texto(s, 1.0, 3.7, 11.3, 1.4, "S(a, b)  =  Σ (yᵢ − a xᵢ − b)²", tam=36, negrita=True, fuente=FUENTE_MATE, alinea=PP_ALIGN.CENTER, ancla=MSO_ANCHOR.MIDDLE, color=ROSA)
    texto(s, 0.8, 5.5, 11.7, 1.2, ["Objetivo: encontrar (a*, b*) que minimizan S.",
                                   "Una función de DOS variables ⇒ gradiente, punto crítico y Hessiano."], tam=19, color=TXT, interlineado=1.3)

    # 6 · Derivadas y sistema normal -----------------------------------------------------------
    s = nueva(prs, "J", "Derivamos S respecto a a y a b con regla de la cadena. Igualamos a cero (gradiente nulo) y distribuimos las sumas: sistema normal 2x2 lineal en a y b.")
    titulo(s, "Derivadas parciales y sistema normal")
    tarjeta(s, 0.8, 1.8, 5.75, 2.2, CIAN)
    texto(s, 1.0, 1.9, 5.4, 0.4, "Derivadas parciales", tam=17, negrita=True, color=CIAN)
    texto(s, 1.0, 2.4, 5.4, 1.6, ["∂S/∂a = −2 Σ xᵢ (yᵢ − a xᵢ − b)", "∂S/∂b = −2 Σ (yᵢ − a xᵢ − b)"], tam=20, fuente=FUENTE_MATE, interlineado=1.5)
    tarjeta(s, 6.8, 1.8, 5.75, 2.2, INDIGO)
    texto(s, 7.0, 1.9, 5.4, 0.4, "Punto crítico", tam=17, negrita=True, color=INDIGO)
    texto(s, 7.0, 2.5, 5.4, 1.4, "∇S(a, b) = (0, 0)", tam=30, fuente=FUENTE_MATE, negrita=True, ancla=MSO_ANCHOR.MIDDLE, alinea=PP_ALIGN.CENTER)
    tarjeta(s, 0.8, 4.25, 11.75, 2.3, ROSA)
    texto(s, 1.0, 4.35, 11.4, 0.4, "Sistema normal", tam=17, negrita=True, color=ROSA)
    texto(s, 1.0, 4.9, 11.4, 1.6, ["a Σxᵢ² + b Σxᵢ = Σxᵢyᵢ", "a Σxᵢ + n b = Σyᵢ"], tam=26, fuente=FUENTE_MATE, interlineado=1.4, alinea=PP_ALIGN.CENTER)

    # 7 · Solución ---------------------------------------------------------------------------
    s = nueva(prs, "J", f"Resolvemos por Cramer. Con nuestros datos: n=15, Σx={f(s_.sx)}, Σy={f(s_.sy)}, Σx²={f(s_.sxx)}, Σxy={f(s_.sxy)}. Resultado a*={f(aj.a)}, b*={f(aj.b)}.")
    titulo(s, "Solución: a* y b*")
    tarjeta(s, 0.8, 1.8, 7.2, 2.5, INDIGO)
    texto(s, 1.0, 1.9, 6.8, 2.4, ["a* = (nΣxy − ΣxΣy) / (nΣx² − (Σx)²)", "b* = (Σy − a* Σx) / n"], tam=24, fuente=FUENTE_MATE, interlineado=1.8, ancla=MSO_ANCHOR.MIDDLE)
    tarjeta(s, 8.3, 1.8, 4.25, 2.5, CIAN)
    texto(s, 8.5, 1.9, 3.9, 0.4, "Sumatorias (x en 10⁵)", tam=15, negrita=True, color=CIAN)
    texto(s, 8.5, 2.35, 3.9, 1.9, [f"n = {s_.n}", f"Σx = {f(s_.sx)}", f"Σy = {f(s_.sy)}", f"Σx² = {f(s_.sxx)}", f"Σxy = {f(s_.sxy)}"], tam=14, interlineado=1.25)
    metrica(s, 0.8, 4.65, 3.7, "a*  (pendiente)", f(aj.a), f"ms por 10⁵ elementos ≈ {f(a_ns, 4)} ns/elemento", INDIGO)
    metrica(s, 4.8, 4.65, 3.7, "b*  (intercepto)", f(aj.b), "ms (costo fijo estimado)", CIAN)
    metrica(s, 8.8, 4.65, 3.75, "S_mín", f(aj.s_min), "ms²", ROSA)

    # 8 · Hessiano ----------------------------------------------------------------------------
    s = nueva(prs, "J", "Calculamos las segundas derivadas. det H = 4n Σ(x-xbar)^2 > 0 y S_aa > 0 ⇒ mínimo local estricto. H constante y definida positiva ⇒ S convexa ⇒ mínimo global único.")
    titulo(s, "Hessiano: ¿es un mínimo?")
    tarjeta(s, 0.8, 1.8, 6.2, 2.9, INDIGO)
    texto(s, 1.0, 1.9, 5.8, 0.4, "Matriz hessiana (constante)", tam=16, negrita=True, color=INDIGO)
    texto(s, 1.0, 2.45, 5.8, 1.0, "H = [ 2Σx²   2Σx ;  2Σx   2n ]", tam=22, fuente=FUENTE_MATE)
    texto(s, 1.0, 3.3, 5.8, 1.3, [f"H = [ {f(cl.hessiano[0, 0])}  {f(cl.hessiano[0, 1])} ;  {f(cl.hessiano[1, 0])}  {f(cl.hessiano[1, 1])} ]",
                                  f"det H = {f(cl.det)} > 0     S_aa = {f(cl.s_aa)} > 0"], tam=17, fuente=FUENTE_MATE, color=CIAN, interlineado=1.4)
    tarjeta(s, 7.3, 1.8, 5.25, 2.9, ROSA)
    texto(s, 7.5, 1.9, 4.9, 0.4, "Autovalores", tam=16, negrita=True, color=ROSA)
    texto(s, 7.5, 2.45, 4.9, 2.2, [f"λ₁ = {f(cl.autovalores[0], 5)}", f"λ₂ = {f(cl.autovalores[1], 5)}", "Ambos > 0 ⇒ H definida positiva",
                                   f"Condición ≈ {f(cond, 3)}: valle muy alargado"], tam=17, interlineado=1.4)
    tarjeta(s, 0.8, 4.95, 11.75, 1.6, CIAN)
    texto(s, 1.05, 5.05, 11.3, 1.4, [[("Conclusión: ", {"negrita": True, "color": CIAN}), ("det H > 0 y S_aa > 0  ⇒  (a*, b*) es un ", {}), ("mínimo local estricto", {"negrita": True})],
                                    "H es constante y definida positiva ⇒ S es convexa ⇒ el mínimo es GLOBAL y único."], tam=19, interlineado=1.35, ancla=MSO_ANCHOR.MIDDLE)

    # 9 · Superficie ---------------------------------------------------------------------------
    s = nueva(prs, "B", "Brayan: la superficie z=S(a,b) es un paraboloide elíptico abierto hacia arriba; tiene un único punto más bajo. Su forma de valle alargado indica que a y b están correlacionados.")
    titulo(s, "Geometría: la superficie S(a, b)")
    imagen(s, fig["superficie"], 0.7, 1.55, w=7.9)
    tarjeta(s, 8.85, 1.8, 3.7, 4.6, NARANJA)
    vinetas(s, 9.05, 2.0, 3.4, ["Paraboloide elíptico abierto hacia arriba.", "Un solo punto mínimo: (a*, b*).",
                                "Valle estrecho: a y b correlacionados.", "H definida positiva ⇒ convexa."], tam=15, sep=1.1)

    # 10 · Curvas de nivel y trazas ----------------------------------------------------------------
    s = nueva(prs, "B", "Curvas de nivel: elipses concéntricas alrededor de (a*,b*). Trazas: cortes con planos b=cte o a=cte son parábolas.")
    titulo(s, "Curvas de nivel, trazas y secciones")
    imagen(s, fig["contornos"], 0.6, 1.6, w=6.5)
    imagen(s, fig["trazas_b"], 7.6, 1.5, w=4.9)
    imagen(s, fig["trazas_a"], 7.6, 4.35, w=4.9)
    texto(s, 0.7, 5.75, 6.4, 1.3, "Elipses concéntricas (mismo error S). La ✕ marca el mínimo (a*, b*).", tam=14, color=SUB)

    # 11 · Ajuste y verificación computacional --------------------------------------------------------
    s = nueva(prs, "B", "Programamos el ajuste desde cero y lo comparamos con numpy.polyfit y scipy.stats.linregress. Coinciden hasta el redondeo de punto flotante.")
    titulo(s, "Verificación computacional")
    imagen(s, fig["ajuste"], 0.6, 1.6, w=6.6)
    cols = ["Parámetro", "Código propio", "Biblioteca", "Dif. máx."]
    xs = [7.5, 9.05, 10.65, 11.95]
    tarjeta(s, 7.4, 1.8, 5.3, 2.7, CIAN)
    for xx, cc in zip(xs, cols):
        texto(s, xx - 0.05, 1.9, 1.7, 0.4, cc, tam=12, negrita=True, color=CIAN)
    for k, (_, fila) in enumerate(tabla.iterrows()):
        yy = 2.45 + k * 0.6
        vals = [fila["Parámetro"], f(fila["Código propio"], 6), f(fila["Biblioteca (linregress)"], 6), f(fila["Diferencia máxima"], 2)]
        for xx, vv in zip(xs, vals):
            texto(s, xx - 0.05, yy, 1.7, 0.4, vv, tam=13)
    tarjeta(s, 7.4, 4.75, 5.3, 1.85, ROSA)
    texto(s, 7.6, 4.85, 4.9, 1.7, ["Código propio = numpy.polyfit = linregress.", "Diferencia: error de redondeo (~10⁻¹⁶).",
                                   "Los residuos eᵢ son tan pequeños que casi no se ven."], tam=14, interlineado=1.3)

    # 12 · Comparación con lo manual -------------------------------------------------------------------
    s = nueva(prs, "B", "El valor analítico manual se compara con el código propio y la biblioteca. Si difiere en las últimas cifras es por redondeo al hacer las cuentas a mano.")
    titulo(s, "Analítico vs. código vs. biblioteca")
    tarjeta(s, 0.8, 1.8, 11.75, 2.2, INDIGO)
    enc = ["Parámetro", "Analítico (manual)", "Código propio", "Biblioteca de Python", "Diferencia máxima"]
    xs2 = [1.05, 3.0, 5.6, 8.0, 10.6]
    for xx, cc in zip(xs2, enc):
        texto(s, xx, 1.9, 2.6, 0.4, cc, tam=13, negrita=True, color=INDIGO)
    for k, (_, fila) in enumerate(tabla.iterrows()):
        yy = 2.4 + k * 0.5
        for xx, vv in zip(xs2, [fila["Parámetro"], "(su cálculo a mano)", f(fila["Código propio"], 7), f(fila["Biblioteca (linregress)"], 7), f(fila["Diferencia máxima"], 2)]):
            texto(s, xx, yy, 2.7, 0.4, vv, tam=14, color=(SUB if vv == "(su cálculo a mano)" else TXT))
    vinetas(s, 0.9, 4.4, 11.5, ["Los tres métodos resuelven el mismo problema ⇒ mismos a*, b*, S_mín.",
                                "Diferencias ≈ 10⁻¹⁶ relativo: precisión de máquina (float64).",
                                "Una diferencia mayor en lo manual = redondeo de sumas hechas a mano."], tam=16, sep=0.7)

    # 13 · Residuos ---------------------------------------------------------------------------------------
    s = nueva(prs, "M", f"Mario: residuos centrados en cero por construcción; la dispersión crece con x (corr |e|-x = {dg['corr_abs_x']:.2f}); {n_at} puntos marginalmente atípicos. Sin patrón curvo (corr curvatura {dg['corr_curvatura']:.2f}).")
    titulo(s, "Análisis de residuos")
    imagen(s, fig["residuos"], 0.8, 1.55, w=5.9)
    imagen(s, fig["histograma"], 7.3, 1.55, w=4.6)
    tarjeta(s, 0.8, 5.0, 11.75, 1.75, ROSA)
    vinetas(s, 1.0, 5.1, 11.4, ["Centrados en cero y sin patrón curvo ni tendencia sistemática ⇒ el modelo lineal es compatible con los datos.",
                                f"La dispersión crece con n (corr |e|–x = {dg['corr_abs_x']:.2f}): el ruido es proporcional al tiempo.",
                                f"{n_at} puntos rozan el límite |t| > 2 (marginales); sin errores graves."], tam=14, sep=0.52)

    # 14 · Calidad -----------------------------------------------------------------------------------------
    s = nueva(prs, "M", "RMSE es el error típico en ms. R2 dice qué parte de la variación explica la recta; es alto porque T depende casi sólo de n, pero no prueba linealidad: por eso se miran residuos.")
    titulo(s, "Calidad del ajuste")
    metrica(s, 0.8, 1.85, 3.7, "RMSE", f(cal.rmse), "ms", CIAN)
    metrica(s, 4.8, 1.85, 3.7, "R²", f"{cal.r2:.6f}", f"explica {100 * cal.r2:.3f} % de la variación", INDIGO)
    metrica(s, 8.8, 1.85, 3.75, "RMSE / T medio", f"{100 * cal.rmse / ctx.y.mean():.2f} %", f"T medio = {f(ctx.y.mean(), 4)} ms", ROSA)
    tarjeta(s, 0.8, 3.6, 5.75, 3.0, CIAN)
    texto(s, 1.0, 3.7, 5.4, 0.4, "¿Qué significa el RMSE?", tam=18, negrita=True, color=CIAN)
    texto(s, 1.0, 4.2, 5.4, 2.4, f"La recta se equivoca, en promedio, unos {f(cal.rmse, 3)} ms: un error pequeño para estimar cuánto tarda una búsqueda de un tamaño dado.", tam=16)
    tarjeta(s, 6.8, 3.6, 5.75, 3.0, INDIGO)
    texto(s, 7.0, 3.7, 5.4, 0.4, "¿Y el R²?", tam=18, negrita=True, color=INDIGO)
    texto(s, 7.0, 4.2, 5.4, 2.4, "Es muy alto porque T depende casi solo de n y el rango de n es amplio. No prueba que el modelo sea lineal: por eso revisamos los residuos.", tam=16)

    # 15 · Análisis adicional ---------------------------------------------------------------------------------
    s = nueva(prs, "M", f"Opción B: eliminar el punto {imax + 1} (el más influyente) cambia a en {100 * ri['delta_a_rel']:.2f}%. Opción C: el término cuadrático es casi cero (p={f(q.p_f, 3)}), el modelo lineal basta.")
    titulo(s, "Análisis adicional: Opciones B y C")
    imagen(s, fig["influencia"], 0.8, 1.55, w=5.5)
    imagen(s, fig["cuadratico"], 7.05, 1.55, w=5.5)
    tarjeta(s, 0.8, 4.85, 5.8, 1.85, NARANJA)
    texto(s, 1.0, 4.9, 5.4, 0.4, "B · Influencia de un dato", tam=16, negrita=True, color=NARANJA)
    texto(s, 1.0, 5.35, 5.4, 1.4, f"Punto más influyente: n.º {imax + 1} (extremo derecho). Al quitarlo, a* cambia solo {100 * ri['delta_a_rel']:.2f} %: la recta es estable.", tam=14)
    tarjeta(s, 6.95, 4.85, 5.6, 1.85, CIAN)
    texto(s, 7.15, 4.9, 5.2, 0.4, "C · Lineal vs. cuadrático", tam=16, negrita=True, color=CIAN)
    texto(s, 7.15, 5.35, 5.2, 1.4, f"Término x² ≈ 0 (p = {f(q.p_f, 3)}) y aporta {100 * q.aporte_relativo:.2f} %. R² ajustado no mejora: el modelo O(n) es suficiente.", tam=14)

    # 16 · Conclusiones ----------------------------------------------------------------------------------------
    s = nueva(prs, "M", "Cerrar con la respuesta a la pregunta central: análisis analítico + geométrico + computacional. Invitar a ver la app en vivo.")
    titulo(s, "Conclusiones")
    items = [("Analítico", "∇S = 0 da el sistema normal; a* y b* salen de fórmulas exactas.", CIAN),
             ("Hessiano", "det H > 0 y S_aa > 0 ⇒ mínimo; H definida positiva ⇒ global y único.", INDIGO),
             ("Geométrico", "Paraboloide con un valle: el mejor ajuste es el fondo.", NARANJA),
             ("Computacional", "Código propio = polyfit = linregress; la app lo verifica y lo visualiza.", ROSA)]
    for k, (a_, b_, c_) in enumerate(items):
        x0 = 0.8 + (k % 2) * 6.0
        y0 = 1.85 + (k // 2) * 2.0
        tarjeta(s, x0, y0, 5.75, 1.75, c_)
        texto(s, x0 + 0.2, y0 + 0.1, 5.3, 0.4, a_, tam=18, negrita=True, color=c_)
        texto(s, x0 + 0.2, y0 + 0.6, 5.3, 1.1, b_, tam=15)
    tarjeta(s, 0.8, 5.95, 11.75, 0.95, ROSA)
    texto(s, 1.0, 5.98, 11.4, 0.9, f"T(n) ≈ {f(aj.a, 4)}·(n/10⁵) + ({f(aj.b, 3)}) ms   ·   RMSE = {f(cal.rmse, 3)} ms   ·   R² = {cal.r2:.5f}",
          tam=19, negrita=True, alinea=PP_ALIGN.CENTER, ancla=MSO_ANCHOR.MIDDLE)

    # 17 · Gracias ----------------------------------------------------------------------------------------------
    s = nueva(prs, None, "Cerrar y abrir preguntas. Tener la app abierta (streamlit run app.py) por si piden demostrar algo.")
    for cx, cy, d, col in ((8.0, 0.2, 6.0, INDIGO), (10.2, 3.6, 4.2, ROSA), (6.6, 4.8, 3.0, CIAN)):
        o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx), Inches(cy), Inches(d), Inches(d))
        o.line.fill.background()
        o.fill.solid()
        o.fill.fore_color.rgb = col
        _transparencia(o, 22)
    texto(s, 0.9, 2.2, 8, 1.4, "¡Gracias!", tam=64, negrita=True)
    texto(s, 0.9, 3.6, 8, 0.8, "¿Preguntas?", tam=30, color=CIAN, negrita=True)
    texto(s, 0.9, 5.0, 8, 1.2, ["Nicoll López · Juan Jurado", "Brayan Guerrero · Mario Zambrano"], tam=17, color=SUB, interlineado=1.3)
    return prs


def main() -> None:
    ctx = construir_ctx()
    print("Generando figuras…")
    fig = generar_figuras(ctx)
    print("Construyendo diapositivas…")
    prs = construir(ctx, fig)
    prs.save(SALIDA)
    print(f"Listo: {SALIDA}")


if __name__ == "__main__":
    main()
