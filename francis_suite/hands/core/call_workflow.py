"""
hands/core/call_workflow.py

WorkflowCallHand implements the <call-workflow> tag.
Loads and executes an external workflow XML file in the current context,
sharing variables and state.

Usage in XML:
    <call-workflow path="scrapers/products.xml"/>

    <if condition="${env} == 'prod'">
        <call-workflow path="config/prod.xml"/>
    </if>
    <else>
        <call-workflow path="config/dev.xml"/>
    </else>
"""

from __future__ import annotations
from pathlib import Path
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="call-workflow")
class WorkflowCallHand(AbstractHand):
    """
    Loads and executes an external workflow XML file.

    The called workflow runs in the same context as the parent,
    sharing all variables and state.

    Attributes:
        path (required): path to the workflow XML file.
                         Relative to current working directory.

    Returns:
        Result of the last executed hand in the called workflow.
        FEmptyVariable if the workflow is empty.

    Example:
        <call-workflow path="scrapers/products.xml"/>
    """

    def execute(self) -> FVariable:
        path_str = self.require_attr("path")
        path = Path(path_str)

        if not path.exists():
            raise FileNotFoundError(
                f"<call-workflow> cannot find workflow file: '{path}'"
            )

        from francis_suite.core.parser import FParser

        parser = FParser()
        root = parser.parse_file(path)

        return self._runtime._execute_children(root, self._session)