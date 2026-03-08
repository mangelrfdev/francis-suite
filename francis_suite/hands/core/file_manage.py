"""
hands/core/file_manage.py

FileManageHand implements the <file-manage> tag.
Performs file system operations: delete, move, copy, list.

Usage in XML:
    <file-manage action="delete" path="temp/file.txt"/>
    <file-manage action="move" path="old/file.txt" dest="new/file.txt"/>
    <file-manage action="copy" path="orig/file.txt" dest="backup/file.txt"/>

    <box-def name="archivos">
        <file-manage action="list" path="data/" filter="*.json"/>
    </box-def>
"""

from __future__ import annotations
import shutil
from pathlib import Path
from francis_suite.core.registry import hand
from francis_suite.core.variables import FVariable, FNodeVariable, FListVariable, FEmptyVariable
from francis_suite.hands.base import AbstractHand
from francis_suite.core.expressions import FrancisExpression


@hand(tag="file-manage")
class FileManageHand(AbstractHand):
    """
    Performs file system operations.

    Attributes:
        action (required): operation to perform — delete, move, copy, list.
        path (required): source path.
        dest (optional): destination path — required for move and copy.
        filter (optional): glob pattern for list action. Default: "*".
        recursive (optional): list files recursively. Default: false.
        mkdir (optional): create parent directories if missing. Default: true.

    Returns:
        FListVariable with file paths for list action.
        FEmptyVariable for delete, move, copy.

    Example:
        <file-manage action="delete" path="temp/file.txt"/>
    """

    def execute(self) -> FVariable:
        engine = FrancisExpression(self.context)
        action = engine.resolve(self.require_attr("action")).lower()
        path_str = engine.resolve(self.require_attr("path"))
        path = Path(path_str)

        if action == "delete":
            return self._delete(path)
        elif action == "move":
            return self._move(path)
        elif action == "copy":
            return self._copy(path)
        elif action == "list":
            return self._list(path)
        else:
            raise ValueError(
                f"<file-manage> unknown action '{action}'. "
                f"Valid actions: delete, move, copy, list"
            )

    def _delete(self, path: Path) -> FVariable:
        if not path.exists():
            raise FileNotFoundError(f"<file-manage delete> cannot find: '{path}'")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return FEmptyVariable()

    def _move(self, path: Path) -> FVariable:
        engine = FrancisExpression(self.context)
        dest_str = engine.resolve(self.require_attr("dest"))
        dest = Path(dest_str)
        mkdir = engine.resolve(self.attr("mkdir", "true")).lower() == "true"

        if mkdir:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
        return FEmptyVariable()

    def _copy(self, path: Path) -> FVariable:
        engine = FrancisExpression(self.context)
        dest_str = engine.resolve(self.require_attr("dest"))
        dest = Path(dest_str)
        mkdir = engine.resolve(self.attr("mkdir", "true")).lower() == "true"

        if mkdir:
            dest.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            shutil.copytree(str(path), str(dest))
        else:
            shutil.copy2(str(path), str(dest))
        return FEmptyVariable()

    def _list(self, path: Path) -> FVariable:
        engine = FrancisExpression(self.context)
        pattern = engine.resolve(self.attr("filter", "*"))
        recursive = engine.resolve(self.attr("recursive", "false")).lower() == "true"

        if not path.exists():
            raise FileNotFoundError(f"<file-manage list> cannot find: '{path}'")

        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        if not files:
            return FEmptyVariable()

        return FListVariable([FNodeVariable(str(f)) for f in sorted(files)])