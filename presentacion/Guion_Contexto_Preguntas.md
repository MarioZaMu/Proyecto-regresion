# Guion, contexto y preguntas — Proyecto de Cálculo Multivariable

**Equipo:** Nicoll López · Juan Jurado · Brayan Guerrero · Mario Zambrano
**Tema:** Regresión lineal y optimización con funciones de varias variables
**Problema real:** tiempo de ejecución de una búsqueda lineal en función del tamaño de la entrada

> Los números de este documento salen de la medición real del 14-nov-2026 (`datos/datos.csv`).
> Si vuelven a correr `datos/medir.py`, los tiempos cambian un poco: ejecuten `python presentacion/generar_pptx.py`
> para regenerar las diapositivas y actualicen las cifras de este guion (están marcadas en **negrita**).

---

## PARTE 1 · CONTEXTO COMPLETO (léanlo todos, para no confundirse)

### 1.1 ¿De qué trata el proyecto, en una frase?
Medimos cuánto tarda una **búsqueda lineal** en Python al crecer el tamaño de la lista, vimos que los puntos forman casi una recta
`T = a·n + b`, y usamos **cálculo multivariable** (derivadas parciales, gradiente, Hessiano) para encontrar **la mejor recta**
y demostrar que es un **mínimo**. Después lo verificamos con código y con bibliotecas, y lo visualizamos en una app.

### 1.2 La pregunta central del enunciado
> *¿Cómo se puede utilizar el Cálculo Multivariable para determinar y analizar el modelo lineal que mejor representa un conjunto de datos?*

Se responde con **tres perspectivas**: **análisis analítico** + **interpretación geométrica** + **análisis computacional**.
Regla de oro del enunciado: *el computador NO sustituye el desarrollo matemático; solo lo verifica y lo visualiza.*

### 1.3 El problema real y por qué es lineal
- Búsqueda lineal = un `for` que recorre la lista comparando elemento por elemento.
- Peor caso: el elemento **no está** → hace exactamente **n comparaciones** → complejidad **O(n)**.
- Por eso `T(n) ≈ a·n + b`:
  - **a** = costo por elemento (una vuelta del bucle).
  - **b** = costo fijo de arranque (llamar la función, leer el cronómetro).
- **Variables:** x = n (tamaño, en elementos) · y = T (tiempo, en ms).
- **Ruido real** (por qué los puntos no caen exactos en la recta): planificador del sistema operativo, memoria caché de la CPU,
  recolector de basura de Python, otros programas abiertos, cambios en la frecuencia del procesador.

### 1.4 Cómo se tomaron los datos (`datos/medir.py`)
- Búsqueda lineal propia (sin `in`), lista `list(range(n))`, se busca `-1` (ausente).
- 15 tamaños: 100 000, 200 000, …, 1 500 000.
- Por cada tamaño: **2 ejecuciones de calentamiento (se descartan)** + **5 mediciones** → se guarda la **mediana**.
- Cronómetro: `time.perf_counter_ns()`. **Los tiempos nunca se simulan ni se editan.**
- Guarda `datos.csv`, `mediciones_detalle.csv` (mín, máx, desviación) y `metadata.json` (fecha, Python, SO, procesador, RAM).
- Equipo usado: Windows 11, AMD64, 15.31 GB RAM, Python 3.14.5.

### 1.5 La matemática (el corazón del trabajo)

**Función de error:** `S(a,b) = Σ (yᵢ − a·xᵢ − b)²` — la suma de los cuadrados de los residuos `eᵢ = yᵢ − (a·xᵢ + b)`.
Se elevan al cuadrado porque unos errores son positivos y otros negativos (se cancelarían).

**Derivadas parciales:**
- ∂S/∂a = −2 Σ xᵢ (yᵢ − a·xᵢ − b)
- ∂S/∂b = −2 Σ (yᵢ − a·xᵢ − b)

**Punto crítico:** ∇S = (0,0) → **sistema normal:**
- a·Σx² + b·Σx = Σxy
- a·Σx + n·b = Σy

**Solución:**
- a\* = (nΣxy − ΣxΣy) / (nΣx² − (Σx)²)
- b\* = (Σy − a\*·Σx) / n

