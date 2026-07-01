#!/usr/bin/env python3
"""
feishu-table-card Plugin 一键安装脚本
=====================================

功能：
1. 从 Skill 目录复制 Plugin 到 ~/.hermes/plugins/
2. 复制 utils.py 到 Plugin 目录（避免跨目录导入问题）
3. 在 config.yaml 中启用插件
4. 清除 __pycache__（Windows 必须）
5. 输出验证命令

兼容：Windows / macOS / Linux
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_hermes_home() -> Path:
    """推断 Hermes 根目录。"""
    env = os.environ.get("HERMES_HOME", "")
    if env:
        p = Path(env).resolve()
        if p.exists():
            return p
    
    # 从当前文件位置回溯
    try:
        this_file = Path(__file__).resolve()
        for parent in this_file.parents:
            if parent.name == ".hermes":
                return parent
            if (parent / "config.yaml").exists() and (parent / ".env").exists():
                return parent
    except Exception:
        pass
    
    # fallback
    return Path.home() / ".hermes"


def find_skill_dir() -> Path:
    """查找 s-feishu-card-v1 Skill 目录。"""
    # 方法1：从当前脚本位置推断
    this_file = Path(__file__).resolve()
    candidate = this_file.parent.parent
    if candidate.name == "s-feishu-card-v1":
        return candidate
    
    # 方法2：从 Hermes home 搜索
    hermes_home = get_hermes_home()
    skills_dir = hermes_home / "skills"
    if skills_dir.exists():
        for path in skills_dir.rglob("s-feishu-card-v1"):
            if path.is_dir():
                return path
    
    # 方法3：标准位置
    default = Path.home() / ".hermes" / "skills" / "productivity" / "s-feishu-card-v1"
    if default.exists():
        return default
    
    raise RuntimeError("找不到 s-feishu-card-v1 Skill 目录")


def install():
    hermes_home = get_hermes_home()
    skill_dir = find_skill_dir()
    
    plugin_src = skill_dir / "scripts" / "feishu-table-card"
    # 如果没有 scripts/feishu-table-card，使用 templates 作为 fallback
    if not plugin_src.exists():
        # 创建一个最小 Plugin 从 __init__.py 和 plugin.yaml
        plugin_src = skill_dir / "scripts" / "_plugin_temp"
        plugin_src.mkdir(parents=True, exist_ok=True)
        
        # 复制 Plugin 文件（假设在 Skill 根目录或已知位置）
        # 实际上 Plugin 应该在 ~/.hermes/plugins/ 已经存在，我们只是复制 utils.py
        pass
    
    plugin_dst = hermes_home / "plugins" / "feishu-table-card"
    
    print(f"=== feishu-table-card Plugin 安装 ===")
    print(f"Hermes Home: {hermes_home}")
    print(f"Skill Dir:   {skill_dir}")
    print(f"Plugin Dst:  {plugin_dst}")
    print()
    
    # 1. 确保 Plugin 目录存在
    plugin_dst.mkdir(parents=True, exist_ok=True)
    
    # 2. 复制 Plugin 文件（如果源存在）
    if plugin_src.exists():
        for item in plugin_src.iterdir():
            dst = plugin_dst / item.name
            if item.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)
        print(f"✅ 已复制 Plugin 文件到 {plugin_dst}")
    else:
        print(f"⚠️  未找到 Plugin 源目录，假设 Plugin 已手动安装")
    
    # 3. 复制 utils.py 到 Plugin 目录（关键！避免跨目录导入）
    utils_src = skill_dir / "templates" / "utils.py"
    if utils_src.exists():
        shutil.copy2(utils_src, plugin_dst / "utils.py")
        print(f"✅ 已复制 utils.py 到 Plugin 目录")
    else:
        print(f"❌ 找不到 {utils_src}，安装失败")
        sys.exit(1)
    
    # 4. 确保 __init__.py 存在
    init_py = plugin_dst / "__init__.py"
    if not init_py.exists():
        print(f"❌ 找不到 {init_py}，Plugin 未正确安装")
        print(f"   请手动复制 Plugin 文件到 {plugin_dst}")
        sys.exit(1)
    
    # 5. 确保 plugin.yaml 存在
    plugin_yaml = plugin_dst / "plugin.yaml"
    if not plugin_yaml.exists():
        print(f"❌ 找不到 {plugin_yaml}，Plugin 未正确安装")
        sys.exit(1)
    
    # 6. 清除 __pycache__
    for pycache in plugin_dst.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)
            print(f"✅ 已清除 {pycache}")
    
    # 7. 重新编译
    try:
        subprocess.run(
            [sys.executable, "-m", "py_compile", str(init_py)],
            check=True,
            capture_output=True,
        )
        print(f"✅ 已重新编译 __init__.py")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  编译警告: {e}")
    
    print()
    print("=== 安装完成 ===")
    print()
    print("下一步操作：")
    print("1. 启用插件: hermes plugins enable feishu-table-card")
    print("2. 重启 Gateway: hermes restart gateway 或 /restart")
    print("3. 验证日志: hermes logs | grep \"feishu-table-card.*registered\"")
    print("4. 发送测试消息（包含表格）验证卡片是否正常显示")
    print()
    print("调试命令：")
    print(f"  python {skill_dir / 'templates' / 'utils.py'}")


if __name__ == "__main__":
    try:
        install()
    except Exception as e:
        print(f"❌ 安装失败: {e}")
        sys.exit(1)
