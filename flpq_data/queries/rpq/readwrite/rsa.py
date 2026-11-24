"""Read (and write) a Recursive State Automaton from (and to) different sources."""

import logging
import pathlib
import re
from dataclasses import dataclass, field
from typing import Optional, Union

from pyformlang.finite_automaton import (
    EpsilonNFA,
    NondeterministicTransitionFunction,
    Symbol,
)
from pyformlang.finite_automaton.finite_automaton import to_state, to_symbol
from pyformlang.rsa import Box
from pyformlang.rsa import RecursiveAutomaton as RSA

from flpq_data.queries.rpq.readwrite.regex import regex_from_text

__all__ = [
    "rsa_from_text",
    "rsa_to_text",
    "rsa_from_txt",
    "rsa_to_txt",
]

_BOX_HEADER_RE = re.compile(r"^\[box\s+(\S+)\]$")
_START_RE = re.compile(r"^start:\s*(\S+)$")
_FINAL_RE = re.compile(r"^final:\s*(.+)$")
_TRANSITION_RE = re.compile(r"^(\S+)\s*--(.+?)-->\s*(\S+)$")

#: The default name of the start box when no ``start:`` line is given.
_DEFAULT_START = "S"


def rsa_from_text(text: str, *, start_symbol: Symbol = Symbol("S")) -> RSA:
    """Create a Recursive State Automaton [1]_ from text.

    The text uses one of two description styles, selected automatically:

    - EBNF style: one production per line, ``N -> E``, where ``E`` is a
      regular expression over terminals and nonterminals in the canonical
      regular expression syntax of :func:`regex_from_text
      <flpq_data.queries.rpq.readwrite.regex.regex_from_text>`; each
      production becomes one box. An empty body is the empty word
      (epsilon).
    - Transition-system style: explicit boxes as labelled graphs with start
      and final states (a ``[box <name>]`` section header selects this
      style).

    In both styles an optional ``start: <N>`` line names the start box
    (``S`` by default).

    Parameters
    ----------
    text : str
        The text with which the Recursive State Machine will be created.

    start_symbol : Symbol
        Start symbol of a Recursive State Machine.

    Examples
    --------
    >>> from flpq_data import *
    >>> rsa = rsa_from_text("S -> a*")
    >>> cfg_to_text(cfg_from_rsa(rsa))
    'S -> \\nS -> a S'

    ``+`` is Kleene-plus and an empty production is the empty word:

    >>> rsa = rsa_from_text("S -> a+")
    >>> cfg = cfg_from_rsa(rsa)
    >>> cfg.contains("")
    False
    >>> cfg.contains("aa")
    True
    >>> rsa = rsa_from_text("S ->")
    >>> cfg_from_rsa(rsa).contains("")
    True
    >>> cfg_from_rsa(rsa).terminals
    set()

    >>> rsa = rsa_from_text(
    ...     "start: S\\n"
    ...     "[box S]\\n"
    ...     "start: 0\\n"
    ...     "final: 2\\n"
    ...     "0 --a--> 1\\n"
    ...     "1 --b--> 2"
    ... )
    >>> cfg_to_text(cfg_from_rsa(rsa))
    'S -> a S_1\\nS_1 -> b S_2\\nS_2 -> '

    Returns
    -------
    rsa : RSA
        Recursive State Automaton.

    References
    ----------
    .. [1] Alur R., Etessami K., Yannakakis M. (2001) Analysis of Recursive
       State Machines.
       In: Berry G., Comon H., Finkel A. (eds) Computer Aided Verification. CAV 2001.
       Lecture Notes in Computer Science, vol 2102.
       Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-44585-4_18
    """
    if any(_BOX_HEADER_RE.match(line.strip()) for line in text.splitlines()):
        return _rsa_from_transition_system(text, start_symbol)

    productions = dict()
    labels = set()

    for production in text.splitlines():
        line = production.strip()
        if not line or line.startswith("#"):
            continue

        start_match = _START_RE.match(line)
        if start_match is not None:
            start_symbol = to_symbol(start_match.group(1))
            continue

        if "->" not in line:
            continue

        head, body = line.split("->", 1)
        head = head.strip()
        body = body.strip()
        labels.add(to_symbol(head))

        if body == "":
            body = "$"

        if head in productions:
            productions[head] += " | " + body
        else:
            productions[head] = body

    if start_symbol.value not in productions:
        raise ValueError(f"Start box {start_symbol.value} is not defined")

    boxes = set()

    for head, body in productions.items():
        nfa = regex_from_text(body).to_epsilon_nfa()
        if nfa is None:
            raise ValueError(f"Cannot build an epsilon NFA for {body=}")
        boxes.add(Box(nfa.minimize(), to_symbol(head)))

    rsa = RSA(labels=labels, initial_label=start_symbol, boxes=boxes)

    logging.info(f"Create {rsa=} from {text=}, {start_symbol=}")

    return rsa


