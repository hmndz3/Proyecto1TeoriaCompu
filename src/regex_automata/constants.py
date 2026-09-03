"""Constantes compartidas por todo el proyecto.

Reune la sintaxis aceptada de expresiones regulares: operadores, precedencias,
caracteres reservados y la representacion interna de epsilon.
"""

from __future__ import annotations

from typing import Final

# --------------------------------------------------------------------------- #
# Epsilon
# --------------------------------------------------------------------------- #

#: Caracter que el usuario escribe para referirse a epsilon dentro de una expresion.
EPSILON_INPUT: Final[str] = "~"

#: Etiqueta visible de epsilon en trazas, resumenes e imagenes.
EPSILON_LABEL: Final[str] = "ε"

#: Representacion interna de epsilon como simbolo de transicion.
#:
#: Es una constante de varios caracteres y por lo tanto no puede colisionar con
#: ningun simbolo del alfabeto, ya que todo simbolo ordinario ocupa exactamente
#: un caracter. Nunca debe compararse contra un simbolo escrito por el usuario.
EPSILON: Final[str] = "\x00epsilon"

# --------------------------------------------------------------------------- #
# Operadores
# --------------------------------------------------------------------------- #

KLEENE_STAR: Final[str] = "*"
PLUS: Final[str] = "+"
OPTIONAL: Final[str] = "?"
CONCATENATION: Final[str] = "."
UNION: Final[str] = "|"
LEFT_PAREN: Final[str] = "("
RIGHT_PAREN: Final[str] = ")"
ESCAPE: Final[str] = "\\"

#: Operadores unarios que se escriben despues de su operando.
POSTFIX_OPERATORS: Final[frozenset[str]] = frozenset({KLEENE_STAR, PLUS, OPTIONAL})

#: Operadores binarios.
BINARY_OPERATORS: Final[frozenset[str]] = frozenset({CONCATENATION, UNION})

OPERATORS: Final[frozenset[str]] = POSTFIX_OPERATORS | BINARY_OPERATORS

#: Precedencia de los operadores. A mayor numero, mayor prioridad.
PRECEDENCE: Final[dict[str, int]] = {
    UNION: 1,
    CONCATENATION: 2,
    KLEENE_STAR: 3,
    PLUS: 3,
    OPTIONAL: 3,
}

#: Los dos operadores binarios son asociativos por la izquierda.
LEFT_ASSOCIATIVE: Final[frozenset[str]] = frozenset({UNION, CONCATENATION})

#: Caracteres que tienen significado especial y que deben escaparse con ``\``
#: para usarse como simbolos literales.
RESERVED_CHARACTERS: Final[frozenset[str]] = frozenset(
    {KLEENE_STAR, PLUS, OPTIONAL, CONCATENATION, UNION, LEFT_PAREN, RIGHT_PAREN, EPSILON_INPUT, ESCAPE}
)

# --------------------------------------------------------------------------- #
# Archivos de entrada
# --------------------------------------------------------------------------- #

#: Prefijo que marca una linea de comentario dentro del archivo de expresiones.
COMMENT_PREFIX: Final[str] = "#"

#: Nombre del estado pozo que se agrega al completar un AFD.
TRAP_STATE_LABEL: Final[str] = "TRAMPA"


def is_epsilon(symbol: str) -> bool:
    """Indica si ``symbol`` es la transicion epsilon interna."""
    return symbol == EPSILON


def display_symbol(symbol: str) -> str:
    """Devuelve la representacion legible de un simbolo de transicion."""
    return EPSILON_LABEL if is_epsilon(symbol) else symbol
