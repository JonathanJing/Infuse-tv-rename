# 多季电视剧批量重命名指南

## 概述

如果你的电视剧有多季，每个季在单独的子文件夹中，可以使用 `multi_season_rename.py` 工具进行批量重命名。

## 支持的文件夹结构

工具可以自动识别以下季文件夹命名模式：

### 英文命名
- `Season 1`, `Season 2`, `Season 3`...
- `Season1`, `Season2`, `Season3`...
- `S01`, `S02`, `S03`...
- `season1`, `season2`, `season3`...

### 中文命名
- `第1季`, `第2季`, `第3季`...

### 数字命名
- `1`, `2`, `3`... (纯数字)

## 文件夹结构示例

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

## 使用方法

### 基本用法

```bash
python3 multi_season_rename.py --folder "/path/to/tv/show" --show "剧名"
```

### 参数说明

- `--folder` 或 `-f`: 包含所有季文件夹的根目录（必需）
- `--show` 或 `-s`: 剧名（必需）
- `--manual` 或 `-m`: 手动选择季文件夹（默认自动检测）
- `--preview` 或 `-p`: 仅预览，不执行重命名（可选）

### 使用示例

#### 1. 自动检测并重命名

```bash
# 自动检测所有季文件夹并重命名
python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends"
```

#### 2. 手动选择季文件夹

```bash
# 手动选择要处理的季文件夹
python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --manual
```

#### 3. 预览重命名结果

```bash
# 仅预览，不执行重命名
python3 multi_season_rename.py --folder "/Users/username/Videos/Friends" --show "Friends" --preview
```

#### 4. 使用短参数

```bash
# 使用短参数形式
python3 multi_season_rename.py -f "/Users/username/Videos/Friends" -s "Friends" -p
```

## 重命名结果

重命名后的文件将符合 Infuse 媒体库命名规范：

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

## 工作流程

1. **检测季文件夹**: 工具会自动扫描根目录下的所有子文件夹，识别季文件夹
2. **预览结果**: 显示每个季的重命名计划
3. **确认执行**: 显示总览信息，要求用户确认
4. **批量重命名**: 按季逐个执行重命名操作
5. **结果报告**: 显示每季的成功/失败统计

## 安全特性

- ✅ 重命名前会检查目标文件名是否已存在
- ✅ 提供预览模式，可以查看重命名结果而不执行
- ✅ 保留原始文件扩展名
- ✅ 按文件名排序确定集数顺序
- ✅ 详细的进度和结果报告

## 故障排除

### 自动检测失败

如果自动检测没有找到正确的季文件夹：

1. 使用 `--manual` 参数手动选择
2. 检查文件夹命名是否符合支持的格式
3. 确保文件夹名称包含季数信息

### 文件重命名失败

可能的原因：
- 目标文件名已存在
- 文件被其他程序占用
- 权限不足

### 获取帮助

```bash
python3 multi_season_rename.py --help
```

## 注意事项

1. **备份重要文件**: 建议在重命名前备份重要文件
2. **检查预览**: 使用 `--preview` 参数先查看重命名结果
3. **文件排序**: 工具按文件名排序确定集数，确保文件命名有序
4. **支持格式**: 支持视频、字幕等多种媒体文件格式

## 示例场景

### 场景1: 标准季文件夹结构

```
Breaking Bad/
├── Season 1/
├── Season 2/
├── Season 3/
├── Season 4/
└── Season 5/
```

命令：
```bash
python3 multi_season_rename.py --folder "/path/to/Breaking Bad" --show "Breaking Bad"
```

### 场景2: 混合命名格式

```
Game of Thrones/
├── S01/
├── Season 2/
├── 3/
└── Season 4/
```

命令：
```bash
python3 multi_season_rename.py --folder "/path/to/Game of Thrones" --show "Game of Thrones"
```

### 场景3: 中文季文件夹

```
权力的游戏/
├── 第1季/
├── 第2季/
└── 第3季/
```

命令：
```bash
python3 multi_season_rename.py --folder "/path/to/权力的游戏" --show "权力的游戏"
``` 