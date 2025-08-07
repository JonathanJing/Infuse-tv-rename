# Infuse TV 电视剧智能重命名工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-green.svg)]()

一个专为 Infuse 媒体库设计的智能电视剧重命名工具，支持单季、多季和多集文件的批量重命名，提供命令行和图形化界面。

## ✨ 功能特色

### 🎯 核心功能
- **智能重命名**: 将文件重命名为 Infuse 标准格式 `ShowName_S01E01.ext`
- **多种模式**: 支持单季、多季、多集（如 `S01E01E02`）重命名
- **智能字幕处理**: 自动匹配同名字幕文件，保留语言标识（zh/en/chs.eng 等）
- **剧名智能提取**: 从原文件名自动提取并保留剧名，支持括号后缀
- **集名保留**: 可选择保留原文件名中的集数标题
- **预览模式**: 重命名前预览结果，确保准确性

### 🛡️ 安全特性
- **文件保护**: 目标文件存在时自动跳过，避免覆盖
- **预览确认**: 支持预览模式，重命名前查看结果
- **扩展名保持**: 完全保留原文件扩展名和字幕语言标识

### 📁 文件夹结构支持
自动识别多种季文件夹命名格式：
- 英文格式: `Season 1`, `Season1`, `S01`, `season1`
- 中文格式: `第1季`, `第2季`
- 数字格式: `1`, `2`, `3`

## 🏗️ 项目架构

```
infuse-tv-rename/
├── tv_rename.py              # 单季重命名核心模块
├── multi_season_rename.py    # 多季重命名模块
├── dual_episode_rename.py    # 多集文件重命名模块
├── name_utils.py             # 智能剧名提取工具
├── streamlit_app.py          # 图形化界面
├── example.py                # 使用示例
├── multi_season_example.py   # 多季使用示例
├── requirements.txt          # Python依赖
├── install.sh               # 安装脚本
├── MULTI_SEASON_GUIDE.md    # 多季使用指南
└── README.md                # 项目文档
```

### 核心组件

#### 1. TVRenameTool 类 (`tv_rename.py`)
- **功能**: 单季重命名处理
- **特色**: 智能集名提取、字幕文件匹配、多集支持
- **输出格式**: `ShowName_S01E01.ext` 或 `ShowName_S01E01E02.ext`

#### 2. MultiSeasonTVRenameTool 类 (`multi_season_rename.py`)  
- **功能**: 多季批量重命名
- **特色**: 自动季文件夹检测、手动选择模式
- **支持格式**: 识别多种季文件夹命名规范

#### 3. DualEpisodeTVRenameTool 类 (`dual_episode_rename.py`)
- **功能**: 多集文件重命名（每文件包含多集）
- **特色**: 智能集数解析、支持 2-3 集合并文件
- **输出格式**: `ShowName_S01E01E02.ext`

#### 4. 剧名提取工具 (`name_utils.py`)
- **功能**: 从文件名智能提取干净的剧名
- **算法**: 去除质量标识、编码信息、季集标记等噪音
- **保持原味**: 尽可能保留原始命名风格

## 🚀 快速开始

### 环境要求
- Python 3.7+
- 操作系统: Windows / macOS / Linux

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/infuse-tv-rename.git
cd infuse-tv-rename

# 安装依赖
pip install -r requirements.txt

# 或使用安装脚本
chmod +x install.sh
./install.sh
```

### 基础使用

#### 1. 单季重命名
```bash
# 基本用法
python3 tv_rename.py --folder "/path/to/season1" --show "Friends" --season 1

# 预览模式
python3 tv_rename.py --folder "/path/to/season1" --show "Friends" --season 1 --preview
```

#### 2. 多季批量重命名
```bash
# 自动检测季文件夹
python3 multi_season_rename.py --folder "/path/to/Friends" --show "Friends"

# 手动选择季文件夹
python3 multi_season_rename.py --folder "/path/to/Friends" --show "Friends" --manual
```

#### 3. 多集文件重命名
```bash
# 每文件包含2集
python3 dual_episode_rename.py --folder "/path/to/Friends" --show "Friends"

# 预览模式
python3 dual_episode_rename.py --folder "/path/to/Friends" --show "Friends" --preview
```

### 图形化界面

启动 Streamlit Web 界面：
```bash
streamlit run streamlit_app.py
```

**界面特色:**
- 🖱️ 原生文件夹选择对话框
- 🧠 智能剧名提取
- ⚙️ 高级选项配置（保留集名、剧名括号后缀等）
- 📊 实时预览和进度显示

## 📖 使用示例

### 文件结构示例

**重命名前:**
```
Friends/
├── Season 1/
│   ├── friends.s01e01.720p.mkv
│   ├── friends.s01e01.chs.srt
│   ├── friends.s01e02.720p.mkv
│   └── friends.s01e02.chs.srt
└── Season 2/
    ├── S02E01 - The One With Ross's New Girlfriend.mp4
    └── S02E01 - The One With Ross's New Girlfriend.zh.srt
