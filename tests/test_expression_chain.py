"""
tests/test_expression_chain.py

Regression tests for FrancisExpression method chaining.

Context: users were forced to split each string transformation into its own
<box-def> because chained calls like ${x.replace(".","").replace(",","")}
were silently broken by a greedy regex. These tests lock in the fix and
prevent the bug from reappearing.
"""

from __future__ import annotations

import pytest

from francis_suite.core.context import FContext
from francis_suite.core.expressions import FrancisExpression
from francis_suite.core.variables import FNodeVariable


def _engine(**variables: str) -> FrancisExpression:
    ctx = FContext()
    for name, value in variables.items():
        ctx.set(name, FNodeVariable(value))
    return FrancisExpression(ctx)


# -----------------------------------------------------------------
# Bare variable lookup
# -----------------------------------------------------------------

def test_bare_variable_resolves():
    eng = _engine(nombre="Francis")
    assert eng.resolve("${nombre}") == "Francis"


def test_unknown_variable_returns_empty():
    """Missing variables resolve to empty string (existing framework behavior)."""
    eng = _engine()
    assert eng.resolve("${missing}") == ""


# -----------------------------------------------------------------
# Single method call (baseline — must keep working)
# -----------------------------------------------------------------

def test_single_trim():
    eng = _engine(text="  hola  ")
    assert eng.resolve("${text.trim()}") == "hola"


def test_single_upper():
    eng = _engine(text="hola")
    assert eng.resolve("${text.toUpperCase()}") == "HOLA"


def test_single_replace():
    eng = _engine(text="1.234")
    assert eng.resolve("${text.replace(\".\",\"\")}") == "1234"


def test_contains_true():
    eng = _engine(text="precio UF 100")
    assert eng.resolve("${text.contains(\"UF\")}") == "True"


def test_contains_false():
    eng = _engine(text="precio CLP 100")
    assert eng.resolve("${text.contains(\"UF\")}") == "False"


# -----------------------------------------------------------------
# Chained method calls — THE FIX
# -----------------------------------------------------------------

def test_chain_two_replaces():
    """Two replace calls in sequence — used to break silently."""
    eng = _engine(price="1.234,50")
    out = eng.resolve('${price.replace(".","").replace(",","")}')
    assert out == "123450"


def test_chain_three_replaces_price_sanitization():
    """
    Real user scenario: sanitizing a scraped CLP/UF price in one expression
    instead of 5 separate <box-def> blocks.
    """
    eng = _engine(price_text="$ 1.234.567 UF")
    out = eng.resolve(
        '${price_text.replace("$","").replace(".","").replace("UF","").trim()}'
    )
    assert out == "1234567"


def test_chain_trim_then_replace():
    eng = _engine(text="  1.234  ")
    assert eng.resolve('${text.trim().replace(".","")}') == "1234"


def test_chain_upper_then_contains():
    eng = _engine(text="precio uf 100")
    assert eng.resolve('${text.toUpperCase().contains("UF")}') == "True"


def test_chain_replace_then_length():
    eng = _engine(text="a.b.c")
    assert eng.resolve('${text.replace(".","").length()}') == "3"


# -----------------------------------------------------------------
# Tricky arguments that used to break the naive regex
# -----------------------------------------------------------------

def test_replace_with_parens_in_argument():
    """Argument containing ')' must not close the method prematurely."""
    eng = _engine(text="foo(bar)baz")
    assert eng.resolve('${text.replace("(","").replace(")","")}') == "foobarbaz"


def test_replace_with_comma_in_argument():
    """Comma inside quoted arg must not split arguments."""
    eng = _engine(text="a,b,c")
    assert eng.resolve('${text.replace(",",";")}') == "a;b;c"


def test_replace_with_dot_preserves_thousands_guard():
    """Chilean thousands formatting must survive auto-number parsing."""
    eng = _engine(price="1.234")
    # 1.234 would become float 1.234 if auto-parsed; guard keeps it as "1.234".
    assert eng.resolve('${price.replace(".","")}') == "1234"


def test_replace_html_entity_dollar():
    """HTML entity &#36; becomes $ after XML parsing; engine sees literal $."""
    eng = _engine(text="$100")
    assert eng.resolve('${text.replace("$","")}') == "100"


# -----------------------------------------------------------------
# Error paths
# -----------------------------------------------------------------

def test_unknown_method_is_silently_kept():
    """
    resolve() is tolerant: if evaluation fails, it leaves the expression
    untouched rather than crashing the whole workflow.
    """
    eng = _engine(text="hello")
    # nonExistentMethod raises AttributeError inside _eval_expr,
    # so resolve() returns the original ${...} block unchanged.
    assert eng.resolve("${text.nonExistentMethod()}") == "${text.nonExistentMethod()}"


def test_empty_variable_gives_empty_string():
    eng = _engine(text="")
    assert eng.resolve("${text.trim()}") == ""
    assert eng.resolve("${text.isEmpty()}") == "True"
