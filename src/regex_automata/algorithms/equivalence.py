"""Comprobacion formal de equivalencia entre dos AFD.

Se recorre el producto de estados desde el par inicial. Si en algun punto un
estado es de aceptacion y el otro no, los automatas reconocen lenguajes
distintos y se devuelve la cadena que lo demuestra. Probar unas pocas cadenas de
muestra no seria suficiente; este recorrido si lo es porque explora todos los
pares alcanzables.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from ..models.dfa import DFA, DFAState


@dataclass(frozen=True)
class EquivalenceReport:
    """Resultado de comparar dos AFD.

    Attributes:
        equivalent: ``True`` si reconocen el mismo lenguaje.
        counterexample: Cadena aceptada por uno y rechazada por el otro.
        pairs_explored: Cantidad de pares de estados visitados.
    """

    equivalent: bool
    counterexample: str | None
    pairs_explored: int


def check_equivalence(first: DFA, second: DFA) -> EquivalenceReport:
    """Determina si ``first`` y ``second`` reconocen el mismo lenguaje.

    El recorrido usa la union de ambos alfabetos y trata la ausencia de
    transicion como un estado pozo implicito, de modo que funciona igual con
    AFD parciales.
    """
    alfabeto = sorted(first.alphabet | second.alphabet)

    inicio: tuple[DFAState | None, DFAState | None] = (first.start, second.start)
    visitados: set[tuple[DFAState | None, DFAState | None]] = {inicio}
    cola: deque[tuple[tuple[DFAState | None, DFAState | None], str]] = deque(
        [(inicio, "")]
    )

    while cola:
        (estado_a, estado_b), cadena = cola.popleft()

        acepta_a = estado_a is not None and first.is_accepting(estado_a)
        acepta_b = estado_b is not None and second.is_accepting(estado_b)
        if acepta_a != acepta_b:
            return EquivalenceReport(
                equivalent=False,
                counterexample=cadena,
                pairs_explored=len(visitados),
            )

        for simbolo in alfabeto:
            siguiente_a = first.transition(estado_a, simbolo) if estado_a else None
            siguiente_b = second.transition(estado_b, simbolo) if estado_b else None
            par = (siguiente_a, siguiente_b)
            if par not in visitados:
                visitados.add(par)
                cola.append((par, cadena + simbolo))

    return EquivalenceReport(
        equivalent=True, counterexample=None, pairs_explored=len(visitados)
    )