@dataclass
class _BoxParse:
    """The parsed state of one box in the transition-system style."""

    start: Optional[str] = None
    final: set[str] = field(default_factory=set)
    transitions: list[tuple[str, str, str]] = field(default_factory=list)


def _rsa_from_transition_system(text: str, start_symbol: Symbol) -> RSA:
    """Parse the transition-system style of the RSM text format.

    Parameters
    ----------
    text : str
        The text with ``[box <name>]`` sections, each holding a
        ``start:``, an optional ``final:`` line and ``from --label--> to``
        transitions. Boxes are deterministic.

    start_symbol : Symbol
        Start symbol of a Recursive State Machine.

    Returns
    -------
    rsa : RSA
        Recursive State Automaton.
    """
    parsed: dict[str, _BoxParse] = dict()
    current = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        header = _BOX_HEADER_RE.match(line)
        if header is not None:
            name = header.group(1)
            if name in parsed:
                raise ValueError(f"Duplicate box {name}")
            current = name
            parsed[name] = _BoxParse()
            continue

        if current is None:
            start_match = _START_RE.match(line)
            if start_match is not None:
                start_symbol = to_symbol(start_match.group(1))
                continue
            raise ValueError(
                f"Cannot parse line {line!r}: expected a [box <name>] section"
            )

        box = parsed[current]

        start_match = _START_RE.match(line)
        if start_match is not None:
            if box.start is not None:
                raise ValueError(f"Box {current} has multiple start states")
            box.start = start_match.group(1)
            continue

        final_match = _FINAL_RE.match(line)
        if final_match is not None:
            box.final.update(re.split(r"[,\s]+", final_match.group(1)))
            continue

        transition = _TRANSITION_RE.match(line)
        if transition is not None:
            box.transitions.append(
                (
                    transition.group(1),
                    transition.group(2),
                    transition.group(3),
                )
            )
            continue

        raise ValueError(f"Cannot parse line {line!r} in box {current}")

    if not parsed:
        raise ValueError("No [box <name>] sections found")

    boxes = set()

    for name, data in parsed.items():
        if data.start is None:
            raise ValueError(f"Box {name} has no start state")

        states = {data.start} | data.final
        labels = set()
        seen = dict()
        transition_function = NondeterministicTransitionFunction()

        for src, label, dst in data.transitions:
            states.update((src, dst))
            labels.add(label)
            if (src, label) in seen and seen[(src, label)] != dst:
                raise ValueError(
                    f"Box {name} is not deterministic: "
                    f"{src} --{label}--> conflicts with {seen[(src, label)]}"
                )
            seen[(src, label)] = dst
            transition_function.add_transition(
                to_state(src), to_symbol(label), to_state(dst)
            )

        nfa = EpsilonNFA(
            states={to_state(state) for state in states},
            input_symbols={to_symbol(label) for label in labels},
            transition_function=transition_function,
            start_state={to_state(data.start)},
            final_states={to_state(state) for state in data.final},
        )
        boxes.add(Box(nfa.minimize(), to_symbol(name)))

    if start_symbol.value not in parsed:
        raise ValueError(f"Start box {start_symbol.value} is not defined")

    rsa = RSA(
        labels={to_symbol(name) for name in parsed},
        initial_label=start_symbol,
        boxes=boxes,
    )

    logging.info(f"Create {rsa=} from {text=}, {start_symbol=}")

    return rsa


def _box_body(box: Box) -> str:
    """The canonical regex body of a box (the language of its DFA).

    pyformlang's ``to_regex()`` emits ``.`` for concatenation and ``$`` for
    the empty word; the dot is an ordinary symbol character in the canonical
    syntax, so it is replaced with whitespace (concatenation). Box names and
    labels must therefore not contain ``.``.
    """
    return str(box.dfa.to_regex()).replace(".", " ")


