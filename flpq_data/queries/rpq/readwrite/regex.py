"""Read (and write) a regular expression from (and to) different sources."""

import logging
import pathlib
from typing import Optional, Union

from pyformlang.regular_expression import Regex
from pyformlang.regular_expression.regex_objects import Epsilon, Node, Symbol

__all__ = [
    "regex_from_text",
    "regex_to_text",
    "regex_from_txt",
    "regex_to_txt",
]

#: The metacharacters of the canonical syntax; every other character is part
#: of a symbol.
_METACHARACTERS = frozenset("|*+()$")

#: Precedence levels of the canonical syntax (higher binds tighter); they
#: drive the printer's parentheses.
_PRECEDENCE_UNION = 0
_PRECEDENCE_CONCAT = 1
_PRECEDENCE_ATOM = 2


def _tokenize(text: str) -> list[str]:
    """Splits text into tokens: symbols and single metacharacters.

    A symbol is a maximal run of characters outside the metacharacter set;
    whitespace separates tokens and is not a token itself.
    """
    tokens: list[str] = []
    i, n = 0, len(text)
    while i < n:
        char = text[i]
        if char.isspace():
            i += 1
            continue
        if char in _METACHARACTERS:
            tokens.append(char)
            i += 1
            continue
        j = i
        while j < n and not text[j].isspace() and text[j] not in _METACHARACTERS:
            j += 1
        tokens.append(text[i:j])
        i = j
    return tokens


