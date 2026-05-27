"""Diagnostic probes for suspected FrancisExpression bugs. Run once, delete after."""
from francis_suite.core.context import FContext
from francis_suite.core.expressions import FrancisExpression
from francis_suite.core.variables import FNodeVariable

def probe(label, actual, expected):
    status = "OK  " if actual == expected else "BUG "
    print(f"[{status}] {label}: got {actual!r}, expected {expected!r}")

def eng(**kw):
    ctx = FContext()
    for k, v in kw.items():
        ctx.set(k, FNodeVariable(v))
    return FrancisExpression(ctx)

print("=== Bug probe: } inside argument ===")
e = eng(text="a}b}c")
probe("replace literal '}'", e.resolve('${text.replace("}","")}'), "abc")

print("\n=== Bug probe: leading zeros in numeric-looking strings ===")
e = eng(code="007")
probe("bare lookup of '007'", e.resolve("${code}"), "007")
probe("chain on '007'", e.resolve("${code.trim()}"), "007")

print("\n=== Bug probe: trailing zeros on decimals ===")
e = eng(price="5.50")
probe("bare '5.50'", e.resolve("${price}"), "5.50")
probe("replace . on 5.50", e.resolve('${price.replace(".",",")}'), "5,50")

print("\n=== Bug probe: whitespace around numbers ===")
e = eng(n="  42  ")
probe("bare whitespace number", e.resolve("${n}"), "  42  ")

print("\n=== Bug probe: nested ${} inside expression ===")
e = eng(a="hello", b="ell")
probe("nested var in argument", e.resolve('${a.replace("${b}","X")}'), "hXo")

print("\n=== Bug probe: sensitive var in method chain (would-be privacy leak) ===")
from francis_suite.core.variables import FVariable
# Simulate a sensitive variable if the framework supports it
try:
    from francis_suite.core.context import FContext as C
    ctx = FContext()
    # NOTE: actual sensitive-var API may differ; this is just a probe.
    v = FNodeVariable("SECRET123")
    # Try common attribute patterns to mark as sensitive
    for attr in ("sensitive", "_sensitive", "is_sensitive"):
        if hasattr(v, attr):
            try:
                setattr(v, attr, True)
                print(f"    (marked sensitive via .{attr})")
            except Exception:
                pass
    ctx.set("api_key", v)
    exp = FrancisExpression(ctx)
    print(f"    resolve_display bare: {exp.resolve_display('${api_key}')!r}")
    print(f"    resolve_display chain: {exp.resolve_display('${api_key.toUpperCase()}')!r}")
except Exception as ex:
    print(f"    (could not probe sensitive vars: {ex})")

print("\n=== Bug probe: bool casing ===")
e = eng(text="UF 100")
probe("contains returns 'True' (Python) vs 'true' (XML-style)",
      e.resolve('${text.contains("UF")}'), "true")
