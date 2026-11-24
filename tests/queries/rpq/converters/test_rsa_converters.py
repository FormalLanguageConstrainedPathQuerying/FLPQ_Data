from typing import cast

import pytest
from pyformlang.cfg import Terminal
from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    EpsilonNFA,
    Symbol,
)
from pyformlang.rsa import Box
from pyformlang.rsa import RecursiveAutomaton as RSA

import flpq_data

WORDS = ["", "a", "b", "c", "e", "aa", "ab", "abc", "aab", "aaab", "abe", "acde"]

EXPRESSIONS = [
    "a",
    "a b c",
    "a | b",
    "a*",
    "a+",
    "$",
    "$ | a",
    "(a | b)*",
    "a* b",
    "a (b | c d) e",
]


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_regex_to_rsa_preserves_language(expression):
    regex = flpq_data.regex_from_text(expression)
    rsa = flpq_data.regex_to_rsa(regex)
    cfg = flpq_data.cfg_from_rsa(rsa)

    for word in WORDS:
        assert cfg.contains(cast("list[Terminal]", word)) == regex.accepts(list(word))


def test_regex_to_rsa_single_box_shape():
    rsa = flpq_data.regex_to_rsa(flpq_data.regex_from_text("a*"))

    assert len(rsa.boxes) == 1
    box = next(iter(rsa.boxes.values()))
    assert box.label.value == "S"
    assert rsa.initial_label.value == "S"
    assert isinstance(box.dfa, DeterministicFiniteAutomaton)


def test_regex_to_rsa_box_name():
    rsa = flpq_data.regex_to_rsa(flpq_data.regex_from_text("a*"), box_name="Q")

    box = next(iter(rsa.boxes.values()))
    assert box.label.value == "Q"
    assert rsa.initial_label.value == "Q"


@pytest.mark.parametrize("expression", EXPRESSIONS)
def test_rsa_to_regex_round_trip(expression):
    regex = flpq_data.regex_from_text(expression)
    rsa = flpq_data.regex_to_rsa(regex)
    regex_2 = flpq_data.rsa_to_regex(rsa)

    for word in WORDS:
        assert regex.accepts(list(word)) == regex_2.accepts(list(word))


def test_rsa_to_regex_multi_box_raises():
    rsa = flpq_data.rsa_from_text("S -> a\nB -> b")

    with pytest.raises(ValueError, match="exactly one box"):
        flpq_data.rsa_to_regex(rsa)


def test_rsa_to_regex_recursive_raises():
    rsa = flpq_data.rsa_from_text("S -> a S b | a b")

    with pytest.raises(ValueError, match="recursive"):
        flpq_data.rsa_to_regex(rsa)


def test_rsa_to_regex_non_dfa_box_raises():
    # An empty automaton is the only way to get a non-deterministic dfa:
    # Box.__init__ minimizes any non-empty automaton it is given, and the
    # minimized empty DFA is falsy, so Box falls back to an empty EpsilonNFA.
    label = Symbol("S")
    rsa = RSA(labels={label}, initial_label=label, boxes={Box(EpsilonNFA(), label)})

    with pytest.raises(ValueError, match="not deterministic"):
        flpq_data.rsa_to_regex(rsa)
