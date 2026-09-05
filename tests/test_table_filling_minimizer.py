"""Pruebas de la minimizacion por tabla de pares distinguibles."""

from __future__ import annotations

import pytest

from conftest import prepared_dfa_of
from regex_automata.algorithms.equivalence import check_equivalence
from regex_automata.algorithms.partition_minimizer import minimize_by_partitions
from regex_automata.algorithms.table_filling_minimizer import minimize_by_table_filling
from regex_automata.simulation.dfa_simulator import simulate_dfa

EXPRESIONES = [
    "(b|b)*abb(a|b)*",
    "(a|b)*abb(a|b)*",
    "a*",
    "a+",
    "a?",
    "~",
    "(a|~)b*",
    "a?b?c?",
    "(a|b)*a(a|b)(a|b)",
    "(a*|b*)+",
]


def test_marcado_inicial_solo_por_aceptacion() -> None:
    afd = prepared_dfa_of("(a|b)*abb(a|b)*")
    resultado = minimize_by_table_filling(afd)
    etiquetas_aceptacion = {estado.label for estado in afd.accepting}
    for marca in resultado.initial_marks:
        assert (marca.first in etiquetas_aceptacion) != (
            marca.second in etiquetas_aceptacion
        )
        assert marca.symbol is None


def test_las_marcas_propagadas_registran_el_simbolo() -> None:
    resultado = minimize_by_table_filling(prepared_dfa_of("(a|b)*abb(a|b)*"))
    propagadas = [marca for marca in resultado.marks if marca.iteration > 0]
    assert propagadas
    for marca in propagadas:
        assert marca.symbol is not None
        assert marca.iteration >= 1


def test_ningun_par_se_marca_dos_veces() -> None:
    resultado = minimize_by_table_filling(prepared_dfa_of("(a|b)*abb(a|b)*"))
    pares = [(marca.first, marca.second) for marca in resultado.marks]
    assert len(pares) == len(set(pares))


def test_pares_equivalentes_y_marcados_son_disjuntos() -> None:
    resultado = minimize_by_table_filling(prepared_dfa_of("(b|b)*abb(a|b)*"))
    marcados = {(marca.first, marca.second) for marca in resultado.marks}
    equivalentes = set(resultado.equivalent_pairs)
    assert marcados & equivalentes == set()


def test_las_clases_cubren_todos_los_estados() -> None:
    afd = prepared_dfa_of("(a|b)*abb")
    resultado = minimize_by_table_filling(afd)
    cubiertos = {estado for clase in resultado.classes for estado in clase}
    assert cubiertos == set(afd.states)


def test_un_afd_ya_minimo_no_deja_pares_equivalentes() -> None:
    resultado = minimize_by_table_filling(prepared_dfa_of("a"))
    assert resultado.equivalent_pairs == ()


@pytest.mark.parametrize("expresion", EXPRESIONES)
def test_coincide_con_la_minimizacion_por_particiones(expresion: str) -> None:
    afd = prepared_dfa_of(expresion)
    por_particiones = minimize_by_partitions(afd).dfa
    por_tabla = minimize_by_table_filling(afd).dfa
    assert por_particiones.state_count == por_tabla.state_count
    assert check_equivalence(por_particiones, por_tabla).equivalent


@pytest.mark.parametrize("expresion", EXPRESIONES)
def test_el_minimo_es_equivalente_al_original(expresion: str) -> None:
    afd = prepared_dfa_of(expresion)
    minimo = minimize_by_table_filling(afd).dfa
    assert check_equivalence(afd, minimo).equivalent


def test_simulacion_sobre_el_minimo() -> None:
    minimo = minimize_by_table_filling(prepared_dfa_of("(b|b)*abb(a|b)*")).dfa
    assert simulate_dfa(minimo, "babbaaaa").accepted is True
    assert simulate_dfa(minimo, "aab").accepted is False
