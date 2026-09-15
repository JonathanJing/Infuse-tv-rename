#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Season TV Rename Tool
批量重命名多季TV剧文件，支持每个季在单独的子文件夹中
"""

import sys
import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from tv_rename import TVRenameTool
from rename_operations import execute_plans


class MultiSeasonTVRenameTool:
    """多季TV剧重命名工具类"""
    
    def __init__(self, root_folder: str, show_name: str, preserve_title: bool = False, preserve_series: bool = False, series_parentheses_suffix: Optional[str] = None, keep_raw_filename: bool = False, renumber: bool = False):
        """
        初始化多季重命名工具
        
        Args:
            root_folder: 包含所有季文件夹的根目录
            show_name: 剧名
            preserve_title: 是否保留集名（默认为False）
        """
        self.root_folder = Path(root_folder)
        self.show_name = show_name.strip()
        self.preserve_title = preserve_title
        self.preserve_series = preserve_series
        self.series_parentheses_suffix = (series_parentheses_suffix or "").strip()
        self.keep_raw_filename = keep_raw_filename
        self.renumber = renumber
        
        # 验证输入
        if not self.root_folder.exists():
            raise FileNotFoundError(f"根目录不存在: {root_folder}")
        
        if not self.root_folder.is_dir():
            raise NotADirectoryError(f"路径不是目录: {root_folder}")
        
        if not self.show_name:
            raise ValueError("剧名不能为空")
    
    def detect_season_folders(self) -> Dict[int, Path]:
        """只识别明确的季标记；重复季号必须由用户消除歧义。"""
        folders = {}
        for item in sorted(self.root_folder.iterdir()):
            if not item.is_dir() or item.is_symlink():
                continue
            match = re.search(r'(?<![A-Za-z0-9])(?:season\s*|s)(\d{1,2})(?!\d)|第\s*(\d{1,2})\s*季|^(\d{1,2})$', item.name, re.I)
            if not match:
                continue
            season = int(next(value for value in match.groups() if value is not None))
            if season in folders:
                raise ValueError(f"重复季号 S{season:02d}: {folders[season].name}, {item.name}")
            folders[season] = item
        return dict(sorted(folders.items()))
    
    def manual_select_season_folders(self) -> Dict[int, Path]:
        """选择目录后逐一输入真实季号，避免把列表序号当季号。"""
        folders = sorted(item for item in self.root_folder.iterdir() if item.is_dir() and not item.is_symlink())
        if not folders:
            return {}
        for index, folder in enumerate(folders, 1):
            print(f"{index}. {folder.name}")
        choice = input("选择目录序号（空格分隔，或 all）: ").strip()
        indices = list(range(len(folders))) if choice.lower() == 'all' else [int(value) - 1 for value in choice.split()]
        if len(set(indices)) != len(indices) or any(index < 0 or index >= len(folders) for index in indices):
            raise ValueError("目录选择无效或重复")
        selected = {}
        for index in indices:
            folder = folders[index]
            season = int(input(f"{folder.name} 的真实季号: "))
            if season < 0 or season in selected:
                raise ValueError("季号无效或重复")
            selected[season] = folder
        return dict(sorted(selected.items()))
    
    def preview_all_seasons(self, season_folders: Dict[int, Path]) -> Dict[int, List[Tuple[Path, str]]]:
        """
        预览所有季的重命名结果
        
        Args:
            season_folders: 季数到文件夹路径的映射字典
            
        Returns:
            季数到重命名计划的映射字典
        """
        all_plans = {}
        
        for season_num, folder_path in season_folders.items():
            print(f"🔍 检查第 {season_num} 季: {folder_path.name}")
            
            try:
                # 创建单季重命名工具
                tool = TVRenameTool(
                    str(folder_path),
                    self.show_name,
                    season_num,
                    1,
                    self.preserve_title,
                    self.preserve_series,
                    self.series_parentheses_suffix,
                    1,  # start_episode
                    self.keep_raw_filename,
                    renumber=self.renumber,
                )  # 单集模式，使用preserve_title/series设置
                rename_plan = tool.preview_rename()
                
                # 转换数据格式以保持兼容性：(Path, str, List[int]) -> (Path, str)
                if rename_plan:
                    rename_plan = [(file_path, new_name) for file_path, new_name, episodes in rename_plan]
                
                if rename_plan:
                    all_plans[season_num] = rename_plan
                    print(f"   ✅ 找到 {len(rename_plan)} 个文件")
                else:
                    print(f"   ⚠️  没有找到媒体文件")
                    
            except Exception as e:
                raise ValueError(f"第 {season_num} 季预览失败: {e}") from e
        
        return all_plans
    
    def execute_all_seasons(self, all_plans: Dict[int, List[Tuple[Path, str]]]) -> Dict[int, Tuple[int, int]]:
        return execute_plans(self.root_folder, all_plans)
    
    def run(self, auto_detect: bool = True, preview_only: bool = False) -> None:
        """
        运行多季重命名工具
        
        Args:
            auto_detect: 是否自动检测季文件夹
            preview_only: 是否仅预览，不执行重命名
        """
        print(f"🎬 Multi-Season Infuse TV Rename Tool")
        print(f"📁 根目录: {self.root_folder}")
        print(f"📺 剧名: {self.show_name}")
        print("=" * 60)
        
        # 检测季文件夹
        if auto_detect:
            print("🔍 自动检测季文件夹...")
            season_folders = self.detect_season_folders()
            
            if not season_folders:
                print("❌ 未找到季文件夹，切换到手动选择模式")
                season_folders = self.manual_select_season_folders()
        else:
            season_folders = self.manual_select_season_folders()
        
        if not season_folders:
            print("❌ 没有选择任何季文件夹")
            return
        
        print(f"\n📋 选择的季文件夹:")
        for season_num, folder_path in sorted(season_folders.items()):
            print(f"   第 {season_num} 季: {folder_path.name}")
        
        # 预览所有季的重命名结果
        print(f"\n🔍 预览重命名结果...")
        all_plans = self.preview_all_seasons(season_folders)
        
        if not all_plans:
            print("❌ 没有找到任何媒体文件")
            return
        
        # 显示总览
        total_files = sum(len(plan) for plan in all_plans.values())
        print(f"\n📊 总览:")
        print(f"   总季数: {len(all_plans)}")
        print(f"   总文件数: {total_files}")
        
        for season_num, rename_plan in sorted(all_plans.items()):
            print(f"   第 {season_num} 季: {len(rename_plan)} 个文件")
            for file_path, new_name in rename_plan:
                print(f"      {file_path.name} -> {new_name}")
        
        if preview_only:
            print("\n🔍 预览模式 - 未执行重命名操作")
            return
        
        # 确认执行
        print(f"\n⚠️  即将重命名 {total_files} 个文件，涉及 {len(all_plans)} 季")
        confirm = input("确认执行重命名操作? (y/N): ").strip().lower()
        
        if confirm not in ['y', 'yes']:
            print("❌ 操作已取消")
            return
        
        # 执行重命名
        results = self.execute_all_seasons(all_plans)
        
        # 显示结果
        print("\n" + "=" * 60)
        print(f"📊 重命名完成:")
        
        total_success = 0
        total_failed = 0
        
        for season_num, (success_count, failed_count) in sorted(results.items()):
            print(f"   第 {season_num} 季: ✅ {success_count} 成功, ❌ {failed_count} 失败")
            total_success += success_count
            total_failed += failed_count
        
        print(f"\n总计: ✅ {total_success} 成功, ❌ {total_failed} 失败")
        
        if total_failed > 0:
            print(f"💡 提示: 失败的文件可能是目标文件名已存在")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量重命名多季TV剧文件，支持每个季在单独的子文件夹中",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 自动检测季文件夹
  python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends"
  
  # 手动选择季文件夹
  python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --manual
  
  # 仅预览
  python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --preview
        """
    )
    
    parser.add_argument(
        '--folder', '-f',
        required=True,
        help='包含所有季文件夹的根目录'
    )
    
    parser.add_argument(
        '--show', '-s',
        required=True,
        help='剧名'
    )
    
    parser.add_argument(
        '--manual', '-m',
        action='store_true',
        help='手动选择季文件夹（默认自动检测）'
    )
    
    parser.add_argument(
        '--preview', '-p',
        action='store_true',
        help='仅预览，不执行重命名'
    )
    
    parser.add_argument("--renumber", action="store_true", help="明确按顺序重新编号")
    args = parser.parse_args()
    
    try:
        # 创建多季重命名工具实例
        tool = MultiSeasonTVRenameTool(args.folder, args.show, renumber=args.renumber)
        
        # 运行重命名工具
        tool.run(auto_detect=not args.manual, preview_only=args.preview)
        
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 