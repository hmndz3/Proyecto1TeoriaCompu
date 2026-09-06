"""Orquestacion del flujo completo de una expresion regular.

Este modulo no imprime ni escribe archivos: construye los automatas y devuelve
los datos. La presentacion vive en la CLI y en el generador de resumenes.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..algorithms.dfa_preparation import PreparedDFA, prepare_for_minimization
from ..algorithms.equivalence import EquivalenceReport, check_equivalence
from ..algorithms.partition_minimizer import (
    PartitionMinimizationResult,
    minimize_by_partitions,
)
from ..algorithms.subset_construction import SubsetConstructionResult, build_dfa
from ..algorithms.table_filling_minimizer import (
    TableFillingResult,
    minimize_by_table_filling,
)
from ..algorithms.thompson import build_nfa
from ..errors import EquivalenceError
from ..models.nfa import NFA
from ..models.token import Token
from ..regex.concatenation import insert_explicit_concatenation, tokens_to_string
from ..regex.shunting_yard import postfix_to_string, to_postfix
from ..regex.tokenizer import tokenize
from ..regex.validator import validate
from ..simulation.dfa_simulator import simulate_dfa
from ..simulation.nfa_simulator import simulate_nfa
from ..simulation.result import SimulationResult


@dataclass(frozen=True)
class ExpressionAnalysis:
    """Todo lo derivado de una expresion regular, sin depender de la cadena.

    Attributes:
        expression: Expresion tal como la escribio el usuario.
        tokens: Tokens originales.
        normalized_tokens: Tokens con la concatenacion explicita insertada.
        postfix: Tokens en notacion postfix.
        nfa: AFN de Thompson.
        subset: AFD por construccion de subconjuntos y su traza.
        prepared: AFD accesible y completo usado por los dos minimizadores.
        partition: Minimizacion por refinamiento de particiones.
        table_filling: Minimizacion por tabla de pares distinguibles.
        equivalence: Comprobacion formal entre los dos AFD minimos.
        line_number: Numero de linea del archivo de origen, si aplica.
    """

    expression: str
    tokens: tuple[Token, ...]
    normalized_tokens: tuple[Token, ...]
    postfix: tuple[Token, ...]
    nfa: NFA
    subset: SubsetConstructionResult
    prepared: PreparedDFA
    partition: PartitionMinimizationResult
    table_filling: TableFillingResult
    equivalence: EquivalenceReport
    line_number: int | None = None

    @property
    def normalized_expression(self) -> str:
        """Expresion infix con la concatenacion explicita."""
        return tokens_to_string(self.normalized_tokens)

    @property
    def postfix_expression(self) -> str:
        """Postfix imprimible, separado por espacios."""
        return postfix_to_string(self.postfix)

    @property
    def alphabet(self) -> list[str]:
        return self.nfa.sorted_alphabet


@dataclass(frozen=True)
class SimulationBundle:
    """Resultado de simular una cadena en los cuatro automatas."""

    word: str
    nfa: SimulationResult
    dfa: SimulationResult
    partition: SimulationResult
    table_filling: SimulationResult

    @property
    def results(self) -> tuple[SimulationResult, ...]:
        return (self.nfa, self.dfa, self.partition, self.table_filling)

    @property
    def consistent(self) -> bool:
        """``True`` si los cuatro automatas coinciden en aceptar o rechazar."""
        return len({resultado.accepted for resultado in self.results}) == 1

    @property
    def accepted(self) -> bool:
        return self.nfa.accepted

    @property
    def answer(self) -> str:
        """Respuesta pedida por el enunciado: ``si`` o ``no``."""
        return "si" if self.accepted else "no"


def analyze_expression(
    expression: str, *, line_number: int | None = None
) -> ExpressionAnalysis:
    """Ejecuta el flujo completo sobre ``expression``.

    Args:
        expression: Expresion regular en notacion infix.
        line_number: Numero de linea del archivo de origen, si aplica.

    Returns:
        Un :class:`ExpressionAnalysis` con los cuatro automatas construidos.

    Raises:
        RegexSyntaxError: Si la expresion no es valida.
        EquivalenceError: Si los dos AFD minimos no reconocen el mismo lenguaje.
    """
    tokens = tokenize(expression, line_number=line_number)
    validate(tokens, expression, line_number=line_number)

    normalizados = insert_explicit_concatenation(tokens)
    postfix = to_postfix(normalizados, expression=expression, line_number=line_number)

    nfa = build_nfa(postfix)
    subconjuntos = build_dfa(nfa)
    preparado = prepare_for_minimization(subconjuntos.dfa)

    particiones = minimize_by_partitions(preparado.dfa)
    tabla = minimize_by_table_filling(preparado.dfa)

    equivalencia = check_equivalence(particiones.dfa, tabla.dfa)
    if not equivalencia.equivalent:
        raise EquivalenceError(
            "error interno: los dos AFD minimos no son equivalentes "
            f"(contraejemplo: '{equivalencia.counterexample}')"
        )
    if particiones.dfa.state_count != tabla.dfa.state_count:
        raise EquivalenceError(
            "error interno: los dos AFD minimos tienen distinta cantidad de estados "
            f"({particiones.dfa.state_count} y {tabla.dfa.state_count})"
        )

    return ExpressionAnalysis(
        expression=expression,
        tokens=tuple(tokens),
        normalized_tokens=tuple(normalizados),
        postfix=tuple(postfix),
        nfa=nfa,
        subset=subconjuntos,
        prepared=preparado,
        partition=particiones,
        table_filling=tabla,
        equivalence=equivalencia,
        line_number=line_number,
    )


def simulate_all(analysis: ExpressionAnalysis, word: str) -> SimulationBundle:
    """Simula ``word`` sobre los cuatro automatas de ``analysis``."""
    return SimulationBundle(
        word=word,
        nfa=simulate_nfa(analysis.nfa, word),
        dfa=simulate_dfa(analysis.subset.dfa, word, name="AFD (subconjuntos)"),
        partition=simulate_dfa(
            analysis.partition.dfa, word, name="AFD minimo (particiones)"
        ),
        table_filling=simulate_dfa(
            analysis.table_filling.dfa, word, name="AFD minimo (tabla de pares)"
        ),
    )
