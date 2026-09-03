"""Division de una expresion regular en tokens.

Reglas aplicadas:

* ``~`` es epsilon.
* ``\\x`` produce el simbolo literal ``x`` (sirve para ``\\*``, ``\\|``, ``\\~``...).
* Los caracteres reservados sin escapar son operadores o parentesis.
* Cualquier otro caracter es un simbolo del alfabeto.
* Los espacios exteriores se ignoran; para un espacio literal se usa ``\\ ``.
"""

from __future__ import annotations

from ..constants import (
    EPSILON_INPUT,
    ESCAPE,
    LEFT_PAREN,
    OPERATORS,
    RIGHT_PAREN,
)
from ..errors import TokenizationError
from ..models.token import Token, TokenType


def tokenize(expression: str, *, line_number: int | None = None) -> list[Token]:
    """Convierte ``expression`` en una lista de tokens.

    Args:
        expression: Expresion regular escrita por el usuario.
        line_number: Numero de linea del archivo de origen, si aplica.

    Returns:
        Lista de tokens en el mismo orden en que aparecen.

    Raises:
        TokenizationError: Si la expresion esta vacia o hay un escape incompleto.
    """
    if not expression.strip():
        raise TokenizationError(
            "la expresion esta vacia",
            expression=expression,
            position=0,
            line_number=line_number,
        )

    tokens: list[Token] = []
    indice = 0
    longitud = len(expression)

    while indice < longitud:
        caracter = expression[indice]

        if caracter.isspace():
            indice += 1
            continue

        if caracter == ESCAPE:
            if indice + 1 >= longitud:
                raise TokenizationError(
                    "escape incompleto: falta el caracter despues de la barra invertida",
                    expression=expression,
                    position=indice,
                    line_number=line_number,
                )
            literal = expression[indice + 1]
            tokens.append(Token(TokenType.SYMBOL, literal, indice, escaped=True))
            indice += 2
            continue

        if caracter == EPSILON_INPUT:
            tokens.append(Token(TokenType.EPSILON, EPSILON_INPUT, indice))
        elif caracter == LEFT_PAREN:
            tokens.append(Token(TokenType.LEFT_PAREN, LEFT_PAREN, indice))
        elif caracter == RIGHT_PAREN:
            tokens.append(Token(TokenType.RIGHT_PAREN, RIGHT_PAREN, indice))
        elif caracter in OPERATORS:
            tokens.append(Token(TokenType.OPERATOR, caracter, indice))
        else:
            tokens.append(Token(TokenType.SYMBOL, caracter, indice))

        indice += 1

    if not tokens:
        raise TokenizationError(
            "la expresion no contiene ningun simbolo",
            expression=expression,
            position=0,
            line_number=line_number,
        )

    return tokens
