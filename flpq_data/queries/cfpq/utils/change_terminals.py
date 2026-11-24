"""Change terminals of a context-free grammar in different formats."""

import logging
import re
from typing import Dict

from pyformlang.cfg import CFG
from pyformlang.regular_expression import Regex
from pyformlang.rsa import RecursiveAutomaton as RSA

from flpq_data.queries.cfpq.readwrite.cfg import cfg_from_text, cfg_to_text
from flpq_data.queries.cfpq.readwrite.cnf import cnf_from_text
from flpq_data.queries.rpq.readwrite.regex import regex_from_text, regex_to_text
from flpq_data.queries.rpq.readwrite.rsa import rsa_from_text, rsa_to_text

__all__ = [
    "change_terminals_in_cfg",
    "change_terminals_in_cnf",
    "change_terminals_in_regex",
    "change_terminals_in_rsa",
]


def change_terminals_in_cfg(cfg: CFG, mapping: Dict[str, str]) -> CFG:
    """Change terminals of a context-free grammar [1]_.

    Parameters
    ----------
    cfg : CFG
        Context-free grammar.

    mapping: Dict[str, str]
        Terminals mapping.

    Examples
    --------
    >>> from flpq_data import *
    >>> cfg = cfg_from_text("S -> a S b S")
    >>> new_cfg = change_terminals_in_cfg(cfg, {"a": "b", "b": "c"})
    >>> cfg_to_text(new_cfg)
    'S -> b S c S'

    Returns
    -------
    cfg : CFG
        Context-free grammar with changed terminals.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Context-free_grammar#Formal_definitions
    """
    regex = re.compile("|".join(map(re.escape, mapping.keys())))
    text = regex.sub(lambda match: mapping[match.group(0)], cfg_to_text(cfg))

    new_cfg = cfg_from_text(text, start_symbol=cfg.start_symbol)

    logging.info(f"Change terminals in {cfg=} with {mapping=} to {new_cfg=}")

    return new_cfg


def change_terminals_in_cnf(cnf: CFG, mapping: Dict[str, str]) -> CFG:
    """Change terminals of a context-free grammar [1]_ in Chomsky normal form.

    Parameters
    ----------
    cnf : CFG
        Context-free grammar
        in Chomsky normal form.

    mapping: Dict[str, str]
        Terminals mapping.

    Examples
    --------
    >>> from flpq_data import *
    >>> cnf = cnf_from_text("S -> a b")
    >>> new_cnf = change_terminals_in_cnf(cnf, {"a": "b", "b": "c"})
    >>> cfg_to_text(new_cnf)
    'S -> b#CNF##CNF# c#CNF##CNF#\\nb#CNF##CNF# -> b#CNF#\\nc#CNF##CNF# -> c#CNF#'

    Returns
    -------
    cnf : CFG
        Context-free grammar in Chomsky normal form with changed terminals.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Chomsky_normal_form
    """
    regex = re.compile("|".join(map(re.escape, mapping.keys())))
    text = regex.sub(lambda match: mapping[match.group(0)], cfg_to_text(cnf))

    new_cnf = cnf_from_text(text, start_symbol=cnf.start_symbol)

    logging.info(f"Change terminals in {cnf=} with {mapping=} to {new_cnf=}")

    return new_cnf


def change_terminals_in_regex(regex: Regex, mapping: Dict[str, str]) -> Regex:
    """Change terminals of a regular expression [1]_.

    Parameters
    ----------
    regex : Regex
        Regular expression.

    mapping: Dict[str, str]
        Terminals mapping.

    Examples
    --------
    >>> from flpq_data import *
    >>> regex = regex_from_text("a (bc|d*)")
    >>> new_regex = change_terminals_in_regex(regex, {"a": "b", "b": "c"})
    >>> regex_to_text(new_regex)
    'b (cc | d*)'

    Returns
    -------
    regex : Regex
        Regular expression with changed terminals.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Regular_expression#Formal_definition
    """
    expr = re.compile("|".join(map(re.escape, mapping.keys())))
    text = expr.sub(lambda match: mapping[match.group(0)], regex_to_text(regex))

    new_regex = regex_from_text(text)

    logging.info(f"Change terminals in {regex=} with {mapping=} to {new_regex=}")

    return new_regex


def change_terminals_in_rsa(rsa: RSA, mapping: Dict[str, str]) -> RSA:
    """Change terminals of a Recursive State Automaton [1]_.

    Parameters
    ----------
    rsa : RSA
        Recursive State Automaton.

    mapping: Dict
        Terminals mapping.

    Examples
    --------
    >>> from flpq_data import *
    >>> rsa = rsa_from_text("S -> a*")
    >>> new_rsa = change_terminals_in_rsa(rsa, {"a": "b"})
    >>> rsa_to_text(new_rsa)
    'S -> (b)*'

    Returns
    -------
    rsa : RSA
        Recursive State Automaton with changed terminals.

    References
    ----------
    .. [1] Alur R., Etessami K., Yannakakis M. (2001) Analysis of Recursive
       State Machines.
       In: Berry G., Comon H., Finkel A. (eds) Computer Aided Verification. CAV 2001.
       Lecture Notes in Computer Science, vol 2102.
       Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-44585-4_18
    """
    regex = re.compile("|".join(map(re.escape, mapping.keys())))
    text = regex.sub(lambda match: mapping[match.group(0)], rsa_to_text(rsa))

    new_rsa = rsa_from_text(text, start_symbol=rsa.initial_label)

    logging.info(f"Change terminals in {rsa=} with {mapping=} to {new_rsa=}")

    return rsa_from_text(text)