**Hessiano:** `H = [[2Σx², 2Σx], [2Σx, 2n]]` (es **constante**: no depende de a ni b).
- `det H = 4[nΣx² − (Σx)²] = 4n·Σ(xᵢ − x̄)²` → es **> 0** siempre que los x no sean todos iguales (Cauchy–Schwarz).
- `S_aa = 2Σx² > 0`.
- Criterio de las segundas derivadas: `det H > 0` y `S_aa > 0` ⇒ **mínimo local estricto**.
- Como H es constante y definida positiva en todo ℝ², S es **convexa** ⇒ el mínimo es **global y único**.

**Geometría:** z = S(a,b) es un **paraboloide elíptico** abierto hacia arriba con un solo punto más bajo (a\*, b\*).
Las **curvas de nivel** son **elipses concéntricas**; las **trazas** (cortar con planos a = cte o b = cte) son **parábolas**.
El valle es muy alargado porque el **número de condición** del Hessiano es grande (λ₂/λ₁ ≈ **373**): a y b están muy correlacionados.

### 1.5.1 Escala de x (para no confundirse con las unidades)
Usamos `x' = n / 10⁵` (unidades de **10⁵ elementos**) para evitar números enormes (Σx² llegaría a ~10¹³).
- `a'` está en **ms por 10⁵ elementos**; `a_original = a' / 10⁵` ms/elemento.
- `b`, `S_mín`, RMSE y R² **no cambian** con la escala.
- Con la escala: a\* = **2.68038** ms por 10⁵ elementos = **26.8 ns por elemento**.

### 1.6 Resultados clave (datos reales del 14-nov-2026)

| Magnitud | Valor |
|---|---|
| n (puntos) | 15 |
| Σx · Σy | **120** · **319.0939** |
| Σx² · Σxy | **1240** · **3303.2564** |
| **a\*** | **2.680376** ms por 10⁵ elementos (≈ 26.8 ns/elemento) |
| **b\*** | **−0.170079** ms |
| **S_mín** | **1.661017** ms² |
| **RMSE** | **0.332768** ms (≈ 1.2 % del tiempo medio) |
| **R²** | **0.999175** |
| Hessiano H | **[[2480, 240], [240, 30]]**, det H = **16800** |
| Autovalores | **6.711** y **2503.29** (ambos > 0) |

Cálculo a mano de comprobación: `a* = (15·3303.2564 − 120·319.0939) / (15·1240 − 120²) = 11257.578 / 4200 = 2.680376`;
`b* = (319.0939 − 2.680376·120) / 15 = −0.170079`.

### 1.7 Verificación computacional
- **Código propio** (fórmulas normales, sin funciones de regresión) = **`numpy.polyfit`** = **`scipy.stats.linregress`**.
- Diferencias máximas ≈ **10⁻¹⁶ a 10⁻¹⁵** → es **error de redondeo** de punto flotante (float64), no un error real.
- Tabla de la sección 9: **Analítico (manual)** | **Código propio** | **Biblioteca** | **Diferencia máxima** para a, b y S_mín.
  El valor "manual" lo escribe Juan en la app con lo que obtuvo en papel.
- Hessiano verificado también por **diferencias finitas** (coincide con el analítico) y gradiente ≈ 0 en (a\*, b\*).

### 1.8 Calidad y residuos
- **RMSE** = √(Σe²/n) = error típico, en ms: **0.333 ms**.
- **R²** = fracción de la variación de T que explica la recta: **99.92 %**. Es altísimo porque T depende casi solo de n,
  pero **R² alto no prueba linealidad** → por eso se miran los residuos.
- Residuos: media 0 **por construcción** (el método con intercepto lo garantiza); no hay patrón curvo (correlación con curvatura **−0.06**);
  la **dispersión crece con n** (corr |e|–x = **0.63**): el ruido es proporcional al tiempo; **2 puntos marginales** (|t| ≈ 2.04 y 2.21).
  No hay desviación sistemática.

### 1.9 Análisis adicional (el enunciado pide al menos uno; hicimos B y C, y A como extra)
- **Opción B (influencia de un dato):** el punto más influyente es el **n.º 15** (n = 1 500 000, extremo derecho; distancia de Cook **0.78** > 4/n = 0.27).
  Al quitarlo, a\* pasa de 2.6804 a **2.7030** (cambia **0.85 %**) y b\* de −0.170 a **−0.291** → la recta es **estable**.
  Los puntos de los extremos tienen más *apalancamiento* (leverage).
