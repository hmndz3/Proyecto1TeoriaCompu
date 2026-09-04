"""Simulacion de una cadena sobre un AFD."""

from __future__ import annotations

from ..models.dfa import DFA
from .result import SimulationResult, TraceStep


def simulate_dfa(dfa: DFA, word: str, *, name: str = "AFD") -> SimulationResult:
    """Simula ``word`` sobre ``dfa`` siguiendo una unica transicion por simbolo.

    Si el simbolo no pertenece al alfabeto, o si el AFD es parcial y no hay
    transicion definida, la cadena se rechaza de forma controlada.
    """
    actual = dfa.start
    pasos: list[TraceStep] = []
    simbolo_rechazo: str | None = None

    for simbolo in word:
        destino = dfa.transition(actual, simbolo) if simbolo in dfa.alphabet else None
        if destino is None:
            simbolo_rechazo = simbolo
            return SimulationResult(
                automaton=name,
                word=word,
                accepted=False,
                trace=tuple(pasos),
                initial=dfa.start.label,
                rejected_symbol=simbolo_rechazo,
            )
        pasos.append(TraceStep(simbolo, actual.label, destino.label))
        actual = destino

    return SimulationResult(
        automaton=name,
        word=word,
        accepted=dfa.is_accepting(actual),
        trace=tuple(pasos),
        initial=dfa.start.label,
        rejected_symbol=None,
    )
