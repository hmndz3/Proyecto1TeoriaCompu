"""Preparacion de un AFD antes de minimizarlo.

Ambos minimizadores parten del mismo AFD preparado: sin estados inaccesibles y
con la funcion de transicion completa. El AFD original nunca se modifica.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import TRAP_STATE_LABEL
from ..models.dfa import DFA, DFAState


@dataclass(frozen=True)
class PreparedDFA:
    """AFD listo para minimizar.

    Attributes:
        dfa: AFD accesible y completo.
        removed: Etiquetas de los estados inaccesibles eliminados.
        trap_added: ``True`` si hubo que agregar un estado pozo.
    """

    dfa: DFA
    removed: tuple[str, ...]
    trap_added: bool


def prepare_for_minimization(dfa: DFA) -> PreparedDFA:
    """Elimina estados inaccesibles y completa la funcion de transicion.

    Args:
        dfa: AFD posiblemente parcial y con estados inaccesibles.

    Returns:
        Un :class:`PreparedDFA` con un AFD nuevo; el original queda intacto.
    """
    alcanzables = dfa.reachable_states()
    eliminados = tuple(
        sorted(estado.label for estado in dfa.states if estado not in alcanzables)
    )

    estados = sorted(alcanzables, key=lambda estado: estado.identifier)
    transiciones = {
        (origen, simbolo): destino
        for (origen, simbolo), destino in dfa.transitions.items()
        if origen in alcanzables and destino in alcanzables
    }

    alfabeto = sorted(dfa.alphabet)
    faltantes = [
        (estado, simbolo)
        for estado in estados
        for simbolo in alfabeto
        if (estado, simbolo) not in transiciones
    ]

    trampa_agregada = bool(faltantes)
    if trampa_agregada:
        pozo = DFAState(
            identifier=max((estado.identifier for estado in estados), default=-1) + 1,
            label=TRAP_STATE_LABEL,
            members=frozenset(),
        )
        estados.append(pozo)
        for estado, simbolo in faltantes:
            transiciones[(estado, simbolo)] = pozo
        for simbolo in alfabeto:
            transiciones[(pozo, simbolo)] = pozo

    preparado = DFA(
        states=frozenset(estados),
        alphabet=frozenset(alfabeto),
        start=dfa.start,
        accepting=frozenset(dfa.accepting & alcanzables),
        transitions=transiciones,
    )
    return PreparedDFA(dfa=preparado, removed=eliminados, trap_added=trampa_agregada)
