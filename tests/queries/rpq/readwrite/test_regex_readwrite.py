import os
import tempfile

import pytest

import flpq_data


@pytest.mark.parametrize(
    "expression, expected, not_expected",
    [
        # symbols and concatenation
        ("friend", [["friend"]], [[]]),
        ("a b c", [["a", "b", "c"]], [["a", "c"], ["a", "b"]]),
        # union
        ("abc|d*", [["abc"], ["d", "d", "d"], []], [["a"], ["a", "d"]]),
        # union has the lowest precedence: a | b c == a | (b c)
        ("a|b c", [["a"], ["b", "c"]], [["b"], ["c"], []]),
        # star
        ("a b*", [["a"], ["a", "b", "b"]], [["b"], []]),
        # plus is Kleene-plus: a+ == a a*
        ("a+", [["a"], ["a", "a", "a"]], [[]]),
        ("(a|b)+", [["a"], ["b"], ["a", "b"]], [[]]),
        # epsilon
        ("$", [[]], [["a"]]),
        ("$|a", [[], ["a"]], [["a", "a"]]),
        ("a $", [["a"]], [[]]),
        # grouping
        ("(a|b)*", [[], ["a"], ["b"], ["a", "b"]], [["c"]]),
        ("(a b)*", [[], ["a", "b"], ["a", "b", "a", "b"]], [["a"], ["b"]]),
        # stacked postfix: a** == (a*)*
        ("a**", [[], ["a"], ["a", "a"]], [["b"]]),
        # the #183 yago2s query (Kleene-plus expanded by the contributor)
        (
            "isMarriedTo livesIn isLocatedIn isLocatedIn* dealsWith dealsWith*",
            [
                ["isMarriedTo", "livesIn", "isLocatedIn", "dealsWith"],
                [
                    "isMarriedTo",
                    "livesIn",
                    "isLocatedIn",
                    "isLocatedIn",
                    "dealsWith",
                    "dealsWith",
                ],
            ],
            [["isMarriedTo", "livesIn", "dealsWith"]],
        ),
    ],
)
def test_regex_from_text_membership(expression, expected, not_expected):
    regex = flpq_data.regex_from_text(expression)

    for word in expected:
        assert regex.accepts(word)

    for word in not_expected:
        assert not regex.accepts(word)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("friend", "friend"),
        ("a b c", "a b c"),
        ("abc|d*", "abc | d*"),
        ("a (bc|d*)", "a (bc | d*)"),
        ("a|b c", "a | b c"),
        ("(a|b)*", "(a | b)*"),
        ("a+", "a a*"),
        ("(a|b)+", "(a | b) (a | b)*"),
        ("$", "$"),
        ("$|a", "$ | a"),
        ("a $", "a $"),
        ("a**", "a**"),
        ("(a|b)*c", "(a | b)* c"),
        ("a (b|c d) e", "a (b | c d) e"),
    ],
)
def test_regex_to_text(expression, expected):
    regex = flpq_data.regex_from_text(expression)

    assert flpq_data.regex_to_text(regex) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "friend",
        "a b c",
        "abc|d*",
        "a (bc|d*)",
        "a|b c",
        "(a|b)*",
        "a+",
        "(a|b)+",
        "$",
        "$|a",
        "a $",
        "a**",
        "(a|b)*c",
        "a (b|c d) e",
        "isMarriedTo livesIn isLocatedIn isLocatedIn* dealsWith dealsWith*",
    ],
)
def test_round_trip(expression):
    regex = flpq_data.regex_from_text(expression)
    text = flpq_data.regex_to_text(regex)

    # idempotence
    assert flpq_data.regex_to_text(flpq_data.regex_from_text(text)) == text

    # language preservation
    for word in ([], ["a"], ["b"], ["c"], ["a", "b"], ["a", "a"], ["b", "c"]):
        assert regex.accepts(word) == flpq_data.regex_from_text(text).accepts(word)


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "   ",
        "(",
        ")",
        "a)",
        "(a",
        "|a",
        "a|",
        "a||b",
        "*a",
        "+a",
        "a|*",
        "a|+",
        "(a|)",
        "a (b",
    ],
)
def test_regex_from_text_errors(expression):
    with pytest.raises(ValueError, match=".*"):
        flpq_data.regex_from_text(expression)


def test_regex_from_and_to_txt():
    (fd, fname) = tempfile.mkstemp()

    regex_1 = flpq_data.regex_from_text("a (bc|d*)")

    path = flpq_data.regex_to_txt(regex_1, fname)

    regex_2 = flpq_data.regex_from_txt(path)

    os.close(fd)
    os.unlink(fname)

    assert flpq_data.regex_to_text(regex_1) == flpq_data.regex_to_text(regex_2)
