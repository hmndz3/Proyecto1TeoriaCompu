"""Construccion del AFD cociente a partir de clases de equivalencia.

Este modulo solo arma el automata resultante. Decidir que estados son
equivalentes es responsabilidad de cada minimizador, que son implementaciones
independientes entre si.
"""

from __future__ import annotations

from collections.abc import Sequence

from ..errors import AutomatonError
from ..models.dfa import DFA, DFAState


def build_quotient_dfa(dfa: DFA, classes: Sequence[frozenset[DFAState]]) -> DFA:
    """Construye el AFD cociente de ``dfa`` respecto de ``classes``.

    Args:
        dfa: AFD preparado (accesible y completo).
        classes: Particion de los estados de ``dfa`` en clases de equivalencia.

    Returns:
        Un AFD con un estado por clase.

    Raises:
        AutomatonError: Si las clases no cubren todos los estados del AFD.
    """
    cubiertos = {estado for clase in classes for estado in clase}
    if cubiertos != set(dfa.states):
        raise AutomatonError(
            "las clases de equivalencia no cubren exactamente los estados del AFD"
        )

    # Orden determinista: por el menor identificador de cada clase, con la clase
    # del estado inicial siempre primero.
    ordenadas = sorted(classes, key=lambda clase: min(e.identifier for e in clase))
    ordenadas.sort(key=lambda clase: dfa.start not in clase)

    clase_de: dict[DFAState, int] = {}
    for indice, clase in enumerate(ordenadas):
        for estado in clase:
            clase_de[estado] = indice

    nuevos: list[DFAState] = []
    for indice, clase in enumerate(ordenadas):
        etiquetas = sorted(estado.label for estado in clase)
        nuevos.append(
            DFAState(
                identifier=indice,
                label="{" + ",".join(etiquetas) + "}",
                members=frozenset(etiquetas),
            )
        )

    transiciones: dict[tuple[DFAState, str], DFAState] = {}
    for indice, clase in enumerate(ordenadas):
        representante = min(clase, key=lambda estado: estado.identifier)
        for simbolo in dfa.sorted_alphabet:
            destino = dfa.transition(representante, simbolo)
            if destino is not None:
                transiciones[(nuevos[indice], simbolo)] = nuevos[clase_de[destino]]

    aceptacion = frozenset(
        nuevos[indice]
        for indice, clase in enumerate(ordenadas)
        if any(estado in dfa.accepting for estado in clase)
    )

    return DFA(
        states=frozenset(nuevos),
        alphabet=frozenset(dfa.alphabet),
        start=nuevos[clase_de[dfa.start]],
        accepting=aceptacion,
        transitions=transiciones,
    )
