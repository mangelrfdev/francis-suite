"""
core/expressions.py

FrancisExpression is the central expression engine for Francis Suite.
It resolves ${variables} from context and evaluates expressions safely
using simpleeval.

Used by:
    - IfHand          — evaluates conditions
    - WhileHand       — evaluates loop conditions
    - EvaluateHand    — evaluates expressions and returns results
    - ComposeHand     — interpolates variables into text
    - LogHand         — interpolates variables for display (uses resolve_display)

Examples:
    ${nombre}                          → value of "nombre" from context
    ${precio} * ${cantidad}            → arithmetic
    ${nombre.isEmpty()}                → method call
    !${lista.isEmpty()} and ${n} > 0   → logical operators
"""

from __future__ import annotations
import re
from typing import Any
from simpleeval import EvalWithCompoundTypes
from francis_suite.core.context import FContext


_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _split_method_args(args_str: str) -> list[str]:
    """
    Split comma-separated method arguments, respecting double- and single-quoted strings.
    Needed for e.g. replace(",", ".") — naive split(",") would break on the comma inside quotes.
    """
    parts: list[str] = []
    cur: list[str] = []
    i = 0
    in_quote = False
    quote_char = ""
    while i < len(args_str):
        c = args_str[i]
        if not in_quote:
            if c in ('"', "'"):
                in_quote = True
                quote_char = c
                cur.append(c)
            elif c == ",":
                parts.append("".join(cur).strip())
                cur = []
            else:
                cur.append(c)
        else:
            cur.append(c)
            if c == quote_char:
                in_quote = False
                quote_char = ""
        i += 1
    if cur:
        parts.append("".join(cur).strip())
    return [p.strip().strip('"').strip("'") for p in parts]


class FrancisString(str):
    """
    A string subclass that exposes helper methods for use in expressions.

    Examples:
        ${nombre.isEmpty()}
        ${texto.toUpperCase()}
        ${valor.trim()}
        ${texto.contains("hola")}
        ${texto.startsWith("http")}
        ${texto.length()}
    """

    def isEmpty(self) -> bool:
        return len(self.strip()) == 0

    def isNotEmpty(self) -> bool:
        return not self.isEmpty()

    def toUpperCase(self) -> "FrancisString":
        return FrancisString(self.upper())

    def toLowerCase(self) -> "FrancisString":
        return FrancisString(self.lower())

    def trim(self) -> "FrancisString":
        return FrancisString(self.strip())

    def length(self) -> int:
        return len(self)

    def contains(self, value: str) -> bool:
        return value in self

    def startsWith(self, value: str) -> bool:
        return self.startswith(value)

    def endsWith(self, value: str) -> bool:
        return self.endswith(value)

    def replace(self, old: str, new: str) -> "FrancisString":
        return FrancisString(str.replace(self, old, new))

    def toInt(self) -> int:
        return int(self.strip())

    def toFloat(self) -> float:
        return float(self.strip())

    def toBoolean(self) -> bool:
        return self.strip().lower() == "true"


class FrancisExpression:
    """
    Central expression engine for Francis Suite.
    """

    def __init__(self, context: FContext) -> None:
        self._context = context

    def resolve(self, template: str) -> str:
        """
        Replace all ${var} expressions with their real string values from context.
        Used internally by the engine — always returns the real value.
        Unknown variables are left as-is.
        """
        def replace(match: re.Match) -> str:
            expr = match.group(1).strip()
            try:
                result = self._eval_expr(expr, display=False)
                return str(result)
            except Exception:
                return match.group(0)

        return _VAR_PATTERN.sub(replace, template)

    def resolve_display(self, template: str) -> str:
        """
        Replace all ${var} expressions with their display values from context.
        Used by LogHand — sensitive variables are masked automatically.
        Unknown variables are left as-is.
        """
        def replace(match: re.Match) -> str:
            expr = match.group(1).strip()
            try:
                result = self._eval_expr(expr, display=True)
                return str(result)
            except Exception:
                return match.group(0)

        return _VAR_PATTERN.sub(replace, template)

    def evaluate(self, expression: str) -> Any:
        """
        Evaluate a full expression and return the result.
        Supports arithmetic, comparisons, logical operators, and method calls.
        Always uses real values — never masked.
        """
        expression = expression.strip()
        if not expression:
            return None

        names: dict[str, Any] = {}
        counter = [0]

        def replace_with_name(match: re.Match) -> str:
            expr = match.group(1).strip()
            try:
                value = self._eval_expr(expr, display=False)
            except Exception:
                value = match.group(0)
            key = f"__v{counter[0]}__"
            counter[0] += 1
            names[key] = value
            return key

        resolved_expr = _VAR_PATTERN.sub(replace_with_name, expression)

        try:
            evaluator = EvalWithCompoundTypes(names=names)
            return evaluator.eval(resolved_expr)
        except Exception:
            return resolved_expr

    def _eval_expr(self, expr: str, display: bool = False) -> Any:
        """
        Evaluate a single expression like:
            nombre           → value of "nombre" from context
            nombre.isEmpty() → method call on the value

        display=True uses to_display() — for logs and UI.
        display=False uses to_string() — for internal engine use.
        """
        method_match = re.match(r"^(\w[\w-]*)\.([\w]+)\((.*)\)$", expr)
        if method_match:
            var_name = method_match.group(1)
            method   = method_match.group(2)
            args_str = method_match.group(3).strip()

            # method calls always use real value — display only affects simple vars
            value = self._get_var(var_name, display=False)
            fs = FrancisString(str(value))

            if not hasattr(fs, method):
                raise AttributeError(f"Unknown method '{method}' on string")

            if args_str:
                args = _split_method_args(args_str)
                return getattr(fs, method)(*args)
            else:
                return getattr(fs, method)()

        return self._get_var(expr, display=display)

    def _get_var(self, name: str, display: bool = False) -> Any:
        """
        Get a variable value from context, converted to appropriate type.
        display=True returns the display value (masked if sensitive).
        display=False returns the real value.
        """
        var = self._context.get(name)
        if var.is_empty():
            return FrancisString("")

        value = var.to_display() if display else var.to_string()

        # only attempt numeric conversion for real values, not masked ones
        if not display:
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except (ValueError, TypeError):
                pass

        return FrancisString(value)
