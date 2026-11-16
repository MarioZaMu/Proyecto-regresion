"""Pruebas del núcleo matemático."""
import numpy as np
import pytest
from scipy import stats

from core import datos, extras, metricas, regresion, verificacion

TOL = 1e-9


@pytest.fixture(scope="module")
def xy():
    df = datos.cargar_csv()
    return df["x"].to_numpy(), df["y"].to_numpy()


@pytest.fixture(scope="module", params=[False, True], ids=["x_original", "x_escalado"])
def xy_ambas(request, xy):
    x, y = xy
    return datos.escalar(x, request.param), y


def test_ajuste_propio_igual_polyfit_y_linregress(xy_ambas):
    x, y = xy_ambas
    f = regresion.ajustar(x, y)
    a_np, b_np = np.polyfit(x, y, 1)
    r = stats.linregress(x, y)
    assert f.a == pytest.approx(a_np, rel=TOL, abs=TOL)
    assert f.b == pytest.approx(b_np, rel=TOL, abs=TOL)
    assert f.a == pytest.approx(r.slope, rel=TOL, abs=TOL)
    assert f.b == pytest.approx(r.intercept, rel=TOL, abs=TOL)


def test_hessiano_definida_positiva(xy_ambas):
    x, y = xy_ambas
    c = regresion.clasificar(x)
    assert c.det > 0 and c.s_aa > 0
    assert all(l > 0 for l in c.autovalores)
    assert np.all(np.linalg.eigvalsh(c.hessiano) > 0)
    assert "mínimo" in c.tipo


def test_gradiente_cero_en_optimo(xy_ambas):
    x, y = xy_ambas
    f = regresion.ajustar(x, y)
    g = regresion.gradiente(f.a, f.b, x, y)
    escala = np.array([np.sum(np.abs(x * y)), np.sum(np.abs(y))])
    assert np.all(np.abs(g) <= 1e-9 * escala)


def test_s_minimo_es_minimo(xy_ambas):
    x, y = xy_ambas
    f = regresion.ajustar(x, y)
    rng = np.random.default_rng(1)
    for _ in range(50):
        da, db = rng.normal(size=2) * [abs(f.a) * 0.05, np.std(y) * 0.05]
        assert regresion.error_cuadratico(f.a + da, f.b + db, x, y) >= f.s_min


def test_hessiano_numerico_coincide(xy_ambas):
    x, y = xy_ambas
    f = regresion.ajustar(x, y)
    ha, hb = regresion.pasos_por_defecto(x, y)
    hn = regresion.hessiano_numerico(x, y, f.a, f.b, ha, hb)
    np.testing.assert_allclose(hn, regresion.hessiano(x), rtol=1e-4)


def test_datos_csv_valido():
    df = datos.cargar_csv()
    assert len(df) >= 10
    assert df["x"].nunique() > 1


def test_validacion_mensajes():
    assert regresion.validar([1, 2], [1, 2])
    assert regresion.validar([3, 3, 3], [1, 2, 3])
    assert not regresion.validar([1, 2, 3], [2, 4, 6])
    with pytest.raises(ValueError):
        regresion.ajustar([1, 1, 1], [1, 2, 3])


def test_recta_exacta():
    x = np.arange(1, 8, dtype=float)
    f = regresion.ajustar(x, 3 * x + 2)
    assert f.a == pytest.approx(3) and f.b == pytest.approx(2) and f.s_min == pytest.approx(0, abs=1e-18)


def test_comparacion_y_diferencias(xy):
    x, y = xy
    r = verificacion.comparar(datos.escalar(x, True), y, manual=(1.0, 0.0, 5.0))
    assert set(r["tabla"]["Parámetro"]) == {"a", "b", "S_mín"}
    r2 = verificacion.comparar(datos.escalar(x, True), y)
    assert (r2["tabla"]["Diferencia máxima"] < 1e-8).all()


def test_metricas(xy_ambas):
    x, y = xy_ambas
    f = regresion.ajustar(x, y)
    e = metricas.residuos(f.a, f.b, x, y)
    assert np.mean(e) == pytest.approx(0, abs=1e-8 * np.std(y))
    c = metricas.calidad(f.a, f.b, x, y)
    assert 0 < c.r2 <= 1
    assert c.rmse == pytest.approx(np.sqrt(f.s_min / len(x)))
    t = metricas.tabla_puntos(f.a, f.b, x, y)
    assert t["apalancamiento"].sum() == pytest.approx(2)


def test_extras(xy):
    x, y = datos.escalar(xy[0], True), xy[1]
    i = extras.mas_influyente(x, y)
    assert 0 <= i < len(x)
    r = extras.sin_punto(x, y, i)
    assert len(r["x"]) == len(x) - 1
    q = extras.ajustar_cuadratico(x, y)
    assert q.s <= regresion.ajustar(x, y).s_min + 1e-9
    assert extras.comparar_modelos(x, y).shape[0] == 2
    assert len(extras.sensibilidad(x, y, 1, 50)) == 50


def test_resumen_markdown(xy):
    from interfaz import exportar
    from interfaz.contexto import Ctx

    x, y = datos.escalar(xy[0], True), xy[1]
    aj = regresion.ajustar(x, y)
    ctx = Ctx(datos.cargar_csv(), {"origen": "x"}, True, x, y, xy[0], aj, metricas.calidad(aj.a, aj.b, x, y),
              regresion.clasificar(x), "n", "T", "u", "ms", False)
    md = exportar.resumen_markdown(ctx, (None, None, None), {})
    assert "Hessiano" in md and "Opción B" in md


def test_descenso_gradiente_converge(xy):
    x, y = datos.escalar(xy[0], True), xy[1]
    f = regresion.ajustar(x, y)
    ruta = regresion.descenso_gradiente(x, y, (f.a + 0.5, f.b - 2.0), 200)
    s = [float(regresion.error_cuadratico(a, b, x, y)) for a, b in ruta]
    assert all(s[i + 1] <= s[i] + 1e-12 for i in range(len(s) - 1))
    assert s[-1] - f.s_min < 1e-3 * (s[0] - f.s_min)