- **Opción C (cuadrático y = ax² + bx + c):** el coeficiente cuadrático es **≈ −0.00126** (casi cero), p = **0.83** (no significativo),
  aporta solo **0.71 %** del tiempo en el extremo y el R² ajustado **no mejora** → el modelo **O(n) es suficiente**.
- **Opción A (sensibilidad):** al perturbar los datos ±1 %, a\* varía muy poco: el modelo es poco sensible.

### 1.10 La aplicación (Streamlit) — qué muestra cada página
1. **Datos:** ficha técnica, tabla, dispersión, justificación O(n), interpretación de a\* y b\*, opción de escalar x.
2. **Modelo y fórmulas:** derivación en LaTeX (solo referencia; el desarrollo manual lo hacemos en papel).
3. **Ajuste:** recta óptima y rectas alternativas con sliders, mostrando su S (siempre mayor que S_mín).
4. **Geometría:** superficie 3D, curvas de nivel, trazas, secciones, y **animación del descenso por gradiente**.
5. **Hessiano:** matriz, determinante, autovalores, verificación numérica y convexidad.
6. **Comparación:** tabla de la sección 9 (con el campo del valor manual).
7. **Calidad y residuos:** gráficos, RMSE, R², diagnóstico automático y espacios de texto.
8. **Análisis adicional:** opciones B, C y A.
9. **Exportar:** PNG de todas las figuras + resumen en PDF/Markdown.

**Cómo abrirla en la defensa:** `streamlit run app.py` (tener ya abierta la pestaña antes de empezar).

### 1.11 Mapa de archivos
| Archivo | Para qué |
|---|---|
| `datos/medir.py` | Mide los tiempos reales |
| `core/regresion.py` | Ajuste **desde cero**, S(a,b), gradiente, Hessiano, criterio, descenso por gradiente |
| `core/verificacion.py` | Compara con `polyfit` y `linregress` |
| `core/metricas.py` | Residuos, RMSE, R², atípicos, Cook |
| `core/extras.py` | Opciones A, B y C |
| `app.py` + `pages/` | La aplicación |
| `tests/` | 19 pruebas con pytest (ajuste propio = polyfit = linregress a 1e-9, H definida positiva, ∇S ≈ 0, etc.) |
| `presentacion/` | Diapositivas y este documento |

### 1.12 Glosario rápido
- **Gradiente ∇S:** vector de derivadas parciales; apunta hacia donde S crece más rápido. En el mínimo vale 0.
- **Punto crítico:** donde ∇S = 0.
- **Hessiano H:** matriz de segundas derivadas; dice si el punto crítico es mínimo, máximo o silla.
- **Definida positiva:** todos sus autovalores son > 0 → la función es convexa.
- **Residuo eᵢ:** distancia vertical entre el dato y la recta.
- **RMSE:** error típico en las unidades de y. **R²:** fracción de variación explicada.
- **Atípico (outlier):** punto que se aleja mucho de la tendencia. **Influyente:** punto que, si se quita, mueve mucho la recta.
- **Convexa:** tiene forma de "cuenco"; su único mínimo local es global.

---

## PARTE 2 · REPARTO Y TIEMPOS (≈ 13–15 min + preguntas)

| Quién | Diapositivas | Tema | Tiempo |
|---|---|---|---|
| **Nicoll López** | 1–4 | Introducción, pregunta central, problema real y datos | ~3 min |
| **Juan Jurado** | 5–8 | Parte analítica: S, derivadas, sistema normal, solución, Hessiano | ~4 min |
| **Brayan Guerrero** | 9–12 | Geometría y verificación computacional | ~3.5 min |
| **Mario Zambrano** | 13–17 | Residuos, calidad, análisis adicional, conclusiones, demo de la app | ~4 min |

**Transiciones:** cada uno termina con una frase que da paso al siguiente (están en el guion).
**Regla:** todos deben saber TODO el proyecto (los profes preguntan a cualquiera). Lean la Parte 1 completa.

