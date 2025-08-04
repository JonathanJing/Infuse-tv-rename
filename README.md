# Infuse TV Rename Tool

一个用于批量重命名TV剧文件以符合Infuse媒体库命名规范的Python工具。

## 功能特性

- 🎬 批量重命名TV剧文件
- 📺 符合Infuse媒体库命名规范
- 🔢 自动生成季集编号 (S01E01格式)
- 📁 支持多种视频格式
- 🛡️ 安全的文件操作，不会覆盖现有文件
- 📋 预览重命名结果

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

### 命令行使用

```bash
python3 tv_rename.py --folder /path/to/tv/folder --show "剧名" --season 1
```

### 参数说明

- `--folder` 或 `-f`: TV剧文件夹路径（必需）
- `--show` 或 `-s`: 剧名（必需）
- `--season` 或 `-n`: 季数（可选，默认为1）
- `--preview` 或 `-p`: 仅预览，不执行重命名（可选）
- `--help` 或 `-h`: 显示帮助信息

### 使用示例

```bash
# 重命名Friends第一季
python3 tv_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --season 1

# 预览重命名结果（不执行）
python3 tv_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --season 1 --preview

# 重命名Breaking Bad第二季
python3 tv_rename.py --folder "/Users/username/Videos/Breaking Bad" --show "Breaking Bad" --season 2
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