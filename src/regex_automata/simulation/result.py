"""Estructuras de resultado de una simulacion.

Los simuladores no imprimen: devuelven datos. La presentacion es responsabilidad
de la CLI y del generador de resumenes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TraceStep:
    """Un paso de la simulacion.

    Attributes:
        symbol: Simbolo consumido en este paso.
        source: Etiqueta del estado (o conjunto de estados) de partida.
        destination: Etiqueta del estado (o conjunto) de llegada.
    """

    symbol: str
    source: str
    destination: str


@dataclass(frozen=True)
class SimulationResult:
    """Resultado de simular una cadena sobre un automata.

    Attributes:
        automaton: Nombre del automata simulado.
        word: Cadena evaluada.
        accepted: ``True`` si la cadena pertenece al lenguaje.
        trace: Pasos recorridos.
        initial: Etiqueta del estado (o conjunto) inicial.
        rejected_symbol: Simbolo que provoco el rechazo temprano, si lo hubo.
    """

    automaton: str
    word: str
    accepted: bool
    trace: tuple[TraceStep, ...] = field(default_factory=tuple)
    initial: str = ""
    rejected_symbol: str | None = None

    @property
    def answer(self) -> str:
        """Respuesta pedida por el enunciado: ``si`` o ``no``."""
        return "si" if self.accepted else "no"

    def format_trace(self) -> str:
        """Traza legible del recorrido, por ejemplo ``A --b--> C --a--> B``."""
        if not self.trace:
            return f"{self.initial} (sin consumir simbolos)"
        partes = [self.trace[0].source]
        for paso in self.trace:
            partes.append(f"--{paso.symbol}--> {paso.destination}")
        return " ".join(partes)
