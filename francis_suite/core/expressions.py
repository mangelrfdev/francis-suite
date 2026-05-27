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


_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")  # legacy, kept for cheap early-outs


def _find_var_blocks(template: str) -> list[tuple[int, int, str]]:
    """
    Scan a template for ${...} blocks, respecting:
        - quoted strings (") or (') that may legally contain '}' or '${'
        - nested ${...} inside arguments

    Returns a list of (start, end_exclusive, inner) tuples in document order.

    This replaces the naive regex `\\$\\{([^}]+)\\}` which used to break on:
        ${text.replace("}","")}          — '}' inside quoted argument
        ${a.replace("${b}","X")}         — nested ${...} inside argument
    """
    blocks: list[tuple[int, int, str]] = []
    n = len(template)
    i = 0
    while i < n:
        if template[i] == "$" and i + 1 < n and template[i + 1] == "{":
            start = i
            j = i + 2
            depth = 1
            in_quote = False
            quote_char = ""
            while j < n and depth > 0:
                c = template[j]
                if in_quote:
                    if c == quote_char:
                        in_quote = False
                        quote_char = ""
                else:
                    if c in ('"', "'"):
                        in_quote = True
                        quote_char = c
                    elif c == "$" and j + 1 < n and template[j + 1] == "{":
                        depth += 1
                        j += 1  # skip the '{' so next iteration does not re-enter
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            break
                j += 1
            if depth == 0:
                inner = template[start + 2 : j]
                blocks.append((start, j + 1, inner))
                i = j + 1
                continue
            # unbalanced — treat literally, skip the '$'
        i += 1
    return blocks


def _looks_like_thousands_with_single_dot(s: str) -> bool:
    """
    True for patterns like 800.000 or 8.000 (CLP/EUR-style grouping).

    Python's float('800.000') is 800.0, not 800000 — auto-coercing breaks
    price sanitization chains (replace('.', '')).
    """
    if s.count(".") != 1:
        return False
    left, right = s.split(".", 1)
    left_core = left.lstrip("-+")
    return (
        len(left_core) >= 1
        and left_core.isdigit()
        and right.isdigit()
        and len(right) == 3
    )


def _try_parse_context_number(value: str) -> int | float | None:
    """
    Parse for arithmetic / comparisons. Returns None if value should stay a plain string.
    """
    s = value.strip()
    if not s:
        return None
    if _looks_like_thousands_with_single_dot(s):
        return None
    if "." in s:
        try:
            return float(s)
        except ValueError:
            return None
    try:
        return int(s)
    except ValueError:
        return None


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