---

## PARTE 3 · GUION DIAPOSITIVA POR DIAPOSITIVA

> Texto en *cursiva* = lo que se dice. Entre corchetes = acción en pantalla.

### 🟦 NICOLL LÓPEZ (diapositivas 1–4)

**Diap. 1 — Portada**
*"Buenos días/tardes, profesor(a). Somos Nicoll López, Juan Jurado, Brayan Guerrero y Mario Zambrano. Nuestro proyecto de Cálculo Multivariable
se llama 'Regresión lineal y optimización con funciones de varias variables'. Vamos a mostrar cómo el cálculo multivariable nos permite encontrar
la mejor recta para un problema real: cuánto tarda una búsqueda lineal cuando crece la entrada."*

**Diap. 2 — Pregunta central**
*"La pregunta que guía el trabajo es: ¿cómo se puede usar el Cálculo Multivariable para determinar y analizar el modelo lineal que mejor representa
un conjunto de datos? La respondemos con tres perspectivas: el análisis analítico, hecho a mano, con derivadas parciales, gradiente y Hessiano;
la interpretación geométrica, con la superficie de error y sus curvas de nivel; y el análisis computacional, donde programamos el ajuste
y lo comparamos con bibliotecas. Es importante: el computador no reemplaza la matemática, la verifica y la visualiza."*

**Diap. 3 — Problema real**
*"Elegimos un problema real: el tiempo de ejecución de una búsqueda lineal. Esta búsqueda recorre la lista elemento por elemento; en el peor caso,
cuando el elemento no está, hace exactamente n comparaciones, o sea es O(n). Por eso esperamos que el tiempo sea T ≈ a·n + b, donde a es el costo
por elemento y b el costo fijo de arranque. La variable x es el tamaño n en elementos y la y es el tiempo en milisegundos. Para evitar números enormes
usamos x' = n/10⁵. Los puntos no caerán exactamente en una recta por el ruido real del sistema: el planificador del sistema operativo, la caché de la CPU,
el recolector de basura y otros procesos."*

**Diap. 4 — Datos**
*"Medimos 15 tamaños, de cien mil a un millón quinientos mil elementos, con el cronómetro perf_counter_ns. Para cada tamaño hicimos dos ejecuciones
de calentamiento que se descartan y cinco mediciones, y guardamos la mediana. Los tiempos nunca se simularon ni se editaron. En el diagrama de dispersión
se ve una tendencia claramente lineal creciente, así que el modelo y = ax + b es razonable. Ahora Juan les muestra cómo encontramos la mejor recta con cálculo."*

---

### 🟪 JUAN JURADO (diapositivas 5–8)  — *tengan a mano la hoja con el desarrollo hecho a mano*

**Diap. 5 — Del problema al cálculo multivariable**
*"Proponemos y = ax + b. Para cada dato, el residuo es e_i = y_i − (a·x_i + b). Como unos residuos son positivos y otros negativos, sumamos sus cuadrados
y definimos la función de error S(a,b) = Σ(y_i − a·x_i − b)². Ahora tenemos una función de dos variables, a y b, y queremos el punto (a*, b*) que la minimice.
Esto es exactamente un problema de optimización multivariable: gradiente, punto crítico y Hessiano."*

**Diap. 6 — Derivadas parciales y sistema normal** *[mostrar el papel]*
*"Derivamos respecto a a: ∂S/∂a = −2Σ x_i(y_i − a·x_i − b). Respecto a b: ∂S/∂b = −2Σ(y_i − a·x_i − b). Una condición necesaria para un mínimo es que el gradiente
sea cero. Igualamos ambas a cero, dividimos entre −2 y distribuimos las sumas. Queda el sistema normal: a·Σx² + b·Σx = Σxy y a·Σx + n·b = Σy.
Es un sistema lineal 2×2 en las incógnitas a y b."*

**Diap. 7 — Solución**
*"Resolviéndolo, por Cramer o por eliminación, obtenemos a* = (nΣxy − ΣxΣy)/(nΣx² − (Σx)²) y b* = (Σy − a*Σx)/n. Con nuestros datos: n = 15,
Σx = 120, Σy = 319.09, Σx² = 1240 y Σxy = 3303.26. Reemplazando, a* = 11257.58 / 4200 = 2.680, es decir 2.68 milisegundos por cada cien mil elementos,
unos 26.8 nanosegundos por elemento. Y b* = −0.17 milisegundos, un costo fijo despreciable frente a los 39 ms del mayor tamaño. El error mínimo es S_mín = 1.661."*

