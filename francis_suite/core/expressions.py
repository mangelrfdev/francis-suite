"""
core/expressions.py

FrancisExpression is the central expression engine for Francis Suite.
It resolves ${variables} from context and evaluates expressions safely
using simpleeval.

Used by:
    - IfHand          — evaluates conditions
    - WhileHand       — evaluates loop conditions
    - EvaluateHand    — evaluates expressions and returns results
    - TextFormatHand  — interpolates variables into text

Examples:
    ${nombre}                          → value of "nombre" from context
    ${precio} * ${cantidad}            → arithmetic
    ${nombre.isEmpty()}                → method call
    !${lista.isEmpty()} and ${n} > 0   → logical operators
"""

from __future__ import annotations
import re
from typing import Any
from simpleeval import NameNotDefined, EvalWithCompoundTypes
from francis_suite.core.context import FContext


_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


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
        Replace all ${var} expressions with their string values from context.
        Used by TextFormatHand for simple interpolation.
        Unknown variables are left as-is.
        """
        def replace(match: re.Match) -> str:
            expr = match.group(1).strip()
            try:
                result = self._eval_expr(expr)
                return str(result)
            except Exception:
                return match.group(0)

        return _VAR_PATTERN.sub(replace, template)

    def evaluate(self, expression: str) -> Any:
        """
        Evaluate a full expression and return the result.
        Supports arithmetic, comparisons, logical operators, and method calls.
        """
        expression = expression.strip()
        if not expression:
            return None

        names: dict[str, Any] = {}
        counter = [0]

        def replace_with_name(match: re.Match) -> str:
            expr = match.group(1).strip()
            try:
                value = self._eval_expr(expr)
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

    def _eval_expr(self, expr: str) -> Any:
        """
        Evaluate a single expression like:
            nombre           → value of "nombre" from context
            nombre.isEmpty() → method call on the value
        """
        method_match = re.match(r"^(\w[\w-]*)\.([\w]+)\((.*)\)$", expr)
        if method_match:
            var_name = method_match.group(1)
            method   = method_match.group(2)
            args_str = method_match.group(3).strip()

            value = self._get_var(var_name)
            fs = FrancisString(str(value))

            if not hasattr(fs, method):
                raise AttributeError(f"Unknown method '{method}' on string")

            if args_str:
                args = [a.strip().strip('"').strip("'") for a in args_str.split(",")]
                return getattr(fs, method)(*args)
            else:
                return getattr(fs, method)()

        return self._get_var(expr)

    def _get_var(self, name: str) -> Any:
        """Get a variable value from context, converted to appropriate type."""
        var = self._context.get(name)
        if var.is_empty():
            return FrancisString("")  # vacío = string vacío, no error
        value = var.to_string()

        try:
            if "." in value:
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            pass

        return FrancisString(value)