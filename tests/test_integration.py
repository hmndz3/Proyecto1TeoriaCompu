"""Pruebas de integracion: los cuatro automatas deben coincidir siempre."""

from __future__ import annotations

import pytest

from regex_automata.services.expression_processor import analyze_expression, simulate_all

#: Casos minimos exigidos por la planificacion del proyecto.
CASOS_MINIMOS = [
    ("a", "a", True),
    ("a", "", False),
    ("~", "", True),
    ("a*", "", True),
    ("a+", "", False),
    ("a+", "aaa", True),
    ("a?", "", True),
    ("a?", "a", True),
    ("a?", "aa", False),
    ("a|b", "b", True),
    ("a.b", "ab", True),
    ("ab", "ab", True),
    ("(a|b)*", "abba", True),
    ("(a|b)*abb(a|b)*", "babbaaaa", True),
]

EXPRESIONES = [
    "(b|b)*abb(a|b)*",
    "(a|b)*abb(a|b)*",
    "(a*|b*)+",
    "((a|b)*)?",
    "(a|~)b*",
    "a?b?c?",
    "(a|b)*a(a|b)(a|b)",
    "a.b.c",
    "(ab|ba)*",
]

CADENAS = ["", "a", "b", "ab", "ba", "abb", "babbaaaa", "aabbab", "c", "abc"]


@pytest.mark.parametrize(("expresion", "cadena", "esperado"), CASOS_MINIMOS)
def test_casos_minimos(expresion: str, cadena: str, esperado: bool) -> None:
    analisis = analyze_expression(expresion)
    paquete = simulate_all(analisis, cadena)
    assert paquete.consistent
    assert paquete.accepted is esperado
    assert paquete.answer == ("si" if esperado else "no")


@pytest.mark.parametrize("expresion", EXPRESIONES)
@pytest.mark.parametrize("cadena", CADENAS)
def test_los_cuatro_automatas_coinciden(expresion: str, cadena: str) -> None:
    analisis = analyze_expression(expresion)
    paquete = simulate_all(analisis, cadena)
    resultados = [resultado.accepted for resultado in paquete.results]
    assert len(set(resultados)) == 1, (
        f"desacuerdo en r={expresion!r} w={cadena!r}: {resultados}"
    )


@pytest.mark.parametrize("expresion", EXPRESIONES)
def test_los_dos_minimos_tienen_el_mismo_tamano(expresion: str) -> None:
    analisis = analyze_expression(expresion)
    assert (
        analisis.partition.dfa.state_count == analisis.table_filling.dfa.state_count
    )
    assert analisis.equivalence.equivalent


def test_el_ejemplo_del_enunciado() -> None:
    analisis = analyze_expression("(b|b)*abb(a|b)*")
    assert analisis.normalized_expression == "(b|b)*.a.b.b.(a|b)*"
    assert analisis.postfix_expression == "b b | * a . b . b . a b | * ."
    assert analisis.alphabet == ["a", "b"]
    paquete = simulate_all(analisis, "babbaaaa")
    assert paquete.answer == "si"
    assert paquete.consistent


def test_el_minimo_nunca_tiene_mas_estados_que_el_afd() -> None:
    for expresion in EXPRESIONES:
        analisis = analyze_expression(expresion)
        assert analisis.partition.dfa.state_count <= analisis.prepared.dfa.state_count
