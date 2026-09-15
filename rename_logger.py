import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RenameLogger:
    """Handles logging of rename operations and restoration."""

    HISTORY_FILE_NAME = "rename_history.json"

    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path)
        self.history_file = self.folder_path / self.HISTORY_FILE_NAME

    def log_batch(self, renames: List[Tuple[Path, Path]]) -> None:
        """Log a batch of successful renames."""
        if not renames:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "renames": [
                {
                    "original": str(p1.absolute()),
                    "new": str(p2.absolute())
                }
                for p1, p2 in renames
            ]
        }

        history = self._load_history_data()
        history.append(entry)
        self._save_history_data(history)

    def _load_history_data(self) -> List[Dict]:
        try:
            with self.history_file.open(encoding="utf-8") as stream:
                history = json.load(stream)
        except FileNotFoundError:
            return []
        if not isinstance(history, list):
            raise ValueError(f"Invalid rename history: {self.history_file}")
        for entry in history:
            if not isinstance(entry, dict) or not isinstance(entry.get("renames"), list):
                raise ValueError(f"Invalid rename history entry: {self.history_file}")
            for item in entry["renames"]:
                if not isinstance(item, dict) or any(
                    not isinstance(item.get(key), str) or not item[key]
                    for key in ("original", "new")
                ):
                    raise ValueError(f"Invalid rename history paths: {self.history_file}")
        return history

    def _save_history_data(self, history: List[Dict]) -> None:
        # Replace only after a complete write; a failed save leaves the old log intact.
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.folder_path,
                prefix=f".{self.HISTORY_FILE_NAME}.", delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                json.dump(history, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.history_file)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def has_history(self) -> bool:
        history = self._load_history_data()
        return len(history) > 0

    def get_last_batch_info(self) -> Optional[Dict]:
        history = self._load_history_data()
        if not history:
            return None
        last_entry = history[-1]
        return {
            "timestamp": last_entry.get("timestamp"),
            "count": len(last_entry.get("renames", []))
        }

    def undo_last_batch(self) -> Tuple[int, int]:
        """
        Undo the last batch of renames.

        Returns:
            (success_count, failed_count)
        """
        history = self._load_history_data()
        if not history:
            return 0, 0

        last_entry = history[-1]
        renames = last_entry.get("renames", [])

        success_count = 0
        pending = []

        # Undo in reverse order so chained renames can be restored.
        for item in reversed(renames):
            original_path = Path(item["original"])
            new_path = Path(item["new"])

            if not new_path.exists():
                print(f"⚠️  无法恢复 {original_path.name}: 文件 {new_path.name} 不存在")
                pending.append(item)
                continue

            try:
                destination_exists = original_path.exists() or original_path.is_symlink()
                case_only = (
                    destination_exists
                    and original_path.parent == new_path.parent
                    and original_path.name != new_path.name
                    and original_path.name.casefold() == new_path.name.casefold()
                    and not original_path.is_symlink()
                    and original_path.samefile(new_path)
                    # Separate directory entries can be hard links on a case-sensitive disk.
                    and original_path.name not in {p.name for p in original_path.parent.iterdir()}
                )
                if destination_exists and not case_only:
                    print(f"⚠️  无法恢复 {original_path.name}: 目标文件已存在")
                    pending.append(item)
                    continue

                new_path.rename(original_path)
                print(f"✅ 已恢复: {new_path.name} -> {original_path.name}")
                success_count += 1
            except OSError as e:
                print(f"❌ 恢复失败 {new_path.name}: {e}")
                pending.append(item)

        if pending:
            last_entry["renames"] = list(reversed(pending))
        else:
            history.pop()
        self._save_history_data(history)
        return success_count, len(pending)
