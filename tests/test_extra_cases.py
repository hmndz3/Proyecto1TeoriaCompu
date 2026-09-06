"""Casos adicionales: escapes, anidamiento, estado pozo y errores en archivo."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import prepared_dfa_of
from regex_automata.algorithms.partition_minimizer import minimize_by_partitions
from regex_automata.algorithms.table_filling_minimizer import minimize_by_table_filling
from regex_automata.constants import TRAP_STATE_LABEL
from regex_automata.errors import RegexAutomataError, RegexSyntaxError
from regex_automata.services.expression_processor import analyze_expression, simulate_all
from regex_automata.services.file_processor import read_expressions
from regex_automata.services.output_writer import write_expression_outputs
from regex_automata.visualization.dot_builder import dfa_to_dot, nfa_to_dot
from regex_automata.visualization.graphviz_renderer import (
    RenderResult,
    graphviz_version,
    installation_hint,
    is_graphviz_available,
    render_image,
)


@pytest.mark.parametrize(
    ("expresion", "cadena", "esperado"),
    [
        (r"\*", "*", True),
        (r"\*", "a", False),
        (r"a\|b", "a|b", True),
        (r"a\|b", "ab", False),
        (r"\~", "~", True),
        (r"\~", "", False),
        (r"\(a\)", "(a)", True),
        (r"\\", "\\", True),
        (r"\.", ".", True),
        (r"\+*", "", True),
        (r"\+*", "+++", True),
    ],
)
def test_escapes_producen_simbolos_literales(
    expresion: str, cadena: str, esperado: bool
) -> None:
    paquete = simulate_all(analyze_expression(expresion), cadena)
    assert paquete.consistent
    assert paquete.accepted is esperado


@pytest.mark.parametrize(
    ("expresion", "cadena", "esperado"),
    [
        ("((a|b)*c)+", "abc", True),
        ("((a|b)*c)+", "cc", True),
        ("((a|b)*c)+", "ab", False),
        ("(a(b(c)))", "abc", True),
        ("((((a))))*", "aaa", True),
        ("(a|(b|(c|d)))*", "dcba", True),
        ("(a|(b|(c|d)))*", "e", False),
    ],
)
def test_anidamiento_profundo(expresion: str, cadena: str, esperado: bool) -> None:
    paquete = simulate_all(analyze_expression(expresion), cadena)
    assert paquete.consistent
    assert paquete.accepted is esperado


@pytest.mark.parametrize(
    ("expresion", "cadena"),
    [("a", "z"), ("(a|b)*", "c"), ("abc", "abd")],
)
def test_simbolos_fuera_del_alfabeto_se_rechazan(expresion: str, cadena: str) -> None:
    paquete = simulate_all(analyze_expression(expresion), cadena)
    assert paquete.consistent
    assert paquete.accepted is False


def test_el_estado_pozo_aparece_en_el_afd_preparado() -> None:
    afd = prepared_dfa_of("abb")
    etiquetas = {estado.label for estado in afd.states}
    assert TRAP_STATE_LABEL in etiquetas
    assert afd.is_complete


def test_el_pozo_no_es_de_aceptacion() -> None:
    afd = prepared_dfa_of("abb")
    pozo = next(
        estado for estado in afd.states if estado.label == TRAP_STATE_LABEL
    )
    assert not afd.is_accepting(pozo)


@pytest.mark.parametrize("expresion", ["a", "ab", "(a|b)*", "a*b*", "abb"])
def test_ambos_minimizadores_dan_el_mismo_tamano(expresion: str) -> None:
    afd = prepared_dfa_of(expresion)
    assert (
        minimize_by_partitions(afd).dfa.state_count
        == minimize_by_table_filling(afd).dfa.state_count
    )


def test_el_dot_generado_es_valido() -> None:
    analisis = analyze_expression("(a|b)*abb")
    for fuente in (
        nfa_to_dot(analisis.nfa),
        dfa_to_dot(analisis.subset.dfa),
        dfa_to_dot(analisis.partition.dfa),
        dfa_to_dot(analisis.table_filling.dfa),
    ):
        assert fuente.startswith("digraph")
        assert fuente.rstrip().endswith("}")
        assert "rankdir=LR" in fuente
        assert fuente.count("{") == fuente.count("}")


def test_el_dot_marca_inicial_y_aceptacion() -> None:
    analisis = analyze_expression("a")
    fuente = nfa_to_dot(analisis.nfa)
    assert "__inicio__ ->" in fuente
    assert "doublecircle" in fuente


def test_el_dot_usa_el_glifo_de_epsilon() -> None:
    assert "ε" in nfa_to_dot(analyze_expression("(a|b)*").nfa)


def test_lectura_de_archivo_ignora_comentarios_y_vacias(tmp_path: Path) -> None:
    archivo = tmp_path / "expresiones.txt"
    archivo.write_text(
        "# comentario\n\n(a|b)*\n\n  a.b  \n# otro\n", encoding="utf-8"
    )
    lineas = read_expressions(archivo)
    assert [linea.expression for linea in lineas] == ["(a|b)*", "a.b"]
    assert [linea.line_number for linea in lineas] == [3, 5]


def test_archivo_inexistente_falla() -> None:
    with pytest.raises(RegexAutomataError):
        read_expressions(Path("no_existe_este_archivo.txt"))


def test_archivo_sin_expresiones_falla(tmp_path: Path) -> None:
    archivo = tmp_path / "vacio.txt"
    archivo.write_text("# solo comentarios\n\n", encoding="utf-8")
    with pytest.raises(RegexAutomataError):
        read_expressions(archivo)


def test_una_linea_invalida_no_detiene_a_las_demas(tmp_path: Path) -> None:
    archivo = tmp_path / "mixto.txt"
    archivo.write_text("a|b\n((a\nab\n", encoding="utf-8")
    lineas = read_expressions(archivo)

    procesadas, fallidas = 0, 0
    for linea in lineas:
        try:
            analyze_expression(linea.expression, line_number=linea.line_number)
        except RegexSyntaxError:
            fallidas += 1
        else:
            procesadas += 1

    assert procesadas == 2
    assert fallidas == 1


def test_se_escriben_las_salidas_esperadas(tmp_path: Path) -> None:
    analisis = analyze_expression("(a|b)*abb")
    paquete = simulate_all(analisis, "abb")
    reporte = write_expression_outputs(
        analisis, [paquete], tmp_path, 1, generate_images=False
    )

    assert reporte.directory.name == "expresion_001"
    assert reporte.summary_file.exists()
    nombres = {ruta.name for ruta in reporte.dot_files}
    assert nombres == {
        "afn.dot",
        "afd.dot",
        "afd_min_particiones.dot",
        "afd_min_pares.dot",
    }
    for ruta in reporte.dot_files:
        assert ruta.exists()

    resumen = reporte.summary_file.read_text(encoding="utf-8")
    assert "EXPRESION REGULAR: (a|b)*abb" in resumen
    assert "Notacion postfix" in resumen
    assert "P0 =" in resumen
    assert "Pares marcados inicialmente" in resumen
    assert "EQUIVALENTES" in resumen


def test_los_archivos_de_texto_usan_saltos_de_linea_unix(tmp_path: Path) -> None:
    """Los archivos deben ser identicos en Windows y en Linux."""
    analisis = analyze_expression("a|b")
    reporte = write_expression_outputs(
        analisis, [simulate_all(analisis, "a")], tmp_path, 1, generate_images=False
    )
    assert b"\r\n" not in reporte.summary_file.read_bytes()
    for ruta in reporte.dot_files:
        assert b"\r\n" not in ruta.read_bytes()


@pytest.mark.skipif(
    not is_graphviz_available(), reason="Graphviz no esta instalado en este equipo"
)
def test_con_graphviz_solo_quedan_las_imagenes(tmp_path: Path) -> None:
    """Los .dot son un paso intermedio: no deben quedar en la carpeta."""
    analisis = analyze_expression("(a|b)*abb")
    reporte = write_expression_outputs(
        analisis, [simulate_all(analisis, "abb")], tmp_path, 1
    )

    assert len(reporte.image_files) == 4
    assert reporte.svg_files == ()
    assert reporte.dot_files == ()
    assert reporte.render_errors == ()

    encontrados = sorted(ruta.name for ruta in reporte.directory.iterdir())
    assert encontrados == [
        "afd.png",
        "afd_min_pares.png",
        "afd_min_particiones.png",
        "afn.png",
        "resumen.txt",
    ]
    for imagen in reporte.image_files:
        assert imagen.stat().st_size > 0


@pytest.mark.skipif(
    not is_graphviz_available(), reason="Graphviz no esta instalado en este equipo"
)
def test_keep_dot_conserva_los_dot_junto_a_las_imagenes(tmp_path: Path) -> None:
    analisis = analyze_expression("(a|b)*abb")
    reporte = write_expression_outputs(
        analisis, [simulate_all(analisis, "abb")], tmp_path, 1, keep_dot=True
    )
    assert len(reporte.image_files) == 4
    assert len(reporte.dot_files) == 4
    assert len(list(reporte.directory.iterdir())) == 9


def test_sin_graphviz_se_cae_al_svg_propio(tmp_path: Path, monkeypatch) -> None:
    """Sin Graphviz no se pierde la imagen: se dibuja en SVG."""
    monkeypatch.setattr(
        "regex_automata.services.output_writer.render_image",
        lambda *a, **k: RenderResult(
            False, "el comando 'dot' de Graphviz no esta en el PATH"
        ),
    )
    analisis = analyze_expression("a|b")
    reporte = write_expression_outputs(
        analisis, [simulate_all(analisis, "a")], tmp_path, 1
    )
    assert reporte.image_files == ()
    assert len(reporte.svg_files) == 4
    assert reporte.dot_files == ()
    assert reporte.images_generated is True
    assert reporte.render_errors == ("el comando 'dot' de Graphviz no esta en el PATH",)
    for svg in reporte.svg_files:
        assert svg.read_text(encoding="utf-8").startswith("<svg")


def test_una_corrida_nueva_limpia_la_anterior(tmp_path: Path, monkeypatch) -> None:
    """Los archivos de una corrida previa no deben quedar sueltos."""
    carpeta = tmp_path / "expresion_001"
    carpeta.mkdir()
    for viejo in ("afn.dot", "afd.dot", "afn.svg", "afd_min_pares.svg"):
        (carpeta / viejo).write_text("basura", encoding="utf-8")
    ajeno = carpeta / "notas_del_usuario.txt"
    ajeno.write_text("no tocar", encoding="utf-8")

    analisis = analyze_expression("a|b")
    write_expression_outputs(analisis, [simulate_all(analisis, "a")], tmp_path, 1)

    assert not (carpeta / "afn.dot").exists()
    assert not (carpeta / "afd.dot").exists()
    # Los archivos que no genera el programa se respetan.
    assert ajeno.read_text(encoding="utf-8") == "no tocar"


def test_un_error_de_dot_se_reporta_con_su_detalle(tmp_path: Path) -> None:
    """Un DOT invalido debe explicar el fallo, no fallar en silencio."""
    if not is_graphviz_available():
        pytest.skip("Graphviz no esta instalado en este equipo")
    resultado = render_image("esto no es DOT valido {{{", tmp_path / "x.png")
    assert resultado.ok is False
    assert resultado.error is not None
    assert "dot" in resultado.error


def test_el_aviso_de_instalacion_menciona_los_tres_sistemas() -> None:
    texto = installation_hint()
    assert "winget install graphviz" in texto
    assert "brew install graphviz" in texto
    assert "apt install graphviz" in texto
    assert "dot -V" in texto


def test_la_version_de_graphviz_es_coherente_con_su_disponibilidad() -> None:
    if is_graphviz_available():
        assert graphviz_version() is not None
    else:
        assert graphviz_version() is None
