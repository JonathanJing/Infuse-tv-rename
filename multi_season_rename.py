#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Season TV Rename Tool
批量重命名多季TV剧文件，支持每个季在单独的子文件夹中
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from tv_rename import TVRenameTool


class MultiSeasonTVRenameTool:
    """多季TV剧重命名工具类"""
    
    def __init__(self, root_folder: str, show_name: str, preserve_title: bool = False, preserve_series: bool = False):
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
        
        # 验证输入
        if not self.root_folder.exists():
            raise FileNotFoundError(f"根目录不存在: {root_folder}")
        
        if not self.root_folder.is_dir():
            raise NotADirectoryError(f"路径不是目录: {root_folder}")
        
        if not self.show_name:
            raise ValueError("剧名不能为空")
    
    def detect_season_folders(self) -> Dict[int, Path]:
        """
        自动检测季文件夹
        
        Returns:
            季数到文件夹路径的映射字典
        """
        season_folders = {}
        
        # 常见的季文件夹命名模式
        season_patterns = [
            r'season\s*(\d+)',  # Season 1, Season1
            r's(\d+)',          # S1, S01
            r'第(\d+)季',        # 第1季
            r'season\s*(\d+)',  # season 1, season1
            r'(\d+)',           # 纯数字
        ]
        
        for item in self.root_folder.iterdir():
            if not item.is_dir():
                continue
            
            folder_name = item.name.lower()
            
            # 尝试匹配季数
            for pattern in season_patterns:
                match = re.search(pattern, folder_name)
                if match:
                    season_num = int(match.group(1))
                    season_folders[season_num] = item
                    break
        
        return season_folders
    
    def manual_select_season_folders(self) -> Dict[int, Path]:
        """
        手动选择季文件夹
        
        Returns:
            季数到文件夹路径的映射字典
        """
        season_folders = {}
        
        print(f"📁 在 {self.root_folder} 中找到以下子文件夹:")
        print()
        
        folders = [item for item in self.root_folder.iterdir() if item.is_dir()]
        folders.sort(key=lambda x: x.name.lower())
        
        for i, folder in enumerate(folders, 1):
            print(f"{i:2d}. {folder.name}")
        
        print()
        print("请选择要处理的季文件夹，输入对应的数字（用空格分隔，如: 1 2 3）:")
        print("或者输入 'all' 处理所有文件夹")
        
        while True:
            try:
                choice = input("选择: ").strip()
                
                if choice.lower() == 'all':
                    # 处理所有文件夹
                    for i, folder in enumerate(folders, 1):
                        season_folders[i] = folder
                    break
                
                # 解析选择的数字
                selected_indices = [int(x) - 1 for x in choice.split()]
                
                for idx in selected_indices:
                    if 0 <= idx < len(folders):
                        season_folders[idx + 1] = folders[idx]
                    else:
                        print(f"❌ 无效的选择: {idx + 1}")
                        continue
                
                if season_folders:
                    break
                else:
                    print("❌ 请至少选择一个文件夹")
                    
            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n❌ 操作被用户中断")
                sys.exit(1)
        
        return season_folders
    
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
                tool = TVRenameTool(str(folder_path), self.show_name, season_num, 1, self.preserve_title, self.preserve_series)  # 单集模式，使用preserve_title/series设置
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
                print(f"   ❌ 处理失败: {e}")
        
        return all_plans
    
    def execute_all_seasons(self, all_plans: Dict[int, List[Tuple[Path, str]]]) -> Dict[int, Tuple[int, int]]:
        """
        执行所有季的重命名操作
        
        Args:
            all_plans: 季数到重命名计划的映射字典
            
        Returns:
            季数到（成功数，失败数）的映射字典
        """
        results = {}
        
        for season_num, rename_plan in all_plans.items():
            print(f"\n🔄 开始重命名第 {season_num} 季...")
            print("-" * 40)
            
            success_count = 0
            failed_count = 0
            
            for file_path, new_name in rename_plan:
                new_path = file_path.parent / new_name
                
                try:
                    # 检查目标文件是否已存在
                    if new_path.exists():
                        print(f"⚠️  跳过 {file_path.name} -> {new_name} (目标文件已存在)")
                        failed_count += 1
                        continue
                    
                    # 执行重命名
                    file_path.rename(new_path)
                    print(f"✅ {file_path.name} -> {new_name}")
                    success_count += 1
                    
                except Exception as e:
                    print(f"❌ 重命名失败 {file_path.name} -> {new_name}: {e}")
                    failed_count += 1
            
            results[season_num] = (success_count, failed_count)
        
        return results
    
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
    
    args = parser.parse_args()
    
    try:
        # 创建多季重命名工具实例
        tool = MultiSeasonTVRenameTool(args.folder, args.show)
        
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