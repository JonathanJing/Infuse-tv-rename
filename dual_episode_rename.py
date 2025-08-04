#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dual Episode TV Rename Tool
专门处理每个文件包含两集的TV剧重命名工具
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict


class DualEpisodeTVRenameTool:
    """双集TV剧重命名工具类"""
    
    # 支持的媒体文件扩展名
    SUPPORTED_EXTENSIONS = {
        # 视频文件
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
        # 其他媒体文件
        '.m4v', '.3gp', '.ogv',
        # 字幕文件
        '.srt', '.ass', '.ssa', '.sub'
    }
    
    def __init__(self, root_folder: str, show_name: str):
        """
        初始化双集重命名工具
        
        Args:
            root_folder: 包含所有季文件夹的根目录
            show_name: 剧名
        """
        self.root_folder = Path(root_folder)
        self.show_name = show_name.strip()
        
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
    
    def extract_episode_numbers(self, filename: str) -> Tuple[int, int]:
        """
        从文件名中提取集数
        
        Args:
            filename: 文件名
            
        Returns:
            两集的集数元组，如果是单集则第二个数为None
        """
        # 匹配 "第XX集 第YY集" 格式
        pattern1 = r'第(\d+)集\s*第(\d+)集'
        match = re.search(pattern1, filename)
        
        if match:
            episode1 = int(match.group(1))
            episode2 = int(match.group(2))
            return episode1, episode2
        
        # 匹配 "第XX-YY集" 格式
        pattern2 = r'第(\d+)-(\d+)集'
        match = re.search(pattern2, filename)
        
        if match:
            episode1 = int(match.group(1))
            episode2 = int(match.group(2))
            return episode1, episode2
        
        # 匹配单集 "第XX集" 格式
        pattern3 = r'第(\d+)集'
        match = re.search(pattern3, filename)
        
        if match:
            episode1 = int(match.group(1))
            return episode1, None
        
        # 如果没有匹配到，返回None
        return None, None
    
    def get_media_files(self, folder_path: Path) -> List[Path]:
        """
        获取文件夹中的媒体文件
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            媒体文件路径列表
        """
        media_files = []
        
        for file_path in folder_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                media_files.append(file_path)
        
        # 按文件名排序
        media_files.sort(key=lambda x: x.name.lower())
        
        return media_files
    
    def generate_new_name(self, file_path: Path, episode1: int, episode2: int, season: int) -> str:
        """
        生成新的文件名
        
        Args:
            file_path: 原文件路径
            episode1: 第一集集数
            episode2: 第二集集数（可能为None）
            season: 季数
            
        Returns:
            新文件名
        """
        # 格式化季集编号
        season_str = f"S{season:02d}"
        episode1_str = f"E{episode1:02d}"
        
        if episode2 is not None:
            episode2_str = f"E{episode2:02d}"
            # 构建新文件名：剧名_S01E01E02.扩展名
            new_name = f"{self.show_name}_{season_str}{episode1_str}{episode2_str}{file_path.suffix}"
        else:
            # 构建新文件名：剧名_S01E01.扩展名
            new_name = f"{self.show_name}_{season_str}{episode1_str}{file_path.suffix}"
        
        return new_name
    
    def preview_season(self, season_num: int, folder_path: Path) -> List[Tuple[Path, str, int, int]]:
        """
        预览单个季的重命名结果
        
        Args:
            season_num: 季数
            folder_path: 季文件夹路径
            
        Returns:
            重命名计划列表
        """
        media_files = self.get_media_files(folder_path)
        
        if not media_files:
            print(f"在文件夹 {folder_path} 中没有找到支持的媒体文件")
            return []
        
        rename_plan = []
        
        for file_path in media_files:
            episode1, episode2 = self.extract_episode_numbers(file_path.name)
            
            if episode1 is not None:
                new_name = self.generate_new_name(file_path, episode1, episode2, season_num)
                rename_plan.append((file_path, new_name, episode1, episode2))
            else:
                print(f"⚠️  无法解析文件名中的集数: {file_path.name}")
        
        return rename_plan
    
    def preview_all_seasons(self, season_folders: Dict[int, Path]) -> Dict[int, List[Tuple[Path, str, int, int]]]:
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
                rename_plan = self.preview_season(season_num, folder_path)
                
                if rename_plan:
                    all_plans[season_num] = rename_plan
                    print(f"   ✅ 找到 {len(rename_plan)} 个文件")
                else:
                    print(f"   ⚠️  没有找到媒体文件")
                    
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
        
        return all_plans
    
    def execute_rename(self, all_plans: Dict[int, List[Tuple[Path, str, int, int]]]) -> Dict[int, Tuple[int, int]]:
        """
        执行重命名操作
        
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
            
            for file_path, new_name, episode1, episode2 in rename_plan:
                new_path = file_path.parent / new_name
                
                try:
                    # 检查目标文件是否已存在
                    if new_path.exists():
                        print(f"⚠️  跳过 {file_path.name} -> {new_name} (目标文件已存在)")
                        failed_count += 1
                        continue
                    
                    # 执行重命名
                    file_path.rename(new_path)
                    if episode2 is not None:
                        print(f"✅ {file_path.name} -> {new_name} (第{episode1}集+第{episode2}集)")
                    else:
                        print(f"✅ {file_path.name} -> {new_name} (第{episode1}集)")
                    success_count += 1
                    
                except Exception as e:
                    print(f"❌ 重命名失败 {file_path.name} -> {new_name}: {e}")
                    failed_count += 1
            
            results[season_num] = (success_count, failed_count)
        
        return results
    
    def run(self, preview_only: bool = False) -> None:
        """
        运行双集重命名工具
        
        Args:
            preview_only: 是否仅预览，不执行重命名
        """
        print(f"🎬 Dual Episode Infuse TV Rename Tool")
        print(f"📁 根目录: {self.root_folder}")
        print(f"📺 剧名: {self.show_name}")
        print("=" * 60)
        
        # 检测季文件夹
        print("🔍 自动检测季文件夹...")
        season_folders = self.detect_season_folders()
        
        if not season_folders:
            print("❌ 未找到季文件夹")
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
        
        # 显示示例重命名
        print(f"\n📝 重命名示例:")
        for season_num, rename_plan in sorted(all_plans.items()):
            if rename_plan:
                file_path, new_name, episode1, episode2 = rename_plan[0]
                print(f"   第 {season_num} 季: {file_path.name} -> {new_name}")
                break
        
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
        results = self.execute_rename(all_plans)
        
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
        description="专门处理每个文件包含两集的TV剧重命名工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 预览重命名结果
  python3 dual_episode_rename.py --folder "/path/to/tv/show" --show "剧名" --preview
  
  # 执行重命名
  python3 dual_episode_rename.py --folder "/path/to/tv/show" --show "剧名"
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
        '--preview', '-p',
        action='store_true',
        help='仅预览，不执行重命名'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建双集重命名工具实例
        tool = DualEpisodeTVRenameTool(args.folder, args.show)
        
        # 运行重命名工具
        tool.run(preview_only=args.preview)
        
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