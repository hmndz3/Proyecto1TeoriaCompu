"""Construccion de subconjuntos: AFN -> AFD.

El estado inicial del AFD es la cerradura epsilon del inicial del AFN. Un estado
compuesto es de aceptacion si contiene al menos un estado final del AFN.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models.dfa import DFA, DFAState
from ..models.nfa import NFA
from ..models.state import State
from ..simulation.nfa_simulator import epsilon_closure, move
from .labels import state_label


@dataclass(frozen=True)
class SubsetConstructionResult:
    """AFD obtenido y la correspondencia con los subconjuntos del AFN.

    Attributes:
        dfa: Automata determinista resultante.
        subsets: Para cada estado del AFD, el subconjunto de estados del AFN
            que representa.
    """

    dfa: DFA
    subsets: dict[DFAState, frozenset[State]]

    def describe_subset(self, state: DFAState) -> str:
        """Formatea el subconjunto de un estado, por ejemplo ``{q0,q1}``."""
        miembros = self.subsets.get(state, frozenset())
        return "{" + ",".join(estado.label for estado in sorted(miembros)) + "}"


def build_dfa(nfa: NFA) -> SubsetConstructionResult:
    """Determiniza ``nfa`` por construccion de subconjuntos.

    Args:
        nfa: Automata no determinista con transiciones epsilon.

    Returns:
        El AFD equivalente junto con la traza de subconjuntos.
    """
    alfabeto = nfa.sorted_alphabet

    inicial = epsilon_closure(nfa, {nfa.start})
    indice_por_subconjunto: dict[frozenset[State], int] = {inicial: 0}
    estados: list[DFAState] = [_make_state(0, inicial, nfa)]
    transiciones: dict[tuple[DFAState, str], DFAState] = {}

    pendientes: list[frozenset[State]] = [inicial]
    while pendientes:
        subconjunto = pendientes.pop(0)
        origen = estados[indice_por_subconjunto[subconjunto]]

        for simbolo in alfabeto:
            destino = epsilon_closure(nfa, move(nfa, subconjunto, simbolo))
            if not destino:
                # Subconjunto vacio: el AFD queda parcial y se completara con un
                # estado pozo en la etapa de preparacion.
                continue
            if destino not in indice_por_subconjunto:
                indice = len(estados)
                indice_por_subconjunto[destino] = indice
                estados.append(_make_state(indice, destino, nfa))
                pendientes.append(destino)
            transiciones[(origen, simbolo)] = estados[indice_por_subconjunto[destino]]

    aceptacion = frozenset(
        estado
        for subconjunto, indice in indice_por_subconjunto.items()
        for estado in [estados[indice]]
        if subconjunto & nfa.accepting
    )

    dfa = DFA(
        states=frozenset(estados),
        alphabet=frozenset(alfabeto),
        start=estados[0],
        accepting=aceptacion,
        transitions=transiciones,
    )
    subsets = {
        estados[indice]: subconjunto
        for subconjunto, indice in indice_por_subconjunto.items()
    }
    return SubsetConstructionResult(dfa=dfa, subsets=subsets)


def _make_state(index: int, subset: frozenset[State], nfa: NFA) -> DFAState:
    """Crea el estado del AFD que representa a ``subset``."""
    del nfa  # se conserva por simetria con futuras extensiones
    return DFAState(
        identifier=index,
        label=state_label(index),
        members=frozenset(estado.label for estado in subset),
    )
