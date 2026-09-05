"""Pruebas de la construccion de subconjuntos y de la preparacion del AFD."""

from __future__ import annotations

import pytest

from conftest import nfa_of
from regex_automata.algorithms.dfa_preparation import prepare_for_minimization
from regex_automata.algorithms.labels import state_label
from regex_automata.algorithms.subset_construction import build_dfa
from regex_automata.models.dfa import DFA, DFAState
from regex_automata.simulation.dfa_simulator import simulate_dfa
from regex_automata.simulation.nfa_simulator import epsilon_closure


def test_el_inicial_es_la_cerradura_del_inicial_del_afn() -> None:
    afn = nfa_of("(a|b)*")
    resultado = build_dfa(afn)
    esperado = epsilon_closure(afn, {afn.start})
    assert resultado.subsets[resultado.dfa.start] == esperado


def test_estado_compuesto_acepta_si_contiene_un_final_del_afn() -> None:
    afn = nfa_of("a*")
    resultado = build_dfa(afn)
    for estado in resultado.dfa.states:
        contiene_final = bool(resultado.subsets[estado] & afn.accepting)
        assert resultado.dfa.is_accepting(estado) is contiene_final


def test_el_afd_es_determinista() -> None:
    resultado = build_dfa(nfa_of("(a|b)*abb"))
    claves = list(resultado.dfa.transitions)
    assert len(claves) == len(set(claves))


def test_no_hay_subconjuntos_repetidos() -> None:
    resultado = build_dfa(nfa_of("(a|b)*abb(a|b)*"))
    subconjuntos = list(resultado.subsets.values())
    assert len(subconjuntos) == len(set(subconjuntos))


@pytest.mark.parametrize(
    ("expresion", "cadena", "esperado"),
    [
        ("(a|b)*abb(a|b)*", "babbaaaa", True),
        ("(a|b)*abb(a|b)*", "aba", False),
        ("a*", "", True),
        ("a+", "", False),
        ("~", "", True),
    ],
)
def test_el_afd_acepta_lo_mismo_que_el_afn(
    expresion: str, cadena: str, esperado: bool
) -> None:
    afd = build_dfa(nfa_of(expresion)).dfa
    assert simulate_dfa(afd, cadena).accepted is esperado


def test_simbolo_fuera_del_alfabeto_se_rechaza() -> None:
    afd = build_dfa(nfa_of("a*")).dfa
    resultado = simulate_dfa(afd, "z")
    assert resultado.accepted is False
    assert resultado.rejected_symbol == "z"


@pytest.mark.parametrize(
    ("indice", "etiqueta"), [(0, "A"), (1, "B"), (25, "Z"), (26, "AA"), (27, "AB")]
)
def test_etiquetas_de_estado(indice: int, etiqueta: str) -> None:
    assert state_label(indice) == etiqueta


def test_la_preparacion_completa_el_afd() -> None:
    afd = build_dfa(nfa_of("abb")).dfa
    preparado = prepare_for_minimization(afd)
    assert preparado.dfa.is_complete
    assert preparado.trap_added is True


def test_la_preparacion_elimina_inaccesibles() -> None:
    a = DFAState(0, "A")
    b = DFAState(1, "B")
    huerfano = DFAState(2, "C")
    afd = DFA(
        states=frozenset({a, b, huerfano}),
        alphabet=frozenset({"x"}),
        start=a,
        accepting=frozenset({b}),
        transitions={(a, "x"): b, (b, "x"): b, (huerfano, "x"): a},
    )
    preparado = prepare_for_minimization(afd)
    assert preparado.removed == ("C",)
    assert huerfano not in preparado.dfa.states


def test_la_preparacion_no_muta_el_original() -> None:
    afd = build_dfa(nfa_of("abb")).dfa
    estados_antes = set(afd.states)
    transiciones_antes = dict(afd.transitions)
    prepare_for_minimization(afd)
    assert set(afd.states) == estados_antes
    assert afd.transitions == transiciones_antes


def test_un_afd_ya_completo_no_agrega_pozo() -> None:
    preparado = prepare_for_minimization(build_dfa(nfa_of("(a|b)*")).dfa)
    assert preparado.trap_added is False
