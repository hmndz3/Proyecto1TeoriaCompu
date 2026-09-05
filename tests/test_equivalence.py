"""Pruebas de la comprobacion formal de equivalencia entre AFD."""

from __future__ import annotations

from conftest import prepared_dfa_of
from regex_automata.algorithms.equivalence import check_equivalence
from regex_automata.models.dfa import DFA, DFAState


def _afd_una_a() -> DFA:
    """AFD que acepta exactamente la cadena 'a'."""
    inicial = DFAState(0, "A")
    final = DFAState(1, "B")
    return DFA(
        states=frozenset({inicial, final}),
        alphabet=frozenset({"a"}),
        start=inicial,
        accepting=frozenset({final}),
        transitions={(inicial, "a"): final},
    )


def _afd_a_estrella() -> DFA:
    """AFD que acepta a*."""
    unico = DFAState(0, "A")
    return DFA(
        states=frozenset({unico}),
        alphabet=frozenset({"a"}),
        start=unico,
        accepting=frozenset({unico}),
        transitions={(unico, "a"): unico},
    )


def test_un_afd_es_equivalente_a_si_mismo() -> None:
    afd = prepared_dfa_of("(a|b)*abb")
    assert check_equivalence(afd, afd).equivalent


def test_automatas_distintos_no_son_equivalentes() -> None:
    reporte = check_equivalence(_afd_una_a(), _afd_a_estrella())
    assert reporte.equivalent is False
    assert reporte.counterexample is not None


def test_el_contraejemplo_distingue_realmente() -> None:
    primero, segundo = _afd_una_a(), _afd_a_estrella()
    reporte = check_equivalence(primero, segundo)
    cadena = reporte.counterexample
    assert cadena is not None

    def acepta(afd: DFA, palabra: str) -> bool:
        actual: DFAState | None = afd.start
        for simbolo in palabra:
            actual = afd.transition(actual, simbolo) if actual else None
        return actual is not None and afd.is_accepting(actual)

    assert acepta(primero, cadena) != acepta(segundo, cadena)


def test_alfabetos_distintos_se_manejan_con_pozo_implicito() -> None:
    solo_a = _afd_a_estrella()
    con_b = prepared_dfa_of("b*")
    assert check_equivalence(solo_a, con_b).equivalent is False


def test_afd_completo_y_parcial_del_mismo_lenguaje_son_equivalentes() -> None:
    parcial = _afd_una_a()
    pozo = DFAState(2, "TRAMPA")
    completo = DFA(
        states=parcial.states | {pozo},
        alphabet=parcial.alphabet,
        start=parcial.start,
        accepting=parcial.accepting,
        transitions={
            **parcial.transitions,
            (DFAState(1, "B"), "a"): pozo,
            (pozo, "a"): pozo,
        },
    )
    assert check_equivalence(parcial, completo).equivalent
