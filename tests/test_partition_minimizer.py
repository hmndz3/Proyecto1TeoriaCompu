"""Pruebas de la minimizacion por refinamiento de particiones."""

from __future__ import annotations

import pytest

from conftest import prepared_dfa_of
from regex_automata.algorithms.equivalence import check_equivalence
from regex_automata.algorithms.partition_minimizer import minimize_by_partitions
from regex_automata.simulation.dfa_simulator import simulate_dfa


def test_particion_inicial_separa_aceptacion() -> None:
    resultado = minimize_by_partitions(prepared_dfa_of("(a|b)*abb(a|b)*"))
    p0 = resultado.history[0]
    assert len(p0) == 2


def test_el_historial_empieza_en_p0_y_es_creciente() -> None:
    resultado = minimize_by_partitions(prepared_dfa_of("(a|b)*abb(a|b)*"))
    tamanos = [len(particion) for particion in resultado.history]
    assert tamanos == sorted(tamanos)
    assert tamanos[0] <= tamanos[-1]


def test_las_clases_cubren_todos_los_estados() -> None:
    afd = prepared_dfa_of("(a|b)*abb")
    resultado = minimize_by_partitions(afd)
    cubiertos = {estado for clase in resultado.classes for estado in clase}
    assert cubiertos == set(afd.states)


def test_no_aumenta_la_cantidad_de_estados() -> None:
    afd = prepared_dfa_of("(a|b)*abb(a|b)*")
    minimo = minimize_by_partitions(afd).dfa
    assert minimo.state_count <= afd.state_count


def test_estados_equivalentes_se_fusionan() -> None:
    # (b|b)* tiene dos ramas identicas que producen estados equivalentes.
    afd = prepared_dfa_of("(b|b)*abb(a|b)*")
    minimo = minimize_by_partitions(afd).dfa
    assert minimo.state_count < afd.state_count


def test_un_afd_ya_minimo_no_cambia_de_tamano() -> None:
    afd = prepared_dfa_of("a")
    minimo = minimize_by_partitions(afd).dfa
    assert minimo.state_count == afd.state_count


def test_el_minimo_es_equivalente_al_original() -> None:
    for expresion in ["(a|b)*abb(a|b)*", "a*", "a+", "(a|~)b*", "a?b?c?"]:
        afd = prepared_dfa_of(expresion)
        minimo = minimize_by_partitions(afd).dfa
        assert check_equivalence(afd, minimo).equivalent


@pytest.mark.parametrize(
    ("expresion", "cadena", "esperado"),
    [
        ("(b|b)*abb(a|b)*", "babbaaaa", True),
        ("(b|b)*abb(a|b)*", "aab", False),
        ("a*", "", True),
        ("a+", "", False),
    ],
)
def test_simulacion_sobre_el_minimo(expresion: str, cadena: str, esperado: bool) -> None:
    minimo = minimize_by_partitions(prepared_dfa_of(expresion)).dfa
    assert simulate_dfa(minimo, cadena).accepted is esperado


def test_el_minimo_es_completo() -> None:
    minimo = minimize_by_partitions(prepared_dfa_of("(a|b)*abb")).dfa
    assert minimo.is_complete
