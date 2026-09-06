"""Dibujo de los automatas: DOT para Graphviz y SVG propio como respaldo."""

from __future__ import annotations

from .dot_builder import dfa_to_dot, graph_to_dot, nfa_to_dot
from .graph_model import (
    AutomatonGraph,
    GraphEdge,
    GraphNode,
    dfa_to_graph,
    nfa_to_graph,
)
from .graphviz_renderer import (
    RenderResult,
    graphviz_version,
    installation_hint,
    is_graphviz_available,
    render_image,
    write_dot,
)
from .svg_renderer import dfa_to_svg, graph_to_svg, nfa_to_svg

__all__ = [
    "AutomatonGraph",
    "GraphEdge",
    "GraphNode",
    "RenderResult",
    "dfa_to_dot",
    "dfa_to_graph",
    "dfa_to_svg",
    "graph_to_dot",
    "graph_to_svg",
    "graphviz_version",
    "installation_hint",
    "is_graphviz_available",
    "nfa_to_dot",
    "nfa_to_graph",
    "nfa_to_svg",
    "render_image",
    "write_dot",
]
