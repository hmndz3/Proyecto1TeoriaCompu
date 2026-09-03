"""Insercion de la concatenacion explicita.

El enunciado usa expresiones como ``(b|b)*abb(a|b)*``, donde la concatenacion es
implicita. Antes de aplicar shunting yard hay que hacerla explicita con el
operador ``.``, sin duplicar la que el usuario ya escribio.
"""

from __future__ import annotations

from collections.abc import Iterable
from itertools import pairwise

from ..constants import CONCATENATION
from ..models.token import Token, TokenType


def _closes_operand(token: Token) -> bool:
    """``True`` si el token termina un operando y algo puede concatenarse a el."""
    return token.is_operand or token.is_right_paren or token.is_postfix_operator


def _opens_operand(token: Token) -> bool:
    """``True`` si el token empieza un operando nuevo."""
    return token.is_operand or token.is_left_paren


def insert_explicit_concatenation(tokens: list[Token]) -> list[Token]:
    """Devuelve ``tokens`` con un ``.`` entre cada par que se concatena.

    Se inserta un operador de concatenacion entre ``a`` y ``b`` cuando ``a``
    cierra un operando (simbolo, epsilon, ``)``, ``*``, ``+`` o ``?``) y ``b``
    abre uno nuevo (simbolo, epsilon o ``(``).

    Ejemplos:
        ``ab`` -> ``a.b``; ``a*b`` -> ``a*.b``; ``(a)(b)`` -> ``(a).(b)``.
        ``a.b`` se deja intacto porque ``.`` no abre un operando.
    """
    if not tokens:
        return []

    resultado: list[Token] = [tokens[0]]
    for anterior, actual in pairwise(tokens):
        if _closes_operand(anterior) and _opens_operand(actual):
            resultado.append(
                Token(TokenType.OPERATOR, CONCATENATION, actual.position)
            )
        resultado.append(actual)
    return resultado


def tokens_to_string(tokens: Iterable[Token]) -> str:
    """Reconstruye la expresion infix a partir de sus tokens."""
    return "".join(token.display for token in tokens)
