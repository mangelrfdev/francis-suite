"""
hands/core/pause_task.py

PauseTaskHand implements the <pause-task> tag.
Pauses workflow execution in development environments.

In development (FRANCIS_ENV=dev or not set):
    - Prints the message
    - Waits for the user to press Enter before continuing
    - Future: Plugin VSCode will replace Enter with a "Continue" button

In production (FRANCIS_ENV=prod):
    - Prints a warning
    - Continues execution without pausing
    - Never blocks production workflows

Usage in XML:
    <pause-task/>
    <pause-task message="Review data before continuing"/>
    <pause-task message="Processed: ${titulo}"/>

Environment:
    FRANCIS_ENV=dev   → pauses (default if not set)
    FRANCIS_ENV=prod  → warning only, continues
"""

from __future__ import annotations
import os
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand


@hand(tag="pause-task")
class PauseTaskHand(AbstractHand):
    """
    Pauses workflow execution for inspection.

    In development — pauses until user presses Enter.
    In production — logs a warning and continues without pausing.

    Attributes:
        message (optional): message to display when pausing.
            Supports ${variables}.

    Returns:
        FEmptyVariable always.

    Examples:
        <pause-task/>
        <pause-task message="Review extracted data before saving"/>
        <pause-task message="Current item: ${titulo} — precio: ${precio}"/>
    """

    def execute(self) -> FVariable:
        from francis_suite.core.expressions import FrancisExpression
        engine  = FrancisExpression(self.context)
        message = engine.resolve(self.attr("message", ""))

        env = os.environ.get("FRANCIS_ENV", "dev").lower().strip()

        if env == "prod":
            print(
                "[PAUSE-TASK] WARNING — pause-task found in workflow. "
                "Remove before deploying to production."
            )
            return FEmptyVariable()

        # dev — pause until user presses Enter
        if message:
            print(f"[PAUSE-TASK] {message}")

        print("[PAUSE-TASK] Workflow paused. Press Enter to continue...")
        input()

        return FEmptyVariable()