**Diap. 8 — Hessiano**
*"Falta demostrar que es un mínimo. Calculamos las segundas derivadas: S_aa = 2Σx², S_bb = 2n y S_ab = 2Σx. El Hessiano es H = [[2480, 240],[240, 30]].
Su determinante es 16800, positivo, y S_aa = 2480, positivo. Por el criterio de las segundas derivadas, (a*, b*) es un mínimo local estricto.
Además, el determinante es 4n por la suma de (x_i − x̄)², que es positivo siempre que los x no sean todos iguales. Como H es constante y definida positiva
—sus autovalores, 6.7 y 2503, son positivos— S es convexa, así que el mínimo es global y único. Brayan nos muestra cómo se ve esto geométricamente."*

---

### 🟧 BRAYAN GUERRERO (diapositivas 9–12)

**Diap. 9 — Superficie**
*"Si graficamos z = S(a,b) obtenemos un paraboloide elíptico abierto hacia arriba, con un único punto más bajo: el (a*, b*), marcado en rosa.
Tiene forma de valle alargado y estrecho, lo que significa que a y b están muy correlacionados: puedo subir a y compensarlo bajando b sin aumentar mucho el error.
El número de condición del Hessiano, de unos 373, lo confirma."*

**Diap. 10 — Curvas de nivel, trazas y secciones**
*"Las curvas de nivel unen los pares (a,b) con el mismo error; son elipses concéntricas alrededor del mínimo, inclinadas por el término cruzado S_ab = 2Σx.
Las trazas son cortes de la superficie con planos b = constante o a = constante: todas son parábolas, con la misma curvatura, y solo cambian de altura y
de posición del vértice. Las secciones nos muestran que fijar un parámetro mal elegido deja un error mayor. En la app hay además una animación del descenso por gradiente
que baja zigzagueando por el valle hasta el mínimo."*

**Diap. 11 — Verificación computacional**
*"Programamos el ajuste desde cero con las fórmulas normales, sin usar funciones de regresión, y luego lo comparamos con numpy.polyfit y scipy.stats.linregress.
Los tres dan los mismos valores: a* = 2.68038, b* = −0.170079, S_mín = 1.66102. Las diferencias máximas son del orden de 10⁻¹⁶: error de redondeo de punto flotante.
También verificamos el Hessiano con diferencias finitas y que el gradiente en el óptimo es prácticamente cero."*

**Diap. 12 — Analítico vs. código vs. biblioteca**
*"Esta es la tabla de la sección 9 del enunciado. La columna analítica es el resultado que Juan obtuvo a mano; si difiere en las últimas cifras es por redondeo en las cuentas manuales.
Lo importante es que los tres métodos resuelven el mismo problema y coinciden. Mario nos cuenta qué tan buena es la recta."*

---

### 🟥 MARIO ZAMBRANO (diapositivas 13–17)

**Diap. 13 — Residuos**
*"Los residuos son la distancia vertical de cada dato a la recta. Están centrados en cero —lo garantiza el método— y no muestran patrón curvo ni tendencia sistemática,
así que el modelo lineal es compatible con los datos. Observamos que la dispersión crece con n: los errores son mayores donde el tiempo es mayor,
algo lógico porque el ruido del sistema es proporcional a lo que dura la operación. Solo dos puntos rozan el límite de atípico y de forma marginal."*

**Diap. 14 — Calidad**
*"El RMSE es de 0.33 milisegundos: la recta se equivoca en promedio ese valor, alrededor del 1.2 % del tiempo medio, un error pequeño para estimar cuánto tarda
una búsqueda. El R² es 0.9992: la recta explica el 99.92 % de la variación. Pero ojo: ese valor es alto porque T depende casi solo de n y el rango es amplio;
no basta para afirmar que el modelo es lineal, por eso revisamos los residuos."*

