from francis_suite.core.expressions import FrancisExpression
from francis_suite.core.context import FContext
from francis_suite.core.variables import FNodeVariable

ctx = FContext()
ctx.set('tipo', FNodeVariable('B'))
engine = FrancisExpression(ctx)

result = engine.evaluate("${tipo} == 'B'")
print(f"Result: {result!r}")
print(f"Type: {type(result)}")
