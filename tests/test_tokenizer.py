"""Pruebas del tokenizador."""

from __future__ import annotations

import pytest

from regex_automata.errors import TokenizationError
from regex_automata.models.token import TokenType
from regex_automata.regex.tokenizer import tokenize


def test_simbolos_simples() -> None:
    tokens = tokenize("ab")
    assert [token.type for token in tokens] == [TokenType.SYMBOL, TokenType.SYMBOL]
    assert [token.value for token in tokens] == ["a", "b"]


def test_operadores_y_parentesis() -> None:
    tokens = tokenize("(a|b)*")
    tipos = [token.type for token in tokens]
    assert tipos == [
        TokenType.LEFT_PAREN,
        TokenType.SYMBOL,
        TokenType.OPERATOR,
        TokenType.SYMBOL,
        TokenType.RIGHT_PAREN,
        TokenType.OPERATOR,
    ]


def test_epsilon_se_reconoce() -> None:
    tokens = tokenize("~")
    assert tokens[0].type is TokenType.EPSILON
    assert tokens[0].display == "ε"


def test_escape_produce_simbolo_literal() -> None:
    tokens = tokenize(r"\*")
    assert tokens[0].type is TokenType.SYMBOL
    assert tokens[0].value == "*"
    assert tokens[0].escaped is True
    assert tokens[0].display == r"\*"


@pytest.mark.parametrize("expresion", [r"\+", r"\.", r"\~", r"\\", r"\(", r"\|"])
def test_todos_los_reservados_se_pueden_escapar(expresion: str) -> None:
    tokens = tokenize(expresion)
    assert len(tokens) == 1
    assert tokens[0].type is TokenType.SYMBOL
    assert tokens[0].escaped is True


def test_espacios_exteriores_se_ignoran() -> None:
    assert [token.value for token in tokenize(" a | b ")] == ["a", "|", "b"]


def test_espacio_escapado_es_simbolo() -> None:
    tokens = tokenize(r"a\ b")
    assert [token.value for token in tokens] == ["a", " ", "b"]


def test_posiciones_se_conservan() -> None:
    tokens = tokenize("a|b")
    assert [token.position for token in tokens] == [0, 1, 2]


def test_expresion_vacia_falla() -> None:
    with pytest.raises(TokenizationError):
        tokenize("")


def test_solo_espacios_falla() -> None:
    with pytest.raises(TokenizationError):
        tokenize("   ")


def test_escape_incompleto_falla() -> None:
    with pytest.raises(TokenizationError) as error:
        tokenize("a\\")
    assert "escape incompleto" in error.value.message
