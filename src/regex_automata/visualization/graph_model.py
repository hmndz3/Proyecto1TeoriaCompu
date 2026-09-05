"""Representacion intermedia de un automata para dibujarlo.

Tanto el generador de DOT como el de SVG parten de la misma estructura, de modo
que ambos dibujan exactamente el mismo grafo: los mismos nodos, las mismas
aristas y las mismas etiquetas agrupadas.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import display_symbol
from ..models.dfa import DFA
from ..models.nfa import NFA


@dataclass(frozen=True)
class GraphNode:
    """Un estado dibujable.

    Attributes:
        key: Identidad del nodo dentro del grafo.
        label: Texto que se muestra dentro del nodo.
        accepting: Se dibuja con doble borde.
        start: Recibe la flecha externa de entrada.
    """

    key: str
    label: str
    accepting: bool
    start: bool


@dataclass(frozen=True)
class GraphEdge:
    """Una transicion dibujable, con los simbolos ya agrupados."""

    source: str
    target: str
    label: str


@dataclass(frozen=True)
class AutomatonGraph:
    """Grafo listo para dibujar, con orden determinista."""

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    start: str

    def node(self, key: str) -> GraphNode:
        """Devuelve el nodo con esa clave."""
        for nodo in self.nodes:
            if nodo.key == key:
                return nodo
        raise KeyError(key)


def _group(pairs: list[tuple[str, str, str]]) -> tuple[GraphEdge, ...]:
    """Agrupa ``(origen, destino, simbolo)`` que comparten origen y destino."""
    agrupadas: dict[tuple[str, str], list[str]] = {}
    for origen, destino, simbolo in pairs:
        agrupadas.setdefault((origen, destino), []).append(simbolo)
    return tuple(
        GraphEdge(origen, destino, ",".join(sorted(set(simbolos))))
        for (origen, destino), simbolos in agrupadas.items()
    )


def nfa_to_graph(nfa: NFA) -> AutomatonGraph:
    """Convierte un AFN en su grafo dibujable."""
    nodos = tuple(
        GraphNode(
            key=estado.label,
            label=estado.label,
            accepting=nfa.is_accepting(estado),
            start=estado == nfa.start,
        )
        for estado in nfa.sorted_states
    )
    pares: list[tuple[str, str, str]] = []
    for origen, simbolo, destinos in nfa.iter_transitions():
        etiqueta = display_symbol(simbolo)
        for destino in sorted(destinos):
            pares.append((origen.label, destino.label, etiqueta))
    return AutomatonGraph(nodes=nodos, edges=_group(pares), start=nfa.start.label)


def dfa_to_graph(dfa: DFA) -> AutomatonGraph:
    """Convierte un AFD en su grafo dibujable."""
    nodos = tuple(
        GraphNode(
            key=estado.label,
            label=estado.label,
            accepting=dfa.is_accepting(estado),
            start=estado == dfa.start,
        )
        for estado in dfa.sorted_states
    )
    pares = [
        (origen.label, destino.label, simbolo)
        for origen, simbolo, destino in dfa.iter_transitions()
    ]
    return AutomatonGraph(nodes=nodos, edges=_group(pares), start=dfa.start.label)
