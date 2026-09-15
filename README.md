# Infuse TV 重命名工具

将电视剧整理为 `剧名_S01E01.ext`，支持单季、多季、每文件多集及同名字幕。
命令行只使用 Python 标准库；图形界面使用 Streamlit。建议 Python 3.10+。

## 使用

先预览；确认映射后去掉 `--preview` 执行，命令行会要求确认。

```bash
# 单季
python3 tv_rename.py --folder '/path/to/Season 1' --show 'Friends' --season 1 --preview

# 多季
python3 multi_season_rename.py --folder '/path/to/Friends' --show 'Friends' --preview

# 每文件两集（可用 --episodes-per-file 1 至 5）
python3 dual_episode_rename.py --folder '/path/to/Friends' --show 'Friends' --preview

# 只有明确需要重新编号时使用
python3 tv_rename.py --folder '/path/to/Season 1' --show 'Friends' --season 1 --renumber --preview
```

图形界面：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 编号规则

- **默认保留已有集号和缺集**：`S02E08`、`S02E10` 不会变为 E08、E09。
- 支持 `S01E01`、`E01`、`EP01`、`episode_01`、中文集号及纯数字文件名。
- 多集标记如 `S01E01E02E03` 保留完整编号；`E01-E03` 展开为 E01E02E03。
- 明确标记优先。仅一个集号且设置每文件 N 集时，从该编号开始分配 N 集；无集号时按排序分配，避开已有编号。无标记的文件必须检查预览。
- 各 CLI 的 `--renumber` / UI「按顺序重新编号」会明确忽略已有集号。UI 可设置起始编号及手动顺序。
- 季目录支持 `Season 1`、`S01`、`第1季`、纯数字目录。重复季号或文件内季号不符会报错。
- 同集多个版本应先选择要处理的版本；工具不会把不同版本自动当成后续集数。

例如：

```text
Friends/
├── S01/
│   ├── Friends_S01E01.mp4
│   └── Friends_S01E01.chs.eng.srt
└── S02/
    ├── Friends_S02E08.mp4
    └── Friends_S02E10.mp4
```

字幕需与视频具有相同基础名，可附加语言标记；匹配忽略大小写与常见分隔符差异。
例如 `Friends.S01E01.1080p.mp4` 对应 `Friends.S01E01.1080p.chs.eng.srt`。

## 安全与恢复

执行前检查整批计划的重复源文件、重复目标、已有目标和无效文件名，冲突时阻止执行。
已经符合目标名称的文件跳过，不记为失败。仅重命名，保留扩展名，不转换媒体内容。

成功改名写入所选根目录的 `rename_history.json`。UI 的「历史记录 / 撤销操作」可恢复上一批；
恢复失败条目保留，可消除冲突后重试。日志损坏会明确报错，不能继续覆盖旧记录。

也可在 Python 中撤销：

```python
from rename_logger import RenameLogger
success, failed = RenameLogger('/path/to/Friends').undo_last_batch()
```

操作期间避免其他程序同时修改目录。日志在批次结束时写入，进程被强制终止或日志写入失败仍可能需要手动恢复；重要媒体应有独立备份。
文件命名成功不代表 Infuse 已刷新索引或验证过播放，需在 Infuse 内另行检查。

## 文件与选项

| 文件 | 用途 |
|---|---|
| `tv_rename.py` | 单季计划、文件名生成及字幕匹配 |
| `multi_season_rename.py` | 季目录检测与多季调度 |
| `dual_episode_rename.py` | 复用上述核心的多集兼容入口 |
| `name_utils.py` | 剧名、集号、日期解析 |
| `rename_operations.py` | 所有模式共用的计划检查与执行 |
| `rename_logger.py` | 历史日志与恢复 |
| `streamlit_app.py` | 图形界面 |
| `example.py` | 临时目录中的完整演示 |

UI 及 Python API 还支持保留集名、保留来源剧名、剧名括号后缀和保留原文件名作为标题。
CLI 具体参数见各入口 `--help`；多季手动选择见 [多季指南](MULTI_SEASON_GUIDE.md)。

支持视频：`.mp4 .mkv .avi .mov .wmv .flv .webm .rmvb .rm .m4v .3gp .ogv`。
支持字幕：`.srt .ass .ssa .sub`。种子文件不会当作视频处理。

本轮整理移除了独立的 MP4→MP3 转换入口、重复多季示例与旧 README 备份；历史实现可在 Git 中找回。

## 验证

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python example.py
```

测试覆盖核心重命名、日志恢复及真实 Streamlit AppTest 交互；UI 测试需先安装依赖，未安装时会跳过。原生目录选择对话框的返回值在自动化测试中模拟。

[English guide](README_EN.md) · [MIT License](LICENSE)
