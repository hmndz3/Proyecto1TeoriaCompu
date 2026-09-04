"""Simulacion de cadenas sobre AFN y AFD."""

from __future__ import annotations

from .dfa_simulator import simulate_dfa
from .nfa_simulator import epsilon_closure, move, simulate_nfa
from .result import SimulationResult, TraceStep

__all__ = [
    "SimulationResult",
    "TraceStep",
    "epsilon_closure",
    "move",
    "simulate_dfa",
    "simulate_nfa",
]
