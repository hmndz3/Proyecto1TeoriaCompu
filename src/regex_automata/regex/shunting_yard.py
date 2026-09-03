"""Conversion de infix a postfix mediante el algoritmo de shunting yard.

Trabaja sobre tokens ya validados y con la concatenacion explicita insertada.
Los operadores binarios ``|`` y ``.`` son asociativos por la izquierda; los
unarios ``*``, ``+`` y ``?`` son postfix, por lo que se emiten directamente a la
salida: su operando ya fue emitido inmediatamente antes.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..errors import ShuntingYardError
from ..models.token import Token


def to_postfix(
    tokens: list[Token], *, expression: str = "", line_number: int | None = None
) -> list[Token]:
    """Convierte una lista de tokens infix a notacion postfix.

    Args:
        tokens: Tokens infix con concatenacion explicita.
        expression: Expresion original, para los mensajes de error.
        line_number: Numero de linea del archivo de origen, si aplica.

    Returns:
        Los mismos tokens reordenados en notacion postfix.

    Raises:
        ShuntingYardError: Si quedan parentesis sin pareja.
    """
    salida: list[Token] = []
    pila: list[Token] = []

    for token in tokens:
        if token.is_operand:
            salida.append(token)

        elif token.is_postfix_operator:
            # Operador unario postfix: su operando ya esta en la salida.
            salida.append(token)

        elif token.is_binary_operator:
            while pila and pila[-1].is_operator:
                cima = pila[-1]
                mayor = cima.precedence > token.precedence
                igual_izquierda = (
                    cima.precedence == token.precedence and token.is_left_associative
                )
                if mayor or igual_izquierda:
                    salida.append(pila.pop())
                else:
                    break
            pila.append(token)

        elif token.is_left_paren:
            pila.append(token)

        elif token.is_right_paren:
            while pila and not pila[-1].is_left_paren:
                salida.append(pila.pop())
            if not pila:
                raise ShuntingYardError(
                    "parentesis de cierre sin su correspondiente apertura",
                    expression=expression,
                    position=token.position,
                    line_number=line_number,
                )
            pila.pop()  # descarta el '(' correspondiente

    while pila:
        cima = pila.pop()
        if cima.is_left_paren:
            raise ShuntingYardError(
                "parentesis de apertura sin cerrar",
                expression=expression,
                position=cima.position,
                line_number=line_number,
            )
        salida.append(cima)

    return salida


def postfix_to_string(tokens: Iterable[Token]) -> str:
    """Representacion imprimible del postfix, separada por espacios.

    Ejemplo: ``(a|b)*.a.b`` produce ``a b | * a . b .``.
    """
    return " ".join(token.display for token in tokens)
