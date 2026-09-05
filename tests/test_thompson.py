"""Pruebas de la construccion de Thompson."""

from __future__ import annotations

import pytest

from conftest import nfa_of, parse
from regex_automata.algorithms.thompson import build_nfa
from regex_automata.constants import EPSILON
from regex_automata.errors import AutomatonError
from regex_automata.models.token import Token, TokenType
from regex_automata.regex.shunting_yard import to_postfix
from regex_automata.simulation.nfa_simulator import simulate_nfa


def test_simbolo_produce_dos_estados() -> None:
    afn = nfa_of("a")
    assert afn.state_count == 2
    assert afn.alphabet == frozenset({"a"})
    assert len(afn.accepting) == 1


def test_epsilon_produce_transicion_vacia() -> None:
    afn = nfa_of("~")
    assert afn.state_count == 2
    assert afn.alphabet == frozenset()
    assert afn.destinations(afn.start, EPSILON)


def test_un_solo_estado_de_aceptacion() -> None:
    for expresion in ["a", "ab", "a|b", "a*", "a+", "a?", "(a|b)*abb(a|b)*"]:
        assert len(nfa_of(expresion).accepting) == 1


def test_el_estado_inicial_no_es_de_aceptacion_en_concatenacion() -> None:
    afn = nfa_of("ab")
    assert afn.start not in afn.accepting


def test_alfabeto_excluye_epsilon() -> None:
    afn = nfa_of("(a|~)b")
    assert afn.alphabet == frozenset({"a", "b"})


@pytest.mark.parametrize(
    ("expresion", "cadena", "esperado"),
    [
        ("a", "a", True),
        ("a", "", False),
        ("~", "", True),
        ("a*", "", True),
        ("a*", "aaa", True),
        ("a+", "", False),
        ("a+", "a", True),
        ("a+", "aaa", True),
        ("a?", "", True),
        ("a?", "a", True),
        ("a?", "aa", False),
        ("a|b", "b", True),
        ("a.b", "ab", True),
        ("ab", "ab", True),
        ("(a|b)*", "abba", True),
        ("(a|b)*abb(a|b)*", "babbaaaa", True),
    ],
)
def test_semantica_de_los_operadores(expresion: str, cadena: str, esperado: bool) -> None:
    assert simulate_nfa(nfa_of(expresion), cadena).accepted is esperado


def test_escapes_se_tratan_como_simbolos() -> None:
    afn = nfa_of(r"\*")
    assert afn.alphabet == frozenset({"*"})
    assert simulate_nfa(afn, "*").accepted is True
    assert simulate_nfa(afn, "").accepted is False


def test_postfix_vacio_falla() -> None:
    with pytest.raises(AutomatonError):
        build_nfa([])


def test_operador_sin_operando_falla() -> None:
    with pytest.raises(AutomatonError):
        build_nfa([Token(TokenType.OPERATOR, "*", 0)])


def test_operandos_sobrantes_fallan() -> None:
    postfix = [
        Token(TokenType.SYMBOL, "a", 0),
        Token(TokenType.SYMBOL, "b", 1),
    ]
    with pytest.raises(AutomatonError):
        build_nfa(postfix)


def test_anidamiento_profundo() -> None:
    afn = build_nfa(to_postfix(parse("((a|b)*c)+"), expression="((a|b)*c)+"))
    assert simulate_nfa(afn, "abc").accepted is True
    assert simulate_nfa(afn, "abcc").accepted is True
    assert simulate_nfa(afn, "ab").accepted is False
