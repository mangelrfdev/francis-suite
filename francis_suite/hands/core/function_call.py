"""
hands/core/function_call.py

FunctionCallHand implements the <function-call> tag.
Executes a previously defined function with optional parameters.

Usage in XML:
    <box-def name="resultado">
        <function-call name="mi-funcion">
            <function-param name="param1">
                <box name="mi-variable"/>
            </function-param>
        </function-call>
    </box-def>
"""

from __future__ import annotations
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable, FNodeVariable
from francis_suite.hands.base import AbstractHand
from francis_suite.core.expressions import FrancisExpression

@hand(tag="function-call")
class FunctionCallHand(AbstractHand):
    """
    Executes a previously defined function.

    Attributes:
        name (required): name of the function to call.

    Child tags:
        <function-param name="...">value</function-param>

    Returns:
        Value returned by <function-return> inside the function,
        or FEmptyVariable if no <function-return> is defined.
    """

    def execute(self) -> FVariable:
        engine = FrancisExpression(self.context)
        name = engine.resolve(self.require_attr("name"))

        functions = getattr(self.session, "_functions", {})
        if name not in functions:
            raise ValueError(
                f"<function-call> function '{name}' is not defined. "
                f"Use <function-create name='{name}'> first."
            )

        fn_node = functions[name]
        params = self._resolve_params()

        with self.context.new_scope():
            for param_name, param_value in params.items():
                self.context.set(param_name, param_value)

            result: FVariable = FEmptyVariable()
            return_node = None

            for child in fn_node.children:
                if child.tag == "function-return":
                    return_node = child
                else:
                    self.execute_child(child)

            if return_node is not None:
                for child in return_node.children:
                    result = self.execute_child(child)

        return result

    def _resolve_params(self) -> dict:
        """Extract and execute function-param children."""
        params = {}
        for child in self._node.children:
            if child.tag == "function-param":
                param_name = child.get_attr("name", "")
                if not param_name:
                    continue
                if child.children:
                    value = self.execute_child(child)
                else:
                    value = FNodeVariable(child.text or "")
                params[param_name] = value
        return params