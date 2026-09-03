"""Validacion sintactica de una secuencia de tokens.

La validacion se hace con una tabla de adyacencia: para cada par de tokens
consecutivos se decide si la transicion es legal. Esto detecta operandos
faltantes, operadores mal colocados y agrupaciones invalidas antes de intentar
convertir a postfix.
"""

from __future__ import annotations

from enum import Enum, auto
from itertools import pairwise

from ..errors import ValidationError
from ..models.token import Token


class _Category(Enum):
    """Categoria de un token a efectos de validacion."""

    OPERAND = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    BINARY = auto()
    POSTFIX = auto()


def _category(token: Token) -> _Category:
    if token.is_operand:
        return _Category.OPERAND
    if token.is_left_paren:
        return _Category.LEFT_PAREN
    if token.is_right_paren:
        return _Category.RIGHT_PAREN
    if token.is_postfix_operator:
        return _Category.POSTFIX
    return _Category.BINARY


#: Categorias que pueden abrir una expresion.
_CAN_START = {_Category.OPERAND, _Category.LEFT_PAREN}

#: Categorias que pueden cerrar una expresion.
_CAN_END = {_Category.OPERAND, _Category.RIGHT_PAREN, _Category.POSTFIX}

#: Categorias validas despues de cada categoria.
_ALLOWED_AFTER: dict[_Category, set[_Category]] = {
    # Tras un operando puede venir cualquier cosa: otro operando implica
    # concatenacion implicita.
    _Category.OPERAND: {
        _Category.OPERAND,
        _Category.LEFT_PAREN,
        _Category.RIGHT_PAREN,
        _Category.BINARY,
        _Category.POSTFIX,
    },
    _Category.RIGHT_PAREN: {
        _Category.OPERAND,
        _Category.LEFT_PAREN,
        _Category.RIGHT_PAREN,
        _Category.BINARY,
        _Category.POSTFIX,
    },
    _Category.POSTFIX: {
        _Category.OPERAND,
        _Category.LEFT_PAREN,
        _Category.RIGHT_PAREN,
        _Category.BINARY,
        _Category.POSTFIX,
    },
    # Tras abrir parentesis hace falta un operando o otra agrupacion.
    _Category.LEFT_PAREN: {_Category.OPERAND, _Category.LEFT_PAREN},
    # Tras un operador binario hace falta el operando derecho.
    _Category.BINARY: {_Category.OPERAND, _Category.LEFT_PAREN},
}


def _explain(previous: Token | None, current: Token) -> str:
    """Construye un mensaje concreto para una adyacencia invalida."""
    categoria = _category(current)

    if previous is None:
        if categoria is _Category.BINARY:
            return f"la expresion no puede empezar con el operador '{current.value}'"
        if categoria is _Category.POSTFIX:
            return f"el operador '{current.value}' no tiene operando a la izquierda"
        return f"la expresion no puede empezar con '{current.display}'"

    anterior = _category(previous)

    if anterior is _Category.LEFT_PAREN and categoria is _Category.RIGHT_PAREN:
        return "parentesis vacios: '()' no es una expresion valida"
    if anterior is _Category.LEFT_PAREN and categoria is _Category.POSTFIX:
        return f"el operador '{current.value}' no tiene operando a la izquierda"
    if anterior is _Category.LEFT_PAREN and categoria is _Category.BINARY:
        return f"falta el operando izquierdo del operador '{current.value}'"
    if anterior is _Category.BINARY and categoria is _Category.BINARY:
        return (
            f"dos operadores binarios seguidos: '{previous.value}' y '{current.value}'"
        )
    if anterior is _Category.BINARY and categoria is _Category.POSTFIX:
        return (
            f"el operador '{current.value}' se aplica al operador '{previous.value}', "
            "que no es un operando"
        )
    if anterior is _Category.BINARY and categoria is _Category.RIGHT_PAREN:
        return f"falta el operando derecho del operador '{previous.value}'"
    return f"no se esperaba '{current.display}' despues de '{previous.display}'"


def validate(
    tokens: list[Token], expression: str, *, line_number: int | None = None
) -> None:
    """Verifica que ``tokens`` formen una expresion regular valida.

    Args:
        tokens: Tokens producidos por el tokenizador.
        expression: Expresion original, usada para senalar la posicion del error.
        line_number: Numero de linea del archivo de origen, si aplica.

    Raises:
        ValidationError: Ante cualquier problema estructural.
    """
    if not tokens:
        raise ValidationError(
            "la expresion esta vacia",
            expression=expression,
            position=0,
            line_number=line_number,
        )

    def fallar(mensaje: str, token: Token) -> None:
        raise ValidationError(
            mensaje,
            expression=expression,
            position=token.position,
            line_number=line_number,
        )

    # Apertura valida.
    primero = tokens[0]
    if _category(primero) not in _CAN_START:
        fallar(_explain(None, primero), primero)

    # Adyacencias y balance de parentesis.
    pila: list[Token] = []
    if primero.is_left_paren:
        pila.append(primero)

    for anterior, actual in pairwise(tokens):
        if _category(actual) not in _ALLOWED_AFTER[_category(anterior)]:
            fallar(_explain(anterior, actual), actual)

        if actual.is_left_paren:
            pila.append(actual)
        elif actual.is_right_paren:
            if not pila:
                fallar("parentesis de cierre sin su correspondiente apertura", actual)
            pila.pop()

    if pila:
        abierto = pila[-1]
        fallar("parentesis de apertura sin cerrar", abierto)

    # Cierre valido.
    ultimo = tokens[-1]
    if _category(ultimo) not in _CAN_END:
        if ultimo.is_binary_operator:
            fallar(
                f"falta el operando derecho del operador '{ultimo.value}'",
                ultimo,
            )
        fallar(f"la expresion no puede terminar con '{ultimo.display}'", ultimo)
