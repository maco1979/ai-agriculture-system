#!/usr/bin/env python3
"""
OpenClaw 自动安装脚本
将AI农业决策系统的Skills自动部署到OpenClaw工作区

用法:
  python install-to-openclaw.py              # 自动检测并安装
  python install-to-openclaw.py --dry-run    # 预览，不实际操作
  python install-to-openclaw.py --uninstall  # 卸载
"""
import os
import sys
import json
import shutil
import argparse
import platform

# ── 配置 ────────────────────────────────────────────────────────────────
SKILL_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_SOURCE_DIR = os.path.join(SKILL_PACKAGE_DIR, "skills")

SKILL_NAMES = [
    "ai-agriculture-system",
    "agriculture",
    "camera-ptz",
    "ai-models",
    "system-monitor",
]


def get_openclaw_dir():
    """获取OpenClaw工作区目录"""
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Windows":
        candidates = [
            os.path.join(home, ".openclaw", "workspace"),
            os.path.join(os.environ.get("APPDATA", home), "openclaw", "workspace"),
            os.path.join(home, "AppData", "Roaming", "openclaw", "workspace"),
        ]
    elif system == "Darwin":  # macOS
        candidates = [
            os.path.join(home, ".openclaw", "workspace"),
            os.path.join(home, "Library", "Application Support", "openclaw", "workspace"),
        ]
    else:  # Linux
        candidates = [
            os.path.join(home, ".openclaw", "workspace"),
            os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(home, ".config")),
                         "openclaw", "workspace"),
        ]

    for c in candidates:
        if os.path.exists(c):
            return c

    # 默认路径（即使不存在也返回）
    return os.path.join(home, ".openclaw", "workspace")


def install(dry_run=False):
    openclaw_dir = get_openclaw_dir()
    skills_dir = os.path.join(openclaw_dir, "skills")

    print("\n[OpenClaw] AI农业决策系统 Skills 安装程序")
    print("-" * 55)
    print(f"  [SRC] 源目录  : {SKILLS_SOURCE_DIR}")
    print(f"  [DST] 目标目录: {skills_dir}")
    if dry_run:
        print("  [!]  DRY RUN 模式 -- 不会实际修改文件")
    print()

    if not os.path.exists(SKILLS_SOURCE_DIR):
        print(f"[ERROR] 源目录不存在: {SKILLS_SOURCE_DIR}")
        sys.exit(1)

    installed = []
    skipped = []
    errors = []

    for skill in SKILL_NAMES:
        src = os.path.join(SKILLS_SOURCE_DIR, skill)
        dst = os.path.join(skills_dir, skill)

        if not os.path.exists(src):
            print(f"  [SKIP] 跳过（源不存在）: {skill}")
            skipped.append(skill)
            continue

        if os.path.exists(dst):
            action = "覆盖更新"
        else:
            action = "新安装"

        print(f"  [PKG] {action}: {skill}")

        if not dry_run:
            try:
                os.makedirs(skills_dir, exist_ok=True)
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                installed.append(skill)
            except Exception as e:
                print(f"       [FAIL] 失败: {e}")
                errors.append((skill, str(e)))
        else:
            installed.append(skill)

    print()
    print("-" * 55)
    print(f"  [OK]  成功安装: {len(installed)} 个")
    if skipped:
        print(f"  [--]  跳过: {len(skipped)} 个")
    if errors:
        print(f"  [ERR] 失败: {len(errors)} 个")

    if not dry_run and installed:
        print()
        print("  安装完成！重启 OpenClaw 后，新技能将自动加载。")
        print()
        print("  快速测试命令（在OpenClaw中）：")
        print('  -> "检查AI农业系统状态"')
        print('  -> "给番茄开花期生成光配方"')
        print('  -> "查看系统CPU和内存使用率"')
        print('  -> "列出所有AI模型"')

    if dry_run:
        print()
        print("  [i] 以上为预览，运行时去掉 --dry-run 参数执行实际安装")

    print()


def uninstall():
    openclaw_dir = get_openclaw_dir()
    skills_dir = os.path.join(openclaw_dir, "skills")

    print("\n[OpenClaw] 卸载 AI农业决策系统 Skills")
    print("-" * 55)

    removed = []
    for skill in SKILL_NAMES:
        dst = os.path.join(skills_dir, skill)
        if os.path.exists(dst):
            shutil.rmtree(dst)
            print(f"  [DEL] 已删除: {skill}")
            removed.append(skill)
        else:
            print(f"  [ - ] 未安装: {skill}")

    print()
    print(f"  卸载完成，已删除 {len(removed)} 个技能。")
    print()


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Skills 安装程序")
    parser.add_argument("--dry-run", action="store_true", help="预览安装，不修改文件")
    parser.add_argument("--uninstall", action="store_true", help="卸载所有技能")
    args = parser.parse_args()

    if args.uninstall:
        uninstall()
    else:
        install(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
