from typing import cast

import pytest
from pyformlang.cfg import Terminal

import flpq_data

grammar_1 = "S -> a b"
grammar_2 = "S -> a"
grammar_3 = "S -> a\nS -> b"
grammar_4 = "S -> \n#comment"

transition_system_1 = "start: S\n[box S]\nstart: 0\nfinal: 2\n0 --a--> 1\n1 --b--> 2"
transition_system_2 = (
    "start: S\n"
    "[box S]\n"
    "start: 0\n"
    "final: 3\n"
    "0 --a--> 1\n"
    "1 --S--> 2\n"
    "2 --b--> 3\n"
    "1 --b--> 3"
)
transition_system_3 = (
    "start: B\n[box S]\nstart: 0\nfinal: 0\n[box B]\nstart: 0\nfinal: 1\n0 --x--> 1"
)


@pytest.mark.parametrize(
    "grammar, expected",
    [
        (grammar_1, ["ab"]),
        (grammar_2, ["a"]),
        (grammar_3, ["a", "b"]),
        (grammar_4, [""]),
    ],
)
def test_rsa_from_text(grammar, expected):
    rsa = flpq_data.rsa_from_text(grammar)
    cfg_from_rsa = flpq_data.cfg_from_rsa(rsa)

    for word in expected:
        if word is not None:
            assert cfg_from_rsa.contains(word)


@pytest.mark.parametrize(
    "grammar, expected",
    [
        (grammar_1, {"S -> ($ (a b))"}),
        (grammar_2, {"S -> ($ a)"}),
        (grammar_3, {"S -> ($ (a|b))", "S -> ($ (b|a))"}),
        (grammar_4, {"S -> $"}),
    ],
)
def test_rsa_to_text(grammar, expected):
    rsa = flpq_data.rsa_from_text(grammar)

    actual = set(flpq_data.rsa_to_text(rsa).splitlines())

    assert actual.issubset(expected)


def test_ebnf_body_plus_is_kleene_plus():
    rsa = flpq_data.rsa_from_text("S -> a+")
    cfg = flpq_data.cfg_from_rsa(rsa)

    assert cfg.contains(cast("list[Terminal]", "a"))
    assert cfg.contains(cast("list[Terminal]", "aaa"))
    assert not cfg.contains(cast("list[Terminal]", ""))


def test_empty_production_has_no_phantom_terminal():
    rsa = flpq_data.rsa_from_text("S ->")
    cfg = flpq_data.cfg_from_rsa(rsa)

    assert cfg.contains(cast("list[Terminal]", ""))
    assert cfg.terminals == set()


def test_round_trip_non_default_start_box():
    rsa = flpq_data.rsa_from_text("start: B\nB -> x\nS -> y")
    canonical = flpq_data.rsa_to_text(rsa)

    assert canonical.startswith("start: B")
    rsa_2 = flpq_data.rsa_from_text(canonical)
    assert rsa_2.initial_label.value == "B"


def test_ebnf_undefined_start_box_raises():
    with pytest.raises(ValueError, match="Start box"):
        flpq_data.rsa_from_text("start: X\nS -> a")


@pytest.mark.parametrize(
    "grammar",
    [
        "S -> a*",
        "S -> a+",
        "S ->",
        "S -> a | b",
        "S -> (a | b)*",
        "S -> a b c",
        "S -> a* b S c",
        "S -> (a S* b S*)*",
        "S -> a+ | $",
    ],
)
def test_rsa_to_text_round_trip_preserves_languages(grammar):
    rsa = flpq_data.rsa_from_text(grammar)
    canonical = flpq_data.rsa_to_text(rsa)
    rsa_2 = flpq_data.rsa_from_text(canonical)

    words = ["", "a", "b", "c", "aa", "ab", "abc", "aab", "aabb", "aaaa"]
    for label in rsa.labels:
        box_1 = rsa.get_box(label)
        box_2 = rsa_2.get_box(label)
        for word in words:
            assert box_1.dfa.accepts(word) == box_2.dfa.accepts(word)


@pytest.mark.parametrize(
    "text, expected",
    [
        (transition_system_1, ["ab"]),
        (transition_system_2, ["ab", "aabb"]),
        (transition_system_3, ["x"]),
    ],
)
def test_rsa_from_text_transition_system(text, expected):
    rsa = flpq_data.rsa_from_text(text)
    cfg = flpq_data.cfg_from_rsa(rsa)

    for word in expected:
        assert cfg.contains(word)


@pytest.mark.parametrize(
    "text, rejected",
    [
        (transition_system_1, ["a", "b", "aba"]),
        (transition_system_2, ["aab", "abab", ""]),
        (transition_system_3, ["", "xx"]),
    ],
)
def test_rsa_from_text_transition_system_rejects(text, rejected):
    rsa = flpq_data.rsa_from_text(text)
    cfg = flpq_data.cfg_from_rsa(rsa)

    for word in rejected:
        assert not cfg.contains(word)


@pytest.mark.parametrize(
    "text",
    [
        transition_system_1,
        transition_system_2,
        transition_system_3,
    ],
)
def test_rsa_to_text_transition_system_round_trip(text):
    rsa = flpq_data.rsa_from_text(text)
    canonical = flpq_data.rsa_to_text(rsa)

    assert flpq_data.rsa_from_text(canonical) == rsa


@pytest.mark.parametrize(
    "text",
    [
        "[box S]\nstart: 0\nfinal: 0\n[box S]\nstart: 1\nfinal: 1",
        "[box S]\nfinal: 1\n0 --a--> 1",
        "[box S]\nstart: 0\nfinal: 1\n0 --a--> 1\n0 --a--> 2",
        "start: X\n[box S]\nstart: 0\nfinal: 0",
        "garbage\n[box S]\nstart: 0\nfinal: 0",
    ],
)
def test_rsa_from_text_transition_system_errors(text):
    with pytest.raises(ValueError):
        flpq_data.rsa_from_text(text)


def test_rsa_from_text_start_header():
    rsa = flpq_data.rsa_from_text("start: B\nB -> x")

    assert rsa.initial_label.value == "B"
