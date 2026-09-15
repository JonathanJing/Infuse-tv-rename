#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Infuse TV Rename Tool
批量重命名TV剧文件以符合Infuse媒体库命名规范
"""

import sys
import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional
from name_utils import extract_series_title_from_filename, extract_date_from_filename, parse_episode_numbers
from rename_operations import execute_plans, validate_plan


class TVRenameTool:
    """TV剧重命名工具类"""
    
    # 媒体文件扩展名分类
    VIDEO_EXTENSIONS = {
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.rmvb', '.rm',
        '.m4v', '.3gp', '.ogv'
    }
    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub'}
    
    def __init__(self, folder_path: str, show_name: str, season: int = 1, episodes_per_file: int = 1, preserve_title: bool = False, preserve_series: bool = False, series_parentheses_suffix: Optional[str] = None, start_episode: int = 1, keep_raw_filename: bool = False, renumber: bool = False):
        """
        初始化重命名工具
        
        Args:
            folder_path: TV剧文件夹路径
            show_name: 剧名
            season: 季数（默认为1）
            episodes_per_file: 每个文件包含的集数（默认为1）
            preserve_title: 是否保留集名（默认为False）
            start_episode: 起始集数（默认为1）
            keep_raw_filename: 是否保留原始文件名作为标题（默认为False）
        """
        self.folder_path = Path(folder_path)
        self.show_name = show_name.strip()
        self.season = season
        self.episodes_per_file = episodes_per_file
        self.preserve_title = preserve_title
        self.preserve_series = preserve_series
        self.series_parentheses_suffix = (series_parentheses_suffix or "").strip()
        self.start_episode = start_episode
        self.keep_raw_filename = keep_raw_filename
        self.renumber = renumber
        
        # 验证输入
        if not self.folder_path.exists():
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")
        
        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"路径不是文件夹: {folder_path}")
        
        if not self.show_name:
            raise ValueError("剧名不能为空")
        
        if self.start_episode < 1:
            raise ValueError("起始集数必须大于等于1")

        if self.season < 0:
            raise ValueError("季数必须大于等于0")
        
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
            episodes = parse_episode_numbers(p.name)
            idx = episodes[0] if episodes else None
            date_str = extract_date_from_filename(p.name)
            # 排序优先级:
            # 1. 有明确的集数 (idx is not None) -> (0, idx)
            # 2. 无集数但有日期 (date_str is not None) -> (1, date_str)
            # 3. 都没有 -> (2, filename)
            
            if idx is not None:
                return (0, idx, p.name.lower())
            if date_str is not None:
                return (1, date_str, p.name.lower())
            
            # 将无索引的放在后面
            return (2, p.name.lower(), "")

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
        """保留字幕末尾语言标记，不依赖原名大小写及分隔符完全一致。"""
        match = re.search(
            r'(?:[._\-\s](?:zh(?:-[A-Za-z]+)?|eng|en|chs|cht|chi|sc|tc|ja|jp|ko|kr|es|fr|de|ru|it|pt-br|pt))+$',
            subtitle_stem, re.I,
        )
        if not match:
            return ""
        tokens = re.findall(r'zh(?:-[A-Za-z]+)?|pt-br|eng|en|chs|cht|chi|sc|tc|ja|jp|ko|kr|es|fr|de|ru|it|pt', match.group(), re.I)
        return '.'.join(dict.fromkeys(t.lower() for t in tokens))

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
        
        # 如果开启了保留原始文件名，直接返回去扩展名的文件名（仅做基础清理）
        if self.keep_raw_filename:
            return Path(filename).stem.strip()
        
        # 移除文件扩展名
        name_without_ext = Path(filename).stem
        
        # 移除剧名（如果存在）
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
    
    def preview_rename(self, files_list: Optional[List[Path]] = None) -> List[Tuple[Path, str, List[int]]]:
        """保留源集号和缺口；只有 renumber=True 时按给定顺序重新编号。"""
        video_files = files_list if files_list is not None else self.get_video_files()
        plan = []
        counter = self.start_episode
        used = set()
        assignments = []
        for path in video_files:
            if self.renumber:
                episodes = None
            else:
                marker = re.search(r'S(\d{1,2})E\d+', path.stem, re.I)
                if marker and int(marker.group(1)) != self.season:
                    raise ValueError(f"源季号与所选季号不符: {path.name}")
                episodes = parse_episode_numbers(path.name)
                if episodes and len(episodes) == 1:
                    episodes = list(range(episodes[0], episodes[0] + self.episodes_per_file))
            if episodes:
                if used.intersection(episodes):
                    raise ValueError(f"重复集号，需先选择保留的版本: {path.name}")
                used.update(episodes)
            assignments.append((path, episodes))
        for path, episodes in assignments:
            if episodes is None:
                while used.intersection(range(counter, counter + self.episodes_per_file)):
                    counter += 1
                episodes = list(range(counter, counter + self.episodes_per_file))
                used.update(episodes)
            counter = max(counter, max(episodes) + 1)
            new_name = self.generate_new_name(path, episodes)
            plan.append((path, new_name, episodes))
            for sub in self.find_associated_subtitles(path):
                lang = self._extract_subtitle_lang_suffix(path.stem, sub.stem)
                suffix = f".{lang}" if lang else ""
                plan.append((sub, f"{Path(new_name).stem}{suffix}{sub.suffix}", episodes))
        validate_plan([(path, name) for path, name, _ in plan])
        return plan
    
    def execute_rename(self, rename_plan: List[Tuple[Path, str, List[int]]]) -> Tuple[int, int]:
        return execute_plans(
            self.folder_path,
            {self.season: [(path, name) for path, name, _ in rename_plan]},
        )[self.season]
    
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
        
        for i, (file_path, new_name, episodes) in enumerate(rename_plan, 1):
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
    
    parser.add_argument("--renumber", action="store_true", help="明确按顺序重新编号，不保留源集号")
    args = parser.parse_args()
    
    try:
        # 创建重命名工具实例
        tool = TVRenameTool(args.folder, args.show, args.season, renumber=args.renumber)
        
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