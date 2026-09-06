"""Lectura de los archivos de entrada.

El programa trabaja con dos archivos de texto:

* ``expresiones.txt``: una expresion regular por linea.
* ``cadenas.txt``: una cadena ``w`` por linea, emparejada por posicion con la
  expresion correspondiente.

En ambos se ignoran las lineas vacias y las que empiezan con ``#``, y se
conserva el numero de linea original para que los mensajes de error apunten al
lugar correcto.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..constants import COMMENT_PREFIX, EPSILON_INPUT
from ..errors import RegexAutomataError


@dataclass(frozen=True)
class ExpressionLine:
    """Una expresion leida del archivo y su numero de linea."""

    line_number: int
    expression: str


@dataclass(frozen=True)
class WordLine:
    """Una cadena leida del archivo y su numero de linea.

    ``~`` en el archivo representa la cadena vacia, de modo que puede escribirse
    de forma explicita sin depender de una linea en blanco.
    """

    line_number: int
    word: str


def _significant_lines(path: Path, descripcion: str) -> list[tuple[int, str]]:
    """Devuelve las lineas utiles de ``path`` como ``(numero, texto)``."""
    if not path.exists():
        raise RegexAutomataError(f"no se encontro el archivo de {descripcion} '{path}'")
    if not path.is_file():
        raise RegexAutomataError(f"'{path}' no es un archivo")

    try:
        contenido = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RegexAutomataError(f"no se pudo leer '{path}': {error}") from error

    utiles: list[tuple[int, str]] = []
    for numero, linea in enumerate(contenido.splitlines(), start=1):
        limpia = linea.strip()
        if not limpia or limpia.startswith(COMMENT_PREFIX):
            continue
        utiles.append((numero, limpia))
    return utiles


def read_expressions(path: Path) -> list[ExpressionLine]:
    """Lee las expresiones regulares de ``path``.

    Args:
        path: Ruta del archivo de texto.

    Returns:
        Lista de expresiones, en el orden del archivo.

    Raises:
        RegexAutomataError: Si el archivo no existe, no puede leerse o no
            contiene ninguna expresion.
    """
    lineas = _significant_lines(path, "expresiones")
    if not lineas:
        raise RegexAutomataError(
            f"el archivo '{path}' no contiene ninguna expresion regular"
        )
    return [ExpressionLine(line_number=numero, expression=texto) for numero, texto in lineas]


def read_words(path: Path) -> list[WordLine]:
    """Lee las cadenas a evaluar de ``path``.

    Una linea con ``~`` representa la cadena vacia.

    Args:
        path: Ruta del archivo de texto.

    Returns:
        Lista de cadenas, en el orden del archivo.

    Raises:
        RegexAutomataError: Si el archivo no existe, no puede leerse o no
            contiene ninguna cadena.
    """
    lineas = _significant_lines(path, "cadenas")
    if not lineas:
        raise RegexAutomataError(f"el archivo '{path}' no contiene ninguna cadena")
    return [
        WordLine(line_number=numero, word="" if texto == EPSILON_INPUT else texto)
        for numero, texto in lineas
    ]


def pair_expressions_and_words(
    expressions: list[ExpressionLine],
    words: list[WordLine],
    *,
    expressions_path: Path,
    words_path: Path,
) -> list[tuple[ExpressionLine, WordLine]]:
    """Empareja cada expresion con la cadena de la misma posicion.

    Args:
        expressions: Expresiones leidas del archivo.
        words: Cadenas leidas del archivo.
        expressions_path: Ruta del archivo de expresiones, para el mensaje de error.
        words_path: Ruta del archivo de cadenas, para el mensaje de error.

    Returns:
        Los pares ``(expresion, cadena)`` en orden.

    Raises:
        RegexAutomataError: Si la cantidad de expresiones y de cadenas no coincide.
    """
    if len(expressions) != len(words):
        raise RegexAutomataError(
            f"hay {len(expressions)} expresiones en '{expressions_path}' y "
            f"{len(words)} cadenas en '{words_path}'. "
            "Debe haber exactamente una cadena por expresion."
        )
    return list(zip(expressions, words, strict=True))
