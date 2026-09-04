"""Pruebas de la insercion de concatenacion explicita."""

from __future__ import annotations

import pytest

from regex_automata.regex.concatenation import (
    insert_explicit_concatenation,
    tokens_to_string,
)
from regex_automata.regex.tokenizer import tokenize


def normalizar(expresion: str) -> str:
    return tokens_to_string(insert_explicit_concatenation(tokenize(expresion)))


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("ab", "a.b"),
        ("a(b)", "a.(b)"),
        ("(a)b", "(a).b"),
        ("a*b", "a*.b"),
        ("a+b", "a+.b"),
        ("a?b", "a?.b"),
        ("(a)(b)", "(a).(b)"),
        ("abc", "a.b.c"),
        ("(a|b)*abb(a|b)*", "(a|b)*.a.b.b.(a|b)*"),
        ("a~", "a.ε"),
        ("~a", "ε.a"),
    ],
)
def test_insercion(entrada: str, esperado: str) -> None:
    assert normalizar(entrada) == esperado


@pytest.mark.parametrize("expresion", ["a.b", "a|b", "(a|b)", "a*", "a"])
def test_no_duplica_concatenacion_existente(expresion: str) -> None:
    assert normalizar(expresion) == expresion


def test_lista_vacia() -> None:
    assert insert_explicit_concatenation([]) == []