```

**重命名后:**
```
Friends/
├── Season 1/
│   ├── Friends_S01E01.mkv
│   ├── Friends_S01E01.chs.srt
│   ├── Friends_S01E02.mkv
│   └── Friends_S01E02.chs.srt
└── Season 2/
    ├── Friends_S02E01.mp4
    └── Friends_S02E01.zh.srt
```

### 高级功能示例

**保留集名:**
```
输入: ShowName.S01E01.The.Pilot.1080p.mkv
输出: ShowName_S01E01_The Pilot.mkv
```

**剧名括号后缀:**
```
设置后缀: 1994
输出: Friends (1994)_S01E01.mkv
```

**多集文件:**
```
输入: Show.E01E02.Dual.Episode.mkv  
输出: Show_S01E01E02.mkv
```

## 🎯 支持的文件格式

### 视频格式
`.mp4` `.mkv` `.avi` `.mov` `.wmv` `.flv` `.webm` `.rmvb` `.rm` `.m4v` `.3gp` `.ogv`

### 字幕格式
`.srt` `.ass` `.ssa` `.sub`

### 字幕语言识别
支持自动识别和保留以下语言标识：
- 中文: `zh` `chs` `cht` `chi` `sc` `tc`
- 英文: `en` `eng`
- 其他: `ja` `ko` `es` `fr` `de` `ru` `it` `pt` `pt-br`

## 🔧 命令行参数

### tv_rename.py (单季)
| 参数 | 缩写 | 说明 | 必需 |
|------|------|------|------|
| `--folder` | `-f` | TV剧文件夹路径 | ✅ |
| `--show` | `-s` | 剧名 | ✅ |
| `--season` | `-n` | 季数 (默认: 1) | ❌ |
| `--preview` | `-p` | 仅预览，不执行重命名 | ❌ |

### multi_season_rename.py (多季)
| 参数 | 缩写 | 说明 | 必需 |
|------|------|------|------|
| `--folder` | `-f` | 根目录路径 | ✅ |
| `--show` | `-s` | 剧名 | ✅ |
| `--manual` | `-m` | 手动选择季文件夹 | ❌ |
| `--preview` | `-p` | 仅预览，不执行重命名 | ❌ |

### dual_episode_rename.py (多集)
| 参数 | 缩写 | 说明 | 必需 |
|------|------|------|------|
| `--folder` | `-f` | 根目录路径 | ✅ |
| `--show` | `-s` | 剧名 | ✅ |
| `--preview` | `-p` | 仅预览，不执行重命名 | ❌ |

## 🧠 智能算法

### 1. 字幕匹配算法
- **规范化匹配**: 忽略大小写、分隔符差异
- **语言后缀保留**: 智能识别并保留字幕语言标识
- **多语言支持**: 支持 `.chs.eng` 等多语言字幕

### 2. 剧名提取算法
- **噪音过滤**: 移除质量标识（720p、1080p等）
- **编码清理**: 去除编码信息（x264、HEVC等）
- **结构分析**: 在季集标记前截取剧名部分
- **智能保留**: 保持原始命名风格和语言特色

### 3. 季文件夹识别
- **模式匹配**: 支持英文、中文、数字等多种格式
- **智能排序**: 按季数正确排序
- **手动备选**: 自动识别失败时提供手动选择

## 💡 最佳实践

### 1. 使用建议
- **备份重要文件**: 重命名前建议备份
- **先用预览模式**: 使用 `--preview` 参数查看结果
- **检查文件顺序**: 确保原文件名顺序正确
- **验证季文件夹**: 多季模式下检查文件夹结构

### 2. 文件组织
```
推荐的文件夹结构:
TV_Shows/
├── Friends/
│   ├── Season 1/
│   ├── Season 2/
│   └── Season 3/
└── Breaking_Bad/
    ├── Season 1/
    ├── Season 2/
    └── Season 3/
```

### 3. 命名规范
- 原文件名尽量包含季集信息
- 字幕文件与视频文件同名
- 避免特殊字符和过长路径

## 🔍 故障排除

### 常见问题

**Q: 自动检测季文件夹失败怎么办？**
A: 使用 `--manual` 参数手动选择，或重命名文件夹为标准格式

**Q: 字幕文件没有正确重命名？**
A: 确保字幕文件与视频文件基础名称一致（忽略语言后缀）

**Q: 重命名失败提示文件被占用？**
A: 关闭正在使用该文件的程序（如播放器、编辑器）

**Q: 如何撤销重命名操作？**
A: 工具不提供撤销功能，建议重命名前备份文件

### 错误代码
- **FileNotFoundError**: 文件夹路径不存在
- **NotADirectoryError**: 路径不是有效文件夹
- **PermissionError**: 缺少文件操作权限
- **ValueError**: 参数值无效

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境
```bash
git clone https://github.com/yourusername/infuse-tv-rename.git
cd infuse-tv-rename
pip install -r requirements.txt
```

### 代码规范
- 遵循 PEP 8 编码风格
- 添加适当的文档字符串
- 编写单元测试
- 提交前测试所有功能

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

感谢所有为此项目做出贡献的开发者和用户！

---

**如有问题或建议，请提交 Issue 或联系作者**

**⭐ 如果这个项目对你有帮助，欢迎给个 Star！**