#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Infuse TV Rename Tool 使用示例
演示如何使用TV重命名工具
"""

import os
import tempfile
from pathlib import Path
from tv_rename import TVRenameTool


def create_sample_files(folder_path: str, show_name: str, num_episodes: int = 5):
    """
    创建示例文件用于测试
    
    Args:
        folder_path: 文件夹路径
        show_name: 剧名
        num_episodes: 集数
    """
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)
    
    # 创建示例文件
    for i in range(1, num_episodes + 1):
        # 创建不同格式的示例文件
        files = [
            f"episode_{i:02d}.mp4",
            f"episode_{i:02d}.mkv",
            f"episode_{i:02d}.srt"
        ]
        
        for filename in files:
            file_path = folder / filename
            file_path.touch()  # 创建空文件
            print(f"创建示例文件: {file_path}")


def demo_basic_usage():
    """演示基本用法"""
    print("🎬 Infuse TV Rename Tool 演示")
    print("=" * 50)
    
    # 创建临时文件夹用于演示
    with tempfile.TemporaryDirectory() as temp_dir:
        show_name = "Friends"
        season = 1
        
        print(f"📁 创建临时文件夹: {temp_dir}")
        print(f"📺 剧名: {show_name}")
        print(f"🔢 季数: {season}")
        print()
        
        # 创建示例文件
        create_sample_files(temp_dir, show_name, 3)
        print()
        
        try:
            # 创建重命名工具实例
            tool = TVRenameTool(temp_dir, show_name, season)
            
            # 预览重命名结果
            print("🔍 预览重命名结果:")
            print("-" * 30)
            tool.run(preview_only=True)
            
        except Exception as e:
            print(f"❌ 演示失败: {e}")


def demo_interactive_usage():
    """演示交互式用法"""
    print("\n🎯 交互式使用演示")
    print("=" * 50)
    
    print("要使用此工具，请按以下步骤操作：")
    print()
    print("1. 准备你的TV剧文件夹")
    print("2. 运行命令：")
    print("   python tv_rename.py --folder /path/to/folder --show \"剧名\" --season 1")
    print()
    print("3. 使用预览模式查看结果：")
    print("   python tv_rename.py --folder /path/to/folder --show \"剧名\" --season 1 --preview")
    print()
    print("4. 确认无误后执行重命名")
    print()
    print("📝 示例命令：")
    print("   python tv_rename.py --folder \"/Users/username/Videos/Friends\" --show \"Friends\" --season 1")
    print("   python tv_rename.py -f \"/Users/username/Videos/Breaking Bad\" -s \"Breaking Bad\" -n 2")


if __name__ == "__main__":
    # 运行演示
    demo_basic_usage()
    demo_interactive_usage()
    
    print("\n✅ 演示完成！")
    print("💡 提示：在实际使用前，请确保备份重要文件") 