**Diap. 15 — Análisis adicional (B y C)**
*"Hicimos la opción B: eliminamos el punto de mayor influencia, el último, y la pendiente cambia solo 0.85 %: la recta es estable. Y la opción C: comparamos con una parábola.
El coeficiente cuadrático es casi cero, el valor-p es 0.83, o sea no significativo, y aporta menos del 1 % del tiempo; el R² ajustado ni siquiera mejora.
Conclusión: el modelo lineal, coherente con una complejidad O(n), es suficiente."*

**Diap. 16 — Conclusiones**
*"Respondiendo la pregunta central: el gradiente igual a cero nos da el sistema normal y las fórmulas exactas de a* y b*; el Hessiano, con determinante y S_aa positivos,
demuestra que es un mínimo, global por la convexidad; la geometría muestra un valle cuyo fondo es el mejor ajuste; y el computador confirmó todo. Nuestro modelo final es
T ≈ 2.68·(n/10⁵) − 0.17 ms, con RMSE de 0.33 ms."* [Opcional: abrir la app y mostrar 1 minuto la superficie y la animación.]

**Diap. 17 — Gracias**
*"Muchas gracias. Quedamos atentos a sus preguntas."*

---

## PARTE 4 · PREGUNTAS POSIBLES (con respuesta sugerida)

### A. Sobre el problema y los datos
1. **¿Por qué eligieron la búsqueda lineal?** Porque es un problema real, fácil de medir en el computador y con una relación teórica lineal (O(n)) que podemos contrastar con los datos.
2. **¿Por qué el peor caso (elemento ausente)?** Para que siempre haga las n comparaciones y el tiempo dependa solo de n, sin que influya la posición del elemento.
3. **¿Por qué mediana y no promedio?** La mediana resiste los picos aislados de ruido (por ejemplo, cuando el sistema operativo interrumpe el programa).
4. **¿Para qué los calentamientos?** La primera ejecución puede ser más lenta (caché fría, asignación de memoria); se descartan para medir en condiciones estables.
5. **¿Los datos son reales o simulados?** Reales, medidos con `perf_counter_ns`; nunca se simulan ni editan. Están en `datos.csv` con su `metadata.json`.
6. **¿Por qué los puntos no están exactamente en la recta?** Por el ruido del sistema real: planificador del SO, caché de la CPU, recolector de basura, otros procesos y frecuencia del procesador.
7. **¿Qué significa b\* negativo (−0.17 ms)?** Un tiempo no puede ser negativo, pero b es una **extrapolación** a n = 0, donde nunca medimos. Es muy pequeño (≈ 0.4 % del tiempo máximo) y está dentro del ruido; en la práctica el costo fijo es despreciable.
8. **¿Por qué escalar x a 10⁵?** Para evitar números enormes en Σx² (~10¹³) y en el Hessiano; los resultados (S_mín, RMSE, R²) no cambian; a se convierte con a_orig = a'/10⁵.
9. **¿Cuántos ns por elemento?** a* = 2.68 ms por 10⁵ elementos = 26.8 ns por elemento (en este equipo y con Python).
10. **Si lo corren en otro computador, ¿saldría igual?** No exactamente: cambia la pendiente (cada máquina tiene su velocidad) pero seguiría siendo lineal.

