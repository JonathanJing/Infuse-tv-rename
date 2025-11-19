#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit UI for batch converting .mp4 files to .mp3 in a selected folder.
Uses the same native folder picker UX as the rename tool.
"""

import streamlit as st
import os
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple

from mp4_to_mp3 import convert_mp4s_to_mp3s, is_ffmpeg_available
from concurrent.futures import ThreadPoolExecutor, as_completed


def select_folder() -> str:
    """Use native OS dialog to select a folder (same UX as the main app)."""
    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            script = '''
            tell application "Finder"
                activate
                set folderPath to choose folder with prompt "选择包含 MP4 的文件夹"
                return POSIX path of folderPath
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return result.stdout.strip()

        elif system == "Windows":  # Windows
            script = '''
            Add-Type -AssemblyName System.Windows.Forms
            $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
            $folderBrowser.Description = "选择包含 MP4 的文件夹"
            $folderBrowser.ShowNewFolderButton = $false
            if ($folderBrowser.ShowDialog() -eq "OK") {
                Write-Output $folderBrowser.SelectedPath
            }
            '''
            result = subprocess.run(['powershell', '-Command', script], capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

        elif system == "Linux":  # Linux
            try:
                result = subprocess.run(['zenity', '--file-selection', '--directory', '--title=选择包含 MP4 的文件夹'], capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    return result.stdout.strip()
            except FileNotFoundError:
                try:
                    result = subprocess.run(['kdedialog', '--getexistingdirectory', os.path.expanduser('~'), '--title', '选择包含 MP4 的文件夹'], capture_output=True, text=True, timeout=60)
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


def main():
    st.set_page_config(page_title="MP4 → MP3 批量转换", page_icon="🎵", layout="wide")

    st.title("🎵 MP4 → MP3 批量转换")
    st.markdown("从选择的文件夹中批量提取音频，输出到 download 目录")

    st.sidebar.header("📁 选择文件夹")

    if 'folder_path' not in st.session_state:
        st.session_state.folder_path = ""
    if 'output_path' not in st.session_state:
        st.session_state.output_path = ""

    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        folder_path = st.text_input(
            "文件夹路径",
            value=st.session_state.folder_path,
            placeholder="输入或粘贴包含 .mp4 文件的文件夹路径",
            key="folder_input_mp4mp3"
        )
    with col2:
        st.write("")
        if st.button("📂 浏览", help="打开系统文件夹选择对话框", key="browse_mp4mp3"):
            selected = select_folder()
            if selected:
                st.session_state.folder_path = selected
                folder_path = selected
                st.rerun()

    # Output options
    st.sidebar.subheader("⚙️ 转换选项")
    use_vbr = st.sidebar.checkbox("使用 VBR (可更快，质量可调)", value=True)
    vbr_quality = st.sidebar.slider("VBR 质量 (0 最好，2 常用)", min_value=0, max_value=9, value=2, disabled=not use_vbr)
    bitrate = st.sidebar.selectbox("CBR 码率 (仅当未启用 VBR)", options=["128k", "160k", "192k", "256k", "320k"], index=2, disabled=use_vbr)
    overwrite = st.sidebar.checkbox("覆盖已存在的 MP3 文件", value=False)
    custom_output = st.sidebar.text_input("自定义输出目录 (可选)", value=st.session_state.output_path, placeholder="留空则使用 <输入目录>/download")
    max_workers = st.sidebar.slider("并发任务数", min_value=1, max_value=os.cpu_count() or 4, value=min(4, (os.cpu_count() or 4)))

    # Validate input directory
    if not folder_path:
        st.info("请在左侧输入或选择一个包含 .mp4 文件的文件夹")
        return

    input_dir = Path(folder_path)
    if not input_dir.exists() or not input_dir.is_dir():
        st.error(f"无效的文件夹路径: {folder_path}")
        return

    # Show simple file count
    mp4_files = [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp4"]
    st.markdown(f"**检测到 MP4 文件:** {len(mp4_files)} 个")

    # ffmpeg check
    if not is_ffmpeg_available():
        st.error("未检测到 ffmpeg，请先安装 ffmpeg 后再使用。macOS 可运行: brew install ffmpeg")
        return

    # Convert button
    if st.button("🎧 开始转换", type="primary"):
        output_dir = Path(custom_output).expanduser() if custom_output.strip() else (input_dir / "download")
        progress_bar = st.progress(0)
        status_area = st.empty()
        log_area = st.empty()

        successes = []
        failures = []

        # Prepare jobs
        jobs = [(p, output_dir / (p.stem + ".mp3")) for p in mp4_files]
        total = len(jobs)
        if total == 0:
            st.info("该目录下没有 mp4 文件。")
            return

        from mp4_to_mp3 import convert_single_mp4_to_mp3

        def run_job(src: Path, dst: Path):
            if use_vbr:
                ok, msg = convert_single_mp4_to_mp3(src, dst, overwrite=overwrite, bitrate=bitrate, vbr_quality=vbr_quality)
            else:
                ok, msg = convert_single_mp4_to_mp3(src, dst, overwrite=overwrite, bitrate=bitrate, vbr_quality=None)
            return src, dst, ok, msg

        completed_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {executor.submit(run_job, src, dst): (src, dst) for src, dst in jobs}
            for future in as_completed(future_to_job):
                src, dst, ok, msg = future.result()
                if ok and dst.exists():
                    successes.append(dst)
                else:
                    failures.append((src, msg))
                completed_count += 1
                progress_bar.progress(int(completed_count * 100 / total))
                status_area.write(f"已完成 {completed_count}/{total}: {src.name}")
                # Append log line
                log_area.write(f"{msg}")

        # Results summary
        if successes:
            st.success(f"成功转换 {len(successes)} 个文件，输出目录: {output_dir}")
        if failures:
            st.warning(f"{len(failures)} 个文件转换失败/跳过")
            with st.expander("查看详情"):
                for src, reason in failures:
                    st.write(f"- {src.name}: {reason}")


if __name__ == "__main__":
    main()


