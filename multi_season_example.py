#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Season TV Rename Tool 使用示例
演示如何使用多季重命名工具处理不同文件夹结构的电视剧
"""

import os
import sys
from pathlib import Path
from multi_season_rename import MultiSeasonTVRenameTool


def create_example_structure():
    """创建示例文件夹结构"""
    base_dir = Path("example_tv_show")
    
    # 创建根目录
    base_dir.mkdir(exist_ok=True)
    
    # 创建不同的季文件夹结构示例
    season_structures = [
        "Season 1",
        "Season 2", 
        "Season 3",
        "S01",
        "S02",
        "第1季",
        "第2季",
        "1",
        "2",
        "season1",
        "season2"
    ]
    
    # 为每个季文件夹创建示例文件
    for i, folder_name in enumerate(season_structures, 1):
        season_dir = base_dir / folder_name
        season_dir.mkdir(exist_ok=True)
        
        # 创建示例视频文件
        for episode in range(1, 6):  # 每季5集
            video_file = season_dir / f"episode_{episode}.mp4"
            video_file.touch()  # 创建空文件作为示例
            
            # 创建对应的字幕文件
            subtitle_file = season_dir / f"episode_{episode}.srt"
            subtitle_file.touch()
    
    print(f"✅ 创建示例文件夹结构: {base_dir}")
    print("📁 文件夹结构:")
    for item in sorted(base_dir.iterdir()):
        if item.is_dir():
            print(f"   {item.name}/")
            for file in sorted(item.iterdir()):
                print(f"     {file.name}")
    print()


def demonstrate_auto_detection():
    """演示自动检测功能"""
    print("🔍 演示自动检测功能")
    print("=" * 50)
    
    try:
        tool = MultiSeasonTVRenameTool("example_tv_show", "Friends")
        season_folders = tool.detect_season_folders()
        
        print("自动检测到的季文件夹:")
        for season_num, folder_path in sorted(season_folders.items()):
            print(f"   第 {season_num} 季: {folder_path.name}")
        
        print(f"\n总共检测到 {len(season_folders)} 个季文件夹")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


def demonstrate_preview():
    """演示预览功能"""
    print("\n🔍 演示预览功能")
    print("=" * 50)
    
    try:
        tool = MultiSeasonTVRenameTool("example_tv_show", "Friends")
        season_folders = tool.detect_season_folders()
        
        if season_folders:
            print("预览重命名结果:")
            all_plans = tool.preview_all_seasons(season_folders)
            
            for season_num, rename_plan in sorted(all_plans.items()):
                print(f"\n第 {season_num} 季:")
                for i, (old_path, new_name) in enumerate(rename_plan[:3], 1):  # 只显示前3个
                    print(f"  {i}. {old_path.name} -> {new_name}")
                if len(rename_plan) > 3:
                    print(f"  ... 还有 {len(rename_plan) - 3} 个文件")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


def show_usage_examples():
    """显示使用示例"""
    print("\n📖 使用示例")
    print("=" * 50)
    
    examples = [
        {
            "description": "自动检测季文件夹并重命名",
            "command": "python3 multi_season_rename.py --folder \"/path/to/tv/show\" --show \"Friends\""
        },
        {
            "description": "手动选择季文件夹",
            "command": "python3 multi_season_rename.py --folder \"/path/to/tv/show\" --show \"Friends\" --manual"
        },
        {
            "description": "仅预览重命名结果",
            "command": "python3 multi_season_rename.py --folder \"/path/to/tv/show\" --show \"Friends\" --preview"
        },
        {
            "description": "使用短参数",
            "command": "python3 multi_season_rename.py -f \"/path/to/tv/show\" -s \"Friends\" -p"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}")
        print(f"   {example['command']}")
        print()


def show_supported_patterns():
    """显示支持的文件夹命名模式"""
    print("📋 支持的季文件夹命名模式")
    print("=" * 50)
    
    patterns = [
        "Season 1, Season 2, Season 3...",
        "Season1, Season2, Season3...", 
        "S01, S02, S03...",
        "第1季, 第2季, 第3季...",
        "season1, season2, season3...",
        "1, 2, 3... (纯数字)"
    ]
    
    for pattern in patterns:
        print(f"   • {pattern}")
    
    print("\n💡 提示: 如果自动检测失败，可以使用 --manual 参数手动选择文件夹")


def main():
    """主函数"""
    print("🎬 Multi-Season TV Rename Tool 使用示例")
    print("=" * 60)
    
    # 检查是否存在示例文件夹
    if not Path("example_tv_show").exists():
        print("📁 创建示例文件夹结构...")
        create_example_structure()
    
    # 演示各种功能
    demonstrate_auto_detection()
    demonstrate_preview()
    show_usage_examples()
    show_supported_patterns()
    
    print("✅ 示例演示完成！")
    print("\n💡 要清理示例文件，请删除 'example_tv_show' 文件夹")


if __name__ == "__main__":
    main() 