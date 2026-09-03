"""Modelo de Automata Finito No Determinista."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from ..constants import EPSILON, display_symbol
from .state import State


@dataclass(frozen=True)
class NFA:
    """AFN con transiciones epsilon.

    La funcion de transicion se modela como ``(origen, simbolo) -> conjunto de
    destinos``. Epsilon se representa con la constante interna
    :data:`~regex_automata.constants.EPSILON` y no forma parte del alfabeto.
    """

    states: frozenset[State]
    alphabet: frozenset[str]
    start: State
    accepting: frozenset[State]
    transitions: dict[tuple[State, str], frozenset[State]]

    # -- consultas --------------------------------------------------------- #

    def destinations(self, state: State, symbol: str) -> frozenset[State]:
        """Estados alcanzables desde ``state`` consumiendo ``symbol``."""
        return self.transitions.get((state, symbol), frozenset())

    def epsilon_destinations(self, state: State) -> frozenset[State]:
        """Estados alcanzables desde ``state`` con una sola transicion epsilon."""
        return self.destinations(state, EPSILON)

    def is_accepting(self, state: State) -> bool:
        return state in self.accepting

    @property
    def sorted_states(self) -> list[State]:
        return sorted(self.states)

    @property
    def sorted_alphabet(self) -> list[str]:
        return sorted(self.alphabet)

    @property
    def state_count(self) -> int:
        return len(self.states)

    @property
    def transition_count(self) -> int:
        return sum(len(destinos) for destinos in self.transitions.values())

    def iter_transitions(self) -> Iterator[tuple[State, str, frozenset[State]]]:
        """Recorre las transiciones en orden determinista."""
        for (origen, simbolo) in sorted(
            self.transitions, key=lambda clave: (clave[0].identifier, clave[1])
        ):
            yield origen, simbolo, self.transitions[(origen, simbolo)]

    def describe_set(self, states: Iterable[State]) -> str:
        """Formatea un conjunto de estados como ``{q0,q1}``."""
        return "{" + ",".join(estado.label for estado in sorted(states)) + "}"

    def __str__(self) -> str:  # pragma: no cover - solo depuracion
        lineas = [
            f"AFN con {self.state_count} estados, inicial {self.start.label}",
            f"  alfabeto: {{{','.join(self.sorted_alphabet)}}}",
            f"  aceptacion: {self.describe_set(self.accepting)}",
        ]
        for origen, simbolo, destinos in self.iter_transitions():
            etiqueta = display_symbol(simbolo)
            lineas.append(f"  {origen.label} --{etiqueta}--> {self.describe_set(destinos)}")
        return "\n".join(lineas)


@dataclass
class NFABuilder:
    """Acumulador mutable usado durante la construccion de Thompson.

    Mantener la mutabilidad aqui permite que :class:`NFA` sea inmutable.
    """

    transitions: dict[tuple[State, str], set[State]] = field(default_factory=dict)
    states: set[State] = field(default_factory=set)
    alphabet: set[str] = field(default_factory=set)

    def register(self, *states: State) -> None:
        """Declara estados aunque todavia no tengan transiciones."""
        self.states.update(states)

    def add_transition(self, source: State, symbol: str, target: State) -> None:
        """Agrega ``source --symbol--> target``."""
        self.states.add(source)
        self.states.add(target)
        if symbol != EPSILON:
            self.alphabet.add(symbol)
        self.transitions.setdefault((source, symbol), set()).add(target)

    def add_epsilon(self, source: State, target: State) -> None:
        """Agrega una transicion epsilon."""
        self.add_transition(source, EPSILON, target)

    def build(self, start: State, accepting: Iterable[State]) -> NFA:
        """Congela el acumulador en un :class:`NFA` inmutable."""
        finales = frozenset(accepting)
        self.states.add(start)
        self.states.update(finales)
        return NFA(
            states=frozenset(self.states),
            alphabet=frozenset(self.alphabet),
            start=start,
            accepting=finales,
            transitions={
                clave: frozenset(destinos) for clave, destinos in self.transitions.items()
            },
        )
