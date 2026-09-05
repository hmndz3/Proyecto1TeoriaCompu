"""Construccion del codigo DOT de un AFN o de un AFD.

Convenciones de dibujo:

* Una flecha externa entra al estado inicial desde un punto invisible.
* Los estados de aceptacion se dibujan con doble circulo.
* Las transiciones epsilon se etiquetan con el glifo griego.
* Los simbolos que comparten origen y destino se agrupan como ``a,b``.
* Estados y simbolos se recorren ordenados, de modo que dos ejecuciones
  producen exactamente el mismo archivo.
"""

from __future__ import annotations

from ..models.dfa import DFA
from ..models.nfa import NFA
from .graph_model import AutomatonGraph, dfa_to_graph, nfa_to_graph

_HEADER = [
    "digraph {name} {{",
    "    rankdir=LR;",
    '    bgcolor="white";',
    '    node [fontname="Helvetica", fontsize=12];',
    '    edge [fontname="Helvetica", fontsize=11];',
    '    __inicio__ [shape=point, width=0.08, color="#333333"];',
]


def _escape(texto: str) -> str:
    """Escapa un texto para incrustarlo dentro de un literal DOT."""
    return texto.replace("\\", "\\\\").replace('"', '\\"')


def _dot_id(name: str) -> str:
    """Convierte un nombre en un identificador valido de grafo DOT."""
    limpio = "".join(caracter if caracter.isalnum() else "_" for caracter in name)
    return limpio or "automata"


def graph_to_dot(graph: AutomatonGraph, *, name: str = "automata") -> str:
    """Devuelve el codigo DOT de un grafo de automata."""
    lineas = [linea.format(name=_dot_id(name)) for linea in _HEADER]

    for nodo in graph.nodes:
        forma = "doublecircle" if nodo.accepting else "circle"
        relleno = "#d6ecff" if nodo.start else "#ffffff"
        lineas.append(
            f'    "{_escape(nodo.label)}" [shape={forma}, style=filled, '
            f'fillcolor="{relleno}", color="#333333"];'
        )

    lineas.append(f'    __inicio__ -> "{_escape(graph.start)}";')

    for arista in graph.edges:
        lineas.append(
            f'    "{_escape(arista.source)}" -> "{_escape(arista.target)}" '
            f'[label="{_escape(arista.label)}"];'
        )

    lineas.append("}")
    return "\n".join(lineas) + "\n"


def nfa_to_dot(nfa: NFA, *, name: str = "AFN") -> str:
    """Devuelve el codigo DOT del AFN."""
    return graph_to_dot(nfa_to_graph(nfa), name=name)


def dfa_to_dot(dfa: DFA, *, name: str = "AFD") -> str:
    """Devuelve el codigo DOT del AFD."""
    return graph_to_dot(dfa_to_graph(dfa), name=name)
