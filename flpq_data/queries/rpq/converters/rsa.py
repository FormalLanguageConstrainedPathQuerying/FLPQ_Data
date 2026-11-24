"""Convert between regular expressions and regular RSMs."""

import logging

from pyformlang.finite_automaton import DeterministicFiniteAutomaton, Symbol
from pyformlang.regular_expression import Regex
from pyformlang.rsa import Box
from pyformlang.rsa import RecursiveAutomaton as RSA

from flpq_data.queries.rpq.readwrite.regex import regex_from_text
from flpq_data.queries.rpq.readwrite.rsa import _box_body

__all__ = [
    "regex_to_rsa",
    "rsa_to_regex",
]


def regex_to_rsa(regex: Regex, *, box_name: str = "S") -> RSA:
    """Create a regular RSM [1]_ from a regular expression.

    The RSM has a single box whose DFA is the minimized epsilon-NFA of
    the regex, so the box language equals the regex language. This is a
    one-way derivation aid: an RSM remains a first-class, independently
    specifiable representation — the archive checker couples ``.re`` and
    ``.rsm`` files only at terminal-set consistency and regularity, so an
    RSM that is not an exact copy of the regex-derived one remains valid.

    Parameters
    ----------
    regex : Regex
        Regular expression.

    box_name : str, optional
        The name of the single box (and the initial label).
        Default: ``"S"``.

    Examples
    --------
    >>> from flpq_data import *
    >>> rsa = regex_to_rsa(regex_from_text("a* b"))
    >>> len(rsa.boxes)
    1
    >>> cfg = cfg_from_rsa(rsa)
    >>> cfg.contains("aab")
    True
    >>> cfg.contains("b")
    False

    Returns
    -------
    rsa : RSA
        Regular State Machine.

    References
    ----------
    .. [1] Alur R., Etessami K., Yannakakis M. (2001) Analysis of Recursive
        State Machines.
        In: Berry G., Comon H., Finkel A. (eds) Computer Aided Verification. CAV 2001.
        Lecture Notes in Computer Science, vol 2102.
        Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-44585-4_18
    """
    dfa = regex.to_epsilon_nfa().minimize()
    label = Symbol(box_name)
    rsa = RSA(labels={label}, initial_label=label, boxes={Box(dfa, label)})

    logging.info(f"Create {rsa=} from {regex=}, {box_name=}")

    return rsa


def rsa_to_regex(rsa: RSA) -> Regex:
    """Create a regular expression from a regular RSM.

    The RSM must have exactly one box, its automaton must be a
    deterministic finite automaton, and it must not be recursive (no
    transition labelled by the box's own label). The result is the
    canonical regular expression of the box language, so
    ``regex_to_rsa(rsa_to_regex(rsa))`` reproduces the box language.

    Parameters
    ----------
    rsa : RSA
        Regular State Machine.

    Examples
    --------
    >>> from flpq_data import *
    >>> rsa = regex_to_rsa(regex_from_text("a* b"))
    >>> regex_to_text(rsa_to_regex(rsa))
    '((a)* b)'

    Returns
    -------
    regex : Regex
        Regular expression.

    Raises
    ------
    ValueError
        If the RSM has more than one box, the box's automaton is not a
        deterministic finite automaton, or the box is recursive.

    References
    ----------
    .. [1] Alur R., Etessami K., Yannakakis M. (2001) Analysis of Recursive
        State Machines.
        In: Berry G., Comon H., Finkel A. (eds) Computer Aided Verification. CAV 2001.
        Lecture Notes in Computer Science, vol 2102.
        Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-44585-4_18
    """
    if len(rsa.boxes) != 1:
        raise ValueError(f"the RSM must have exactly one box (it has {len(rsa.boxes)})")
    box = next(iter(rsa.boxes.values()))
    if not isinstance(box.dfa, DeterministicFiniteAutomaton):
        raise ValueError("the box's automaton is not deterministic")
    if box.label in box.dfa.symbols:
        raise ValueError("the box is recursive (a transition is labelled by it)")

    regex = regex_from_text(_box_body(box))

    logging.info(f"Create {regex=} from {rsa=}")

    return regex
