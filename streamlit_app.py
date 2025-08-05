#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit UI for Infuse TV Rename Tool
为Infuse电视剧重命名工具提供图形化界面
"""

import streamlit as st
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from tv_rename import TVRenameTool
from multi_season_rename import MultiSeasonTVRenameTool


def select_folder():
    """使用文件对话框选择文件夹"""
    try:
        # 创建一个隐藏的根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        root.wm_attributes('-topmost', 1)  # 置于最前
        
        # 打开文件夹选择对话框
        folder_path = filedialog.askdirectory(
            title="选择TV剧文件夹"
        )
        
        root.destroy()  # 销毁窗口
        return folder_path
    except Exception as e:
        st.error(f"文件夹选择出错: {e}")
        return ""


def main():
    st.set_page_config(
        page_title="Infuse TV 重命名工具",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Infuse TV 重命名工具")
    st.markdown("批量重命名TV剧文件以符合Infuse媒体库命名规范")
    
    # 侧边栏配置
    st.sidebar.header("⚙️ 配置")
    
    # 模式选择
    mode = st.sidebar.radio(
        "选择模式",
        ["单季模式 (文件在主文件夹)", "多季模式 (每季一个子文件夹)"],
        help="单季模式：所有视频文件直接在选择的文件夹中\n多季模式：每个季度的视频文件在单独的子文件夹中"
    )
    
    # 文件夹选择
    st.sidebar.subheader("📁 选择文件夹")
    
    # 初始化session state
    if 'folder_path' not in st.session_state:
        st.session_state.folder_path = ""
    
    col1, col2 = st.sidebar.columns([3, 1])
    
    with col1:
        folder_path = st.text_input(
            "文件夹路径",
            value=st.session_state.folder_path,
            placeholder="输入或粘贴文件夹路径",
            help="输入包含TV剧文件的文件夹完整路径",
            key="folder_input"
        )
    
    with col2:
        st.write("")  # 添加空行对齐
        if st.button("📂 浏览", help="点击打开文件夹选择对话框"):
            selected_folder = select_folder()
            if selected_folder:
                st.session_state.folder_path = selected_folder
                folder_path = selected_folder
                st.rerun()  # 刷新页面以更新输入框
    
    # 更新session state
    if folder_path != st.session_state.folder_path:
        st.session_state.folder_path = folder_path
    
    # 剧名输入
    show_name = st.sidebar.text_input(
        "剧名",
        placeholder="如: Friends",
        help="输入电视剧的名称，将用于文件重命名"
    )
    
    # 季数输入（仅单季模式）
    season_number = 1
    if mode == "单季模式 (文件在主文件夹)":
        season_number = st.sidebar.number_input(
            "季数",
            min_value=1,
            max_value=50,
            value=1,
            help="指定这个文件夹中视频文件的季数"
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
    
    # 主界面
    st.header(f"📺 {show_name}")
    st.markdown(f"**文件夹:** `{folder_path}`")
    st.markdown(f"**模式:** {mode}")
    
    if mode == "单季模式 (文件在主文件夹)":
        handle_single_season_mode(folder_path, show_name, season_number)
    else:
        handle_multi_season_mode(folder_path, show_name)


def handle_single_season_mode(folder_path: str, show_name: str, season_number: int):
    """处理单季模式"""
    st.markdown(f"**季数:** {season_number}")
    
    try:
        # 创建重命名工具
        tool = TVRenameTool(folder_path, show_name, season_number)
        
        # 获取预览
        rename_plan = tool.preview_rename()
        
        if not rename_plan:
            st.warning("在选择的文件夹中没有找到支持的媒体文件")
            st.info("支持的文件格式: mp4, mkv, avi, mov, wmv, flv, webm, m4v, 3gp, ogv, srt, ass, ssa, sub")
            return
        
        # 显示预览
        st.subheader(f"📋 预览重命名结果 ({len(rename_plan)} 个文件)")
        
        preview_data = []
        for i, (file_path, new_name) in enumerate(rename_plan, 1):
            preview_data.append({
                "序号": i,
                "原文件名": file_path.name,
                "新文件名": new_name,
                "路径": str(file_path.parent)
            })
        
        st.dataframe(preview_data, use_container_width=True)
        
        # 执行重命名
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 执行重命名", type="primary", use_container_width=True):
                execute_single_season_rename(tool, rename_plan)
        
        with col2:
            if st.button("🔍 仅预览", use_container_width=True):
                st.success("预览完成，未执行重命名操作")
    
    except Exception as e:
        st.error(f"错误: {e}")


def handle_multi_season_mode(folder_path: str, show_name: str):
    """处理多季模式"""
    try:
        # 创建多季重命名工具
        tool = MultiSeasonTVRenameTool(folder_path, show_name)
        
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
        
        st.dataframe(season_info, use_container_width=True)
        
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
                for i, (file_path, new_name) in enumerate(rename_plan, 1):
                    season_preview_data.append({
                        "序号": i,
                        "原文件名": file_path.name,
                        "新文件名": new_name
                    })
                st.dataframe(season_preview_data, use_container_width=True)
            total_files += len(rename_plan)
        
        # 显示总览
        st.info(f"总计: {len(all_plans)} 季，{total_files} 个文件")
        
        # 执行重命名
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 执行所有重命名", type="primary", use_container_width=True):
                execute_multi_season_rename(tool, all_plans)
        
        with col2:
            if st.button("🔍 仅预览", use_container_width=True):
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
                        min_value=1,
                        max_value=50,
                        value=i+1,
                        key=f"season_{i}"
                    )
                    season_folders[season_num] = folder
    
    return season_folders


def execute_single_season_rename(tool: TVRenameTool, rename_plan: List[Tuple[Path, str]]):
    """执行单季重命名"""
    with st.spinner("正在重命名文件..."):
        try:
            success_count, failed_count = tool.execute_rename(rename_plan)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("成功", success_count, delta=None)
            with col2:
                st.metric("失败", failed_count, delta=None)
            
            if success_count > 0:
                st.success(f"重命名完成! 成功: {success_count}, 失败: {failed_count}")
            
            if failed_count > 0:
                st.warning("部分文件重命名失败，可能是目标文件名已存在")
        
        except Exception as e:
            st.error(f"重命名过程中发生错误: {e}")


def execute_multi_season_rename(tool: MultiSeasonTVRenameTool, all_plans: Dict[int, List[Tuple[Path, str]]]):
    """执行多季重命名"""
    with st.spinner("正在重命名文件..."):
        try:
            results = tool.execute_all_seasons(all_plans)
            
            # 显示每季结果
            st.subheader("📊 重命名结果")
            
            total_success = 0
            total_failed = 0
            
            result_data = []
            for season_num, (success_count, failed_count) in sorted(results.items()):
                result_data.append({
                    "季数": f"第 {season_num} 季",
                    "成功": success_count,
                    "失败": failed_count,
                    "总计": success_count + failed_count
                })
                total_success += success_count
                total_failed += failed_count
            
            st.dataframe(result_data, use_container_width=True)
            
            # 显示总计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总成功", total_success)
            with col2:
                st.metric("总失败", total_failed)
            with col3:
                st.metric("总文件数", total_success + total_failed)
            
            if total_success > 0:
                st.success(f"重命名完成! 总成功: {total_success}, 总失败: {total_failed}")
            
            if total_failed > 0:
                st.warning("部分文件重命名失败，可能是目标文件名已存在")
        
        except Exception as e:
            st.error(f"重命名过程中发生错误: {e}")


if __name__ == "__main__":
    main()