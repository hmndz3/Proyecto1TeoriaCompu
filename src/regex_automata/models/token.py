"""Token de una expresion regular.

Los algoritmos trabajan sobre tokens tipados y no sobre manipulaciones de
strings, de modo que un simbolo escapado como ``\\*`` nunca se confunde con el
operador ``*``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from ..constants import (
    BINARY_OPERATORS,
    EPSILON_LABEL,
    LEFT_ASSOCIATIVE,
    POSTFIX_OPERATORS,
    PRECEDENCE,
)


class TokenType(Enum):
    """Categoria lexica de un token."""

    SYMBOL = auto()
    EPSILON = auto()
    OPERATOR = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()


@dataclass(frozen=True)
class Token:
    """Unidad lexica de una expresion regular.

    Attributes:
        type: Categoria del token.
        value: Texto del token. Para un simbolo escapado guarda el caracter
            literal, sin la barra invertida.
        position: Indice del token dentro de la expresion original.
        escaped: ``True`` cuando el simbolo provino de una secuencia de escape.
    """

    type: TokenType
    value: str
    position: int
    escaped: bool = False

    # -- clasificacion ----------------------------------------------------- #

    @property
    def is_operand(self) -> bool:
        """Un simbolo del alfabeto o epsilon."""
        return self.type in (TokenType.SYMBOL, TokenType.EPSILON)

    @property
    def is_operator(self) -> bool:
        return self.type is TokenType.OPERATOR

    @property
    def is_postfix_operator(self) -> bool:
        return self.is_operator and self.value in POSTFIX_OPERATORS

    @property
    def is_binary_operator(self) -> bool:
        return self.is_operator and self.value in BINARY_OPERATORS

    @property
    def is_left_paren(self) -> bool:
        return self.type is TokenType.LEFT_PAREN

    @property
    def is_right_paren(self) -> bool:
        return self.type is TokenType.RIGHT_PAREN

    # -- propiedades de operador ------------------------------------------- #

    @property
    def precedence(self) -> int:
        """Precedencia del operador. Cero para lo que no es operador."""
        return PRECEDENCE.get(self.value, 0) if self.is_operator else 0

    @property
    def is_left_associative(self) -> bool:
        return self.is_operator and self.value in LEFT_ASSOCIATIVE

    # -- presentacion ------------------------------------------------------ #

    @property
    def display(self) -> str:
        """Texto con el que se muestra el token al usuario."""
        if self.type is TokenType.EPSILON:
            return EPSILON_LABEL
        if self.type is TokenType.SYMBOL and self.escaped:
            return f"\\{self.value}"
        return self.value

    def __str__(self) -> str:  # pragma: no cover - delegacion trivial
        return self.display
