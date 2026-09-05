"""Pruebas de los simuladores de AFN y AFD."""

from __future__ import annotations

import pytest

from conftest import nfa_of
from regex_automata.algorithms.subset_construction import build_dfa
from regex_automata.constants import EPSILON
from regex_automata.simulation.dfa_simulator import simulate_dfa
from regex_automata.simulation.nfa_simulator import epsilon_closure, move, simulate_nfa


def test_la_cerradura_incluye_al_conjunto_de_partida() -> None:
    afn = nfa_of("a")
    assert afn.start in epsilon_closure(afn, {afn.start})


def test_la_cerradura_sigue_cadenas_de_epsilon() -> None:
    afn = nfa_of("(a|b)*")
    cerradura = epsilon_closure(afn, {afn.start})
    assert len(cerradura) > 1


def test_mover_no_aplica_cerradura() -> None:
    afn = nfa_of("a")
    destinos = move(afn, {afn.start}, "a")
    assert destinos == afn.destinations(afn.start, "a")


def test_mover_con_simbolo_desconocido_da_vacio() -> None:
    afn = nfa_of("a")
    assert move(afn, {afn.start}, "z") == frozenset()


def test_epsilon_no_se_consume_como_simbolo() -> None:
    afn = nfa_of("(a|~)")
    assert move(afn, {afn.start}, EPSILON) != frozenset()
    assert simulate_nfa(afn, "~").accepted is False


def test_la_traza_del_afn_registra_cada_simbolo() -> None:
    resultado = simulate_nfa(nfa_of("abc"), "abc")
    assert len(resultado.trace) == 3
    assert [paso.symbol for paso in resultado.trace] == ["a", "b", "c"]


def test_la_traza_del_afd_registra_estados() -> None:
    afd = build_dfa(nfa_of("abc")).dfa
    resultado = simulate_dfa(afd, "abc")
    assert resultado.initial == afd.start.label
    assert resultado.trace[0].source == afd.start.label


def test_respuesta_en_espanol() -> None:
    assert simulate_nfa(nfa_of("a"), "a").answer == "si"
    assert simulate_nfa(nfa_of("a"), "b").answer == "no"


def test_cadena_vacia_en_afn_y_afd() -> None:
    afn = nfa_of("a*")
    afd = build_dfa(afn).dfa
    assert simulate_nfa(afn, "").accepted is True
    assert simulate_dfa(afd, "").accepted is True
    assert simulate_nfa(afn, "").trace == ()


def test_el_afd_se_detiene_en_el_primer_simbolo_invalido() -> None:
    afd = build_dfa(nfa_of("ab")).dfa
    resultado = simulate_dfa(afd, "az")
    assert resultado.accepted is False
    assert resultado.rejected_symbol == "z"
    assert len(resultado.trace) == 1


def test_el_afn_registra_el_simbolo_que_provoco_el_rechazo() -> None:
    resultado = simulate_nfa(nfa_of("ab"), "ax")
    assert resultado.accepted is False
    assert resultado.rejected_symbol == "x"


@pytest.mark.parametrize(
    ("expresion", "cadena", "esperado"),
    [
        ("(a|b)*abb(a|b)*", "babbaaaa", True),
        ("(a|b)*abb(a|b)*", "abb", True),
        ("(a|b)*abb(a|b)*", "ab", False),
        ("(a|b)*abb(a|b)*", "", False),
    ],
)
def test_afn_y_afd_coinciden(expresion: str, cadena: str, esperado: bool) -> None:
    afn = nfa_of(expresion)
    afd = build_dfa(afn).dfa
    assert simulate_nfa(afn, cadena).accepted is esperado
    assert simulate_dfa(afd, cadena).accepted is esperado


def test_formato_de_traza_legible() -> None:
    afd = build_dfa(nfa_of("ab")).dfa
    texto = simulate_dfa(afd, "ab").format_trace()
    assert "-->" in texto
