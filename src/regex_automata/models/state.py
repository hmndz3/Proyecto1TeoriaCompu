"""Estados de un AFN y fabrica de identificadores."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class State:
    """Estado de un automata finito no determinista.

    La identidad logica es el entero ``identifier``. La etiqueta ``q0``, ``q1``
    y demas pertenece a la presentacion y se deriva de el.
    """

    identifier: int

    @property
    def label(self) -> str:
        return f"q{self.identifier}"

    def __str__(self) -> str:  # pragma: no cover - delegacion trivial
        return self.label


class StateFactory:
    """Genera estados con identificadores consecutivos y estables."""

    def __init__(self, start: int = 0) -> None:
        self._next = start

    def new_state(self) -> State:
        """Crea y devuelve un estado nuevo."""
        state = State(self._next)
        self._next += 1
        return state

    @property
    def created(self) -> int:
        """Cantidad de estados creados hasta ahora."""
        return self._next
