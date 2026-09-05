"""Dibujo de automatas en SVG, sin depender de Graphviz.

Es el respaldo cuando el ejecutable ``dot`` no esta disponible: produce un SVG
autocontenido que se abre en cualquier navegador. El resultado es mas sencillo
que el de Graphviz, pero muestra lo mismo: estado inicial, estados de
aceptacion, transiciones y sus simbolos.

El posicionamiento es por capas: se calcula la distancia en aristas desde el
estado inicial y cada nivel forma una columna de izquierda a derecha, que es la
forma natural de leer un automata.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass

from ..models.dfa import DFA
from ..models.nfa import NFA
from .graph_model import AutomatonGraph, GraphEdge, dfa_to_graph, nfa_to_graph

# Medidas del dibujo, en pixeles.
_FONT_SIZE = 13.0
_CHAR_WIDTH = 7.3
_MIN_RX = 21.0
_RY = 21.0
_ROW_GAP = 86.0
_COL_GAP = 74.0
_MARGIN = 40.0
_START_ARROW = 34.0

_STROKE = "#333333"
_START_FILL = "#d6ecff"
_NODE_FILL = "#ffffff"
_TEXT = "#111111"
_LABEL_BG = "#ffffff"


@dataclass(frozen=True)
class _Placed:
    """Un nodo ya colocado en el lienzo."""

    key: str
    label: str
    accepting: bool
    start: bool
    x: float
    y: float
    rx: float
    ry: float


def _node_rx(label: str) -> float:
    """Semieje horizontal necesario para que quepa la etiqueta."""
    return max(_MIN_RX, len(label) * _CHAR_WIDTH / 2 + 11.0)


def _depths(graph: AutomatonGraph) -> dict[str, int]:
    """Distancia en aristas desde el estado inicial, por recorrido en anchura."""
    adyacencia: dict[str, list[str]] = defaultdict(list)
    for arista in graph.edges:
        adyacencia[arista.source].append(arista.target)

    profundidad: dict[str, int] = {graph.start: 0}
    cola: deque[str] = deque([graph.start])
    while cola:
        actual = cola.popleft()
        for vecino in sorted(adyacencia[actual]):
            if vecino not in profundidad:
                profundidad[vecino] = profundidad[actual] + 1
                cola.append(vecino)

    # Los estados inalcanzables se dibujan en una columna extra al final.
    maxima = max(profundidad.values(), default=0)
    for nodo in graph.nodes:
        profundidad.setdefault(nodo.key, maxima + 1)
    return profundidad


#: Altura que ocupa un lazo por encima del nodo.
_LOOP_HEIGHT = 70.0


def _place(graph: AutomatonGraph) -> tuple[list[_Placed], float, float]:
    """Coloca los nodos en columnas y devuelve tambien el tamano del lienzo."""
    profundidad = _depths(graph)
    hay_lazos = any(arista.source == arista.target for arista in graph.edges)

    columnas: dict[int, list[str]] = defaultdict(list)
    for nodo in graph.nodes:
        columnas[profundidad[nodo.key]].append(nodo.key)

    etiquetas = {nodo.key: nodo.label for nodo in graph.nodes}
    radios = {clave: _node_rx(texto) for clave, texto in etiquetas.items()}

    niveles = sorted(columnas)
    alto_maximo = max(len(columnas[nivel]) for nivel in niveles)
    alto = (alto_maximo - 1) * _ROW_GAP + 2 * _RY
    # Espacio extra arriba para que los lazos no queden cortados.
    superior = _MARGIN + (_LOOP_HEIGHT if hay_lazos else 0.0)
    centro_y = superior + alto / 2

    posiciones: dict[str, tuple[float, float]] = {}
    x = _MARGIN + _START_ARROW
    for nivel in niveles:
        claves = columnas[nivel]
        radio_columna = max(radios[clave] for clave in claves)
        x += radio_columna
        altura = (len(claves) - 1) * _ROW_GAP
        y = centro_y - altura / 2
        for clave in claves:
            posiciones[clave] = (x, y)
            y += _ROW_GAP
        x += radio_columna + _COL_GAP

    ancho = x - _COL_GAP + _MARGIN
    total_alto = superior + alto + _MARGIN

    colocados = [
        _Placed(
            key=nodo.key,
            label=nodo.label,
            accepting=nodo.accepting,
            start=nodo.start,
            x=posiciones[nodo.key][0],
            y=posiciones[nodo.key][1],
            rx=radios[nodo.key],
            ry=_RY,
        )
        for nodo in graph.nodes
    ]
    return colocados, ancho, total_alto


def _boundary(nodo: _Placed, hacia_x: float, hacia_y: float) -> tuple[float, float]:
    """Punto del borde de la elipse en direccion a ``(hacia_x, hacia_y)``."""
    dx = hacia_x - nodo.x
    dy = hacia_y - nodo.y
    if dx == 0 and dy == 0:
        return nodo.x + nodo.rx, nodo.y
    escala = 1.0 / math.sqrt((dx / nodo.rx) ** 2 + (dy / nodo.ry) ** 2)
    return nodo.x + dx * escala, nodo.y + dy * escala


def _curvature(origen: _Placed, destino: _Placed, dobles: set[tuple[str, str]]) -> float:
    """Cuanto se arquea una arista para no montarse sobre otras."""
    if (origen.key, destino.key) in dobles:
        # Hay transicion en ambos sentidos: cada una se arquea hacia su lado.
        return 26.0
    if destino.x < origen.x:
        # Arista hacia atras: se arquea bastante para rodear los nodos.
        return 58.0
    if abs(destino.x - origen.x) < 1.0:
        # Misma columna.
        return 34.0
    salto = abs(destino.x - origen.x)
    if salto > _COL_GAP * 2:
        # Salta varias columnas: se arquea para no cruzar los nodos intermedios.
        return -min(34.0 + salto * 0.09, 96.0)
    return 0.0


_ARROW_LEN = 10.0
_ARROW_HALF = 4.2


def _arrow_head(x: float, y: float, dx: float, dy: float) -> str:
    """Triangulo de la punta de flecha, con la punta en ``(x, y)``.

    Se dibuja como un poligono y no como un ``marker`` de SVG para que se vea
    igual en cualquier visor, incluidos los conversores mas antiguos.
    """
    largo = math.hypot(dx, dy) or 1.0
    ux, uy = dx / largo, dy / largo
    base_x, base_y = x - ux * _ARROW_LEN, y - uy * _ARROW_LEN
    # Perpendicular a la direccion.
    px, py = -uy * _ARROW_HALF, ux * _ARROW_HALF
    return (
        f'<path d="M {x:.1f} {y:.1f} L {base_x + px:.1f} {base_y + py:.1f} '
        f'L {base_x - px:.1f} {base_y - py:.1f} Z" fill="{_STROKE}"/>'
    )


def _escape(texto: str) -> str:
    """Escapa texto para incrustarlo en el SVG."""
    return (
        texto.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _self_loop(nodo: _Placed, etiqueta: str) -> list[str]:
    """Dibuja un lazo sobre el propio nodo."""
    x1 = nodo.x - nodo.rx * 0.45
    x2 = nodo.x + nodo.rx * 0.45
    borde = nodo.y - nodo.ry * 0.86
    cima = nodo.y - nodo.ry - 46.0
    partes = [
        f'<path d="M {x1:.1f} {borde:.1f} C {x1 - 26:.1f} {cima:.1f} '
        f'{x2 + 26:.1f} {cima:.1f} {x2:.1f} {borde:.1f}" '
        f'fill="none" stroke="{_STROKE}" stroke-width="1.4"/>',
        # La curva llega al nodo bajando y hacia la izquierda.
        _arrow_head(x2, borde, x2 - (x2 + 26), borde - cima),
    ]
    partes.extend(_label(nodo.x, cima + 14.0, etiqueta))
    return partes


def _label(x: float, y: float, texto: str) -> list[str]:
    """Etiqueta de una transicion, con fondo para que se lea sobre las lineas."""
    ancho = len(texto) * _CHAR_WIDTH + 8.0
    return [
        f'<rect x="{x - ancho / 2:.1f}" y="{y - 10.0:.1f}" width="{ancho:.1f}" '
        f'height="17" rx="3" fill="{_LABEL_BG}" fill-opacity="0.92"/>',
        f'<text x="{x:.1f}" y="{y + 3.0:.1f}" text-anchor="middle" '
        f'font-size="{_FONT_SIZE - 1:.0f}" fill="{_TEXT}">{_escape(texto)}</text>',
    ]


def _edge(origen: _Placed, destino: _Placed, arista: GraphEdge, curvatura: float) -> list[str]:
    """Dibuja una transicion entre dos nodos distintos."""
    medio_x = (origen.x + destino.x) / 2
    medio_y = (origen.y + destino.y) / 2
    dx = destino.x - origen.x
    dy = destino.y - origen.y
    largo = math.hypot(dx, dy) or 1.0
    # Perpendicular a la direccion de la arista.
    control_x = medio_x + (-dy / largo) * curvatura
    control_y = medio_y + (dx / largo) * curvatura

    inicio = _boundary(origen, control_x, control_y)
    fin = _boundary(destino, control_x, control_y)

    # La tangente al final de una curva cuadratica apunta desde el control.
    tang_x, tang_y = fin[0] - control_x, fin[1] - control_y
    largo_t = math.hypot(tang_x, tang_y) or 1.0
    corte_x = fin[0] - tang_x / largo_t * (_ARROW_LEN - 1.5)
    corte_y = fin[1] - tang_y / largo_t * (_ARROW_LEN - 1.5)

    partes = [
        f'<path d="M {inicio[0]:.1f} {inicio[1]:.1f} '
        f'Q {control_x:.1f} {control_y:.1f} {corte_x:.1f} {corte_y:.1f}" '
        f'fill="none" stroke="{_STROKE}" stroke-width="1.4"/>',
        _arrow_head(fin[0], fin[1], tang_x, tang_y),
    ]
    # Punto medio de la curva cuadratica.
    etiqueta_x = 0.25 * inicio[0] + 0.5 * control_x + 0.25 * fin[0]
    etiqueta_y = 0.25 * inicio[1] + 0.5 * control_y + 0.25 * fin[1]
    partes.extend(_label(etiqueta_x, etiqueta_y - 3.0, arista.label))
    return partes


def graph_to_svg(graph: AutomatonGraph, *, title: str = "automata") -> str:
    """Devuelve el SVG completo del grafo.

    Args:
        graph: Grafo del automata.
        title: Titulo accesible del dibujo.

    Returns:
        Un documento SVG autocontenido.
    """
    colocados, ancho, alto = _place(graph)
    por_clave = {nodo.key: nodo for nodo in colocados}

    pares = {(arista.source, arista.target) for arista in graph.edges}
    dobles = {
        (origen, destino)
        for origen, destino in pares
        if origen != destino and (destino, origen) in pares
    }

    cuerpo: list[str] = []
    for arista in graph.edges:
        origen = por_clave[arista.source]
        destino = por_clave[arista.target]
        if arista.source == arista.target:
            cuerpo.extend(_self_loop(origen, arista.label))
        else:
            cuerpo.extend(
                _edge(origen, destino, arista, _curvature(origen, destino, dobles))
            )

    for nodo in colocados:
        relleno = _START_FILL if nodo.start else _NODE_FILL
        cuerpo.append(
            f'<ellipse cx="{nodo.x:.1f}" cy="{nodo.y:.1f}" rx="{nodo.rx:.1f}" '
            f'ry="{nodo.ry:.1f}" fill="{relleno}" stroke="{_STROKE}" stroke-width="1.5"/>'
        )
        if nodo.accepting:
            cuerpo.append(
                f'<ellipse cx="{nodo.x:.1f}" cy="{nodo.y:.1f}" '
                f'rx="{nodo.rx - 4.5:.1f}" ry="{nodo.ry - 4.5:.1f}" '
                f'fill="none" stroke="{_STROKE}" stroke-width="1.5"/>'
            )
        cuerpo.append(
            f'<text x="{nodo.x:.1f}" y="{nodo.y + 4.5:.1f}" text-anchor="middle" '
            f'font-size="{_FONT_SIZE:.0f}" fill="{_TEXT}">{_escape(nodo.label)}</text>'
        )

    # Flecha externa hacia el estado inicial.
    inicial = por_clave[graph.start]
    cuerpo.append(
        f'<circle cx="{inicial.x - inicial.rx - _START_ARROW:.1f}" '
        f'cy="{inicial.y:.1f}" r="3.2" fill="{_STROKE}"/>'
    )
    cuerpo.append(
        f'<path d="M {inicial.x - inicial.rx - _START_ARROW + 4:.1f} {inicial.y:.1f} '
        f'L {inicial.x - inicial.rx - _ARROW_LEN + 1.5:.1f} {inicial.y:.1f}" '
        f'stroke="{_STROKE}" stroke-width="1.4"/>'
    )
    cuerpo.append(_arrow_head(inicial.x - inicial.rx, inicial.y, 1.0, 0.0))

    encabezado = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho:.0f}" '
        f'height="{alto:.0f}" viewBox="0 0 {ancho:.0f} {alto:.0f}" '
        f'font-family="Helvetica, Arial, sans-serif">',
        f"<title>{_escape(title)}</title>",
        f'<rect width="{ancho:.0f}" height="{alto:.0f}" fill="white"/>',
    )
    return "\n".join([*encabezado, *cuerpo, "</svg>"]) + "\n"


def nfa_to_svg(nfa: NFA, *, title: str = "AFN") -> str:
    """Devuelve el SVG del AFN."""
    return graph_to_svg(nfa_to_graph(nfa), title=title)


def dfa_to_svg(dfa: DFA, *, title: str = "AFD") -> str:
    """Devuelve el SVG del AFD."""
    return graph_to_svg(dfa_to_graph(dfa), title=title)
