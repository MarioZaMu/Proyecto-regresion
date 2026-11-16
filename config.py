"""Configuración editable del proyecto (portada e identificación)."""

CURSO = "Cálculo Multivariable"
UNIVERSIDAD = "Universidad Cooperativa de Colombia (UCC)"
ESTUDIANTES = [
    "Nicoll Valentina López Andrade",
    "Juan David Jurado Paz",
    "Brayan Steven Guerrero Acosta",
    "Mario Alberto Zambrano Muñoz",
]
ESTUDIANTE = " · ".join(ESTUDIANTES)  # texto en una línea (encabezados, PDF, Markdown)
PERIODO = "2026-B"
TITULO_PROYECTO = "Regresión lineal y optimización con funciones de varias variables"
TITULO_CORTO = "Regresión lineal · Cálculo Multivariable"

# Paleta sobria (3-4 colores) coherente en toda la interfaz
COLOR_PRIMARIO = "#4F46E5"   # indigo vivo: datos / recta óptima
COLOR_SECUNDARIO = "#F97316"  # naranja vivo: recta alternativa / comparación
COLOR_ACENTO = "#EC4899"     # magenta: mínimo / atípicos
COLOR_NEUTRO = "#64748B"     # auxiliares
COLOR_CIAN = "#06B6D4"       # degradados y resaltes

# Cifras significativas para mostrar resultados
CIFRAS = 6
