"""Jerarquia de errores del proyecto.

Los errores de sintaxis conservan la posicion aproximada dentro de la expresion
para poder senalar al usuario donde esta el problema.
"""

from __future__ import annotations


class RegexAutomataError(Exception):
    """Error base de la aplicacion."""


class RegexSyntaxError(RegexAutomataError):
    """Error de sintaxis en una expresion regular.

    Guarda la expresion original, la posicion aproximada del problema y, cuando
    se conoce, el numero de linea del archivo de entrada.
    """

    def __init__(
        self,
        message: str,
        *,
        expression: str = "",
        position: int | None = None,
        line_number: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.expression = expression
        self.position = position
        self.line_number = line_number

    def describe(self) -> str:
        """Devuelve un mensaje multilinea listo para mostrar en consola."""
        partes: list[str] = []
        encabezado = "Error de sintaxis"
        if self.line_number is not None:
            encabezado += f" (linea {self.line_number})"
        if self.position is not None:
            encabezado += f" (posicion {self.position + 1})"
        partes.append(f"{encabezado}: {self.message}")

        if self.expression:
            partes.append(f"  {self.expression}")
            if self.position is not None and 0 <= self.position <= len(self.expression):
                partes.append("  " + " " * self.position + "^")
        return "\n".join(partes)

    def __str__(self) -> str:  # pragma: no cover - delegacion trivial
        return self.describe()


class TokenizationError(RegexSyntaxError):
    """La expresion no pudo dividirse en tokens."""


class ValidationError(RegexSyntaxError):
    """La secuencia de tokens no forma una expresion regular valida."""


class ShuntingYardError(RegexSyntaxError):
    """La conversion de infix a postfix fallo."""


class AutomatonError(RegexAutomataError):
    """Error al construir o manipular un automata."""


class EquivalenceError(RegexAutomataError):
    """Dos automatas que deberian reconocer el mismo lenguaje no lo hacen."""


class GraphvizNotAvailableError(RegexAutomataError):
    """El ejecutable ``dot`` de Graphviz no esta disponible en el sistema."""
