#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit UI for Infuse TV Rename Tool
为Infuse电视剧重命名工具提供图形化界面
"""

import streamlit as st
import os
import subprocess
import platform
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict
from tv_rename import TVRenameTool
from multi_season_rename import MultiSeasonTVRenameTool
from dual_episode_rename import DualEpisodeTVRenameTool
from rename_logger import RenameLogger


def extract_show_name_from_folder(folder_path: str) -> str:
    """从文件夹路径中提取剧名"""
    if not folder_path:
        return ""
    
    try:
        folder_name = Path(folder_path).name
        
        # 清理常见的文件夹命名模式
        # 移除年份 (1990-2099)
        import re
        show_name = re.sub(r'\b(19|20)\d{2}\b', '', folder_name)
        
        # 移除常见的季数标识
        show_name = re.sub(r'\b[Ss]eason\s*\d+\b', '', show_name, flags=re.IGNORECASE)
        show_name = re.sub(r'\b[Ss]\d+\b', '', show_name)
        show_name = re.sub(r'\b第\d+季\b', '', show_name)
        
        # 移除常见的分隔符和多余空格
        show_name = re.sub(r'[._\-\[\](){}]', ' ', show_name)
        show_name = re.sub(r'\s+', ' ', show_name).strip()
        
        # 移除常见的质量标识
        quality_keywords = ['720p', '1080p', '4k', 'hdtv', 'web-dl', 'bluray', 'bdrip', 'dvdrip', 'webrip']
        for keyword in quality_keywords:
            show_name = re.sub(r'\b' + keyword + r'\b', '', show_name, flags=re.IGNORECASE)
        
        show_name = re.sub(r'\s+', ' ', show_name).strip()
        
        return show_name if show_name else folder_name
        
    except Exception:
        return Path(folder_path).name if folder_path else ""


def select_folder():
    """使用系统原生文件对话框选择文件夹"""
    try:
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # 使用AppleScript打开文件夹选择对话框
            script = '''
            tell application "Finder"
                activate
                set folderPath to choose folder with prompt "选择TV剧文件夹"
                return POSIX path of folderPath
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return result.stdout.strip()
            
        elif system == "Windows":  # Windows
            # 使用PowerShell打开文件夹选择对话框
            script = '''
            Add-Type -AssemblyName System.Windows.Forms
            $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
            $folderBrowser.Description = "选择TV剧文件夹"
            $folderBrowser.ShowNewFolderButton = $false
            if ($folderBrowser.ShowDialog() -eq "OK") {
                Write-Output $folderBrowser.SelectedPath
            }
            '''
            result = subprocess.run(['powershell', '-Command', script], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
                
        elif system == "Linux":  # Linux
            # 尝试使用zenity或kdekdialog
            try:
                result = subprocess.run(['zenity', '--file-selection', '--directory', 
                                       '--title=选择TV剧文件夹'], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    return result.stdout.strip()
            except FileNotFoundError:
                try:
                    result = subprocess.run(['kdedialog', '--getexistingdirectory', 
                                           os.path.expanduser('~'), '--title', '选择TV剧文件夹'], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        return result.stdout.strip()
                except FileNotFoundError:
                    pass
        
        return ""
        
    except subprocess.TimeoutExpired:
        st.warning("文件夹选择超时，请手动输入路径")
        return ""
    except Exception as e:
        st.error(f"文件夹选择出错: {e}")
        return ""


def update_show_name_from_folder():
    if not st.session_state.get("show_name_input"):
        st.session_state.show_name_input = extract_show_name_from_folder(
            st.session_state.get("folder_input", "")
        )


def browse_folder():
    selected = select_folder()
    if selected:
        st.session_state.folder_input = selected
        update_show_name_from_folder()


def use_folder_show_name():
    st.session_state.show_name_input = extract_show_name_from_folder(
        st.session_state.get("folder_input", "")
    )


def refresh_after_operation(success, failed, operation):
    st.session_state.operation_notice = (success, failed, operation)
    st.rerun()


def undo_previous_batch(folder_path):
    try:
        success, failed = RenameLogger(folder_path).undo_last_batch()
        st.session_state.operation_notice = (success, failed, "恢复")
    except Exception as error:
        st.session_state.operation_error = f"恢复失败: {error}"


def main():
    st.set_page_config(
        page_title="Infuse TV 重命名工具",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Infuse TV 重命名工具")
    st.markdown("批量重命名TV剧文件以符合Infuse媒体库命名规范")
    error = st.session_state.pop("operation_error", None)
    if error:
        st.error(error)
    notice = st.session_state.pop("operation_notice", None)
    if notice:
        success, failed, operation = notice
        message = f"{operation}完成：成功 {success} 个文件，失败 {failed} 个文件"
        if failed:
            st.warning(message)
        elif success:
            st.success(message)
        else:
            st.info("所有文件已符合命名，无需修改")
    
    # 侧边栏配置
    st.sidebar.header("⚙️ 配置")
    
    # 模式选择
    mode = st.sidebar.radio(
        "选择模式",
        ["单季模式 (文件在主文件夹)", "多季模式 (每季一个子文件夹)"],
        help="单季模式：所有视频文件直接在选择的文件夹中\n多季模式：每个季度的视频文件在单独的子文件夹中"
    )
    
    # 多集模式选项（仅多季模式）
    use_multi_episode = False
    episodes_per_file = 1
    multi_season_preserve_series = False
    series_parentheses_suffix = ""
    if mode == "多季模式 (每季一个子文件夹)":
        use_multi_episode = st.sidebar.checkbox(
            "🎬 多集模式",
            help="每个文件包含多集内容，生成如 S01E01E02 或 S01E01E02E03 格式的文件名"
        )
        
        if use_multi_episode:
            episodes_per_file = st.sidebar.selectbox(
                "每个文件的集数",
                options=[2, 3],
                index=0,
                help="选择每个文件包含的集数"
            )
        
        multi_season_preserve_title = st.sidebar.checkbox(
            "📝 保留集名",
            help="从原文件名中提取并保留集数标题，如：ShowName_S01E01_集名.ext"
        )
        multi_season_preserve_series = st.sidebar.checkbox(
            "🏷️ 保留剧名",
            help="更智能：从原文件名中提取并保留剧名（优先使用文件中的剧名片段）"
        )
        series_parentheses_suffix = st.sidebar.text_input(
            "📎 剧名括号后缀",
            value="",
            placeholder="如：1987",
            help="追加到剧名后并用括号包裹。例如：红楼梦 (1987)_S01E01"
        )
    
    # 文件夹选择
    st.sidebar.subheader("📁 选择文件夹")
    
    st.session_state.setdefault("folder_input", "")
    st.session_state.setdefault("show_name_input", "")
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        folder_path = st.text_input(
            "文件夹路径", placeholder="输入或粘贴文件夹路径",
            help="输入包含TV剧文件的文件夹完整路径", key="folder_input",
            on_change=update_show_name_from_folder,
        )
    with col2:
        st.write("")
        st.button("📂 浏览", help="点击打开文件夹选择对话框", on_click=browse_folder)

    show_name = st.sidebar.text_input(
        "剧名", placeholder="如: Friends", key="show_name_input",
        help="剧名会从文件夹名自动提取，你可以手动修改",
    )
    if folder_path and show_name:
        extracted_name = extract_show_name_from_folder(folder_path)
        if extracted_name and extracted_name != show_name:
            st.sidebar.info(f"💡 从文件夹提取的剧名: {extracted_name}")
            st.sidebar.button("🔄 使用提取的剧名", on_click=use_folder_show_name)

    # 季数输入和多集选项（仅单季模式）
    season_number = 1
    start_episode = 1
    single_season_multi_episode = False
    single_season_episodes_per_file = 1
    single_season_preserve_title = False
    single_season_preserve_series = False
    single_season_keep_raw_filename = False  # 默认不开启
    if mode == "单季模式 (文件在主文件夹)":
        season_number = st.sidebar.number_input(
            "季数",
            min_value=0,
            max_value=50,
            value=1,
            help="指定这个文件夹中视频文件的季数"
        )

        start_episode = st.sidebar.number_input(
            "起始集数",
            min_value=1,
            max_value=999,
            value=1,
            help="无集号文件的起始编号；开启重新编号时，全部文件从这里递增"
        )
        
        single_season_multi_episode = st.sidebar.checkbox(
            "🎬 多集模式",
            help="每个文件包含多集内容，生成如 S01E01E02 或 S01E01E02E03 格式的文件名"
        )
        
        if single_season_multi_episode:
            single_season_episodes_per_file = st.sidebar.selectbox(
                "每个文件的集数",
                options=[2, 3],
                index=0,
                help="选择每个文件包含的集数"
            )
        
        single_season_preserve_title = st.sidebar.checkbox(
            "📝 保留集名",
            help="从原文件名中提取并保留集数标题，如：ShowName_S01E01_集名.ext"
        )
        
        if single_season_preserve_title:
             single_season_keep_raw_filename = st.sidebar.checkbox(
                "📄 使用原文件名作为标题",
                help="直接使用去除扩展名的原文件名作为标题，不做其他清理（适用于特殊命名格式，如日期开头的标题）"
            )
            
        single_season_preserve_series = st.sidebar.checkbox(
            "🏷️ 保留剧名",
            help="更智能：从原文件名中提取并保留剧名（优先使用文件中的剧名片段）"
        )
        series_parentheses_suffix = st.sidebar.text_input(
            "📎 剧名括号后缀",
            value="",
            placeholder="如：1987",
            help="追加到剧名后并用括号包裹。例如：红楼梦 (1987)_S01E01"
        )
    
    # 验证输入
    if not folder_path or not show_name:
        st.info("请在左侧配置中输入文件夹路径和剧名")
        return
    
    # 验证文件夹存在
    folder_path_obj = Path(folder_path)
    if not folder_path_obj.exists():
        st.error(f"文件夹不存在: {folder_path}")
        return
    
    if not folder_path_obj.is_dir():
        st.error(f"路径不是文件夹: {folder_path}")
        return
    
    # 历史回退功能
    check_and_show_undo(folder_path)
    
    # 主界面
    st.header(f"📺 {show_name}")
    st.markdown(f"**文件夹:** `{folder_path}`")
    st.markdown(f"**模式:** {mode}")
    
    if mode == "单季模式 (文件在主文件夹)":
        handle_single_season_mode(
            folder_path,
            show_name,
            season_number,
            single_season_multi_episode,
            single_season_episodes_per_file,
            single_season_preserve_title,
            single_season_preserve_series,
            series_parentheses_suffix,
            start_episode,
            single_season_keep_raw_filename,
        )
    else:
        handle_multi_season_mode(
            folder_path,
            show_name,
            use_multi_episode,
            episodes_per_file,
            multi_season_preserve_title,
            multi_season_preserve_series,
            series_parentheses_suffix,
        )


def check_and_show_undo(folder_path: str):
    """检查并显示撤销选项"""
    try:
        logger = RenameLogger(folder_path)
        if logger.has_history():
            last_info = logger.get_last_batch_info()
            if last_info:
                with st.expander("⏪ 历史记录 / 撤销操作", expanded=True):
                    st.info(f"发现最近一次重命名记录: {last_info['timestamp']} (涉及 {last_info['count']} 个文件)")
                    st.button(
                        "↩️ 撤销上次重命名", type="secondary",
                        help="将文件恢复到重命名之前的状态",
                        on_click=undo_previous_batch, args=(folder_path,),
                    )
    except Exception as e:
        st.error(f"读取历史记录出错: {e}")


def handle_single_season_mode(folder_path: str, show_name: str, season_number: int, use_multi_episode: bool = False, episodes_per_file: int = 1, preserve_title: bool = False, preserve_series: bool = False, series_parentheses_suffix: str = "", start_episode: int = 1, keep_raw_filename: bool = False):
    """处理单季模式"""
    st.markdown(f"**季数:** {season_number}")
    if start_episode > 1:
        st.markdown(f"**起始集数:** {start_episode}")
    if use_multi_episode:
        st.markdown(f"**多集模式:** 开启 - 每个文件包含 {episodes_per_file} 集内容")
    if preserve_title:
        st.markdown(f"**保留集名:** 开启 - 从原文件名中提取集数标题")
        if keep_raw_filename:
             st.markdown(f"  - **原文件名模式:** 开启 (直接使用原文件名作为标题)")
    if preserve_series:
        st.markdown(f"**保留剧名:** 开启 - 从原文件名中提取剧名片段")
    if series_parentheses_suffix:
        st.markdown(f"**剧名括号后缀:** ({series_parentheses_suffix})")
    
    try:
        # 创建重命名工具
        tool = TVRenameTool(folder_path, show_name, season_number, episodes_per_file, preserve_title, preserve_series, series_parentheses_suffix, start_episode, keep_raw_filename)
        
        # 获取初始文件列表
        current_files = tool.get_video_files()
        
        if not current_files:
            st.warning("在选择的文件夹中没有找到支持的媒体文件")
            st.info("支持的文件格式: mp4, mkv, avi, mov, wmv, flv, webm, rmvb, rm, m4v, 3gp, ogv, srt, ass, ssa, sub")
            return
            
        tool.renumber = st.checkbox("按顺序重新编号", help="默认保留已有集号及缺集；仅需要改变集号时开启")

        # 手动排序选项
        enable_manual_sort = st.checkbox("🔢 手动调整文件顺序", disabled=not tool.renumber, help="先开启按顺序重新编号，再调整对应顺序")
        
        final_files = current_files
        
        if enable_manual_sort and tool.renumber:
            st.info("👇 在下方表格中修改【排序】列的数字来调整顺序，然后按 Enter 确认")
            
            # 构建 DataFrame
            df_data = []
            for idx, f in enumerate(current_files, 1):
                df_data.append({
                    "排序": idx,
                    "文件名": f.name,
                    "路径": str(f) # 隐藏列，用于映射回 Path
                })
            
            df = pd.DataFrame(df_data)
            
            # 使用 data_editor
            edited_df = st.data_editor(
                df,
                column_config={
                    "排序": st.column_config.NumberColumn(
                        "顺序 (修改以此排序)",
                        help="数字越小越靠前",
                        min_value=1,
                        max_value=len(current_files),
                        step=1,
                        required=True,
                    ),
                    "文件名": st.column_config.TextColumn(
                        "文件名",
                        disabled=True, # 文件名不可修改
                    ),
                    "路径": None # 隐藏路径列
                },
                hide_index=True,
                width="stretch",
                key="file_sort_editor"
            )
            
            # 根据编辑后的 DataFrame 排序
            if edited_df is not None:
                # 按"排序"列排序
                sorted_df = edited_df.sort_values(by="排序")
                
                # 重新构建 Path 列表
                # 注意：这里假设路径是唯一的，这在同一个文件夹下是成立的
                sorted_paths = []
                for _, row in sorted_df.iterrows():
                    # 从原始列表中找到对应的 Path 对象（比用字符串重建更安全）
                    path_str = row["路径"]
                    original_path_obj = next((p for p in current_files if str(p) == path_str), None)
                    if original_path_obj:
                        sorted_paths.append(original_path_obj)
                
                final_files = sorted_paths

        # 获取预览 (传入可能已排序的文件列表)
        rename_plan = tool.preview_rename(files_list=final_files)
        
        if not rename_plan:
            st.warning("无法生成重命名预览")
            return
        
        # 显示预览
        st.subheader(f"📋 预览重命名结果 ({len(rename_plan)} 个文件)")
        
        preview_data = []
        for i, item in enumerate(rename_plan, 1):
            if use_multi_episode and len(item) == 3:
                # 多集模式：(file_path, new_name, episodes_list)
                file_path, new_name, episodes = item
                episode_text = "".join([f"E{ep:02d}" for ep in episodes])
                preview_data.append({
                    "序号": i,
                    "原文件名": file_path.name,
                    "新文件名": new_name,
                    "集数": episode_text,
                    "路径": str(file_path.parent)
                })
            else:
                # 普通模式：(file_path, new_name, [episode])
                file_path, new_name, episodes = item
                preview_data.append({
                    "序号": i,
                    "原文件名": file_path.name,
                    "新文件名": new_name,
                    "路径": str(file_path.parent)
                })
        
        st.dataframe(preview_data, width="stretch")
        
        # 执行重命名
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 执行重命名", type="primary", width="stretch"):
                execute_single_season_rename(tool, rename_plan)
        
        with col2:
            if st.button("🔍 仅预览", width="stretch"):
                st.success("预览完成，未执行重命名操作")
    
    except Exception as e:
        st.error(f"错误: {e}")


def handle_multi_season_mode(folder_path: str, show_name: str, use_multi_episode: bool = False, episodes_per_file: int = 2, preserve_title: bool = False, preserve_series: bool = False, series_parentheses_suffix: str = ""):
    """处理多季模式"""
    try:
        # 根据是否多集模式选择不同的工具
        if use_multi_episode:
            tool = DualEpisodeTVRenameTool(folder_path, show_name, episodes_per_file, preserve_title, preserve_series, series_parentheses_suffix)
            st.markdown(f"**多集模式:** 开启 - 每个文件包含 {episodes_per_file} 集内容")
            if preserve_title:
                st.markdown(f"**保留集名:** 开启 - 从原文件名中提取集数标题")
            if preserve_series:
                st.markdown(f"**保留剧名:** 开启 - 从原文件名中提取剧名片段")
            if series_parentheses_suffix:
                st.markdown(f"**剧名括号后缀:** ({series_parentheses_suffix})")
        else:
            tool = MultiSeasonTVRenameTool(folder_path, show_name, preserve_title, preserve_series, series_parentheses_suffix)
            if preserve_title:
                st.markdown(f"**保留集名:** 开启 - 从原文件名中提取集数标题")
            if preserve_series:
                st.markdown(f"**保留剧名:** 开启 - 从原文件名中提取剧名片段")
            if series_parentheses_suffix:
                st.markdown(f"**剧名括号后缀:** ({series_parentheses_suffix})")
        
        tool.renumber = st.checkbox("按顺序重新编号", help="默认保留集号。若 01、02 表示多集文件的包序号，请开启此项")

        # 检测季文件夹
        season_folders = tool.detect_season_folders()
        
        if not season_folders:
            st.warning("未能自动检测到季文件夹")
            season_folders = manual_select_season_folders(folder_path)
        
        if not season_folders:
            st.info("请确保子文件夹包含季数信息，如: Season 1, S01, 第1季 等")
            return
        
        # 显示检测到的季文件夹
        st.subheader("📁 检测到的季文件夹")
        season_info = []
        for season_num, folder_path_obj in sorted(season_folders.items()):
            season_info.append({
                "季数": f"第 {season_num} 季",
                "文件夹名": folder_path_obj.name,
                "路径": str(folder_path_obj)
            })
        
        st.dataframe(season_info, width="stretch")
        
        # 获取预览
        st.subheader("🔍 预览重命名结果")
        all_plans = tool.preview_all_seasons(season_folders)
        
        if not all_plans:
            st.warning("没有找到任何媒体文件")
            return
        
        # 显示每季的预览
        total_files = 0
        for season_num, rename_plan in sorted(all_plans.items()):
            with st.expander(f"第 {season_num} 季 ({len(rename_plan)} 个文件)", expanded=False):
                season_preview_data = []
                for i, item in enumerate(rename_plan, 1):
                    if use_multi_episode and len(item) == 3:
                        # 多集模式：(file_path, new_name, episodes_list)
                        file_path, new_name, episodes = item
                        episode_text = "".join([f"E{ep:02d}" for ep in episodes])
                        season_preview_data.append({
                            "序号": i,
                            "原文件名": file_path.name,
                            "新文件名": new_name,
                            "集数": episode_text
                        })
                    else:
                        # 普通模式：(file_path, new_name)
                        file_path, new_name = item
                        season_preview_data.append({
                            "序号": i,
                            "原文件名": file_path.name,
                            "新文件名": new_name
                        })
                st.dataframe(season_preview_data, width="stretch")
            total_files += len(rename_plan)
        
        # 显示总览
        st.info(f"总计: {len(all_plans)} 季，{total_files} 个文件")
        
        # 执行重命名
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 执行所有重命名", type="primary", width="stretch"):
                execute_multi_season_rename(tool, all_plans, use_multi_episode)
        
        with col2:
            if st.button("🔍 仅预览", width="stretch"):
                st.success("预览完成，未执行重命名操作")
    
    except Exception as e:
        st.error(f"错误: {e}")


def manual_select_season_folders(root_folder: str) -> Dict[int, Path]:
    """手动选择季文件夹"""
    root_path = Path(root_folder)
    folders = [item for item in root_path.iterdir() if item.is_dir()]
    
    if not folders:
        return {}
    
    folders.sort(key=lambda x: x.name.lower())
    
    st.subheader("📁 手动选择季文件夹")
    st.markdown("由于无法自动检测季文件夹，请手动选择:")
    
    season_folders = {}
    
    for i, folder in enumerate(folders):
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.text(folder.name)
        
        with col2:
            if st.checkbox(f"选择", key=f"folder_{i}"):
                with col3:
                    season_num = st.number_input(
                        "季数",
                        min_value=0,
                        max_value=50,
                        value=i+1,
                        key=f"season_{i}"
                    )
                    if season_num in season_folders:
                        st.error(f"季号 {season_num} 重复，请为每个目录选择不同季号")
                        return {}
                    season_folders[season_num] = folder
    
    return season_folders


def execute_single_season_rename(tool: TVRenameTool, rename_plan: List[Tuple[Path, str, List[int]]]):
    with st.spinner("正在重命名文件..."):
        try:
            success, failed = tool.execute_rename(rename_plan)
            refresh_after_operation(success, failed, "重命名")
        except Exception as e:
            st.error(f"重命名过程中发生错误: {e}")


def execute_multi_season_rename(tool, all_plans, use_multi_episode=False):
    with st.spinner("正在重命名文件..."):
        try:
            results = tool.execute_rename(all_plans) if use_multi_episode else tool.execute_all_seasons(all_plans)
            success = sum(result[0] for result in results.values())
            failed = sum(result[1] for result in results.values())
            refresh_after_operation(success, failed, "重命名")
        except Exception as e:
            st.error(f"重命名过程中发生错误: {e}")


if __name__ == "__main__":
    main()