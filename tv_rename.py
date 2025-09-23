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
from name_utils import extract_series_title_from_filename, extract_episode_index_from_filename


class TVRenameTool:
    """TV剧重命名工具类"""
    
    # 媒体文件扩展名分类
    VIDEO_EXTENSIONS = {
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.rmvb', '.rm',
        '.m4v', '.3gp', '.ogv'
    }
    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub'}
    
    def __init__(self, folder_path: str, show_name: str, season: int = 1, episodes_per_file: int = 1, preserve_title: bool = False, preserve_series: bool = False, series_parentheses_suffix: Optional[str] = None):
        """
        初始化重命名工具
        
        Args:
            folder_path: TV剧文件夹路径
            show_name: 剧名
            season: 季数（默认为1）
            episodes_per_file: 每个文件包含的集数（默认为1）
            preserve_title: 是否保留集名（默认为False）
        """
        self.folder_path = Path(folder_path)
        self.show_name = show_name.strip()
        self.season = season
        self.episodes_per_file = episodes_per_file
        self.preserve_title = preserve_title
        self.preserve_series = preserve_series
        self.series_parentheses_suffix = (series_parentheses_suffix or "").strip()
        
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
    
    def get_video_files(self) -> List[Path]:
        """
        获取文件夹中的视频文件（用于编号）
        """
        video_files = []
        for file_path in self.folder_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.VIDEO_EXTENSIONS:
                video_files.append(file_path)
        # 优先按文件名中的集数排序（支持中文数字，如“第三十一回”），其次按名称
        def sort_key(p: Path):
            idx = extract_episode_index_from_filename(p.name)
            # 将无索引的放在后面
            return (idx is None, idx if idx is not None else 10**9, p.name.lower())

        video_files.sort(key=sort_key)
        return video_files

    def _normalized_stem_for_match(self, stem: str) -> str:
        """生成用于匹配的视频/字幕文件名规范化stem（不去除季集标记）。"""
        text = stem
        # 去括号内容
        text = re.sub(r'[\[\(（【].*?[\]\)）】]', ' ', text)
        # 去除结尾语言代码段（以分隔符分段的token）
        lang_pat = re.compile(r'(?:[._\-\s])(zh(?:-[A-Za-z]+)?|en|eng|chs|cht|chi|sc|tc|ja|jp|ko|kr|es|fr|de|ru|it|pt|pt-br)(?=$|[._\-\s])', re.IGNORECASE)
        # 反复清理直到不再匹配（处理多段如 .chs.eng）
        while True:
            new_text = lang_pat.sub('', text)
            if new_text == text:
                break
            text = new_text
        # 统一分隔符和大小写
        text = re.sub(r'[._\-]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip().lower()
        return text

    def _extract_subtitle_lang_suffix(self, video_stem: str, subtitle_stem: str) -> str:
        """从字幕stem中提取语言后缀（如 'zh' 或 'chs.eng'）。"""
        remainder = ''
        if subtitle_stem.startswith(video_stem):
            remainder = subtitle_stem[len(video_stem):]
        # 也尝试以分隔符开头的差异
        if remainder and remainder[0] in ['.', '_', '-', ' ']:
            remainder = remainder[1:]
        # 提取所有语言token
        tokens = re.findall(r'(?:^|[._\-\s])(zh(?:-[A-Za-z]+)?|en|eng|chs|cht|chi|sc|tc|ja|jp|ko|kr|es|fr|de|ru|it|pt|pt-br)(?=$|[._\-\s])', remainder, flags=re.IGNORECASE)
        # 规范化、去重保持顺序
        seen = set()
        norm_tokens = []
        for t in tokens:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                norm_tokens.append(key)
        return '.'.join(norm_tokens)

    def find_associated_subtitles(self, video_path: Path) -> List[Path]:
        """为给定视频查找同名字幕文件。"""
        results: List[Path] = []
        video_stem = video_path.stem
        norm_video = self._normalized_stem_for_match(video_stem)
        for file_path in self.folder_path.iterdir():
            if not file_path.is_file() or file_path.suffix.lower() not in self.SUBTITLE_EXTENSIONS:
                continue
            sub_stem = file_path.stem
            norm_sub = self._normalized_stem_for_match(sub_stem)
            if norm_sub == norm_video:
                results.append(file_path)
        # 按名称排序，保证稳定
        results.sort(key=lambda x: x.name.lower())
        return results
    
    def extract_episode_title(self, filename: str, series_name_for_file: Optional[str] = None) -> str:
        """
        从文件名中提取集名
        
        Args:
            filename: 文件名
            series_name_for_file: 实际用于该文件的新剧名（可能包含括号后缀或从原文件提取的剧名）
            
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
        
        # 使用实际用于该文件的剧名（更智能移除中文等不适配\b的情况）
        base_series = (series_name_for_file or self.show_name).strip()
        # 生成变体：原始、分隔符替换、去特殊符号、去尾部括号注
        base_series_no_paren = re.sub(r'\s*\([^()]*\)\s*$', '', base_series).strip()
        raw_variants = [base_series, base_series_no_paren]
        variants: List[str] = []
        for v in raw_variants:
            if not v:
                continue
            variants.extend([
                v,
                v.replace(' ', '.'),
                v.replace(' ', '_'),
                v.replace(' ', '-'),
                re.sub(r'[^\w\s]', '', v)
            ])
        # 去重保持顺序
        seen = set()
        uniq_variants = []
        for v in variants:
            if v and v not in seen:
                seen.add(v)
                uniq_variants.append(v)
        # 用分隔符边界而非\b去移除（兼容中文）
        for variant in uniq_variants:
            sep_bounded = rf'(?i)(^|[\s._\-]){re.escape(variant)}(?=$|[\s._\-])'
            cleaned_name = re.sub(sep_bounded, ' ', cleaned_name)
        
        # 清理常见的标识符（使用分隔边界，避免下划线导致 \b 失效）
        patterns_to_remove = [
            r'(^|[\s._-])[Ss]\d{1,2}[Ee]\d{1,3}(?=$|[\s._-])',  # S01E01 格式
            r'(^|[\s._-])[Ee]\d{1,3}(?=$|[\s._-])',              # E01 格式
            r'(^|[\s._-])第\s*\d+\s*集(?=$|[\s._-])',            # 第01集 格式
            r'(^|[\s._-])第\s*\d+\s*季(?=$|[\s._-])',            # 第01季 格式
            r'\b\d+\b',                                           # 纯数字
            r'\b(720p|1080p|4k|hd|sd|hdtv|web-dl|bluray|bdrip|dvdrip|webrip)\b',  # 质量标识
            r'\b(mp4|mkv|avi|mov|wmv|flv|webm|rmvb|rm|m4v)\b',     # 格式标识
            r'[._\-\[\](){}]',                                    # 特殊字符
        ]
        
        for pattern in patterns_to_remove:
            cleaned_name = re.sub(pattern, ' ', cleaned_name, flags=re.IGNORECASE)
        
        # 清理多余空格并返回
        episode_title = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        # 如果提取的标题太短或包含太多数字，则认为无效
        if len(episode_title) < 2 or len(re.findall(r'\d', episode_title)) > len(episode_title) * 0.5:
            return ""
        
        return episode_title
    
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
        
        # 选择剧名（可从原文件名提取）
        series_name = self.show_name
        if self.preserve_series:
            series_name = extract_series_title_from_filename(file_path.name, fallback=self.show_name)

        # 应用剧名括号后缀（如 年份）
        if self.series_parentheses_suffix:
            # 去除尾部已有的括号尾注，替换为新的
            series_name = re.sub(r'\s*\([^()]*\)\s*$', '', series_name).strip()
            series_name = f"{series_name} ({self.series_parentheses_suffix})"

        # 提取集名（如果需要）
        episode_title = self.extract_episode_title(file_path.name, series_name_for_file=series_name)
        
        # 构建新文件名
        if episode_title:
            new_name = f"{series_name}_{season_str}{episode_str}_{episode_title}{file_path.suffix}"
        else:
            new_name = f"{series_name}_{season_str}{episode_str}{file_path.suffix}"
        
        return new_name
    
    def preview_rename(self) -> List[Tuple[Path, str, List[int]]]:
        """
        预览重命名结果
        
        Returns:
            原文件路径、新文件名和集数列表的元组列表
        """
        video_files = self.get_video_files()
        
        if not video_files:
            print(f"在文件夹 {self.folder_path} 中没有找到支持的媒体文件")
            return []
        
        rename_plan = []
        episode_counter = 1
        
        for file_path in video_files:
            # 根据每个文件包含的集数生成集数列表
            episodes = list(range(episode_counter, episode_counter + self.episodes_per_file))
            new_name = self.generate_new_name(file_path, episodes)
            rename_plan.append((file_path, new_name, episodes))
            # 同步字幕文件改名（与视频同基名）
            new_base = Path(new_name).stem
            associated_subs = self.find_associated_subtitles(file_path)
            for sub_path in associated_subs:
                # 尝试保留原有语言后缀
                lang_suffix = self._extract_subtitle_lang_suffix(file_path.stem, sub_path.stem)
                if lang_suffix:
                    sub_new_name = f"{new_base}.{lang_suffix}{sub_path.suffix}"
                else:
                    sub_new_name = f"{new_base}{sub_path.suffix}"
                rename_plan.append((sub_path, sub_new_name, episodes))
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