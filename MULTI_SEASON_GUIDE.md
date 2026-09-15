# 多季操作指南

```text
Friends/
├── S01/
├── Season 2/
└── 第3季/
```

```bash
python3 multi_season_rename.py --folder '/path/to/Friends' --show Friends --preview
```

预览显示每个文件的旧名和新名。确认后去掉 `--preview` 执行。
默认保留已有集号和缺集，不按文件数量重新填补编号。

每文件多集时使用：

```bash
python3 dual_episode_rename.py --folder '/path/to/Friends' --show Friends --episodes-per-file 2 --preview
```

无法自动识别季目录时，可在 UI 为每个目录指定季号，或使用交互式 CLI：

```bash
python3 multi_season_rename.py --folder '/path/to/Friends' --show Friends --manual --preview
```

自动检测只识别明确季标记，不将年份或分辨率当作季号；重复季号会报错。
同集多版本、目标重名、源季号不符需要先解决再执行。

全部季的成功改名保存在根目录的一批 `rename_history.json` 中，可从 UI 撤销。
失败的恢复条目保留以供重试。

完整规则、字幕匹配、恢复限制及验证命令见 [README](README.md)。