def rsa_to_text(rsa: RSA) -> str:
    """Turns a Recursive State Automaton [1]_ into its text representation.

    The output uses the EBNF style with the productions sorted (the initial
    box first, then alphabetically); each body is the canonical regular
    expression of the box's language. A ``start: <N>`` line is emitted when
    the initial box is not the default ``S``, so
    ``rsa_from_text(rsa_to_text(rsa))`` preserves the language of every box
    and the initial box.

    Parameters
    ----------
    rsa : RSA
        Recursive State Automaton.

    Examples
    --------
    >>> from flpq_data import *
    >>> rsa = rsa_from_text("S -> a*")
    >>> rsa_to_text(rsa)
    'S -> (a)*'

    Returns
    -------
    text : str
        Recursive State Automaton text representation.

    References
    ----------
    .. [1] Alur R., Etessami K., Yannakakis M. (2001) Analysis of Recursive
       State Machines.
       In: Berry G., Comon H., Finkel A. (eds) Computer Aided Verification. CAV 2001.
       Lecture Notes in Computer Science, vol 2102.
       Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-44585-4_18
    """
    productions = []

    for symbol in rsa.labels:
        box = rsa.get_box(symbol)
        if box is None:
            raise ValueError(f"RSA has no box for label {symbol.value}")
        productions.append(f"{box.label.value} -> {_box_body(box)}")

    productions.sort(
        key=lambda s: (s.split(" -> ")[0] != rsa.initial_label.value, s),
    )

    lines = []
    if rsa.initial_label.value != _DEFAULT_START:
        lines.append(f"start: {rsa.initial_label.value}")
    lines.extend(productions)

    text = "\n".join(lines)

    logging.info(f"Turn {rsa=} into {text=}")

    return text


def rsa_from_txt(
    path: Union[pathlib.Path, str], *, start_symbol: Symbol = Symbol("S")
) -> RSA:
    """Create a Recursive State Automaton [1]_ from TXT file.

    Parameters
    ----------
    path : Union[Path, str]
        The path to the TXT file with which the Recursive State Machine
        will be created.

    start_symbol : Symbol
        Start symbol of a Recursive State Machine.

    Examples
    --------
    >>> from flpq_data import *
    >>> rsa_1 = rsa_from_text("S -> a*")
    >>> path = rsa_to_txt(rsa_1, "test.txt")
    >>> rsa = rsa_from_txt(path)
    >>> rsa_to_text(rsa)
    'S -> (a)*'

    Returns
    -------
    rsa : RSA
        Recursive State Automaton.

    References
    ----------
    .. [1] Alur R., Etessami K., Yannakakis M. (2001) Analysis of Recursive
       State Machines.
       In: Berry G., Comon H., Finkel A. (eds) Computer Aided Verification. CAV 2001.
       Lecture Notes in Computer Science, vol 2102.
       Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-44585-4_18
    """
    with open(path, "r") as f:
        productions = f.read()

    rsa = rsa_from_text(productions, start_symbol=start_symbol)

    logging.info(f"Create {rsa=} from {path=}, {start_symbol=}")

    return rsa


def rsa_to_txt(rsa: RSA, path: Union[pathlib.Path, str]) -> pathlib.Path:
    """Saves a Recursive State Automaton text representation into TXT file.

    Parameters
    ----------
    rsa : RSA
        Recursive State Automaton.

    path : Union[Path, str]
        The path to the TXT file where Recursive State Machine
        text representation will be saved.

    Examples
    --------
    >>> from flpq_data import *
    >>> rsa = rsa_from_text("S -> (a S* b S*)*")
    >>> path = rsa_to_txt(rsa, "test.txt")

    Returns
    -------
    path : Path
        The path to the TXT file where Recursive State Automaton
        text representation will be saved.

    References
    ----------
    .. [1] Alur R., Etessami K., Yannakakis M. (2001) Analysis of Recursive
       State Machines.
       In: Berry G., Comon H., Finkel A. (eds) Computer Aided Verification. CAV 2001.
       Lecture Notes in Computer Science, vol 2102.
       Springer, Berlin, Heidelberg. https://doi.org/10.1007/3-540-44585-4_18
    """
    with open(path, "w") as f:
        f.write(rsa_to_text(rsa))

    dest = pathlib.Path(path).resolve()

    logging.info(f"Save {rsa=} to {dest=}")

    return dest