class _RegexParser:
    """Recursive-descent parser of the canonical syntax into a Regex.

    Grammar (precedence: postfix > concatenation > union)::

        expr   := term ('|' term)*
        term   := factor+
        factor := atom postfix*
        atom   := SYMBOL | '$' | '(' expr ')'
        postfix:= '*' | '+'
    """

    def __init__(self, tokens: list[str]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Optional[str]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> str:
        token = self._peek()
        assert token is not None
        self._pos += 1
        return token

    def parse(self) -> Regex:
        """Parses the whole token stream and returns the Regex."""
        regex = self._parse_expr()
        token = self._peek()
        if token is not None:
            raise ValueError(f"unexpected {token!r} at the end of the expression")
        return regex

    def _parse_expr(self) -> Regex:
        regex = self._parse_term()
        while self._peek() == "|":
            self._advance()
            if self._peek() in (None, ")"):
                raise ValueError("dangling '|' with no term after it")
            regex = regex.union(self._parse_term())
        return regex

    def _parse_term(self) -> Regex:
        factors: list[Regex] = []
        while self._peek() not in (None, "|", ")"):
            factors.append(self._parse_factor())
        if not factors:
            token = self._peek()
            if token is None:
                raise ValueError("unexpected end of the expression")
            if token == "|":
                raise ValueError("consecutive '|' operators")
            raise ValueError(f"unexpected {token!r} with no term before it")
        regex = factors[0]
        for factor in factors[1:]:
            regex = regex.concatenate(factor)
        return regex

    def _parse_factor(self) -> Regex:
        atom = self._parse_atom()
        while self._peek() in ("*", "+"):
            operator = self._advance()
            if operator == "*":
                atom = atom.kleene_star()
            else:
                atom = atom.concatenate(atom.kleene_star())
        return atom

    def _parse_atom(self) -> Regex:
        token = self._peek()
        if token is None:
            raise ValueError("unexpected end of the expression")
        if token == "(":
            self._advance()
            inner = self._parse_expr()
            if self._peek() != ")":
                raise ValueError("unclosed '(' in the expression")
            self._advance()
            return inner
        if token == "$":
            self._advance()
            return Regex("$")
        if token in ("|", "*", "+", ")"):
            raise ValueError(f"dangling {token!r} with no operand before it")
        self._advance()
        return Regex(token)


def _head(node: Regex) -> Node:
    """The AST node's top operator (always set for a parsed Regex)."""
    head = node.head
    assert head is not None
    return head


def _sons(node: Regex) -> list[Regex]:
    """The AST node's children (always set for a parsed Regex)."""
    sons = node.sons
    assert sons is not None
    return sons


def _node_precedence(node: Regex) -> int:
    """The precedence of a Regex AST node's top operator."""
    head = _head(node)
    if isinstance(head, (Symbol, Epsilon)):
        return _PRECEDENCE_ATOM
    if head.value == "Union":
        return _PRECEDENCE_UNION
    if head.value == "Concatenation":
        return _PRECEDENCE_CONCAT
    return _PRECEDENCE_ATOM  # Kleene star


def _print_body(node: Regex) -> str:
    """Prints one AST node without outer parentheses."""
    head = _head(node)
    if isinstance(head, Epsilon):
        return "$"
    if isinstance(head, Symbol):
        return head.value
    sons = _sons(node)
    if head.value == "Kleene Star":
        return _print_node(sons[0], _PRECEDENCE_ATOM) + "*"
    if head.value == "Concatenation":
        return " ".join(_print_node(child, _PRECEDENCE_CONCAT) for child in sons)
    return " | ".join(_print_node(child, _PRECEDENCE_UNION) for child in sons)


def _print_node(node: Regex, min_precedence: int) -> str:
    """Prints one AST node, parenthesizing it when the context demands it."""
    text = _print_body(node)
    if _node_precedence(node) < min_precedence:
        return f"({text})"
    return text


def regex_from_text(text: str) -> Regex:
    """Create a regular expression [1]_ from text.

    The text uses the dataset's canonical regular expression syntax:

    - a symbol is a maximal run of characters outside the metacharacter set
      (an edge label or a nonterminal);
    - concatenation is whitespace, union is ``|``, grouping is parentheses;
    - ``*`` and ``+`` are postfix Kleene star and Kleene plus (``X+`` is
      sugar for ``X X*``);
    - ``$`` is the empty word (epsilon).

    Precedence: postfix operators > concatenation > union.

    Parameters
    ----------
    text : str
        The text with which the regular expression will be created.

    Examples
    --------
    >>> from flpq_data import *
    >>> regex = regex_from_text("a (bc|d*)")
    >>> regex_to_text(regex)
    'a (bc | d*)'
    >>> regex = regex_from_text("a+")
    >>> regex.accepts(["a"])
    True
    >>> regex.accepts([])
    False

    Returns
    -------
    regex : Regex
        Regular expression.

    Raises
    ------
    ValueError
        If the text is empty or is not a well-formed expression (unbalanced
        parentheses, dangling operators).

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Regular_expression#Formal_definition
    """
    tokens = _tokenize(text)
    if not tokens:
        raise ValueError("the regular expression is empty")

    regex = _RegexParser(tokens).parse()

    logging.info(f"Create {regex=} from {text=}")

    return regex


def regex_to_text(regex: Regex) -> str:
    """Turns a regular expression [1]_ into its canonical text representation.

    The output follows the canonical syntax of :func:`regex_from_text` with
    minimal parentheses, so ``regex_from_text(regex_to_text(r))`` is
    equivalent to ``r`` and ``regex_to_text`` is idempotent.

    Parameters
    ----------
    regex : Regex
        Regular expression.

    Examples
    --------
    >>> from flpq_data import *
    >>> regex = regex_from_text("a (bc|d*)")
    >>> regex_to_text(regex)
    'a (bc | d*)'

    Returns
    -------
    text : str
        Regular expression text representation.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Regular_expression#Formal_definition
    """

    text = _print_node(regex, _PRECEDENCE_UNION)

    logging.info(f"Turn {regex=} into {text=}")

    return text


def regex_from_txt(path: Union[pathlib.Path, str]) -> Regex:
    """Create a regular expression [1]_ from TXT file.

    Parameters
    ----------
    path : Union[Path, str]
        The path to the TXT file with which the regular expression will be created.

    Examples
    --------
    >>> from flpq_data import *
    >>> regex_1 = regex_from_text("a (bc|d*)")
    >>> path = regex_to_txt(regex_1, "test.txt")
    >>> regex = regex_from_txt(path)
    >>> regex_to_text(regex)
    'a (bc | d*)'

    Returns
    -------
    regex : Regex
        Regular expression.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Regular_expression#Formal_definition
    """
    with open(path, "r") as f:
        expression = f.read()

    regex = regex_from_text(expression)

    logging.info(f"Create {regex=} from {path=}")

    return regex


def regex_to_txt(regex: Regex, path: Union[pathlib.Path, str]) -> pathlib.Path:
    """Saves a regular expression [1]_ text representation into TXT file.

    Parameters
    ----------
    regex : Regex
        Regular expression.

    path : Union[Path, str]
        The path to the TXT file where regular expression text representation
        will be saved.

    Examples
    --------
    >>> from flpq_data import *
    >>> regex = regex_from_text("a (bc|d*)")
    >>> path = regex_to_txt(regex, "test.txt")

    Returns
    -------
    path : Path
        The path to the TXT file where regular expression text representation
        will be saved.

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Regular_expression#Formal_definition
    """
    with open(path, "w") as f:
        f.write(regex_to_text(regex))

    dest = pathlib.Path(path).resolve()

    logging.info(f"Save {regex=} to {dest=}")

    return dest
