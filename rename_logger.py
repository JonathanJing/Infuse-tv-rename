import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional

class RenameLogger:
    """Handles logging of rename operations and restoration."""
    
    HISTORY_FILE_NAME = "rename_history.json"
    
    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path)
        self.history_file = self.folder_path / self.HISTORY_FILE_NAME
        
    def log_batch(self, renames: List[Tuple[Path, Path]]) -> None:
        """
        Log a batch of successful renames.
        
        Args:
            renames: List of (original_path, new_path) tuples
        """
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
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
            
    def _save_history_data(self, history: List[Dict]) -> None:
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            
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
            
        last_entry = history.pop()
        renames = last_entry.get("renames", [])
        
        success_count = 0
        failed_count = 0
        
        # Reverse order to handle potential chains (though typically not an issue here)
        for item in reversed(renames):
            original_path = Path(item["original"])
            new_path = Path(item["new"])
            
            if not new_path.exists():
                print(f"⚠️  无法恢复 {original_path.name}: 文件 {new_path.name} 不存在")
                failed_count += 1
                continue
                
            if original_path.exists():
                 print(f"⚠️  无法恢复 {original_path.name}: 目标文件已存在")
                 failed_count += 1
                 continue
                 
            try:
                new_path.rename(original_path)
                print(f"✅ 已恢复: {new_path.name} -> {original_path.name}")
                success_count += 1
            except Exception as e:
                print(f"❌ 恢复失败 {new_path.name}: {e}")
                failed_count += 1
        
        # Update history file if we popped an entry
        # Note: If restoration partially fails, we still remove the entry from history?
        # Ideally we should keep track of what's left, but for simplicity we remove it 
        # or maybe only remove if fully successful. 
        # Let's remove it to prevent stuck loops, but user should be warned.
        self._save_history_data(history)
        
        return success_count, failed_count
