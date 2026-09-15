"""所有入口共用的计划校验与文件重命名执行器。"""
from pathlib import Path
from rename_logger import RenameLogger


def _is_case_only_rename(source, target):
    return (source.parent == target.parent and source.name.casefold() == target.name.casefold()
            and not target.is_symlink() and target.exists() and source.samefile(target)
            and target.name not in {entry.name for entry in target.parent.iterdir()})


def validate_plan(plan):
    sources, targets = set(), set()
    for source, name in plan:
        source = Path(source)
        if not name or name in {'.', '..'} or '/' in name or '\\' in name or '\0' in name:
            raise ValueError(f"目标必须是文件名: {name!r}")
        target = source.parent / name
        source_key = str(source.absolute()).casefold()
        target_key = str(target.absolute()).casefold()
        if source_key in sources or target_key in targets:
            raise ValueError(f"计划包含重复源文件或目标: {source} -> {name}")
        sources.add(source_key)
        targets.add(target_key)
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"源文件不存在或是符号链接: {source}")
        if target != source and (target.exists() or target.is_symlink()) and not _is_case_only_rename(source, target):
            raise FileExistsError(f"目标已存在: {target}")


def execute_plans(root, plans):
    """全批预检后执行；已标准命名的文件跳过，不记为失败。"""
    validate_plan([item for plan in plans.values() for item in plan])
    logger = RenameLogger(str(root))
    logger.has_history()  # 坏日志必须在首次文件修改之前报错。
    results, renamed = {}, []
    try:
        for season, plan in plans.items():
            success, failed = 0, 0
            for source, name in plan:
                source = Path(source)
                target = source.parent / name
                if source == target:
                    continue
                try:
                    if (target.exists() or target.is_symlink()) and not _is_case_only_rename(source, target):
                        raise FileExistsError(f"目标已存在: {target}")
                    source.rename(target)
                    renamed.append((source, target))
                    success += 1
                    print(f"✅ {source.name} -> {name}")
                except OSError as error:
                    failed += 1
                    print(f"❌ {source.name}: {error}")
            results[season] = (success, failed)
    finally:
        if renamed:
            logger.log_batch(renamed)
    return results
