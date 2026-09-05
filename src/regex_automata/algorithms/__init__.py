"""Algoritmos sobre automatas: Thompson, subconjuntos, minimizacion y equivalencia."""

from __future__ import annotations

from .dfa_preparation import PreparedDFA, prepare_for_minimization
from .equivalence import EquivalenceReport, check_equivalence
from .partition_minimizer import PartitionMinimizationResult, minimize_by_partitions
from .subset_construction import SubsetConstructionResult, build_dfa
from .table_filling_minimizer import (
    PairMark,
    TableFillingResult,
    minimize_by_table_filling,
)
from .thompson import build_nfa

__all__ = [
    "EquivalenceReport",
    "PairMark",
    "PartitionMinimizationResult",
    "PreparedDFA",
    "SubsetConstructionResult",
    "TableFillingResult",
    "build_dfa",
    "build_nfa",
    "check_equivalence",
    "minimize_by_partitions",
    "minimize_by_table_filling",
    "prepare_for_minimization",
]
