"""
hands/core/file_manage.py

FileManageHand implements the <file-manage> tag.
Performs file system operations.

Usage in XML:
    <file-manage action="delete"       path="temp/file.txt"/>
    <file-manage action="move"         path="old/file.txt"  to="new/file.txt"/>
    <file-manage action="copy"         path="orig/file.txt" to="backup/file.txt"/>
    <file-manage action="rename"       path="foto_1.jpg"    to="foto_001.jpg"/>
    <file-manage action="mkdir"        path="output/fotos/"/>
    <file-manage action="check-exists" path="output/reporte.pdf"/>
    <file-manage action="get-size"     path="output/reporte.pdf"/>
    <file-manage action="list"         path="output/fotos/"/>
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
        action (required): operation to perform.
            delete       — remove a file or directory
            move         — move a file or directory to a new location
            copy         — copy a file or directory to a new location
            rename       — rename a file or directory in the same location
            mkdir        — create a directory and all parent directories
            check-exists — check if a file or directory exists
            get-size     — get the size of a file or directory
            list         — list files and/or directories in a path

        path (required): source path. Supports ${variables}.

        to (optional): destination path or new name.
            Required for: move, copy, rename.
            Supports ${variables}.

        force-delete (optional): force delete non-empty directory. Default: false.
        force-move   (optional): overwrite destination if exists. Default: false.
        force-copy   (optional): overwrite destination if exists. Default: false.
        size-format  (optional): size unit for get-size. Default: bytes.
            Values: bytes, kb, mb, gb, auto
        filter       (optional): glob pattern for list. Default: *
        type         (optional): item type for list. Default: files.
            Values: files, folders, all
        search-in-subfolders (optional): search inside subfolders for list. Default: false.

    Returns:
        list         — FListVariable with matching paths. Folders end with /.
        check-exists — FNodeVariable("true") or FNodeVariable("false")
        get-size     — FNodeVariable with formatted size string
        others       — FEmptyVariable

    Examples:
        <!-- delete -->
        <file-manage action="delete" path="output/reporte.tmp"/>
        <file-manage action="delete" path="output/fotos/" force-delete="true"/>

        <!-- move -->
        <file-manage action="move" path="old/foto.jpg" to="new/foto.jpg"/>
        <file-manage action="move" path="old/foto.jpg" to="new/foto.jpg" force-move="true"/>

        <!-- copy -->
        <file-manage action="copy" path="orig/foto.jpg" to="backup/foto.jpg"/>
        <file-manage action="copy" path="orig/foto.jpg" to="backup/foto.jpg" force-copy="true"/>

        <!-- rename -->
        <file-manage action="rename" path="output/foto_1.jpg" to="output/foto_001.jpg"/>
        <file-manage action="rename" path="output/reporte.tmp" to="output/reporte.pdf"/>

        <!-- mkdir -->
        <file-manage action="mkdir" path="output/fotos/"/>

        <!-- check-exists -->
        <box-def name="existe">
            <file-manage action="check-exists" path="output/reporte.pdf"/>
        </box-def>
        <if condition="${existe.toBoolean()}">
            <log>archivo existe</log>
        </if>

        <!-- get-size -->
        <box-def name="tamano">
            <file-manage action="get-size" path="output/reporte.pdf" size-format="auto"/>
        </box-def>
        <log>Tamaño: ${tamano}</log>

        <!-- list -->
        <box-def name="fotos">
            <file-manage action="list" path="output/fotos/" filter="*.jpg"/>
        </box-def>

        <box-def name="todas_las_fotos">
            <file-manage action="list" path="output/" filter="*.jpg" search-in-subfolders="true"/>
        </box-def>

        <box-def name="carpetas">
            <file-manage action="list" path="output/" type="folders"/>
        </box-def>
    """

    def execute(self) -> FVariable:
        engine   = FrancisExpression(self.context)
        action   = engine.resolve(self.require_attr("action")).lower()
        path_str = engine.resolve(self.require_attr("path"))
        path     = Path(path_str)

        if action == "delete":
            return self._delete(engine, path)
        elif action == "move":
            return self._move(engine, path)
        elif action == "copy":
            return self._copy(engine, path)
        elif action == "rename":
            return self._rename(engine, path)
        elif action == "mkdir":
            return self._mkdir(path)
        elif action == "check-exists":
            return self._check_exists(path)
        elif action == "get-size":
            return self._get_size(engine, path)
        elif action == "list":
            return self._list(engine, path)
        else:
            raise ValueError(
                f"<file-manage> unknown action '{action}'. "
                f"Valid actions: delete, move, copy, rename, mkdir, "
                f"check-exists, get-size, list"
            )

    # -------------------------------------------------------------------------
    # delete
    # -------------------------------------------------------------------------

    def _delete(self, engine: FrancisExpression, path: Path) -> FVariable:
        if not path.exists():
            raise FileNotFoundError(
                f"[FILE-MANAGE] delete: ERROR — not found: '{path}'"
            )

        force = engine.resolve(self.attr("force-delete", "false")).lower() == "true"

        if path.is_dir():
            if not force and any(path.iterdir()):
                raise ValueError(
                    f"[FILE-MANAGE] delete: ERROR — directory is not empty: '{path}' "
                    f"— use force-delete=\"true\" to force delete"
                )
            try:
                shutil.rmtree(path)
                print(f"[FILE-MANAGE] delete: removed directory '{path}'")
            except PermissionError:
                raise PermissionError(
                    f"[FILE-MANAGE] delete: ERROR — permission denied: '{path}'"
                )
            except OSError as e:
                if "WinError 32" in str(e) or "being used" in str(e).lower():
                    raise OSError(
                        f"[FILE-MANAGE] delete: ERROR — file is locked by another process: '{path}'"
                    )
                raise
        else:
            try:
                path.unlink()
                print(f"[FILE-MANAGE] delete: removed file '{path}'")
            except PermissionError:
                raise PermissionError(
                    f"[FILE-MANAGE] delete: ERROR — permission denied: '{path}'"
                )
            except OSError as e:
                if "WinError 32" in str(e) or "being used" in str(e).lower():
                    raise OSError(
                        f"[FILE-MANAGE] delete: ERROR — file is locked by another process: '{path}'"
                    )
                raise

        return FEmptyVariable()

    # -------------------------------------------------------------------------
    # move
    # -------------------------------------------------------------------------

    def _move(self, engine: FrancisExpression, path: Path) -> FVariable:
        to_str = engine.resolve(self.require_attr("to"))
        to     = Path(to_str)
        force  = engine.resolve(self.attr("force-move", "false")).lower() == "true"

        if not path.exists():
            raise FileNotFoundError(
                f"[FILE-MANAGE] move: ERROR — not found: '{path}'"
            )

        if to.exists() and not force:
            raise FileExistsError(
                f"[FILE-MANAGE] move: ERROR — destination already exists: '{to}' "
                f"— use force-move=\"true\" to replace"
            )

        to.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(path, to)
            print(f"[FILE-MANAGE] move: '{path}' → '{to}'")
        except PermissionError:
            raise PermissionError(
                f"[FILE-MANAGE] move: ERROR — permission denied: '{path}'"
            )
        except OSError as e:
            if "WinError 32" in str(e) or "being used" in str(e).lower():
                raise OSError(
                    f"[FILE-MANAGE] move: ERROR — file is locked by another process: '{path}'"
                )
            if "no space" in str(e).lower():
                raise OSError(
                    f"[FILE-MANAGE] move: ERROR — no space left on device"
                )
            raise

        return FEmptyVariable()

    # -------------------------------------------------------------------------
    # copy
    # -------------------------------------------------------------------------

    def _copy(self, engine: FrancisExpression, path: Path) -> FVariable:
        to_str = engine.resolve(self.require_attr("to"))
        to     = Path(to_str)
        force  = engine.resolve(self.attr("force-copy", "false")).lower() == "true"

        if not path.exists():
            raise FileNotFoundError(
                f"[FILE-MANAGE] copy: ERROR — not found: '{path}'"
            )

        if to.exists() and not force:
            raise FileExistsError(
                f"[FILE-MANAGE] copy: ERROR — destination already exists: '{to}' "
                f"— use force-copy=\"true\" to replace"
            )

        to.parent.mkdir(parents=True, exist_ok=True)

        try:
            if path.is_dir():
                if to.exists():
                    shutil.rmtree(to)
                shutil.copytree(path, to)
            else:
                shutil.copy2(path, to)
            print(f"[FILE-MANAGE] copy: '{path}' → '{to}'")
        except PermissionError:
            raise PermissionError(
                f"[FILE-MANAGE] copy: ERROR — permission denied: '{path}'"
            )
        except OSError as e:
            if "WinError 32" in str(e) or "being used" in str(e).lower():
                raise OSError(
                    f"[FILE-MANAGE] copy: ERROR — file is locked by another process: '{path}'"
                )
            if "no space" in str(e).lower():
                raise OSError(
                    f"[FILE-MANAGE] copy: ERROR — no space left on device"
                )
            raise

        return FEmptyVariable()

    # -------------------------------------------------------------------------
    # rename
    # -------------------------------------------------------------------------

    def _rename(self, engine: FrancisExpression, path: Path) -> FVariable:
        to_str = engine.resolve(self.require_attr("to"))
        to     = Path(to_str)

        if not path.exists():
            raise FileNotFoundError(
                f"[FILE-MANAGE] rename: ERROR — not found: '{path}'"
            )

        # rename must stay in the same directory
        if path.parent != to.parent:
            raise ValueError(
                f"[FILE-MANAGE] rename: ERROR — 'to' must be in the same directory as 'path'. "
                f"Use action='move' to move files to a different location."
            )

        if to.exists():
            raise FileExistsError(
                f"[FILE-MANAGE] rename: ERROR — destination already exists: '{to}'"
            )

        # detect duplicate extension
        original_ext = path.suffix.lower()
        new_ext      = to.suffix.lower()
        new_stem     = to.stem.lower()

        if original_ext and original_ext.lstrip(".") in new_stem:
            raise ValueError(
                f"[FILE-MANAGE] rename: ERROR — duplicate extension detected in '{to.name}'. "
                f"The original extension '{original_ext}' appears twice."
            )

        try:
            path.rename(to)
            print(f"[FILE-MANAGE] rename: '{path.name}' → '{to.name}'")

            # warn if extension changed
            if original_ext != new_ext:
                print(
                    f"[FILE-MANAGE] rename: WARNING — extension changed from "
                    f"'{original_ext}' to '{new_ext}' — file content was not converted"
                )
        except PermissionError:
            raise PermissionError(
                f"[FILE-MANAGE] rename: ERROR — permission denied: '{path}'"
            )
        except OSError as e:
            if "WinError 32" in str(e) or "being used" in str(e).lower():
                raise OSError(
                    f"[FILE-MANAGE] rename: ERROR — file is locked by another process: '{path}'"
                )
            raise

        return FEmptyVariable()

    # -------------------------------------------------------------------------
    # mkdir
    # -------------------------------------------------------------------------

    def _mkdir(self, path: Path) -> FVariable:
        if path.exists() and path.is_file():
            raise FileExistsError(
                f"[FILE-MANAGE] mkdir: ERROR — a file with that name already exists: '{path}'"
            )

        if path.exists():
            print(f"[FILE-MANAGE] mkdir: '{path}' already exists, skipping")
            return FEmptyVariable()

        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"[FILE-MANAGE] mkdir: created '{path}'")
        except PermissionError:
            raise PermissionError(
                f"[FILE-MANAGE] mkdir: ERROR — permission denied: '{path}'"
            )
        except OSError as e:
            if "no space" in str(e).lower():
                raise OSError(
                    f"[FILE-MANAGE] mkdir: ERROR — no space left on device"
                )
            raise

        return FEmptyVariable()

    # -------------------------------------------------------------------------
    # check-exists
    # -------------------------------------------------------------------------

    def _check_exists(self, path: Path) -> FVariable:
        result = path.exists()
        print(f"[FILE-MANAGE] check-exists: '{path}' → {str(result).lower()}")
        return FNodeVariable(str(result).lower())

    # -------------------------------------------------------------------------
    # get-size
    # -------------------------------------------------------------------------

    def _get_size(self, engine: FrancisExpression, path: Path) -> FVariable:
        if not path.exists():
            raise FileNotFoundError(
                f"[FILE-MANAGE] get-size: ERROR — not found: '{path}'"
            )

        size_format = engine.resolve(self.attr("size-format", "bytes")).lower()

        try:
            if path.is_dir():
                total    = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                count    = sum(1 for f in path.rglob("*") if f.is_file())
                size_str = self._format_size(total, size_format)
                print(f"[FILE-MANAGE] get-size: '{path}' → {count} files, {size_str} total")
                return FNodeVariable(size_str)
            else:
                total    = path.stat().st_size
                size_str = self._format_size(total, size_format)
                print(f"[FILE-MANAGE] get-size: '{path}' → {size_str}")
                return FNodeVariable(size_str)
        except PermissionError:
            raise PermissionError(
                f"[FILE-MANAGE] get-size: ERROR — permission denied: '{path}'"
            )

    def _format_size(self, size_bytes: int, size_format: str) -> str:
        """Format size in the requested unit."""
        if size_format == "auto":
            if size_bytes >= 1024 ** 3:
                return f"{size_bytes / 1024 ** 3:.2f} GB"
            elif size_bytes >= 1024 ** 2:
                return f"{size_bytes / 1024 ** 2:.2f} MB"
            elif size_bytes >= 1024:
                return f"{size_bytes / 1024:.2f} KB"
            else:
                return f"{size_bytes} bytes"
        elif size_format == "gb":
            return f"{size_bytes / 1024 ** 3:.2f} GB"
        elif size_format == "mb":
            return f"{size_bytes / 1024 ** 2:.2f} MB"
        elif size_format == "kb":
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} bytes"

    # -------------------------------------------------------------------------
    # list
    # -------------------------------------------------------------------------

    def _list(self, engine: FrancisExpression, path: Path) -> FVariable:
        if not path.exists():
            raise FileNotFoundError(
                f"[FILE-MANAGE] list: ERROR — not found: '{path}'"
            )

        try:
            pattern            = engine.resolve(self.attr("filter", "*"))
            item_type          = engine.resolve(self.attr("type", "files")).lower()
            search_subfolders  = engine.resolve(self.attr("search-in-subfolders", "false")).lower() == "true"

            if search_subfolders:
                all_items = list(path.rglob(pattern))
            else:
                all_items = list(path.glob(pattern))

            # filter by type
            if item_type == "folders":
                items = [i for i in all_items if i.is_dir()]
            elif item_type == "all":
                items = all_items
            else:
                items = [i for i in all_items if i.is_file()]

            if not items:
                if any(path.iterdir()):
                    print(
                        f"[FILE-MANAGE] list: no items found in '{path}' "
                        f"matching '{pattern}'"
                    )
                else:
                    print(f"[FILE-MANAGE] list: '{path}' exists but is empty")
                return FEmptyVariable()

            # folders end with / to distinguish from files
            def format_path(p: Path) -> str:
                return p.as_posix() + ("/" if p.is_dir() else "")

            sorted_items = sorted(items)
            file_count   = sum(1 for i in sorted_items if i.is_file())
            dir_count    = sum(1 for i in sorted_items if i.is_dir())

            if item_type == "folders":
                print(f"[FILE-MANAGE] list: found {dir_count} folders in '{path}'")
            elif item_type == "all":
                print(f"[FILE-MANAGE] list: found {file_count} files and {dir_count} folders in '{path}'")
            else:
                print(f"[FILE-MANAGE] list: found {file_count} files in '{path}' matching '{pattern}'")

            return FListVariable([FNodeVariable(format_path(i)) for i in sorted_items])

        except PermissionError:
            raise PermissionError(
                f"[FILE-MANAGE] list: ERROR — permission denied: '{path}'"
            )
