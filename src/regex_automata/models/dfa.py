"""Modelo de Automata Finito Determinista."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DFAState:
    """Estado de un AFD.

    Solo ``identifier`` participa en la igualdad y el hash: la etiqueta y los
    miembros son informacion de presentacion y de trazabilidad, no identidad.

    Attributes:
        identifier: Identificador interno estable.
        label: Nombre visible (``A``, ``B``, ``{A,B}``...).
        members: Nombres de los estados de origen que dieron lugar a este
            estado, util para explicar subconjuntos y clases de equivalencia.
    """

    identifier: int
    label: str = field(compare=False, default="")
    members: frozenset[str] = field(compare=False, default=frozenset())

    @property
    def members_label(self) -> str:
        """Miembros ordenados con formato ``{q0,q1}``."""
        if not self.members:
            return self.label
        return "{" + ",".join(sorted(self.members)) + "}"

    def __str__(self) -> str:  # pragma: no cover - delegacion trivial
        return self.label

    def __lt__(self, other: DFAState) -> bool:
        return self.identifier < other.identifier


@dataclass(frozen=True)
class DFA:
    """AFD con una transicion como maximo por par estado-simbolo.

    Un AFD puede ser parcial: ``transitions`` no necesita cubrir todos los
    pares. La preparacion previa a la minimizacion se encarga de completarlo.
    """

    states: frozenset[DFAState]
    alphabet: frozenset[str]
    start: DFAState
    accepting: frozenset[DFAState]
    transitions: dict[tuple[DFAState, str], DFAState]

    # -- consultas --------------------------------------------------------- #

    def transition(self, state: DFAState, symbol: str) -> DFAState | None:
        """Destino de ``state`` con ``symbol``, o ``None`` si no esta definido."""
        return self.transitions.get((state, symbol))

    def is_accepting(self, state: DFAState) -> bool:
        return state in self.accepting

    @property
    def sorted_states(self) -> list[DFAState]:
        return sorted(self.states, key=lambda estado: estado.identifier)

    @property
    def sorted_alphabet(self) -> list[str]:
        return sorted(self.alphabet)

    @property
    def state_count(self) -> int:
        return len(self.states)

    @property
    def is_complete(self) -> bool:
        """``True`` si hay transicion definida para todo par estado-simbolo."""
        return all(
            (estado, simbolo) in self.transitions
            for estado in self.states
            for simbolo in self.alphabet
        )

    def iter_transitions(self) -> Iterator[tuple[DFAState, str, DFAState]]:
        """Recorre las transiciones en orden determinista."""
        for (origen, simbolo) in sorted(
            self.transitions, key=lambda clave: (clave[0].identifier, clave[1])
        ):
            yield origen, simbolo, self.transitions[(origen, simbolo)]

    def reachable_states(self) -> frozenset[DFAState]:
        """Estados alcanzables desde el inicial."""
        vistos: set[DFAState] = {self.start}
        pendientes: list[DFAState] = [self.start]
        while pendientes:
            actual = pendientes.pop()
            for simbolo in self.sorted_alphabet:
                destino = self.transition(actual, simbolo)
                if destino is not None and destino not in vistos:
                    vistos.add(destino)
                    pendientes.append(destino)
        return frozenset(vistos)

    def describe_set(self, states: Iterable[DFAState]) -> str:
        return "{" + ",".join(estado.label for estado in sorted(states)) + "}"

    def __str__(self) -> str:  # pragma: no cover - solo depuracion
        lineas = [
            f"AFD con {self.state_count} estados, inicial {self.start.label}",
            f"  alfabeto: {{{','.join(self.sorted_alphabet)}}}",
            f"  aceptacion: {self.describe_set(self.accepting)}",
        ]
        for origen, simbolo, destino in self.iter_transitions():
            lineas.append(f"  {origen.label} --{simbolo}--> {destino.label}")
        return "\n".join(lineas)
