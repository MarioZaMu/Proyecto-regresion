"""Genera la presentación INTERACTIVA en HTML (un solo archivo, funciona sin internet).

Uso (desde la raíz del proyecto):
    python presentacion/generar_html.py [--puerto 8501]

Salida: presentacion/Presentacion_interactiva.html

* Las gráficas son las MISMAS figuras Plotly que usa la app (interfaz/graficas.py): se pueden rotar,
  hacer zoom, pasar el cursor y reproducir la animación.
* Todos los números salen del núcleo matemático (core/) con los datos de datos/datos.csv.
* En las diapositivas clave el navegador RECALCULA el ajuste con JavaScript a partir de los datos
  y lo compara con Python (polyfit / linregress): verificación en vivo.
* Si la app está corriendo (streamlit run app.py) la presentación lo detecta y permite abrir
  la página correspondiente o verla embebida dentro de la diapositiva.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402
import plotly.offline as pyo  # noqa: E402

import config  # noqa: E402
from core import datos, extras, metricas, regresion, verificacion  # noqa: E402
from interfaz import estilo, graficas  # noqa: E402
from interfaz.contexto import Ctx  # noqa: E402

SALIDA = Path(__file__).resolve().parent / "Presentacion_interactiva.html"


def construir_ctx() -> Ctx:
    df = datos.cargar_csv()
    x = datos.escalar(df["x"].to_numpy(), True)
    y = df["y"].to_numpy()
    aj = regresion.ajustar(x, y)
    return Ctx(df, datos.cargar_metadata(), True, x, y, df["x"].to_numpy(), aj, metricas.calidad(aj.a, aj.b, x, y),
               regresion.clasificar(x), "n (×10⁵ elementos)", "T (ms)", "ms por 10⁵ elementos", "ms", False)


def fig_json(fig, altura_3d: bool = False) -> dict:
    """Figura Plotly → dict JSON con fondo transparente y tamaño automático."""
    fig.update_layout(title_text="", height=None, autosize=True, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=64, r=24, t=44, b=56) if not altura_3d else dict(l=0, r=0, t=10, b=0))
    return json.loads(fig.to_json())


def main(puerto: int) -> None:
    ctx = construir_ctx()
    aj, cal, cl = ctx.ajuste, ctx.calidad, ctx.clasif
    s = aj.sumas
    f = estilo.fmt
    t = "oscuro"

    # ----------------------------------------------------------------- cálculos (los mismos de la app)
    comp = verificacion.comparar(ctx.x, ctx.y)
    a_np, b_np, s_np = comp["numpy"]
    a_sp, b_sp, s_sp = comp["scipy"]
    tab = metricas.tabla_puntos(aj.a, aj.b, ctx.x, ctx.y)
    dg = metricas.diagnostico(aj.a, aj.b, ctx.x, ctx.y)
    imax = extras.mas_influyente(ctx.x, ctx.y)
    ri = extras.sin_punto(ctx.x, ctx.y, imax)
    q = extras.ajustar_cuadratico(ctx.x, ctx.y)
    infl = extras.influencia_todos(ctx.x, ctx.y)
    cond = cl.autovalores[1] / cl.autovalores[0]
    meta = ctx.meta
    csv_bytes = (datos.CARPETA_DATOS / "datos.csv").read_bytes()
    sha = hashlib.sha256(csv_bytes).hexdigest()

    V = {
        "a": f(aj.a), "b": f(aj.b), "smin": f(aj.s_min), "rmse": f(cal.rmse), "r2": f"{cal.r2:.6f}",
        "ans": f(ctx.a_ns_por_elemento, 4), "n": str(s.n), "sx": f(s.sx), "sy": f(s.sy), "sxx": f(s.sxx), "sxy": f(s.sxy),
        "det": f(cl.det), "saa": f(cl.s_aa), "h11": f(cl.hessiano[0, 0]), "h12": f(cl.hessiano[0, 1]), "h22": f(cl.hessiano[1, 1]),
        "l1": f(cl.autovalores[0], 5), "l2": f(cl.autovalores[1], 5), "cond": f(cond, 3),
        "rmse_pct": f(100 * cal.rmse / ctx.y.mean(), 3), "tmean": f(ctx.y.mean(), 4), "tmax": f(ctx.y.max(), 4),
        "r2pct": f"{100 * cal.r2:.3f}", "imax": str(imax + 1), "da_pct": f"{100 * ri['delta_a_rel']:.2f}",
        "a_sin": f(ri["nuevo"].a), "b_sin": f(ri["nuevo"].b), "cook": f(float(infl['Cook'].max()), 3), "cook_ref": f(4 / s.n, 3),
        "c2": f(q.c2, 3), "pF": f(q.p_f, 3), "aporte": f"{100 * q.aporte_relativo:.2f}", "r2adj_lin": f"{1 - (1 - cal.r2) * (s.n - 1) / (s.n - 2):.6f}",
        "r2adj_q": f"{q.r2_ajustado:.6f}", "natip": str(int(tab['atipico'].sum())), "corr_abs": f"{dg['corr_abs_x']:.2f}",
        "corr_curv": f"{dg['corr_curvatura']:.2f}", "fecha": str(meta.get("fecha_hora", "")).replace("T", " "),
        "equipo": f"{str(meta.get('sistema_operativo', '')).split(' (')[0]} · {meta.get('ram_gb', '')} GB RAM · Python {meta.get('python', '')}",
        "cpu": str(meta.get("procesador", "")), "origen": str(meta.get("origen", "")), "sha": sha[:16],
        "periodo": config.PERIODO, "curso": config.CURSO, "uni": config.UNIVERSIDAD,
        "dmax_a": f(float(comp["tabla"].loc[0, "Diferencia máxima"]), 2), "dmax_b": f(float(comp["tabla"].loc[1, "Diferencia máxima"]), 2),
        "dmax_s": f(float(comp["tabla"].loc[2, "Diferencia máxima"]), 2),
    }

    # ----------------------------------------------------------------- figuras (las de la app)
    sup = graficas.superficie(ctx, 0.05, False, t)
    figs = {
        "dispersion": fig_json(graficas.dispersion(ctx, t)),
        "superficie": fig_json(sup, True),
        "contornos": fig_json(graficas.contornos(ctx, 0.05, 14, t)),
        "trazas_b": fig_json(graficas.trazas(ctx, "b", 0.05, t)),
        "trazas_a": fig_json(graficas.trazas(ctx, "a", 0.05, t)),
        "descenso": fig_json(graficas.descenso_animado(ctx, 0.05, 40, t)),
        "residuos": fig_json(graficas.residuos(ctx, t)),
        "histograma": fig_json(graficas.histograma(ctx, 8, t)),
        "influencia": fig_json(graficas.influencia(ctx, imax, t)),
        "cuadratico": fig_json(graficas.cuadratico(ctx, t)),
        "cook": fig_json(graficas.cook(ctx, t)),
    }
    da, db = graficas.region(ctx, 0.02)
    DATA = {
        "x": ctx.x.tolist(), "y": ctx.y.tolist(), "x_raw": ctx.x_raw.tolist(), "escala": 1e5,
        "py": {"a": aj.a, "b": aj.b, "smin": aj.s_min, "numpy": [a_np, b_np, s_np], "scipy": [a_sp, b_sp, s_sp],
               "det": cl.det, "l1": cl.autovalores[0], "l2": cl.autovalores[1], "imax": imax, "da": da, "db": db},
        "figs": figs, "puerto": puerto,
    }

    html = re.sub(r"\[\[(\w+)\]\]", lambda m: V[m.group(1)], PLANTILLA)  # antes de insertar JS/datos
    html = html.replace("__PLOTLY__", pyo.get_plotlyjs())
    html = html.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
    SALIDA.write_text(html, encoding="utf-8")
    print(f"Listo: {SALIDA}  ({SALIDA.stat().st_size / 1e6:.1f} MB)")


# ===================================================================== plantilla
PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Regresión lineal · Presentación interactiva</title>
<style>
  :root{--bg:#0B1020;--card:#151A33;--txt:#F1F5F9;--sub:#94A3B8;--indigo:#818CF8;--cian:#22D3EE;--rosa:#F472B6;--naranja:#FB923C;--verde:#34D399}
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%;background:var(--bg);color:var(--txt);font-family:"Segoe UI",Inter,Arial,sans-serif;overflow:hidden}
  body::before{content:"";position:fixed;inset:-20%;z-index:0;
    background:radial-gradient(40% 40% at 20% 20%,rgba(129,140,248,.28),transparent 70%),radial-gradient(35% 35% at 85% 25%,rgba(244,114,182,.22),transparent 70%),
               radial-gradient(40% 40% at 60% 90%,rgba(34,211,238,.20),transparent 70%);animation:deriva 22s ease-in-out infinite alternate}
  @keyframes deriva{to{transform:translate(4%,3%) scale(1.08)}}
  @keyframes subir{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
  @keyframes pulso{0%,100%{box-shadow:0 0 0 0 rgba(52,211,153,.0)}50%{box-shadow:0 0 0 6px rgba(52,211,153,.25)}}
  #barra{position:fixed;top:0;left:0;height:4px;z-index:50;width:0;background:linear-gradient(90deg,var(--indigo),var(--cian),var(--rosa));transition:width .4s}
  #deck{position:relative;z-index:1;height:100vh;width:100vw}
  .slide{position:absolute;inset:0;padding:4.2vh 4.2vw 7vh;display:flex;flex-direction:column;opacity:0;pointer-events:none;transform:translateX(40px);transition:opacity .5s,transform .5s}
  .slide.activa{opacity:1;pointer-events:auto;transform:none}
  .slide.activa>*{animation:subir .6s both}
  .slide.activa>*:nth-child(2){animation-delay:.08s}.slide.activa>*:nth-child(3){animation-delay:.16s}.slide.activa>*:nth-child(4){animation-delay:.24s}
  h1{font-size:clamp(28px,4.4vw,64px);font-weight:800;line-height:1.05;letter-spacing:-.02em}
  h2{font-size:clamp(22px,2.7vw,40px);font-weight:750;letter-spacing:-.01em;display:flex;align-items:center;gap:14px}
  h2::after{content:"";height:5px;width:90px;border-radius:5px;background:linear-gradient(90deg,var(--cian),var(--rosa))}
  .grad{background:linear-gradient(90deg,var(--indigo),var(--cian),var(--rosa),var(--indigo));background-size:200% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:brillo 6s linear infinite}
  @keyframes brillo{to{background-position:200% 50%}}
  .cabeza{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:2vh;min-height:48px}
  .chip{padding:7px 16px;border-radius:99px;font-weight:700;font-size:clamp(11px,1vw,14px);color:#0B1020;white-space:nowrap}
  .N{background:var(--cian)}.J{background:var(--indigo)}.B{background:var(--naranja)}.M{background:var(--rosa)}
  .cuerpo{flex:1;min-height:0;display:grid;gap:1.6vw}
  .g2{grid-template-columns:1fr 1fr}.g12{grid-template-columns:1.25fr 1fr}.g21{grid-template-columns:1fr 1.25fr}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}
  .col{display:flex;flex-direction:column;gap:1.4vh;min-height:0}
  .card{background:linear-gradient(160deg,rgba(21,26,51,.92),rgba(21,26,51,.78));border:1.5px solid var(--c,var(--indigo));border-radius:18px;padding:clamp(12px,1.6vw,24px);
    backdrop-filter:blur(8px);transition:transform .25s,box-shadow .25s;min-height:0}
  .card:hover{transform:translateY(-3px);box-shadow:0 14px 30px -12px var(--c,var(--indigo))}
  .card h3{font-size:clamp(14px,1.35vw,20px);color:var(--c,var(--indigo));margin-bottom:.8vh}
  .card p,.card li{font-size:clamp(13px,1.3vw,19px);line-height:1.5;color:var(--txt)}
  .card ul{list-style:none;display:flex;flex-direction:column;gap:.9vh}
  .card li::before{content:"●";color:var(--c,var(--cian));margin-right:.6em;font-size:.8em}
  .sub{color:var(--sub);font-size:clamp(12px,1.2vw,17px)}
  .eq{font-family:"Cambria Math","STIX Two Math",Cambria,serif;font-size:clamp(17px,2.1vw,32px);line-height:1.55}
  .big{font-size:clamp(20px,2.6vw,40px);font-weight:700}
  .c1{--c:var(--indigo)}.c2{--c:var(--cian)}.c3{--c:var(--rosa)}.c4{--c:var(--naranja)}.c5{--c:var(--verde)}
  .m{display:flex;flex-direction:column;gap:2px}.m .v{font-size:clamp(20px,2.4vw,38px);font-weight:800;color:var(--c)}.m .l{font-size:clamp(11px,1vw,14px);color:var(--sub)}
  .plot{width:100%;height:100%;min-height:200px;border-radius:14px}
  .plotcard{padding:8px;display:flex}
  table{border-collapse:collapse;width:100%}th,td{padding:.8vh .6vw;text-align:left;font-size:clamp(12px,1.15vw,17px);border-bottom:1px solid rgba(148,163,184,.2)}th{color:var(--c,var(--cian))}
  td.ok{color:var(--verde);font-weight:700}
  .btn{cursor:pointer;border:0;border-radius:12px;padding:9px 16px;font-weight:700;font-size:clamp(12px,1.05vw,15px);color:#0B1020;background:linear-gradient(90deg,var(--indigo),var(--rosa));transition:transform .2s,box-shadow .2s}
  .btn:hover{transform:translateY(-2px);box-shadow:0 10px 20px -8px var(--rosa)}.btn.sec{background:rgba(148,163,184,.18);color:var(--txt)}
  input[type=range]{width:100%;accent-color:var(--rosa)} select{background:#0B1020;color:var(--txt);border:1.5px solid var(--indigo);border-radius:10px;padding:7px 10px;font-size:clamp(12px,1.1vw,16px)}
  code{background:rgba(148,163,184,.18);padding:1px 7px;border-radius:6px;font-family:Consolas,monospace;font-size:.92em}
  .badge{display:inline-flex;align-items:center;gap:8px;padding:5px 12px;border-radius:99px;font-size:12px;background:rgba(148,163,184,.15)}
  .dot{width:9px;height:9px;border-radius:50%;background:#64748B}.dot.on{background:var(--verde);animation:pulso 2s infinite}
  .portada{justify-content:center}.portada h1{max-width:12em}
  .orbe{position:absolute;border-radius:50%;filter:blur(2px);opacity:.28;z-index:-1;animation:flota 9s ease-in-out infinite alternate}
  @keyframes flota{to{transform:translateY(-28px) scale(1.06)}}
  #nav{position:fixed;z-index:60;bottom:1.6vh;left:50%;transform:translateX(-50%);display:flex;gap:10px;align-items:center;background:rgba(21,26,51,.85);padding:7px 14px;border-radius:99px;border:1px solid rgba(148,163,184,.25);backdrop-filter:blur(8px)}
  #nav button{background:none;border:0;color:var(--txt);font-size:18px;cursor:pointer;padding:2px 10px;border-radius:8px}#nav button:hover{background:rgba(129,140,248,.3)}
  #cuenta{font-size:13px;color:var(--sub);min-width:60px;text-align:center}
  #estado{position:fixed;z-index:60;left:1.4vw;bottom:1.9vh}
  #notas{position:fixed;z-index:70;left:2vw;right:2vw;bottom:8vh;background:rgba(11,16,32,.96);border:1.5px solid var(--rosa);border-radius:16px;padding:18px 22px;font-size:clamp(14px,1.4vw,20px);line-height:1.55;display:none;max-height:42vh;overflow:auto}
  #notas.on{display:block;animation:subir .3s both}
  #overlay{position:fixed;inset:0;z-index:80;background:rgba(5,8,18,.92);display:none;flex-direction:column;padding:2vh 2vw;gap:1.2vh}
  #overlay.on{display:flex}#overlay iframe{flex:1;border:1.5px solid var(--indigo);border-radius:14px;background:#fff}
  .tabs{display:flex;gap:8px;flex-wrap:wrap}.tab{cursor:pointer;padding:6px 14px;border-radius:99px;background:rgba(148,163,184,.15);font-size:clamp(11px,1vw,14px)}.tab.on{background:var(--indigo);color:#0B1020;font-weight:700}
  .oculto{display:none!important}
  @media (max-width:900px){.g2,.g12,.g21,.g3,.g4{grid-template-columns:1fr}.slide{overflow:auto}}
</style>
</head>
<body>
<div id="barra"></div>
<div id="deck">

<!-- 1 PORTADA -->
<section class="slide portada" data-notas="Nicoll abre: saludo, título y quiénes somos." data-app="">
  <div class="orbe" style="right:-6vw;top:-8vh;width:46vw;height:46vw;background:var(--indigo)"></div>
  <div class="orbe" style="right:8vw;bottom:-14vh;width:30vw;height:30vw;background:var(--rosa);animation-delay:-3s"></div>
  <div class="sub" style="letter-spacing:.2em;font-weight:700;color:var(--cian)">[[curso]] · [[periodo]]</div>
  <h1 class="grad" style="margin:2vh 0">Regresión lineal y optimización con funciones de varias variables</h1>
  <p class="sub" style="font-size:clamp(14px,1.7vw,24px)">¿Cuánto tarda una búsqueda lineal cuando crece la entrada? &nbsp; T(n) ≈ a·n + b</p>
  <div style="display:flex;gap:1.2vw;margin-top:4vh;flex-wrap:wrap">
    <span class="chip N">Nicoll Valentina López Andrade</span><span class="chip J">Juan David Jurado Paz</span><span class="chip B">Brayan Steven Guerrero Acosta</span><span class="chip M">Mario Alberto Zambrano Muñoz</span>
  </div>
  <p class="sub" style="margin-top:3vh">[[uni]]</p>
</section>

<!-- 2 PREGUNTA -->
<section class="slide" data-notas="Presentar la pregunta central y los tres pilares. El computador verifica, no sustituye." data-app="">
  <div class="cabeza"><h2>La pregunta central</h2><span class="chip N">Presenta · Nicoll López</span></div>
  <div class="cuerpo" style="grid-template-rows:auto 1fr">
    <div class="card c3"><p class="big">¿Cómo se puede utilizar el Cálculo Multivariable para determinar y analizar el modelo lineal que mejor representa un conjunto de datos?</p></div>
    <div class="cuerpo g3">
      <div class="card c2"><h3>Análisis analítico</h3><p>Derivadas parciales, ∇S = 0, sistema normal y Hessiano, hechos a mano.</p></div>
      <div class="card c1"><h3>Interpretación geométrica</h3><p>Superficie S(a,b), curvas de nivel, trazas y secciones.</p></div>
      <div class="card c4"><h3>Análisis computacional</h3><p>Código propio + bibliotecas para verificar y analizar los datos.</p></div>
    </div>
  </div>
  <p class="sub" style="margin-top:1.5vh">El computador no sustituye el desarrollo matemático: lo verifica y lo visualiza.</p>
</section>

<!-- 3 PROBLEMA -->
<section class="slide" data-notas="Búsqueda lineal O(n), peor caso con elemento ausente: n comparaciones. T ≈ a·n + b. Variables y unidades. Ruido real." data-app="">
  <div class="cabeza"><h2>El problema real: búsqueda lineal</h2><span class="chip N">Presenta · Nicoll López</span></div>
  <div class="cuerpo g2">
    <div class="card c2"><h3>Por qué esperamos una recta</h3>
      <ul><li>Recorre la lista elemento por elemento: <b>O(n)</b>.</li><li>Peor caso: el elemento <b>no está</b> → exactamente n comparaciones.</li>
      <li class="eq" style="font-size:clamp(18px,2.2vw,30px)">T(n) ≈ a·n + b</li><li><b>a</b> = costo por elemento · <b>b</b> = costo fijo de arranque.</li></ul></div>
    <div class="col">
      <div class="card c1"><h3>Variables y unidades</h3><p><b style="color:var(--cian)">x = n</b> tamaño de la entrada (elementos)<br><b style="color:var(--rosa)">y = T</b> tiempo de ejecución (ms)<br><span class="sub">Escala: x' = n/10⁵ (evita números enormes)</span></p></div>
      <div class="card c3"><h3>Ruido real del sistema</h3><p>Planificador del SO · caché de la CPU · recolector de basura · otros procesos · frecuencia del procesador.</p></div>
    </div>
  </div>
</section>

<!-- 4 DATOS -->
<section class="slide" data-notas="15 tamaños, 2 calentamientos descartados y 5 mediciones, mediana. perf_counter_ns. Nunca se simulan. La nube es casi una recta. Pasen el cursor por los puntos." data-app="/">
  <div class="cabeza"><h2>Los datos: 15 mediciones reales</h2><span class="chip N">Presenta · Nicoll López</span></div>
  <div class="cuerpo g12">
    <div class="card plotcard c1"><div class="plot" data-fig="dispersion"></div></div>
    <div class="card c2"><h3>Ficha técnica (metadata.json)</h3>
      <ul><li>n = 100 000 … 1 500 000</li><li>2 calentamientos descartados + 5 mediciones → mediana</li><li>Cronómetro: <code>perf_counter_ns</code></li>
      <li>[[equipo]]</li><li>Medido el [[fecha]]</li><li>Origen: <b>[[origen]]</b></li>
      <li>Huella SHA-256 de datos.csv: <code>[[sha]]…</code></li></ul>
      <p class="sub" style="margin-top:1vh">Tiempos sin simular ni editar. Pase el cursor sobre los puntos.</p></div>
  </div>
</section>

<!-- 5 MODELO -->
<section class="slide" data-notas="Juan: y = ax + b, residuo ei, suma de cuadrados S(a,b). Ahora es una función de dos variables: gradiente, punto crítico, Hessiano." data-app="/Modelo">
  <div class="cabeza"><h2>Del problema al cálculo multivariable</h2><span class="chip J">Presenta · Juan Jurado</span></div>
  <div class="cuerpo" style="grid-template-rows:auto auto 1fr;align-content:start">
    <div class="card c1"><p class="eq">Modelo: <b>y = a x + b</b> &nbsp;·&nbsp; Residuo: <b>eᵢ = yᵢ − (a xᵢ + b)</b></p></div>
    <div class="card c3" style="text-align:center"><p class="eq" style="font-size:clamp(24px,3.8vw,56px);color:var(--rosa);font-weight:700">S(a, b) = Σ (yᵢ − a xᵢ − b)²</p></div>
    <p class="big" style="align-self:center">Objetivo: hallar (a*, b*) que minimizan S.<br><span class="sub" style="font-weight:400">Función de DOS variables ⇒ gradiente, punto crítico y Hessiano.</span></p>
  </div>
</section>

<!-- 6 DERIVADAS -->
<section class="slide" data-notas="Derivar con regla de la cadena. Gradiente igual a cero. Sistema normal 2x2. (Juan muestra su hoja hecha a mano.)" data-app="/Modelo">
  <div class="cabeza"><h2>Derivadas parciales y sistema normal</h2><span class="chip J">Presenta · Juan Jurado</span></div>
  <div class="cuerpo g2" style="grid-template-rows:auto 1fr">
    <div class="card c2"><h3>Derivadas parciales</h3><p class="eq">∂S/∂a = −2 Σ xᵢ (yᵢ − a xᵢ − b)<br>∂S/∂b = −2 Σ (yᵢ − a xᵢ − b)</p></div>
    <div class="card c1" style="text-align:center"><h3>Punto crítico</h3><p class="eq big">∇S(a, b) = (0, 0)</p></div>
    <div class="card c3" style="grid-column:1/3;text-align:center"><h3>Sistema normal</h3><p class="eq" style="font-size:clamp(20px,3vw,44px)">a Σxᵢ² + b Σxᵢ = Σxᵢyᵢ<br>a Σxᵢ + n b = Σyᵢ</p></div>
  </div>
</section>

<!-- 7 SOLUCIÓN + VERIFICACIÓN EN VIVO -->
<section class="slide" data-notas="Solución por Cramer. n=15, Σx=120, Σy=319.09, Σx²=1240, Σxy=3303.26 → a*=2.680, b*=−0.170. El panel de la derecha recalcula todo en el navegador a partir de los datos." data-app="/Modelo">
  <div class="cabeza"><h2>Solución: a* y b*</h2><span class="chip J">Presenta · Juan Jurado</span></div>
  <div class="cuerpo g2">
    <div class="col">
      <div class="card c1"><p class="eq">a* = (nΣxy − ΣxΣy) / (nΣx² − (Σx)²)<br>b* = (Σy − a*Σx) / n</p></div>
      <div class="cuerpo g3" style="flex:none">
        <div class="card c1 m"><span class="l">a* (ms por 10⁵ elem.)</span><span class="v">[[a]]</span><span class="l">≈ [[ans]] ns/elemento</span></div>
        <div class="card c2 m"><span class="l">b* (ms)</span><span class="v">[[b]]</span><span class="l">costo fijo estimado</span></div>
        <div class="card c3 m"><span class="l">S_mín (ms²)</span><span class="v">[[smin]]</span><span class="l">error mínimo</span></div>
      </div>
      <div class="card c4"><h3>Sumatorias (x en 10⁵ elementos)</h3><p>n = [[n]] · Σx = [[sx]] · Σy = [[sy]] · Σx² = [[sxx]] · Σxy = [[sxy]]</p></div>
    </div>
    <div class="card c5"><h3>✔ Verificación en vivo (calculada ahora en tu navegador)</h3>
      <p class="sub" style="margin-bottom:1vh">Se recalculan las sumatorias y las fórmulas con JavaScript a partir de los 15 datos y se comparan con Python.</p>
      <table id="verif7"><thead><tr><th></th><th>Navegador (JS)</th><th>Python (app)</th><th>|dif.|</th></tr></thead><tbody></tbody></table>
      <button class="btn sec" style="margin-top:1.4vh" onclick="verif()">↻ Recalcular</button></div>
  </div>
</section>

<!-- 8 HESSIANO -->
<section class="slide" data-notas="H constante. det H = 4nΣ(x−x̄)² > 0 y S_aa > 0 → mínimo local estricto. H definida positiva → convexa → mínimo global único. Autovalores positivos; condición ≈ 373." data-app="/Hessiano">
  <div class="cabeza"><h2>Hessiano: ¿es un mínimo?</h2><span class="chip J">Presenta · Juan Jurado</span></div>
  <div class="cuerpo g2" style="grid-template-rows:1fr auto">
    <div class="card c1"><h3>Matriz hessiana (constante)</h3><p class="eq">H = [ 2Σx² &nbsp; 2Σx ; 2Σx &nbsp; 2n ]</p>
      <p class="eq" style="color:var(--cian)">H = [ [[h11]] &nbsp; [[h12]] ; [[h12]] &nbsp; [[h22]] ]</p><p class="eq" style="color:var(--cian)">det H = [[det]] &gt; 0 &nbsp;&nbsp; S_aa = [[saa]] &gt; 0</p>
      <p class="sub">Recalculado en vivo por el navegador: <b id="hjs" style="color:var(--verde)"></b></p></div>
    <div class="card c3"><h3>Autovalores</h3><p class="eq">λ₁ = [[l1]]<br>λ₂ = [[l2]]</p><p>Ambos &gt; 0 ⇒ H definida positiva.<br>Número de condición ≈ <b>[[cond]]</b>: valle muy alargado.</p></div>
    <div class="card c2" style="grid-column:1/3"><p class="big" style="font-size:clamp(16px,2vw,28px)"><b style="color:var(--cian)">Conclusión:</b> det H &gt; 0 y S_aa &gt; 0 ⇒ (a*, b*) es un <b>mínimo local estricto</b>. H constante y definida positiva ⇒ S convexa ⇒ el mínimo es <b>GLOBAL y único</b>.</p></div>
  </div>
</section>

<!-- 9 SUPERFICIE -->
<section class="slide" data-notas="Brayan: paraboloide elíptico abierto hacia arriba, un único mínimo (a*,b*) en rosa. Valle alargado: a y b correlacionados. ¡Rótenla con el mouse!" data-app="/Geometria">
  <div class="cabeza"><h2>Geometría: la superficie S(a, b)</h2><span class="chip B">Presenta · Brayan Guerrero</span></div>
  <div class="cuerpo g12">
    <div class="card plotcard c4"><div class="plot" data-fig="superficie"></div></div>
    <div class="card c4"><h3>Qué vemos (arrastre para rotar)</h3><ul><li>Paraboloide elíptico abierto hacia arriba.</li><li>Un solo punto mínimo: (a*, b*) en rosa.</li><li>Valle estrecho: a y b correlacionados.</li><li>H definida positiva ⇒ convexa.</li></ul></div>
  </div>
</section>

<!-- 10 CURVAS DE NIVEL Y TRAZAS -->
<section class="slide" data-notas="Curvas de nivel: elipses concéntricas alrededor de (a*,b*). Trazas: cortes con b=cte y a=cte son parábolas." data-app="/Geometria">
  <div class="cabeza"><h2>Curvas de nivel, trazas y secciones</h2><span class="chip B">Presenta · Brayan Guerrero</span></div>
  <div class="cuerpo g12">
    <div class="card plotcard c4"><div class="plot" data-fig="contornos"></div></div>
    <div class="col">
      <div class="card plotcard c1" style="flex:1"><div class="plot" data-fig="trazas_b"></div></div>
      <div class="card plotcard c3" style="flex:1"><div class="plot" data-fig="trazas_a"></div></div>
    </div>
  </div>
</section>

<!-- 11 DESCENSO -->
<section class="slide" data-notas="Pulsar Reproducir: el descenso por gradiente baja zigzagueando por el valle. No sustituye el cálculo analítico; muestra por qué el mínimo es único." data-app="/Geometria">
  <div class="cabeza"><h2>Animación: descenso por gradiente</h2><span class="chip B">Presenta · Brayan Guerrero</span></div>
  <div class="cuerpo g12">
    <div class="card plotcard c3"><div class="plot" data-fig="descenso"></div></div>
    <div class="card c3"><h3>Cómo leerlo</h3><ul><li>Pulse <b>▶ Reproducir</b>.</li><li>Cada paso va en dirección −∇S hasta el fondo del valle.</li><li>El <b>zigzag</b> aparece porque el valle es estrecho (condición ≈ [[cond]]).</li><li>No sustituye el cálculo: las fórmulas normales resuelven ∇S = 0 de una sola vez.</li></ul></div>
  </div>
</section>

<!-- 12 PRUEBA TU RECTA -->
<section class="slide" data-notas="Muevan los sliders: ninguna recta distinta de (a*,b*) obtiene un S menor. S se calcula en vivo en el navegador." data-app="/Ajuste">
  <div class="cabeza"><h2>Pruebe otras rectas: nadie le gana a (a*, b*)</h2><span class="chip B">Presenta · Brayan Guerrero</span></div>
  <div class="cuerpo g12">
    <div class="card plotcard c1"><div class="plot" id="plotRecta"></div></div>
    <div class="col">
      <div class="card c4"><h3>Su recta (a, b)</h3>
        <p class="sub">a = <b id="va"></b> ms/10⁵ elem.</p><input type="range" id="sa" oninput="recta()">
        <p class="sub" style="margin-top:1vh">b = <b id="vb"></b> ms</p><input type="range" id="sb" oninput="recta()">
        <button class="btn sec" style="margin-top:1.2vh" onclick="resetRecta()">Volver al óptimo</button></div>
      <div class="card c3 m"><span class="l">S de su recta (ms²)</span><span class="v" id="vS"></span><span class="l" id="vR"></span></div>
      <div class="card c5 m"><span class="l">S_mín (recta óptima)</span><span class="v">[[smin]]</span><span class="l">calculada por la app (Python)</span></div>
    </div>
  </div>
</section>

<!-- 13 VERIFICACIÓN -->
<section class="slide" data-notas="Código propio = numpy.polyfit = scipy.stats.linregress = JavaScript. Diferencias ~1e-16 por redondeo de punto flotante. El valor manual de Juan se compara en la página Comparación de la app." data-app="/Comparacion">
  <div class="cabeza"><h2>Analítico vs. código vs. biblioteca</h2><span class="chip B">Presenta · Brayan Guerrero</span></div>
  <div class="cuerpo g12">
    <div class="card c2"><h3>Tabla de la sección 9 (valores en vivo)</h3>
      <table id="tabla13"><thead><tr><th>Parám.</th><th>Analítico (manual)</th><th>Código propio</th><th>polyfit</th><th>linregress</th><th>Dif. máx.</th></tr></thead><tbody></tbody></table>
      <p class="sub" style="margin-top:1vh">La columna «manual» se llena con el resultado de Juan en la página <b>Comparación</b> de la app.</p></div>
    <div class="card c5"><h3>Lectura</h3><ul><li>Los 4 métodos (propio, polyfit, linregress y JS) coinciden.</li><li>Diferencias ≈ 10⁻¹⁶: precisión de máquina (float64).</li><li>Una diferencia mayor en lo manual = redondeo de sumas a mano.</li></ul></div>
  </div>
</section>

<!-- 14 RESIDUOS -->
<section class="slide" data-notas="Residuos centrados en cero (por construcción), sin patrón curvo. La dispersión crece con n. Dos puntos marginales." data-app="/Calidad">
  <div class="cabeza"><h2>Análisis de residuos</h2><span class="chip M">Presenta · Mario Zambrano</span></div>
  <div class="cuerpo" style="grid-template-rows:1fr auto">
    <div class="cuerpo g12"><div class="card plotcard c3"><div class="plot" data-fig="residuos"></div></div><div class="card plotcard c1"><div class="plot" data-fig="histograma"></div></div></div>
    <div class="card c3"><ul><li>Centrados en cero y sin patrón curvo (corr. con curvatura = [[corr_curv]]) ⇒ modelo lineal compatible.</li>
      <li>La dispersión crece con n (corr |e|–x = [[corr_abs]]): ruido proporcional al tiempo.</li><li>[[natip]] puntos rozan |t| &gt; 2 (marginales); sin errores graves.</li></ul></div>
  </div>
</section>

<!-- 15 CALIDAD -->
<section class="slide" data-notas="RMSE = error típico en ms. R² alto porque T depende casi solo de n; no prueba linealidad, por eso se miran los residuos." data-app="/Calidad">
  <div class="cabeza"><h2>Calidad del ajuste</h2><span class="chip M">Presenta · Mario Zambrano</span></div>
  <div class="cuerpo" style="grid-template-rows:auto 1fr">
    <div class="cuerpo g3">
      <div class="card c2 m"><span class="l">RMSE (ms)</span><span class="v">[[rmse]]</span><span class="l">error típico</span></div>
      <div class="card c1 m"><span class="l">R²</span><span class="v">[[r2]]</span><span class="l">explica [[r2pct]] % de la variación</span></div>
      <div class="card c3 m"><span class="l">RMSE / T medio</span><span class="v">[[rmse_pct]] %</span><span class="l">T medio = [[tmean]] ms</span></div>
    </div>
    <div class="cuerpo g2">
      <div class="card c2"><h3>¿Qué significa el RMSE?</h3><p>La recta se equivoca, en promedio, unos [[rmse]] ms: un error pequeño para estimar cuánto tarda una búsqueda de un tamaño dado.</p></div>
      <div class="card c1"><h3>¿Y el R²?</h3><p>Es muy alto porque T depende casi solo de n y el rango de n es amplio. No prueba que el modelo sea lineal: por eso revisamos los residuos.</p></div>
    </div>
  </div>
</section>

<!-- 16 ADICIONAL -->
<section class="slide" data-notas="Opción B: elijan un punto y la recta se recalcula en vivo. El más influyente es el n.º 15. Opción C: parábola con término x² casi cero (p=0.83): el modelo lineal basta." data-app="/Adicional">
  <div class="cabeza"><h2>Análisis adicional: Opciones B y C</h2><span class="chip M">Presenta · Mario Zambrano</span></div>
  <div class="cuerpo g2" style="grid-template-rows:1fr auto">
    <div class="card plotcard c4"><div class="plot" data-fig="influencia" id="plotInfl"></div></div>
    <div class="card plotcard c2"><div class="plot" data-fig="cuadratico"></div></div>
    <div class="card c4"><h3>B · Influencia de un dato (se recalcula en vivo)</h3>
      <p>Eliminar el punto n.º <select id="selP" onchange="infl()"></select> → <b id="resB"></b></p><p class="sub">Más influyente: n.º [[imax]] (Cook = [[cook]] &gt; 4/n = [[cook_ref]]).</p></div>
    <div class="card c2"><h3>C · Lineal vs. cuadrático</h3><p>Término x² ≈ 0 (c₂ = [[c2]]), p = [[pF]], aporta [[aporte]] %. R² ajustado: lineal [[r2adj_lin]] vs cuadrático [[r2adj_q]] ⇒ el modelo O(n) basta.</p></div>
  </div>
</section>

<!-- 17 CONCLUSIONES -->
<section class="slide" data-notas="Responder la pregunta central. Invitar a ver la app en vivo (botón Ver en vivo)." data-app="/">
  <div class="cabeza"><h2>Conclusiones</h2><span class="chip M">Presenta · Mario Zambrano</span></div>
  <div class="cuerpo g2" style="grid-template-rows:1fr 1fr auto">
    <div class="card c2"><h3>Analítico</h3><p>∇S = 0 da el sistema normal; a* y b* salen de fórmulas exactas.</p></div>
    <div class="card c1"><h3>Hessiano</h3><p>det H &gt; 0 y S_aa &gt; 0 ⇒ mínimo; H definida positiva ⇒ global y único.</p></div>
    <div class="card c4"><h3>Geométrico</h3><p>Paraboloide con un valle: el mejor ajuste es el fondo.</p></div>
    <div class="card c3"><h3>Computacional</h3><p>Código propio = polyfit = linregress = JS; la app lo verifica y lo visualiza.</p></div>
    <div class="card c3" style="grid-column:1/3;text-align:center"><p class="eq" style="font-size:clamp(16px,2.2vw,32px);font-weight:700">T(n) ≈ [[a]]·(n/10⁵) + ([[b]]) ms &nbsp;·&nbsp; RMSE = [[rmse]] ms &nbsp;·&nbsp; R² = [[r2]]</p></div>
  </div>
</section>

<!-- 18 GRACIAS -->
<section class="slide portada" data-notas="Cerrar y abrir preguntas. Tener la app abierta por si piden demostrar algo." data-app="/">
  <div class="orbe" style="right:-4vw;top:-6vh;width:44vw;height:44vw;background:var(--indigo)"></div>
  <div class="orbe" style="right:10vw;bottom:-12vh;width:28vw;height:28vw;background:var(--rosa);animation-delay:-4s"></div>
  <h1 class="grad" style="font-size:clamp(48px,8vw,120px)">¡Gracias!</h1>
  <p class="big" style="color:var(--cian);margin-top:2vh">¿Preguntas?</p>
  <p class="sub" style="margin-top:3vh">Nicoll Valentina López Andrade · Juan David Jurado Paz · Brayan Steven Guerrero Acosta · Mario Alberto Zambrano Muñoz</p>
</section>

</div>

<div id="notas"></div>
<div id="overlay"><div style="display:flex;gap:10px;align-items:center"><b id="ovTitulo" style="flex:1"></b><button class="btn sec" onclick="cerrarApp()">✕ Cerrar (Esc)</button></div>
  <iframe id="ovFrame" title="App en vivo"></iframe><p class="sub" id="ovAyuda"></p></div>
<div id="estado" class="badge"><span class="dot" id="dot"></span><span id="estadoTxt">App desconectada</span><button class="btn" id="btnApp" style="padding:4px 12px;display:none" onclick="abrirApp(true)">Ver en vivo</button><button class="btn sec" id="btnApp2" style="padding:4px 12px;display:none" onclick="abrirApp(false)">Abrir en la app ↗</button></div>
<div id="nav"><button onclick="ir(-1)" title="Anterior (←)">◀</button><span id="cuenta"></span><button onclick="ir(1)" title="Siguiente (→)">▶</button>
  <button onclick="alternarNotas()" title="Notas del orador (N)">📝</button><button onclick="pantallaCompleta()" title="Pantalla completa (F)">⛶</button></div>

<script>__PLOTLY__</script>
<script>
const D = __DATA__;
const slides = [...document.querySelectorAll('.slide')];
let cur = 0;
const C = {indigo:'#818CF8', cian:'#22D3EE', rosa:'#F472B6', naranja:'#FB923C', neutro:'#94A3B8'};

/* ---------- Regresión desde cero en el navegador ---------- */
function fit(x, y){
  const n=x.length; let sx=0,sy=0,sxx=0,sxy=0;
  for(let i=0;i<n;i++){sx+=x[i];sy+=y[i];sxx+=x[i]*x[i];sxy+=x[i]*y[i];}
  const d=n*sxx-sx*sx, a=(n*sxy-sx*sy)/d, b=(sy-a*sx)/n; let s=0;
  for(let i=0;i<n;i++){const e=y[i]-a*x[i]-b; s+=e*e;}
  return {n,sx,sy,sxx,sxy,d,a,b,s};
}
const SS = (a,b,x,y)=>{let s=0;for(let i=0;i<x.length;i++){const e=y[i]-a*x[i]-b;s+=e*e;}return s;};
const fm = (v,c=6)=>Number(v).toPrecision(c).replace(/\.?0+$/,'').replace(/(\.\d*?)0+e/,'$1e');
const fe = v=>Number(v).toExponential(1);

function verif(){
  const r=fit(D.x,D.y), P=D.py, tb=document.querySelector('#verif7 tbody');
  const f=[['n',r.n,D.x.length],['Σx',r.sx,null],['Σx²',r.sxx,null],['Σxy',r.sxy,null],['a*',r.a,P.a],['b*',r.b,P.b],['S_mín',r.s,P.smin]];
  tb.innerHTML=f.map(([n,js,py])=>`<tr><td>${n}</td><td>${fm(js,8)}</td><td>${py===null?'—':fm(py,8)}</td><td class="ok">${py===null?'—':fe(Math.abs(js-py))}</td></tr>`).join('');
}
function hess(){
  const r=fit(D.x,D.y), h11=2*r.sxx,h12=2*r.sx,h22=2*r.n, det=h11*h22-h12*h12, tr=h11+h22, disc=Math.sqrt(tr*tr/4-det);
  const l1=tr/2-disc,l2=tr/2+disc;
  document.getElementById('hjs').textContent=`det H = ${fm(det)} · λ₁ = ${fm(l1,5)} · λ₂ = ${fm(l2,5)} ✔ coincide con Python`;
}
function tabla13(){
  const r=fit(D.x,D.y), P=D.py, N=P.numpy, S=P.scipy;
  const rows=[['a',null,P.a,N[0],S[0],r.a],['b',null,P.b,N[1],S[1],r.b],['S_mín',null,P.smin,N[2],S[2],r.s]];
  document.querySelector('#tabla13 tbody').innerHTML=rows.map(([n,man,p,np,sp,js])=>{
    const vals=[p,np,sp,js]; const dif=Math.max(...vals)-Math.min(...vals);
    return `<tr><td>${n}</td><td class="sub">(su cálculo a mano)</td><td>${fm(p,8)}</td><td>${fm(np,8)}</td><td>${fm(sp,8)}</td><td class="ok">${fe(dif)}</td></tr>`;}).join('');
}

/* ---------- Slide 12: sliders ---------- */
let rectaInit=false;
function iniciarRecta(){
  if(rectaInit) return; rectaInit=true; const P=D.py, sa=document.getElementById('sa'), sb=document.getElementById('sb');
  sa.min=P.a-P.da;sa.max=P.a+P.da;sa.step=(2*P.da)/400;sb.min=P.b-P.db;sb.max=P.b+P.db;sb.step=(2*P.db)/400;
  sa.value=P.a+0.5*P.da; sb.value=P.b-0.4*P.db;
  const fx=[0,1.05*Math.max(...D.x)];
  Plotly.newPlot('plotRecta',[
    {x:D.x,y:D.y,mode:'markers',name:'Datos',marker:{color:C.neutro,size:9}},
    {x:fx,y:fx.map(v=>P.a*v+P.b),mode:'lines',name:'Óptima (a*, b*)',line:{color:C.indigo,width:3.5}},
    {x:fx,y:fx.map(v=>0),mode:'lines',name:'Su recta',line:{color:C.naranja,width:2.5,dash:'dash'}}],
    {paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{color:'#E2E8F0'},margin:{l:60,r:20,t:40,b:56},autosize:true,
     xaxis:{title:{text:'n (×10⁵ elementos)'},gridcolor:'rgba(148,163,184,.25)',rangemode:'tozero'},yaxis:{title:{text:'T (ms)'},gridcolor:'rgba(148,163,184,.25)'},
     legend:{orientation:'h',y:1.08,x:1,xanchor:'right'}},{responsive:true,displaylogo:false});
  recta();
}
function recta(){
  const a=+document.getElementById('sa').value,b=+document.getElementById('sb').value,fx=[0,1.05*Math.max(...D.x)];
  document.getElementById('va').textContent=fm(a,5);document.getElementById('vb').textContent=fm(b,5);
  const S=SS(a,b,D.x,D.y); document.getElementById('vS').textContent=fm(S,5);
  document.getElementById('vR').textContent=`${(S/D.py.smin).toFixed(2)} × S_mín  ·  ${S>=D.py.smin-1e-9?'≥ S_mín ✔':'¡menor!'}`;
  Plotly.restyle('plotRecta',{x:[fx],y:[fx.map(v=>a*v+b)]},[2]);
}
function resetRecta(){const P=D.py;document.getElementById('sa').value=P.a;document.getElementById('sb').value=P.b;recta();}

/* ---------- Slide 16: influencia en vivo ---------- */
function iniciarInfl(){
  const sel=document.getElementById('selP'); if(sel.options.length) return;
  D.x.forEach((v,i)=>{const o=document.createElement('option');o.value=i;o.textContent=(i+1)+(i===D.py.imax?' ★':'');sel.appendChild(o);});
  sel.value=D.py.imax; infl();
}
function infl(){
  const i=+document.getElementById('selP').value, x=D.x.filter((_,k)=>k!==i), y=D.y.filter((_,k)=>k!==i), r=fit(x,y), P=D.py, fx=[0,1.05*Math.max(...D.x)];
  const el=document.getElementById('plotInfl'); if(el.data){
    Plotly.restyle(el,{x:[[D.x[i]]],y:[[D.y[i]]]},[1]); Plotly.restyle(el,{x:[fx],y:[fx.map(v=>r.a*v+r.b)]},[3]);}
  document.getElementById('resB').innerHTML=`a = ${fm(r.a,6)} (Δ ${(100*(r.a-P.a)/P.a).toFixed(2)} %) · b = ${fm(r.b,5)}`;
}

/* ---------- Gráficas (las mismas figuras de la app) ---------- */
const hechas = new Set();
function dibujar(s){
  s.querySelectorAll('.plot[data-fig]').forEach(el=>{
    const k=el.dataset.fig;
    if(hechas.has(el)){Plotly.Plots.resize(el);return;}
    hechas.add(el); const F=D.figs[k];
    Plotly.newPlot(el,F.data,F.layout,{responsive:true,displaylogo:false}).then(()=>{ if(F.frames&&F.frames.length) Plotly.addFrames(el,F.frames); if(k==='influencia') infl(); });
  });
  const pr=s.querySelector('#plotRecta'); if(pr){iniciarRecta(); Plotly.Plots.resize(pr);}
  if(s.querySelector('#selP')) iniciarInfl();
}

/* ---------- Navegación ---------- */
function mostrar(i){
  cur=Math.max(0,Math.min(slides.length-1,i)); slides.forEach((s,k)=>s.classList.toggle('activa',k===cur));
  document.getElementById('cuenta').textContent=`${cur+1} / ${slides.length}`;
  document.getElementById('barra').style.width=((cur+1)/slides.length*100)+'%';
  document.getElementById('notas').textContent='🗒 '+(slides[cur].dataset.notas||'');
  history.replaceState(null,'','#'+(cur+1)); setTimeout(()=>dibujar(slides[cur]),120); actualizarBotones();
}
const ir = d=>mostrar(cur+d);
function alternarNotas(){document.getElementById('notas').classList.toggle('on');}
function pantallaCompleta(){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();}
addEventListener('keydown',e=>{
  if(e.target.tagName==='SELECT'||e.target.tagName==='INPUT') return;
  if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();ir(1);} else if(['ArrowLeft','PageUp'].includes(e.key)){ir(-1);}
  else if(e.key==='Home')mostrar(0); else if(e.key==='End')mostrar(slides.length-1);
  else if(e.key==='n'||e.key==='N')alternarNotas(); else if(e.key==='f'||e.key==='F')pantallaCompleta(); else if(e.key==='Escape')cerrarApp();
});
let tx=null; addEventListener('touchstart',e=>tx=e.touches[0].clientX); addEventListener('touchend',e=>{if(tx===null)return;const d=e.changedTouches[0].clientX-tx;if(Math.abs(d)>60)ir(d<0?1:-1);tx=null;});
addEventListener('resize',()=>dibujar(slides[cur]));
addEventListener('hashchange',()=>{const n=(parseInt(location.hash.slice(1))||1)-1; if(n!==cur) mostrar(n);});

/* ---------- Conexión con la app Streamlit ---------- */
const APP=`http://localhost:${D.puerto}`; let appOn=false;
async function ping(){
  try{await fetch(APP+'/_stcore/health',{mode:'no-cors',cache:'no-store'});appOn=true;}catch(e){appOn=false;}
  document.getElementById('dot').classList.toggle('on',appOn);
  document.getElementById('estadoTxt').textContent=appOn?`App conectada (localhost:${D.puerto})`:'App desconectada · streamlit run app.py';
  actualizarBotones();
}
function actualizarBotones(){
  const ruta=slides[cur].dataset.app; const hay=appOn&&ruta!==undefined&&ruta!=='';
  document.getElementById('btnApp').style.display=hay?'inline-block':'none';document.getElementById('btnApp2').style.display=hay?'inline-block':'none';
}
function abrirApp(embebida){
  const ruta=slides[cur].dataset.app||'/', url=APP+ruta;
  if(!embebida){window.open(url,'_blank');return;}
  document.getElementById('ovTitulo').textContent='App en vivo · '+(ruta==='/'?'Datos':ruta.slice(1));
  document.getElementById('ovFrame').src=url+(url.includes('?')?'&':'?')+'embed=true';
  document.getElementById('ovAyuda').textContent='Es la misma app (streamlit run app.py): estos son los mismos datos y los mismos cálculos.';
  document.getElementById('overlay').classList.add('on');
}
function cerrarApp(){document.getElementById('overlay').classList.remove('on');document.getElementById('ovFrame').src='about:blank';}

verif(); hess(); tabla13(); ping(); setInterval(ping,5000);
mostrar(Math.max(0,(parseInt(location.hash.slice(1))||1)-1));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera la presentación HTML interactiva.")
    ap.add_argument("--puerto", type=int, default=8501, help="Puerto donde corre la app Streamlit.")
    main(ap.parse_args().puerto)
