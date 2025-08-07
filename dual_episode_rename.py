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
from name_utils import extract_series_title_from_filename


class DualEpisodeTVRenameTool:
    """双集TV剧重命名工具类"""
    
    # 支持的媒体文件扩展名
    SUPPORTED_EXTENSIONS = {
        # 视频文件
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.rmvb', '.rm',
        # 其他媒体文件
        '.m4v', '.3gp', '.ogv',
        # 字幕文件
        '.srt', '.ass', '.ssa', '.sub'
    }
    
    def __init__(self, root_folder: str, show_name: str, episodes_per_file: int = 2, preserve_title: bool = False, preserve_series: bool = False):
        """
        初始化多集重命名工具
        
        Args:
            root_folder: 包含所有季文件夹的根目录
            show_name: 剧名
            episodes_per_file: 每个文件包含的集数（默认为2）
            preserve_title: 是否保留集名（默认为False）
        """
        self.root_folder = Path(root_folder)
        self.show_name = show_name.strip()
        self.episodes_per_file = episodes_per_file
        self.preserve_title = preserve_title
        self.preserve_series = preserve_series
        
        # 验证输入
        if not self.root_folder.exists():
            raise FileNotFoundError(f"根目录不存在: {root_folder}")
        
        if not self.root_folder.is_dir():
            raise NotADirectoryError(f"路径不是目录: {root_folder}")
        
        if not self.show_name:
            raise ValueError("剧名不能为空")
        
        if episodes_per_file < 1 or episodes_per_file > 5:
            raise ValueError("每个文件的集数必须在1-5之间")
    
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
        
        # 匹配 "EXX EYY" 或 "EXXEYY" 格式
        pattern3 = r'[Ee](\d+)\s*[Ee](\d+)'
        match = re.search(pattern3, filename)
        
        if match:
            episode1 = int(match.group(1))
            episode2 = int(match.group(2))
            return episode1, episode2
        
        # 匹配 "EXX-EYY" 格式
        pattern4 = r'[Ee](\d+)-[Ee](\d+)'
        match = re.search(pattern4, filename)
        
        if match:
            episode1 = int(match.group(1))
            episode2 = int(match.group(2))
            return episode1, episode2
        
        # 匹配 "XX-YY" 格式（纯数字）
        pattern5 = r'(\d+)-(\d+)'
        match = re.search(pattern5, filename)
        
        if match:
            episode1 = int(match.group(1))
            episode2 = int(match.group(2))
            # 只有当数字在合理范围内才认为是集数
            if 1 <= episode1 <= 999 and 1 <= episode2 <= 999 and episode2 > episode1:
                return episode1, episode2
        
        # 匹配单集 "第XX集" 格式
        pattern6 = r'第(\d+)集'
        match = re.search(pattern6, filename)
        
        if match:
            episode1 = int(match.group(1))
            return episode1, None
        
        # 匹配单集 "EXX" 格式
        pattern7 = r'[Ee](\d+)'
        match = re.search(pattern7, filename)
        
        if match:
            episode1 = int(match.group(1))
            return episode1, None
        
        # 匹配单集纯数字格式（最后尝试）
        pattern8 = r'(\d+)'
        matches = re.findall(pattern8, filename)
        
        if matches:
            # 取最后一个数字作为集数（通常文件名末尾的数字是集数）
            for match in reversed(matches):
                episode1 = int(match)
                if 1 <= episode1 <= 999:
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
    
    def extract_episode_title(self, filename: str) -> str:
        """
        从文件名中提取集名
        
        Args:
            filename: 文件名
            
        Returns:
            提取的集名，如果没有找到则返回空字符串
        """
        if not self.preserve_title:
            return ""
        
        # 移除文件扩展名
        name_without_ext = Path(filename).stem
        
        # 移除剧名（如果存在）
        import re
        cleaned_name = name_without_ext
        
        # 尝试移除剧名的各种变体
        show_name_variants = [
            self.show_name,
            self.show_name.replace(' ', '.'),
            self.show_name.replace(' ', '_'),
            self.show_name.replace(' ', '-'),
            re.sub(r'[^\w\s]', '', self.show_name)  # 移除特殊字符
        ]
        
        for variant in show_name_variants:
            if variant:
                cleaned_name = re.sub(rf'\b{re.escape(variant)}\b', '', cleaned_name, flags=re.IGNORECASE)
        
        # 清理常见的标识符
        patterns_to_remove = [
            r'\b[Ss]\d+[Ee]\d+\b',  # S01E01 格式
            r'\b[Ee]\d+\b',         # E01 格式
            r'\b第\d+集\b',         # 第01集 格式
            r'\b\d+\b',             # 纯数字
            r'\b(720p|1080p|4k|hd|sd|hdtv|web-dl|bluray|bdrip|dvdrip|webrip)\b',  # 质量标识
            r'\b(mp4|mkv|avi|mov|wmv|flv|webm|rmvb|rm|m4v)\b',  # 格式标识
            r'[._\-\[\](){}]',      # 特殊字符
        ]
        
        for pattern in patterns_to_remove:
            cleaned_name = re.sub(pattern, ' ', cleaned_name, flags=re.IGNORECASE)
        
        # 清理多余空格并返回
        episode_title = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        # 如果提取的标题太短或包含太多数字，则认为无效
        if len(episode_title) < 2 or len(re.findall(r'\d', episode_title)) > len(episode_title) * 0.5:
            return ""
        
        return episode_title
    
    def generate_new_name(self, file_path: Path, episodes: List[int], season: int) -> str:
        """
        生成新的文件名
        
        Args:
            file_path: 原文件路径
            episodes: 集数列表
            season: 季数
            
        Returns:
            新文件名
        """
        # 格式化季集编号
        season_str = f"S{season:02d}"
        
        # 构建集数部分
        episode_parts = [f"E{ep:02d}" for ep in episodes]
        episode_str = "".join(episode_parts)
        
        # 选择剧名（可从原文件名提取）
        series_name = self.show_name
        if self.preserve_series:
            series_name = extract_series_title_from_filename(file_path.name, fallback=self.show_name)

        # 提取集名（如果需要）
        episode_title = self.extract_episode_title(file_path.name)
        
        # 构建新文件名
        if episode_title:
            new_name = f"{series_name}_{season_str}{episode_str}_{episode_title}{file_path.suffix}"
        else:
            new_name = f"{series_name}_{season_str}{episode_str}{file_path.suffix}"
        
        return new_name
    
    def preview_season(self, season_num: int, folder_path: Path) -> List[Tuple[Path, str, List[int]]]:
        """
        预览单个季的重命名结果
        
        Args:
            season_num: 季数
            folder_path: 季文件夹路径
            
        Returns:
            重命名计划列表：(文件路径, 新文件名, 集数列表)
        """
        media_files = self.get_media_files(folder_path)
        
        if not media_files:
            print(f"在文件夹 {folder_path} 中没有找到支持的媒体文件")
            return []
        
        rename_plan = []
        episode_counter = 1  # 用于按顺序分配集数
        
        for file_path in media_files:
            # 尝试从文件名解析集数（目前仅支持双集，可以扩展）
            episode1, episode2 = self.extract_episode_numbers(file_path.name)
            
            if episode1 is not None and episode2 is not None and self.episodes_per_file == 2:
                # 成功解析到双集
                episodes = [episode1, episode2]
                new_name = self.generate_new_name(file_path, episodes, season_num)
                rename_plan.append((file_path, new_name, episodes))
            elif episode1 is not None and episode2 is None and self.episodes_per_file == 1:
                # 成功解析到单集
                episodes = [episode1]
                new_name = self.generate_new_name(file_path, episodes, season_num)
                rename_plan.append((file_path, new_name, episodes))
            else:
                # 无法解析或格式不匹配，按顺序分配集数
                print(f"⚠️  按顺序分配集数 (每文件{self.episodes_per_file}集): {file_path.name}")
                episodes = list(range(episode_counter, episode_counter + self.episodes_per_file))
                new_name = self.generate_new_name(file_path, episodes, season_num)
                rename_plan.append((file_path, new_name, episodes))
                episode_counter += self.episodes_per_file
        
        return rename_plan
    
    def preview_all_seasons(self, season_folders: Dict[int, Path]) -> Dict[int, List[Tuple[Path, str, List[int]]]]:
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
    
    def execute_rename(self, all_plans: Dict[int, List[Tuple[Path, str, List[int]]]]) -> Dict[int, Tuple[int, int]]:
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