### B. Sobre la matemática (las más probables)
11. **¿Por qué se elevan los errores al cuadrado?** Para que no se cancelen positivos con negativos, para que S sea derivable en todo punto (el valor absoluto no lo es en 0) y porque da un problema con solución cerrada y mínimo único.
12. **¿Qué es el gradiente y qué significa que sea cero?** Es el vector de derivadas parciales; apunta a la dirección de mayor crecimiento. Si es cero, no hay dirección de ascenso/descenso inmediato: es un **punto crítico** (candidato a extremo).
13. **¿Cómo derivaron S?** Regla de la cadena: d/da (y − ax − b)² = 2(y − ax − b)·(−x); se suma sobre i.
14. **¿Cómo se pasa del gradiente cero al sistema normal?** Se iguala a cero cada derivada, se divide entre −2 y se distribuye: a·Σx² + b·Σx = Σxy y a·Σx + n·b = Σy.
15. **¿Cómo resolvieron el sistema?** Por Cramer o eliminando b: del segundo, b = (Σy − aΣx)/n; se sustituye en el primero y se despeja a.
16. **¿Qué es el Hessiano y cómo se usa?** Matriz de segundas derivadas. Con det H > 0 y S_aa > 0 el punto crítico es un **mínimo local estricto**; con det < 0 sería silla; con det > 0 y S_aa < 0, máximo.
17. **¿Por qué det H > 0?** det H = 4[nΣx² − (Σx)²] = 4n·Σ(x_i − x̄)², una suma de cuadrados: es positiva a menos que todos los x sean iguales.
18. **¿Cómo saben que el mínimo es global y no solo local?** H es constante y definida positiva en todo ℝ² → S es **convexa** → todo mínimo local es global, y además es único.
19. **¿Qué pasaría si todos los x fueran iguales?** det H = 0, el sistema es singular y no existe una recta única (los datos estarían en una línea vertical). La app lo valida con un mensaje.
20. **¿Qué son los autovalores del Hessiano?** Miden la curvatura en las direcciones principales. Ambos positivos (6.7 y 2503) ⇒ definida positiva. Su cociente (≈ 373) es el número de condición: valle muy alargado.
21. **¿Por qué las curvas de nivel son elipses inclinadas?** Porque S es una cuadrática; la inclinación viene del término cruzado S_ab = 2Σx ≠ 0.
22. **¿Qué son las trazas?** Intersección de la superficie con un plano a = constante o b = constante; son parábolas.
23. **¿Qué es la sección transversal que mostraron?** Lo mismo con un valor fijado por slider; su mínimo coincide con S_mín solo si el valor fijado es el óptimo.
24. **¿El descenso por gradiente reemplaza el cálculo?** No. Las fórmulas normales resuelven ∇S = 0 de una sola vez; la animación solo muestra por qué el mínimo es único y cómo se llega.
25. **¿Por qué S_mín se puede escribir como Σy² − a*Σxy − b*Σy?** Porque en el óptimo Σe_i = 0 y Σx_i·e_i = 0, entonces S = Σe_i·y_i.
26. **¿Cuántos grados de libertad/por qué n − 2?** Se estiman 2 parámetros (a y b). Se usa en la varianza residual s² = S_mín/(n − 2).

### C. Sobre el código y la verificación
27. **¿Qué programaron "desde cero"?** `core/regresion.py`: sumatorias, a*, b*, S, gradiente, Hessiano, autovalores y criterio, sin funciones de regresión de bibliotecas.
28. **¿Con qué lo compararon?** Con `numpy.polyfit` y `scipy.stats.linregress`; coinciden hasta ~10⁻¹⁶ (verificado también con tests de 1e-9).
29. **¿Por qué hay diferencias de 10⁻¹⁶ si es el mismo problema?** Redondeo de punto flotante (float64): los métodos suman en distinto orden/algoritmo.
30. **¿Cómo verificaron el Hessiano numéricamente?** Con diferencias finitas centrales de S; como S es cuadrática, el resultado coincide con el analítico salvo redondeo. Además ∇S(a*, b*) ≈ 0.
31. **¿Qué pruebas automáticas tiene?** 19 tests con pytest: ajuste propio = polyfit = linregress, H definida positiva, gradiente ≈ 0 en el óptimo, datos con ≥ 10 filas y x no constante, el descenso por gradiente converge, etc.
32. **¿Y si el valor manual y el del código no coinciden?** Suele ser redondeo de sumas hechas a mano, o unidades distintas (escala de x). Si la diferencia es grande, hay un error algebraico.