def _parse_balanced_args(s: str) -> tuple[str, int]:
    """
    Given `s` that starts right AFTER the opening '(' of a method call, walk
    characters until the matching ')', returning:
        - args_content: everything inside the parens (without the closing paren)
        - consumed:     number of characters consumed INCLUDING the closing ')'

    Correctly handles nested parentheses and single/double quoted strings.

    Example:
        _parse_balanced_args('"a","b")rest')  -> ('"a","b"', 8)
        _parse_balanced_args('f(x), y)rest')  -> ('f(x), y', 9)

    Raises SyntaxError if no matching ')' is found.
    """
    depth = 1
    i = 0
    in_quote = False
    quote_char = ""
    while i < len(s):
        c = s[i]
        if in_quote:
            if c == quote_char:
                in_quote = False
                quote_char = ""
        else:
            if c in ('"', "'"):
                in_quote = True
                quote_char = c
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return s[:i], i + 1
        i += 1
    raise SyntaxError(f"Unclosed parenthesis in method call: {s!r}")


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

    def _substitute(self, template: str, display: bool) -> str:
        """
        Walk ${...} blocks with the quote/nesting-aware scanner and replace
        each with its evaluated result. Blocks whose evaluation fails are
        left untouched (tolerant behavior).
        """
        blocks = _find_var_blocks(template)
        if not blocks:
            return template

        parts: list[str] = []
        cursor = 0
        for start, end, inner in blocks:
            parts.append(template[cursor:start])
            expr = inner.strip()
            try:
                result = self._eval_expr(expr, display=display)
                parts.append(str(result))
            except Exception:
                parts.append(template[start:end])
            cursor = end
        parts.append(template[cursor:])
        return "".join(parts)

    def resolve(self, template: str) -> str:
        """
        Replace all ${var} expressions with their real string values from context.
        Used internally by the engine — always returns the real value.
        Unknown variables are left as-is.
        """
        return self._substitute(template, display=False)

    def resolve_display(self, template: str) -> str:
        """
        Replace all ${var} expressions with their display values from context.
        Used by LogHand — sensitive variables are masked automatically.
        Unknown variables are left as-is.
        """
        return self._substitute(template, display=True)

    def evaluate(self, expression: str) -> Any:
        """
        Evaluate a full expression and return the result.
        Supports arithmetic, comparisons, logical operators, and method calls.
        Always uses real values — never masked.

        Numeric coercion happens here (not in `_get_var`) so that `resolve()`
        preserves original string formatting like '007', '5.50', '  42  '.
        """
        expression = expression.strip()
        if not expression:
            return None

        names: dict[str, Any] = {}
        counter = [0]

        blocks = _find_var_blocks(expression)
        if not blocks:
            resolved_expr = expression
        else:
            parts: list[str] = []
            cursor = 0
            for start, end, inner in blocks:
                parts.append(expression[cursor:start])
                expr = inner.strip()
                try:
                    value = self._eval_expr(expr, display=False)
                except Exception:
                    value = expression[start:end]
                # Auto-coerce to number for arithmetic/comparison. Only strings
                # reach this branch; method-call results stay as-is.
                if isinstance(value, str):
                    parsed = _try_parse_context_number(value)
                    if parsed is not None:
                        value = parsed
                key = f"__v{counter[0]}__"
                counter[0] += 1
                names[key] = value
                parts.append(key)
                cursor = end
            parts.append(expression[cursor:])
            resolved_expr = "".join(parts)

        try:
            evaluator = EvalWithCompoundTypes(names=names)
            return evaluator.eval(resolved_expr)
        except Exception:
            return resolved_expr

    def _eval_expr(self, expr: str, display: bool = False) -> Any:
        """
        Evaluate a single expression. Supports method chaining.

            nombre                                          → value from context
            nombre.isEmpty()                                → single method call
            nombre.trim().replace(".","").replace(",","")   → CHAINED method calls

        display=True uses to_display() — for logs and UI.
        display=False uses to_string() — for internal engine use.
        Method calls always use real values (display only affects the base variable).
        """
        expr = expr.strip()

        # Bare variable reference (no method call)
        if re.fullmatch(r"\w[\w-]*", expr):
            return self._get_var(expr, display=display)

        # Must start with a variable name followed by '.'
        head_match = re.match(r"^(\w[\w-]*)\.(.*)$", expr)
        if not head_match:
            # Unrecognized shape; fall back to plain variable lookup
            return self._get_var(expr, display=display)

        var_name = head_match.group(1)
        rest = head_match.group(2)

        # Start with the base variable value.
        # IMPORTANT: propagate `display` to `_get_var` so sensitive variables
        # stay masked when the chain runs inside resolve_display (e.g. <log>).
        # Before this fix, ${secret.toUpperCase()} in a log leaked the raw value.
        base_value = self._get_var(var_name, display=display)
        current: Any = base_value if isinstance(base_value, FrancisString) else FrancisString(str(base_value))

        # Iteratively consume ".method(args)" calls
        pos = 0
        while pos < len(rest):
            m = re.match(r"(\w+)\(", rest[pos:])
            if not m:
                raise SyntaxError(
                    f"Expected method call in expression '{expr}' at '{rest[pos:]}'"
                )
            method_name = m.group(1)
            pos += m.end()  # past the '('

            args_str, consumed = _parse_balanced_args(rest[pos:])
            pos += consumed  # past the matching ')'

            # Re-wrap in FrancisString for every step so method chain keeps working
            if not isinstance(current, FrancisString):
                current = FrancisString(str(current))

            if not hasattr(current, method_name):
                raise AttributeError(
                    f"Unknown method '{method_name}' on string (expression: '{expr}')"
                )

            args = _split_method_args(args_str) if args_str.strip() else []
            current = getattr(current, method_name)(*args)

            # Chain separator or end
            if pos >= len(rest):
                break
            if rest[pos] != ".":
                raise SyntaxError(
                    f"Unexpected character '{rest[pos]}' in expression '{expr}'"
                )
            pos += 1  # skip the '.' and continue

        return current

    def _get_var(self, name: str, display: bool = False) -> Any:
        """
        Get a variable value from context as a FrancisString.

        Returns the raw string value as-is — no numeric coercion.
        Formatting like '007', '5.50', or '  42  ' is preserved.

        Numeric coercion only happens in `evaluate()` where arithmetic is needed.
        This keeps `resolve()` and method chains string-faithful.

        display=True returns the display value (masked if sensitive).
        display=False returns the real value.
        """
        var = self._context.get(name)
        if var.is_empty():
            return FrancisString("")

        value = var.to_display() if display else var.to_string()
        return FrancisString(value)
