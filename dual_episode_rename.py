#!/usr/bin/env python3
"""多集文件的兼容入口；复用单季命名与多季执行逻辑。"""
import argparse

from multi_season_rename import MultiSeasonTVRenameTool
from tv_rename import TVRenameTool


class DualEpisodeTVRenameTool(MultiSeasonTVRenameTool):
    def __init__(self, root_folder, show_name, episodes_per_file=2,
                 preserve_title=False, preserve_series=False,
                 series_parentheses_suffix=None, keep_raw_filename=False, renumber=False):
        super().__init__(root_folder, show_name, preserve_title, preserve_series,
                         series_parentheses_suffix, keep_raw_filename, renumber)
        if not 1 <= episodes_per_file <= 5:
            raise ValueError("每个文件的集数必须在1-5之间")
        self.episodes_per_file = episodes_per_file

    def preview_season(self, season_num, folder_path):
        return TVRenameTool(
            str(folder_path), self.show_name, season=season_num,
            episodes_per_file=self.episodes_per_file,
            preserve_title=self.preserve_title, preserve_series=self.preserve_series,
            series_parentheses_suffix=self.series_parentheses_suffix,
            keep_raw_filename=self.keep_raw_filename, renumber=self.renumber,
        ).preview_rename()

    def preview_all_seasons(self, season_folders):
        plans = {}
        for season, folder in sorted(season_folders.items()):
            plan = self.preview_season(season, folder)
            if plan:
                plans[season] = plan
        return plans

    def execute_rename(self, all_plans):
        return self.execute_all_seasons({
            season: [(path, name) for path, name, _ in plan]
            for season, plan in all_plans.items()
        })

    def run(self, preview_only=False):
        plans = self.preview_all_seasons(self.detect_season_folders())
        if not plans:
            print("没有找到媒体文件")
            return
        for season, plan in plans.items():
            print(f"S{season:02d}: {len(plan)} 个文件")
            for path, name, _ in plan:
                print(f"  {path.name} -> {name}")
        if preview_only:
            return
        if input("确认执行重命名操作? (y/N): ").strip().lower() in {'y', 'yes'}:
            print(self.execute_rename(plans))


def main():
    parser = argparse.ArgumentParser(description="多集文件重命名")
    parser.add_argument('--folder', '-f', required=True)
    parser.add_argument('--show', '-s', required=True)
    parser.add_argument('--episodes-per-file', type=int, choices=range(1, 6), default=2)
    parser.add_argument('--preview', '-p', action='store_true')
    parser.add_argument("--renumber", action="store_true", help="按文件顺序重新分配集号")
    args = parser.parse_args()
    try:
        DualEpisodeTVRenameTool(args.folder, args.show, args.episodes_per_file, renumber=args.renumber).run(args.preview)
    except (OSError, ValueError) as error:
        parser.exit(1, f"错误: {error}\n")


if __name__ == '__main__':
    main()
