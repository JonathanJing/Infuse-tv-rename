# Infuse TV Rename Tool

一个用于批量重命名TV剧文件以符合Infuse媒体库命名规范的Python工具。

## 功能特性

- 🎬 批量重命名TV剧文件
- 📺 符合Infuse媒体库命名规范
- 🔢 自动生成季集编号 (S01E01格式)
- 📁 支持多种视频格式
- 🛡️ 安全的文件操作，不会覆盖现有文件
- 📋 预览重命名结果
- 🌟 **新增**: 支持多季电视剧批量重命名

## 命名规范

程序会将文件重命名为以下格式：
```
剧名_S01E01.扩展名
剧名_S01E02.扩展名
...
剧名_S02E01.扩展名
...
```

例如：
- `Friends_S01E01.mp4`
- `Breaking Bad_S01E01.mkv`
- `Game of Thrones_S01E01.avi`

## 安装要求

- Python 3.7+
- 操作系统：Windows, macOS, Linux

## 安装步骤

1. 克隆或下载项目到本地
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用方法

### 单季重命名

```bash
python3 tv_rename.py --folder /path/to/tv/folder --show "剧名" --season 1
```

#### 参数说明

- `--folder` 或 `-f`: TV剧文件夹路径（必需）
- `--show` 或 `-s`: 剧名（必需）
- `--season` 或 `-n`: 季数（可选，默认为1）
- `--preview` 或 `-p`: 仅预览，不执行重命名（可选）
- `--help` 或 `-h`: 显示帮助信息

#### 使用示例

```bash
# 重命名Friends第一季
python3 tv_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --season 1

# 预览重命名结果（不执行）
python3 tv_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --season 1 --preview

# 重命名Breaking Bad第二季
python3 tv_rename.py --folder "/Users/username/Videos/Breaking Bad" --show "Breaking Bad" --season 2
```

### 多季批量重命名

如果你的电视剧有多季，每个季在单独的子文件夹中，可以使用多季重命名工具：

```bash
python3 multi_season_rename.py --folder /path/to/tv/show/root --show "剧名"
```

#### 支持的文件夹结构

工具可以自动识别以下季文件夹命名模式：
- `Season 1`, `Season 2`, `Season 3`...
- `Season1`, `Season2`, `Season3`...
- `S01`, `S02`, `S03`...
- `第1季`, `第2季`, `第3季`...
- `season1`, `season2`, `season3`...
- `1`, `2`, `3`... (纯数字)

#### 参数说明

- `--folder` 或 `-f`: 包含所有季文件夹的根目录（必需）
- `--show` 或 `-s`: 剧名（必需）
- `--manual` 或 `-m`: 手动选择季文件夹（默认自动检测）
- `--preview` 或 `-p`: 仅预览，不执行重命名（可选）

#### 使用示例

```bash
# 自动检测季文件夹并重命名
python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends"

# 手动选择季文件夹
python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --manual

# 仅预览重命名结果
python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --preview

# 使用短参数
python3 multi_season_rename.py -f "/Users/username/Videos/Friends" -s "Friends" -p
```

#### 文件夹结构示例

```
Friends/
├── Season 1/
│   ├── episode_1.mp4
│   ├── episode_2.mp4
│   └── ...
├── Season 2/
│   ├── episode_1.mp4
│   ├── episode_2.mp4
│   └── ...
└── Season 3/
    ├── episode_1.mp4
    ├── episode_2.mp4
    └── ...
```

重命名后的结果：
```
Friends/
├── Season 1/
│   ├── Friends_S01E01.mp4
│   ├── Friends_S01E02.mp4
│   └── ...
├── Season 2/
│   ├── Friends_S02E01.mp4
│   ├── Friends_S02E02.mp4
│   └── ...
└── Season 3/
    ├── Friends_S03E01.mp4
    ├── Friends_S03E02.mp4
    └── ...
```

## 支持的文件格式

- 视频文件：`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`
- 字幕文件：`.srt`, `.ass`, `.ssa`, `.sub`
- 其他媒体文件：`.m4v`, `.3gp`, `.ogv`

## 安全特性

- 重命名前会检查目标文件名是否已存在
- 提供预览模式，可以查看重命名结果而不执行
- 保留原始文件扩展名
- 支持撤销操作（通过备份）

## 注意事项

1. 确保有足够的磁盘空间
2. 建议在重命名前备份重要文件
3. 程序会按文件名排序来确定集数顺序
4. 如果目标文件名已存在，程序会跳过该文件并显示警告

## 故障排除

### 常见问题

1. **权限错误**: 确保对目标文件夹有读写权限
2. **文件被占用**: 关闭可能正在使用这些文件的程序
3. **路径错误**: 使用绝对路径或确保相对路径正确

### 获取帮助

如果遇到问题，请检查：
- Python版本是否为3.7+
- 是否正确安装了所有依赖
- 文件路径是否正确
- 是否有足够的权限

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个工具！ 