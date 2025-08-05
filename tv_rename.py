#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Infuse TV Rename Tool
批量重命名TV剧文件以符合Infuse媒体库命名规范
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional


class TVRenameTool:
    """TV剧重命名工具类"""
    
    # 支持的媒体文件扩展名
    SUPPORTED_EXTENSIONS = {
        # 视频文件
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.rmvb', '.rm',
        # 其他媒体文件
        '.m4v', '.3gp', '.ogv',
        # 字幕文件
        '.srt', '.ass', '.ssa', '.sub'
    }
    
    def __init__(self, folder_path: str, show_name: str, season: int = 1, episodes_per_file: int = 1):
        """
        初始化重命名工具
        
        Args:
            folder_path: TV剧文件夹路径
            show_name: 剧名
            season: 季数（默认为1）
            episodes_per_file: 每个文件包含的集数（默认为1）
        """
        self.folder_path = Path(folder_path)
        self.show_name = show_name.strip()
        self.season = season
        self.episodes_per_file = episodes_per_file
        
        # 验证输入
        if not self.folder_path.exists():
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")
        
        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"路径不是文件夹: {folder_path}")
        
        if not self.show_name:
            raise ValueError("剧名不能为空")
        
        if self.season < 1:
            raise ValueError("季数必须大于0")
        
        if episodes_per_file < 1 or episodes_per_file > 5:
            raise ValueError("每个文件的集数必须在1-5之间")
    
    def get_media_files(self) -> List[Path]:
        """
        获取文件夹中的媒体文件
        
        Returns:
            媒体文件路径列表
        """
        media_files = []
        
        for file_path in self.folder_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                media_files.append(file_path)
        
        # 按文件名排序
        media_files.sort(key=lambda x: x.name.lower())
        
        return media_files
    
    def generate_new_name(self, file_path: Path, episodes: List[int]) -> str:
        """
        生成新的文件名
        
        Args:
            file_path: 原文件路径
            episodes: 集数列表
            
        Returns:
            新文件名
        """
        # 格式化季集编号
        season_str = f"S{self.season:02d}"
        
        # 构建集数部分
        episode_parts = [f"E{ep:02d}" for ep in episodes]
        episode_str = "".join(episode_parts)
        
        # 构建新文件名
        new_name = f"{self.show_name}_{season_str}{episode_str}{file_path.suffix}"
        
        return new_name
    
    def preview_rename(self) -> List[Tuple[Path, str, List[int]]]:
        """
        预览重命名结果
        
        Returns:
            原文件路径、新文件名和集数列表的元组列表
        """
        media_files = self.get_media_files()
        
        if not media_files:
            print(f"在文件夹 {self.folder_path} 中没有找到支持的媒体文件")
            return []
        
        rename_plan = []
        episode_counter = 1
        
        for file_path in media_files:
            # 根据每个文件包含的集数生成集数列表
            episodes = list(range(episode_counter, episode_counter + self.episodes_per_file))
            new_name = self.generate_new_name(file_path, episodes)
            rename_plan.append((file_path, new_name, episodes))
            episode_counter += self.episodes_per_file
        
        return rename_plan
    
    def execute_rename(self, rename_plan: List[Tuple[Path, str, List[int]]]) -> Tuple[int, int]:
        """
        执行重命名操作
        
        Args:
            rename_plan: 重命名计划（原文件路径、新文件名和集数列表的元组列表）
            
        Returns:
            成功和失败的文件数量元组
        """
        success_count = 0
        failed_count = 0
        
        for file_path, new_name, episodes in rename_plan:
            new_path = file_path.parent / new_name
            
            try:
                # 检查目标文件是否已存在
                if new_path.exists():
                    print(f"⚠️  跳过 {file_path.name} -> {new_name} (目标文件已存在)")
                    failed_count += 1
                    continue
                
                # 执行重命名
                file_path.rename(new_path)
                episode_text = "+".join([f"第{ep}集" for ep in episodes])
                print(f"✅ {file_path.name} -> {new_name} ({episode_text})")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 重命名失败 {file_path.name} -> {new_name}: {e}")
                failed_count += 1
        
        return success_count, failed_count
    
    def run(self, preview_only: bool = False) -> None:
        """
        运行重命名工具
        
        Args:
            preview_only: 是否仅预览，不执行重命名
        """
        print(f"🎬 Infuse TV Rename Tool")
        print(f"📁 文件夹: {self.folder_path}")
        print(f"📺 剧名: {self.show_name}")
        print(f"🔢 季数: {self.season}")
        print("-" * 50)
        
        # 获取重命名计划
        rename_plan = self.preview_rename()
        
        if not rename_plan:
            return
        
        # 显示预览
        print(f"📋 找到 {len(rename_plan)} 个媒体文件:")
        print()
        
        for i, (file_path, new_name) in enumerate(rename_plan, 1):
            print(f"{i:2d}. {file_path.name}")
            print(f"    -> {new_name}")
            print()
        
        if preview_only:
            print("🔍 预览模式 - 未执行重命名操作")
            return
        
        # 确认执行
        print(f"⚠️  即将重命名 {len(rename_plan)} 个文件")
        confirm = input("确认执行重命名操作? (y/N): ").strip().lower()
        
        if confirm not in ['y', 'yes']:
            print("❌ 操作已取消")
            return
        
        print()
        print("🔄 开始重命名...")
        print("-" * 50)
        
        # 执行重命名
        success_count, failed_count = self.execute_rename(rename_plan)
        
        print("-" * 50)
        print(f"📊 重命名完成:")
        print(f"   ✅ 成功: {success_count} 个文件")
        print(f"   ❌ 失败: {failed_count} 个文件")
        
        if failed_count > 0:
            print(f"💡 提示: 失败的文件可能是目标文件名已存在")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量重命名TV剧文件以符合Infuse媒体库命名规范",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 tv_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --season 1
  python3 tv_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --season 1 --preview
  python3 tv_rename.py -f "/Users/username/Videos/Breaking Bad" -s "Breaking Bad" -n 2
        """
    )
    
    parser.add_argument(
        '--folder', '-f',
        required=True,
        help='TV剧文件夹路径'
    )
    
    parser.add_argument(
        '--show', '-s',
        required=True,
        help='剧名'
    )
    
    parser.add_argument(
        '--season', '-n',
        type=int,
        default=1,
        help='季数 (默认: 1)'
    )
    
    parser.add_argument(
        '--preview', '-p',
        action='store_true',
        help='仅预览，不执行重命名'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建重命名工具实例
        tool = TVRenameTool(args.folder, args.show, args.season)
        
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