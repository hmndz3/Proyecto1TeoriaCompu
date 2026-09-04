"""Pruebas de la validacion sintactica."""

from __future__ import annotations

import pytest

from regex_automata.errors import ValidationError
from regex_automata.regex.tokenizer import tokenize
from regex_automata.regex.validator import validate

VALIDAS = [
    "a",
    "~",
    "ab",
    "a.b",
    "a|b",
    "a*",
    "a+",
    "a?",
    "a**",
    "(a)",
    "(a|b)*abb(a|b)*",
    "(a|~).b*",
    "((a|b)c)*",
    r"\*a",
]

INVALIDAS = [
    "()",
    "(a",
    "a)",
    "|a",
    "*a",
    "+a",
    "?a",
    ".a",
    "a|",
    "a.",
    "a||b",
    "a|.b",
    "(|a)",
    "(a|)",
    "(*)",
]


@pytest.mark.parametrize("expresion", VALIDAS)
def test_expresiones_validas(expresion: str) -> None:
    validate(tokenize(expresion), expresion)


@pytest.mark.parametrize("expresion", INVALIDAS)
def test_expresiones_invalidas(expresion: str) -> None:
    with pytest.raises(ValidationError):
        validate(tokenize(expresion), expresion)


def test_parentesis_vacios_tiene_mensaje_propio() -> None:
    with pytest.raises(ValidationError) as error:
        validate(tokenize("()"), "()")
    assert "vacios" in error.value.message


def test_el_error_incluye_posicion_y_marcador() -> None:
    with pytest.raises(ValidationError) as error:
        validate(tokenize("a||b"), "a||b")
    assert error.value.position == 2
    assert "^" in error.value.describe()


def test_numero_de_linea_se_propaga() -> None:
    with pytest.raises(ValidationError) as error:
        validate(tokenize("a|"), "a|", line_number=7)
    assert error.value.line_number == 7
    assert "linea 7" in error.value.describe()
