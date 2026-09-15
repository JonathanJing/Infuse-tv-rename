#!/usr/bin/env python3
"""在临时目录演示多季、缺集、字幕及撤销，不操作真实媒体。"""
import tempfile
from pathlib import Path

from multi_season_rename import MultiSeasonTVRenameTool
from rename_logger import RenameLogger


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for season, episodes in [(1, [1, 2]), (2, [8, 10])]:
            folder = root / f'S{season:02d}'
            folder.mkdir()
            for episode in episodes:
                stem = f'Friends.S{season:02d}E{episode:02d}.1080p'
                (folder / f'{stem}.mp4').write_bytes(b'demo')
                (folder / f'{stem}.zh.srt').write_text('示例字幕')
        tool = MultiSeasonTVRenameTool(directory, 'Friends')
        plans = tool.preview_all_seasons(tool.detect_season_folders())
        for plan in plans.values():
            for path, name in plan:
                print(f'{path.name} -> {name}')
        print('重命名:', tool.execute_all_seasons(plans))
        print('恢复:', RenameLogger(directory).undo_last_batch())


if __name__ == '__main__':
    main()
