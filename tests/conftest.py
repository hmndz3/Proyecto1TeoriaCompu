"""Utilidades compartidas por las pruebas."""

from __future__ import annotations

import pytest

from regex_automata.algorithms.dfa_preparation import prepare_for_minimization
from regex_automata.algorithms.subset_construction import build_dfa
from regex_automata.algorithms.thompson import build_nfa
from regex_automata.models.nfa import NFA
from regex_automata.models.token import Token
from regex_automata.regex.concatenation import insert_explicit_concatenation
from regex_automata.regex.shunting_yard import postfix_to_string, to_postfix
from regex_automata.regex.tokenizer import tokenize
from regex_automata.regex.validator import validate


def parse(expression: str) -> list[Token]:
    """Tokeniza, valida e inserta la concatenacion explicita."""
    tokens = tokenize(expression)
    validate(tokens, expression)
    return insert_explicit_concatenation(tokens)


def postfix(expression: str) -> str:
    """Devuelve el postfix imprimible de una expresion."""
    return postfix_to_string(to_postfix(parse(expression), expression=expression))


def nfa_of(expression: str) -> NFA:
    """Construye el AFN de una expresion."""
    return build_nfa(to_postfix(parse(expression), expression=expression))


def prepared_dfa_of(expression: str):
    """Construye el AFD preparado (accesible y completo) de una expresion."""
    return prepare_for_minimization(build_dfa(nfa_of(expression)).dfa).dfa


@pytest.fixture()
def enunciado() -> str:
    """Expresion de ejemplo del enunciado del proyecto."""
    return "(b|b)*abb(a|b)*"
