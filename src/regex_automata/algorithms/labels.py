"""Generacion de etiquetas para estados de AFD.

Las etiquetas siguen la convencion ``A``, ``B``, ..., ``Z``, ``AA``, ``AB``...
Son unicamente presentacion: la identidad logica de un estado es su entero.
"""

from __future__ import annotations

from string import ascii_uppercase


def state_label(index: int) -> str:
    """Devuelve la etiqueta alfabetica del estado numero ``index`` (base cero)."""
    if index < 0:
        raise ValueError("el indice de estado no puede ser negativo")

    letras: list[str] = []
    numero = index
    while True:
        letras.append(ascii_uppercase[numero % 26])
        numero = numero // 26 - 1
        if numero < 0:
            break
    return "".join(reversed(letras))
