"""Pruebas del algoritmo de shunting yard."""

from __future__ import annotations

import pytest

from conftest import postfix
from regex_automata.errors import ShuntingYardError
from regex_automata.models.token import Token, TokenType
from regex_automata.regex.shunting_yard import to_postfix


@pytest.mark.parametrize(
    ("expresion", "esperado"),
    [
        ("a", "a"),
        ("ab", "a b ."),
        ("a.b", "a b ."),
        ("a|b", "a b |"),
        ("a*", "a *"),
        ("a+", "a +"),
        ("a?", "a ?"),
        ("ab|c", "a b . c |"),
        ("a|bc", "a b c . |"),
        ("(a|b)*", "a b | *"),
        ("(a|b)*ab", "a b | * a . b ."),
        ("(a|b)*abb(a|b)*", "a b | * a . b . b . a b | * ."),
        ("a**", "a * *"),
        ("(ab)*", "a b . *"),
        ("~", "ε"),
        ("a|b|c", "a b | c |"),
    ],
)
def test_conversion_a_postfix(expresion: str, esperado: str) -> None:
    assert postfix(expresion) == esperado


def test_concatenacion_tiene_mas_precedencia_que_union() -> None:
    # a.b|c debe agrupar como (a.b)|c
    assert postfix("a.b|c") == "a b . c |"


def test_estrella_tiene_mas_precedencia_que_concatenacion() -> None:
    # ab* debe agrupar como a.(b*)
    assert postfix("ab*") == "a b * ."


def test_union_es_asociativa_por_la_izquierda() -> None:
    assert postfix("a|b|c|d") == "a b | c | d |"


def test_parentesis_cambian_el_agrupamiento() -> None:
    assert postfix("a(b|c)") == "a b c | ."


def test_parentesis_de_cierre_sobrante_falla() -> None:
    tokens = [
        Token(TokenType.SYMBOL, "a", 0),
        Token(TokenType.RIGHT_PAREN, ")", 1),
    ]
    with pytest.raises(ShuntingYardError):
        to_postfix(tokens, expression="a)")


def test_parentesis_de_apertura_sobrante_falla() -> None:
    tokens = [
        Token(TokenType.LEFT_PAREN, "(", 0),
        Token(TokenType.SYMBOL, "a", 1),
    ]
    with pytest.raises(ShuntingYardError):
        to_postfix(tokens, expression="(a")
