"""Minimizacion de un AFD por refinamiento sucesivo de particiones.

Se parte de la particion ``P0 = {aceptacion, no aceptacion}`` y en cada paso se
separan los estados de un mismo bloque cuyas transiciones caen en bloques
distintos, hasta alcanzar un punto fijo.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models.dfa import DFA, DFAState
from .quotient import build_quotient_dfa


@dataclass(frozen=True)
class PartitionMinimizationResult:
    """AFD minimo y el historial del refinamiento.

    Attributes:
        dfa: AFD minimo.
        history: Secuencia ``P0, P1, ..., Pn``. Cada particion es una tupla de
            bloques y cada bloque una tupla de etiquetas ordenadas.
        classes: Clases de equivalencia finales sobre el AFD de entrada.
    """

    dfa: DFA
    history: tuple[tuple[tuple[str, ...], ...], ...]
    classes: tuple[frozenset[DFAState], ...]

    @property
    def iterations(self) -> int:
        """Cantidad de refinamientos aplicados (sin contar ``P0``)."""
        return max(len(self.history) - 1, 0)


def minimize_by_partitions(dfa: DFA) -> PartitionMinimizationResult:
    """Minimiza ``dfa`` por refinamiento de particiones.

    Args:
        dfa: AFD preparado (accesible y con la funcion de transicion completa).

    Returns:
        El AFD minimo junto con el historial de particiones.
    """
    alfabeto = dfa.sorted_alphabet

    aceptacion = frozenset(estado for estado in dfa.states if estado in dfa.accepting)
    rechazo = frozenset(estado for estado in dfa.states if estado not in dfa.accepting)
    # Los bloques vacios no forman parte de la particion.
    particion: list[frozenset[DFAState]] = [
        bloque for bloque in (aceptacion, rechazo) if bloque
    ]

    historial: list[tuple[tuple[str, ...], ...]] = [_snapshot(particion)]

    while True:
        indice_de_bloque = _block_index(particion)
        nueva: list[frozenset[DFAState]] = []

        for bloque in particion:
            por_firma: dict[tuple[int | None, ...], set[DFAState]] = {}
            for estado in bloque:
                firma = tuple(
                    _destination_block(dfa, estado, simbolo, indice_de_bloque)
                    for simbolo in alfabeto
                )
                por_firma.setdefault(firma, set()).add(estado)
            nueva.extend(
                frozenset(grupo)
                for _, grupo in sorted(
                    por_firma.items(),
                    key=lambda par: min(estado.identifier for estado in par[1]),
                )
            )

        if len(nueva) == len(particion):
            # Punto fijo: ningun bloque se dividio en esta pasada.
            break

        particion = nueva
        historial.append(_snapshot(particion))

    minimo = build_quotient_dfa(dfa, particion)
    return PartitionMinimizationResult(
        dfa=minimo,
        history=tuple(historial),
        classes=tuple(particion),
    )


def _block_index(particion: list[frozenset[DFAState]]) -> dict[DFAState, int]:
    """Mapa de estado a indice de bloque en la particion actual."""
    return {
        estado: indice for indice, bloque in enumerate(particion) for estado in bloque
    }


def _destination_block(
    dfa: DFA, state: DFAState, symbol: str, indice_de_bloque: dict[DFAState, int]
) -> int | None:
    """Bloque al que llega ``state`` con ``symbol``; ``None`` si no hay transicion."""
    destino = dfa.transition(state, symbol)
    return None if destino is None else indice_de_bloque[destino]


def _snapshot(particion: list[frozenset[DFAState]]) -> tuple[tuple[str, ...], ...]:
    """Congela la particion como tuplas de etiquetas, para el historial."""
    bloques = [
        tuple(sorted(estado.label for estado in bloque)) for bloque in particion
    ]
    return tuple(sorted(bloques))
