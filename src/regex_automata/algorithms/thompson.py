"""Construccion de Thompson: postfix -> AFN.

Se recorre la expresion en notacion postfix con una pila de fragmentos. Cada
fragmento es un sub-AFN con exactamente un estado inicial y un estado final, lo
que permite componerlos sin ambiguedad.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import CONCATENATION, KLEENE_STAR, OPTIONAL, PLUS, UNION
from ..errors import AutomatonError
from ..models.nfa import NFA, NFABuilder
from ..models.state import State, StateFactory
from ..models.token import Token, TokenType


@dataclass(frozen=True)
class _Fragment:
    """Sub-AFN con un unico estado inicial y un unico estado final."""

    start: State
    end: State


def build_nfa(postfix: list[Token]) -> NFA:
    """Construye el AFN correspondiente a una expresion en postfix.

    Args:
        postfix: Tokens en notacion postfix.

    Returns:
        El AFN de Thompson, con un solo estado de aceptacion.

    Raises:
        AutomatonError: Si el postfix esta mal formado (faltan o sobran operandos).
    """
    if not postfix:
        raise AutomatonError("no hay tokens para construir el AFN")

    fabrica = StateFactory()
    constructor = NFABuilder()
    pila: list[_Fragment] = []

    for token in postfix:
        if token.type is TokenType.SYMBOL:
            pila.append(_symbol(constructor, fabrica, token.value))
        elif token.type is TokenType.EPSILON:
            pila.append(_epsilon(constructor, fabrica))
        elif token.is_operator:
            _apply_operator(token, pila, constructor, fabrica)
        else:  # pragma: no cover - los parentesis no llegan al postfix
            raise AutomatonError(f"token inesperado en postfix: {token.display}")

    if len(pila) != 1:
        raise AutomatonError(
            f"la expresion en postfix dejo {len(pila)} fragmentos en la pila; "
            "se esperaba exactamente 1"
        )

    fragmento = pila.pop()
    return constructor.build(fragmento.start, {fragmento.end})


def _apply_operator(
    token: Token, pila: list[_Fragment], constructor: NFABuilder, fabrica: StateFactory
) -> None:
    """Aplica un operador consumiendo fragmentos de la pila."""
    if token.value == UNION:
        derecho, izquierdo = _pop_two(pila, token)
        pila.append(_union(constructor, fabrica, izquierdo, derecho))
    elif token.value == CONCATENATION:
        derecho, izquierdo = _pop_two(pila, token)
        pila.append(_concatenation(constructor, izquierdo, derecho))
    elif token.value == KLEENE_STAR:
        pila.append(_kleene_star(constructor, fabrica, _pop_one(pila, token)))
    elif token.value == PLUS:
        pila.append(_positive_closure(constructor, fabrica, _pop_one(pila, token)))
    elif token.value == OPTIONAL:
        pila.append(_optional(constructor, fabrica, _pop_one(pila, token)))
    else:  # pragma: no cover - operador desconocido
        raise AutomatonError(f"operador no soportado: {token.value}")


def _pop_one(pila: list[_Fragment], token: Token) -> _Fragment:
    if not pila:
        raise AutomatonError(f"el operador '{token.value}' no tiene operando")
    return pila.pop()


def _pop_two(pila: list[_Fragment], token: Token) -> tuple[_Fragment, _Fragment]:
    if len(pila) < 2:
        raise AutomatonError(
            f"el operador binario '{token.value}' necesita dos operandos"
        )
    derecho = pila.pop()
    izquierdo = pila.pop()
    return derecho, izquierdo


# --------------------------------------------------------------------------- #
# Construcciones basicas
# --------------------------------------------------------------------------- #


def _symbol(constructor: NFABuilder, fabrica: StateFactory, symbol: str) -> _Fragment:
    """``s --a--> e``"""
    inicio = fabrica.new_state()
    fin = fabrica.new_state()
    constructor.add_transition(inicio, symbol, fin)
    return _Fragment(inicio, fin)


def _epsilon(constructor: NFABuilder, fabrica: StateFactory) -> _Fragment:
    """``s --epsilon--> e``"""
    inicio = fabrica.new_state()
    fin = fabrica.new_state()
    constructor.add_epsilon(inicio, fin)
    return _Fragment(inicio, fin)


def _union(
    constructor: NFABuilder,
    fabrica: StateFactory,
    izquierdo: _Fragment,
    derecho: _Fragment,
) -> _Fragment:
    """``r|s``: un inicio nuevo se ramifica y ambos finales convergen."""
    inicio = fabrica.new_state()
    fin = fabrica.new_state()
    constructor.add_epsilon(inicio, izquierdo.start)
    constructor.add_epsilon(inicio, derecho.start)
    constructor.add_epsilon(izquierdo.end, fin)
    constructor.add_epsilon(derecho.end, fin)
    return _Fragment(inicio, fin)


def _concatenation(
    constructor: NFABuilder, izquierdo: _Fragment, derecho: _Fragment
) -> _Fragment:
    """``r.s``: el final del primero enlaza con el inicio del segundo."""
    constructor.add_epsilon(izquierdo.end, derecho.start)
    return _Fragment(izquierdo.start, derecho.end)


def _kleene_star(
    constructor: NFABuilder, fabrica: StateFactory, fragmento: _Fragment
) -> _Fragment:
    """``r*``: cero o mas repeticiones."""
    inicio = fabrica.new_state()
    fin = fabrica.new_state()
    constructor.add_epsilon(inicio, fragmento.start)
    constructor.add_epsilon(inicio, fin)
    constructor.add_epsilon(fragmento.end, fragmento.start)
    constructor.add_epsilon(fragmento.end, fin)
    return _Fragment(inicio, fin)


def _positive_closure(
    constructor: NFABuilder, fabrica: StateFactory, fragmento: _Fragment
) -> _Fragment:
    """``r+``: una o mas repeticiones. Sin el atajo directo de inicio a fin."""
    inicio = fabrica.new_state()
    fin = fabrica.new_state()
    constructor.add_epsilon(inicio, fragmento.start)
    constructor.add_epsilon(fragmento.end, fragmento.start)
    constructor.add_epsilon(fragmento.end, fin)
    return _Fragment(inicio, fin)


def _optional(
    constructor: NFABuilder, fabrica: StateFactory, fragmento: _Fragment
) -> _Fragment:
    """``r?``: epsilon o una aparicion. Sin el ciclo de repeticion."""
    inicio = fabrica.new_state()
    fin = fabrica.new_state()
    constructor.add_epsilon(inicio, fragmento.start)
    constructor.add_epsilon(inicio, fin)
    constructor.add_epsilon(fragmento.end, fin)
    return _Fragment(inicio, fin)