### D. Sobre residuos y calidad
33. **¿Qué es un residuo?** e_i = y_i − (a*x_i + b*): la distancia vertical entre el dato y la recta.
34. **¿Por qué la media de los residuos es cero?** Porque ∂S/∂b = 0 implica Σe_i = 0 (cuando el modelo incluye intercepto). Es una propiedad del método, no una prueba de buen ajuste.
35. **¿Cómo reconocen una desviación sistemática?** Si los residuos tienen patrón: negativos en una región y positivos en otra, o forma curva. Aquí no aparece (correlación con la curvatura −0.06).
36. **¿Qué significa que la dispersión crezca con x?** Los errores absolutos son mayores cuando el tiempo es mayor: ruido proporcional a la duración (heterocedasticidad). No invalida el modelo, pero es una limitación.
37. **¿Qué es el RMSE y qué dice aquí?** √(Σe²/n) = 0.333 ms: error típico de predicción, ~1.2 % del tiempo medio.
38. **¿Qué dice R² = 0.9992?** Que la recta explica el 99.92 % de la variabilidad de T. Pero un R² alto no prueba linealidad; hay que mirar residuos y el propósito del modelo.
39. **¿Hay atípicos?** Dos puntos rozan el límite |t| > 2 (2.04 y 2.21), muy marginales; no hay errores graves.
40. **¿Cuáles son las limitaciones del modelo?** Solo vale en el rango medido (100 000–1 500 000); la dispersión no es constante; depende del equipo; b\* se extrapola a n = 0 y no es fiable; con memoria muy grande aparecerían efectos de caché que curvarían la relación.

### E. Sobre el análisis adicional
41. **¿Qué es la distancia de Cook?** Mide cuánto cambian los parámetros al quitar un punto, combinando apalancamiento y tamaño del residuo. Referencia: 4/n.
42. **¿Qué punto es el más influyente y por qué?** El n.º 15 (el de mayor n): está en el extremo del rango (alto apalancamiento) y tiene residuo grande. Aun así a* cambia solo 0.85 %.
43. **¿Qué es el apalancamiento (leverage)?** Cuánto pesa la posición de x_i en el ajuste; los extremos pesan más.
44. **¿Por qué comparar con un modelo cuadrático?** Para ver si el modelo más complejo representa los datos de forma significativamente distinta. Si O(n) es correcto, el término x² debería ser ≈ 0.
45. **¿Por qué un modelo con más parámetros siempre reduce S?** Porque incluye al lineal como caso particular; por eso se usa la prueba F y el R² ajustado. Aquí p = 0.83 → la mejora no es significativa.
46. **¿Qué mostraría la sensibilidad (opción A)?** Perturbando los datos ±1 %, a* varía una fracción pequeña; el modelo es poco sensible porque el ruido se promedia sobre 15 puntos.

### F. Preguntas "trampa" o de comprensión
47. **¿Podrían usar |e| en lugar de e²?** Sí (regresión LAD), pero no es derivable en 0, no hay fórmula cerrada y el mínimo puede no ser único.
48. **¿La recta de mínimos cuadrados pasa por (x̄, ȳ)?** Sí: de ∂S/∂b = 0, ȳ = a*·x̄ + b*.
49. **¿Cambia a* si cambian las unidades de x?** Sí (a se escala), pero la recta predice lo mismo; S_mín, RMSE y R² no cambian.
50. **¿Por qué el Hessiano no depende de a ni b?** Porque S es cuadrática en (a, b); sus segundas derivadas son constantes.
51. **¿El computador hizo el trabajo?** No: el desarrollo analítico se hizo a mano en papel; el computador lo verifica, visualiza y permite analizar a fondo.
52. **¿Qué mejorarían?** Más tamaños de n, más repeticiones, otros algoritmos (O(n²) para probar el modelo cuadrático) y comparar equipos.

---

## PARTE 5 · CONSEJOS DE DEFENSA

- **Todos** deben poder explicar: qué es S, cómo salen el gradiente y el sistema normal, y por qué el Hessiano dice "mínimo".
- **Juan** lleva la hoja con el desarrollo manual (derivadas, sistema, solución, Hessiano); **escriban en la app** los valores manuales en la página *Comparación*.
- **No lean las diapositivas**: usen el guion como guía y mírense entre ustedes al pasar la palabra.
- **Honestidad:** si no saben algo, digan *"no lo hemos profundizado, pero entendemos que…"*; no inventen.
- **Evitar:** decir que "el computador calculó todo", que "R² alto prueba linealidad" o que "b* negativo es un error".
- **Antes de entrar:** abrir la app (`streamlit run app.py`), tener la presentación en pantalla completa, comprobar que la página *Datos* **no** muestre el aviso "DATOS DE PRUEBA" (los datos actuales son los reales) y cargar la hoja manual.
- **Plan B:** si falla la app, las diapositivas tienen todas las gráficas importantes.
