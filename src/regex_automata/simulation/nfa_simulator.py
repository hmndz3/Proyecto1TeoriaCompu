"""Cerradura epsilon, funcion mover y simulacion de un AFN."""

from __future__ import annotations

from collections.abc import Iterable

from ..constants import EPSILON
from ..models.nfa import NFA
from ..models.state import State
from .result import SimulationResult, TraceStep


def epsilon_closure(nfa: NFA, states: Iterable[State]) -> frozenset[State]:
    """Conjunto de estados alcanzables desde ``states`` usando solo epsilon.

    El propio conjunto de partida siempre forma parte del resultado.
    """
    cerradura: set[State] = set(states)
    pendientes: list[State] = list(cerradura)

    while pendientes:
        actual = pendientes.pop()
        for destino in nfa.destinations(actual, EPSILON):
            if destino not in cerradura:
                cerradura.add(destino)
                pendientes.append(destino)

    return frozenset(cerradura)


def move(nfa: NFA, states: Iterable[State], symbol: str) -> frozenset[State]:
    """Estados alcanzables desde ``states`` consumiendo exactamente ``symbol``.

    No aplica cerradura epsilon: eso corresponde al paso siguiente.
    """
    alcanzados: set[State] = set()
    for estado in states:
        alcanzados.update(nfa.destinations(estado, symbol))
    return frozenset(alcanzados)


def simulate_nfa(nfa: NFA, word: str) -> SimulationResult:
    """Simula ``word`` sobre ``nfa``.

    En cada paso se aplica mover y luego cerradura epsilon. La cadena se acepta
    si el conjunto final contiene algun estado de aceptacion, lo que cubre
    correctamente el caso de la cadena vacia.
    """
    actuales = epsilon_closure(nfa, {nfa.start})
    inicial = nfa.describe_set(actuales)
    pasos: list[TraceStep] = []
    simbolo_rechazo: str | None = None

    for simbolo in word:
        origen = nfa.describe_set(actuales)
        siguientes = epsilon_closure(nfa, move(nfa, actuales, simbolo))
        pasos.append(TraceStep(simbolo, origen, nfa.describe_set(siguientes)))
        actuales = siguientes
        if not actuales:
            simbolo_rechazo = simbolo
            break

    aceptada = bool(actuales & nfa.accepting)
    return SimulationResult(
        automaton="AFN",
        word=word,
        accepted=aceptada,
        trace=tuple(pasos),
        initial=inicial,
        rejected_symbol=simbolo_rechazo,
    )
