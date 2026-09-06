"""Pruebas del dibujante de automatas en SVG.

El SVG es el respaldo cuando no hay Graphviz, asi que debe funcionar siempre y
para cualquier automata, por raro que sea.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from conftest import nfa_of, prepared_dfa_of
from regex_automata.algorithms.partition_minimizer import minimize_by_partitions
from regex_automata.algorithms.subset_construction import build_dfa
from regex_automata.services.expression_processor import analyze_expression
from regex_automata.visualization.graph_model import dfa_to_graph, nfa_to_graph
from regex_automata.visualization.svg_renderer import (
    dfa_to_svg,
    graph_to_svg,
    nfa_to_svg,
)

EXPRESIONES = [
    "a",
    "~",
    "a*",
    "a+",
    "a?",
    "a|b",
    "ab",
    "(a|b)*",
    "(b|b)*abb(a|b)*",
    "(a|b)*abb(a|b)*",
    "((~|a)|b*)*",
    "a?b?c?",
    "(a*|b*)+",
    "(a|b)*a(a|b)(a|b)",
    r"\(a\|b\)",
]


@pytest.mark.parametrize("expresion", EXPRESIONES)
def test_el_svg_es_xml_bien_formado(expresion: str) -> None:
    """Un SVG mal formado no lo abre ningun navegador."""
    for fuente in (
        nfa_to_svg(nfa_of(expresion)),
        dfa_to_svg(build_dfa(nfa_of(expresion)).dfa),
        dfa_to_svg(minimize_by_partitions(prepared_dfa_of(expresion)).dfa),
    ):
        raiz = ET.fromstring(fuente)
        assert raiz.tag.endswith("svg")


def test_el_svg_declara_su_espacio_de_nombres_y_tamano() -> None:
    fuente = nfa_to_svg(nfa_of("(a|b)*abb"))
    assert fuente.startswith("<svg")
    assert 'xmlns="http://www.w3.org/2000/svg"' in fuente
    assert "viewBox=" in fuente
    ancho = re.search(r'width="(\d+)"', fuente)
    alto = re.search(r'height="(\d+)"', fuente)
    assert ancho is not None and int(ancho.group(1)) > 0
    assert alto is not None and int(alto.group(1)) > 0


@pytest.mark.parametrize("expresion", EXPRESIONES)
def test_aparecen_todos_los_estados(expresion: str) -> None:
    afd = build_dfa(nfa_of(expresion)).dfa
    fuente = dfa_to_svg(afd)
    for estado in afd.states:
        assert f">{estado.label}<" in fuente


def test_hay_una_elipse_por_estado_y_una_extra_por_aceptacion() -> None:
    afd = build_dfa(nfa_of("(a|b)*abb")).dfa
    fuente = dfa_to_svg(afd)
    esperadas = len(afd.states) + len(afd.accepting)
    assert fuente.count("<ellipse") == esperadas


def test_el_estado_inicial_se_resalta() -> None:
    fuente = dfa_to_svg(build_dfa(nfa_of("(a|b)*")).dfa)
    # Relleno azul claro del estado inicial y el punto de la flecha de entrada.
    assert "#d6ecff" in fuente
    assert "<circle" in fuente


def test_las_transiciones_epsilon_usan_el_glifo() -> None:
    assert "ε" in nfa_to_svg(nfa_of("(a|b)*"))


def test_los_simbolos_compartidos_se_agrupan() -> None:
    minimo = minimize_by_partitions(prepared_dfa_of("(a|b)*")).dfa
    fuente = dfa_to_svg(minimo)
    # El unico estado se queda con un lazo etiquetado 'a,b'.
    assert ">a,b<" in fuente


def test_hay_una_punta_de_flecha_por_transicion_mas_la_de_entrada() -> None:
    grafo = dfa_to_graph(build_dfa(nfa_of("abb")).dfa)
    fuente = graph_to_svg(grafo)
    # Las puntas son <path ... fill="#333333"/>, una por arista mas la inicial.
    puntas = fuente.count('Z" fill="#333333"')
    assert puntas == len(grafo.edges) + 1


def test_el_texto_se_escapa() -> None:
    """Un simbolo como '<' no debe romper el XML."""
    fuente = dfa_to_svg(build_dfa(nfa_of(r"\<|\&")).dfa)
    ET.fromstring(fuente)
    assert "&lt;" in fuente
    assert "&amp;" in fuente


def test_los_lazos_no_se_salen_del_lienzo() -> None:
    """Un estado con lazo necesita margen extra arriba."""
    fuente = dfa_to_svg(build_dfa(nfa_of("(a|b)*")).dfa)
    coordenadas = [float(v) for v in re.findall(r'cy="([-\d.]+)"', fuente)]
    assert coordenadas
    assert min(coordenadas) > 60.0


def test_el_svg_no_depende_de_recursos_externos() -> None:
    """Debe abrirse sin conexion y sin archivos adicionales."""
    fuente = nfa_to_svg(nfa_of("(a|b)*abb"))
    assert "http://" not in fuente.replace("http://www.w3.org/2000/svg", "")
    assert "<image" not in fuente
    assert "<script" not in fuente


def test_dot_y_svg_dibujan_el_mismo_grafo() -> None:
    """Ambos generadores parten del mismo modelo intermedio."""
    analisis = analyze_expression("(b|b)*abb(a|b)*")
    grafo_afn = nfa_to_graph(analisis.nfa)
    grafo_afd = dfa_to_graph(analisis.subset.dfa)
    assert len(grafo_afn.nodes) == analisis.nfa.state_count
    assert len(grafo_afd.nodes) == analisis.subset.dfa.state_count
    assert grafo_afd.start == analisis.subset.dfa.start.label


def test_un_automata_de_un_solo_estado_se_dibuja() -> None:
    minimo = minimize_by_partitions(prepared_dfa_of("(a|b)*")).dfa
    assert minimo.state_count == 1
    fuente = dfa_to_svg(minimo)
    ET.fromstring(fuente)
    assert fuente.count("<ellipse") == 2  # estado unico, ademas de aceptacion
