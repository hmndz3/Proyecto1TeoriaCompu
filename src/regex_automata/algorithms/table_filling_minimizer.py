"""Minimizacion de un AFD por tabla de pares distinguibles (Myhill-Nerode).

Se construye la tabla triangular de todos los pares no ordenados de estados
distintos. Se marcan primero los pares donde exactamente un estado es de
aceptacion y luego, iterativamente, los pares cuyos destinos con algun simbolo
ya estan marcados. Los pares que quedan sin marcar son equivalentes.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models.dfa import DFA, DFAState
from .quotient import build_quotient_dfa


@dataclass(frozen=True)
class PairMark:
    """Registro del marcado de un par de estados.

    Attributes:
        first: Etiqueta del primer estado del par.
        second: Etiqueta del segundo estado del par.
        iteration: Iteracion en que se marco. ``0`` es el marcado inicial.
        symbol: Simbolo que demostro la distincion. ``None`` en el marcado
            inicial, donde la razon es la aceptacion.
        reason: Explicacion breve del marcado.
    """

    first: str
    second: str
    iteration: int
    symbol: str | None
    reason: str


@dataclass(frozen=True)
class TableFillingResult:
    """AFD minimo y la informacion del llenado de la tabla.

    Attributes:
        dfa: AFD minimo.
        marks: Marcas en el orden en que se produjeron.
        equivalent_pairs: Pares que quedaron sin marcar.
        classes: Clases de equivalencia finales sobre el AFD de entrada.
        iterations: Cantidad de pasadas que produjeron marcas nuevas.
    """

    dfa: DFA
    marks: tuple[PairMark, ...]
    equivalent_pairs: tuple[tuple[str, str], ...]
    classes: tuple[frozenset[DFAState], ...]
    iterations: int

    @property
    def initial_marks(self) -> tuple[PairMark, ...]:
        """Pares marcados en el paso inicial por diferencia de aceptacion."""
        return tuple(marca for marca in self.marks if marca.iteration == 0)


def minimize_by_table_filling(dfa: DFA) -> TableFillingResult:
    """Minimiza ``dfa`` con la tabla de pares distinguibles.

    Args:
        dfa: AFD preparado (accesible y con la funcion de transicion completa).

    Returns:
        El AFD minimo junto con la traza del marcado.
    """
    estados = dfa.sorted_states
    alfabeto = dfa.sorted_alphabet

    pares = [
        (estados[i], estados[j])
        for i in range(len(estados))
        for j in range(i + 1, len(estados))
    ]

    marcados: set[tuple[DFAState, DFAState]] = set()
    marcas: list[PairMark] = []

    # Paso 1: marcar los pares donde exactamente un estado es de aceptacion.
    for primero, segundo in pares:
        if dfa.is_accepting(primero) != dfa.is_accepting(segundo):
            marcados.add((primero, segundo))
            marcas.append(
                PairMark(
                    first=primero.label,
                    second=segundo.label,
                    iteration=0,
                    symbol=None,
                    reason="uno es de aceptacion y el otro no",
                )
            )

    # Paso 2: propagar el marcado hasta que no aparezcan marcas nuevas.
    iteracion = 0
    while True:
        iteracion += 1
        nuevas = 0
        for primero, segundo in pares:
            if (primero, segundo) in marcados:
                continue
            for simbolo in alfabeto:
                destino_a = dfa.transition(primero, simbolo)
                destino_b = dfa.transition(segundo, simbolo)
                if destino_a is None or destino_b is None or destino_a == destino_b:
                    continue
                if _ordered(destino_a, destino_b) in marcados:
                    marcados.add((primero, segundo))
                    marcas.append(
                        PairMark(
                            first=primero.label,
                            second=segundo.label,
                            iteration=iteracion,
                            symbol=simbolo,
                            reason=(
                                f"con '{simbolo}' van a "
                                f"({destino_a.label},{destino_b.label}), que ya esta marcado"
                            ),
                        )
                    )
                    nuevas += 1
                    break
        if nuevas == 0:
            iteracion -= 1
            break

    equivalentes = [par for par in pares if par not in marcados]
    clases = _equivalence_classes(estados, equivalentes)
    minimo = build_quotient_dfa(dfa, clases)

    return TableFillingResult(
        dfa=minimo,
        marks=tuple(marcas),
        equivalent_pairs=tuple(
            (primero.label, segundo.label) for primero, segundo in equivalentes
        ),
        classes=tuple(clases),
        iterations=iteracion,
    )


def _ordered(first: DFAState, second: DFAState) -> tuple[DFAState, DFAState]:
    """Normaliza un par no ordenado para poder usarlo como clave."""
    return (first, second) if first.identifier < second.identifier else (second, first)


def _equivalence_classes(
    estados: list[DFAState], equivalentes: list[tuple[DFAState, DFAState]]
) -> list[frozenset[DFAState]]:
    """Agrupa los estados en clases usando union-find sobre los pares equivalentes."""
    padre: dict[DFAState, DFAState] = {estado: estado for estado in estados}

    def buscar(estado: DFAState) -> DFAState:
        raiz = estado
        while padre[raiz] != raiz:
            raiz = padre[raiz]
        # Compresion de caminos.
        actual = estado
        while padre[actual] != raiz:
            padre[actual], actual = raiz, padre[actual]
        return raiz

    def unir(a: DFAState, b: DFAState) -> None:
        raiz_a, raiz_b = buscar(a), buscar(b)
        if raiz_a == raiz_b:
            return
        if raiz_a.identifier < raiz_b.identifier:
            padre[raiz_b] = raiz_a
        else:
            padre[raiz_a] = raiz_b

    for primero, segundo in equivalentes:
        unir(primero, segundo)

    grupos: dict[DFAState, set[DFAState]] = {}
    for estado in estados:
        grupos.setdefault(buscar(estado), set()).add(estado)

    return [
        frozenset(grupo)
        for _, grupo in sorted(grupos.items(), key=lambda par: par[0].identifier)
    ]
