# ============================================================
# s-feishu-card-v1 / templates/utils.py
# 共用工具模块（Skill + Plugin 共用）
# 跨平台路径推断、凭证读取、环境检测
# 兼容 Windows / macOS / Linux
# ============================================================

import os
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict


# ============================================================
# 1. Hermes 环境检测
# ============================================================

def get_hermes_home() -> Path:
    """
    获取当前 Hermes 实例的根目录（~/.hermes 或 profile 子目录）
    
    推断优先级：
    1. HERMES_HOME 环境变量
    2. 当前文件位置回溯（utils.py → templates/ → skill/ → skills/ → .hermes/）
    3. 当前工作目录（cwd）
    4. 标准用户目录 ~/.hermes
    """
    # 方法1：环境变量
    env = os.environ.get("HERMES_HOME", "")
    if env:
        p = Path(env).resolve()
        if p.exists():
            return p
    
    # 方法2：从当前文件位置回溯
    # utils.py 通常在 ~/.hermes/skills/xxx/s-feishu-card-v1/templates/utils.py
    try:
        this_file = Path(__file__).resolve()
        for parent in this_file.parents:
            # 如果找到 .hermes 目录
            if parent.name == ".hermes":
                return parent
            # 或者找到包含 config.yaml 和 .env 的目录
            if (parent / "config.yaml").exists() and (parent / ".env").exists():
                return parent
    except Exception:
        pass
    
    # 方法3：当前工作目录
    cwd = Path.cwd().resolve()
    if (cwd / "config.yaml").exists() or (cwd / ".env").exists():
        return cwd
    
    # 方法4：标准用户目录（跨平台）
    return Path.home() / ".hermes"


def is_profile_mode() -> bool:
    """判断当前是否在 profile（子 agent）模式下运行"""
    hermes_home = get_hermes_home()
    return "profiles" in str(hermes_home).split(os.sep)


def get_current_profile_name() -> Optional[str]:
    """获取当前 profile 名称（如果不是 profile 模式返回 None）"""
    hermes_home = get_hermes_home()
    parts = str(hermes_home).split(os.sep)
    if "profiles" in parts:
        idx = parts.index("profiles")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


# ============================================================
# 2. 路径推断
# ============================================================

def get_hermes_repo_path() -> str:
    """
    动态推断 Hermes 源码/安装目录（用于导入 lark_oapi 等依赖）
    
    兼容任意安装位置：pip install / git clone / 打包安装
    """
    # 方法1：通过 hermes_cli 模块位置推断
    try:
        import hermes_cli
        repo = Path(hermes_cli.__file__).resolve().parent.parent
        if repo.exists():
            return str(repo)
    except Exception:
        pass
    
    # 方法2：通过 sys.path 中的 hermes 相关目录
    for p in sys.path:
        path = Path(p).resolve()
        if not path.exists():
            continue
        # 检查是否包含 Hermes 特征文件/目录
        if any(
            (path / marker).exists()
            for marker in ["gateway", "agent", "hermes_cli", "lark_oapi"]
        ):
            return str(path)
    
    # 方法3：从 HERMES_HOME 推断（venv 通常在 hermes-agent 目录下）
    hermes_home = get_hermes_home()
    if hermes_home.name == "hermes-agent":
        return str(hermes_home)
    parent = hermes_home.parent
    if parent.name == "hermes-agent":
        return str(parent)
    
    # 方法4：环境变量（用户自定义）
    env_path = os.environ.get("HERMES_REPO_PATH", "")
    if env_path:
        p = Path(env_path).resolve()
        if p.exists():
            return str(p)
    
    raise RuntimeError(
        "无法自动推断 Hermes 安装路径。请尝试以下方法之一：\n"
        "1. 设置 HERMES_REPO_PATH 环境变量指向 hermes-agent 目录\n"
        "2. 确保 hermes_cli 模块可在 Python 路径中导入\n"
        "3. 手动安装 lark_oapi: pip install lark-oapi"
    )


def find_skill_template(skill_name: str = "s-feishu-card-v1") -> Optional[Path]:
    """
    查找 Skill 模板目录（不假设分类名称）
    
    搜索范围：
    1. 当前 Hermes 实例的 skills 目录（含 profile 子目录）
    2. 标准 ~/.hermes/skills（递归搜索）
    3. sys.path 中的 skills 目录
    """
    # 方法1：当前实例的 skills 目录
    hermes_home = get_hermes_home()
    skills_dir = hermes_home / "skills"
    if skills_dir.exists():
        for path in skills_dir.rglob(skill_name):
            if path.is_dir():
                template_dir = path / "templates"
                if template_dir.exists():
                    return template_dir
    
    # 方法2：标准 ~/.hermes/skills
    default_skills = Path.home() / ".hermes" / "skills"
    if default_skills.exists() and default_skills != skills_dir:
        for path in default_skills.rglob(skill_name):
            if path.is_dir():
                template_dir = path / "templates"
                if template_dir.exists():
                    return template_dir
    
    # 方法3：sys.path
    for p in sys.path:
        candidate = Path(p).resolve() / "skills" / skill_name / "templates"
        if candidate.exists():
            return candidate
    
    return None


def get_env_path() -> Path:
    """
    获取当前 Hermes 实例的 .env 文件路径
    
    优先级：
    1. HERMES_HOME/.env
    2. 当前工作目录/.env
    3. 通过 FEISHU_APP_ID 匹配 profile/.env
    4. ~/.hermes/.env（fallback）
    """
    # 方法1：HERMES_HOME
    hermes_home = get_hermes_home()
    env_file = hermes_home / ".env"
    if env_file.exists():
        return env_file
    
    # 方法2：当前工作目录
    cwd_env = Path.cwd().resolve() / ".env"
    if cwd_env.exists():
        return cwd_env
    
    # 方法3：通过 FEISHU_APP_ID 匹配 profile
    current_app_id = os.environ.get("FEISHU_APP_ID", "")
    if current_app_id:
        profiles_dir = Path.home() / ".hermes" / "profiles"
        if profiles_dir.exists():
            for profile_dir in profiles_dir.iterdir():
                if not profile_dir.is_dir():
                    continue
                candidate = profile_dir / ".env"
                if candidate.exists():
                    content = candidate.read_text(encoding="utf-8")
                    if f"FEISHU_APP_ID={current_app_id}" in content:
                        return candidate
    
    # 方法4：fallback
    return Path.home() / ".hermes" / ".env"


# ============================================================
# 3. 凭证读取
# ============================================================

def read_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """读取 .env 文件，返回键值对字典"""
    result = {}
    path = env_path or get_env_path()
    if not path.exists():
        return result
    
    try:
        content = path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip()
    except Exception:
        pass
    
    return result


def get_feishu_credentials(
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    env_path: Optional[Path] = None,
) -> Tuple[str, str]:
    """
    获取飞书凭证（优先参数 > 环境变量 > .env 文件）
    
    返回: (app_id, app_secret)
    如果获取失败返回 ("", "")
    """
    _app_id = app_id or os.environ.get("FEISHU_APP_ID", "")
    _app_secret = app_secret or os.environ.get("FEISHU_APP_SECRET", "")
    
    if _app_id and _app_secret:
        return _app_id, _app_secret
    
    # 从 .env 文件读取
    env_vars = read_env_file(env_path)
    if not _app_id:
        _app_id = env_vars.get("FEISHU_APP_ID", "")
    if not _app_secret:
        _app_secret = env_vars.get("FEISHU_APP_SECRET", "")
    
    return _app_id, _app_secret


def get_feishu_chat_id(
    chat_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> str:
    """
    获取飞书 chat_id（优先参数 > session_id 解析 > 环境变量）
    
    注意：不再硬编码任何 fallback chat_id
    """
    # 方法1：直接传入
    if chat_id and chat_id.startswith("oc_"):
        return chat_id
    
    # 方法2：从 session_id 解析（格式：feishu:ou_xxx:oc_xxx）
    if session_id and "oc_" in session_id:
        parts = session_id.split(":")
        for part in parts:
            if part.startswith("oc_"):
                return part
    
    # 方法3：环境变量（用户显式配置）
    env_chat_id = os.environ.get("FEISHU_DEFAULT_CHAT_ID", "")
    if env_chat_id and env_chat_id.startswith("oc_"):
        return env_chat_id
    
    return ""


# ============================================================
# 4. 跨平台兼容
# ============================================================

def ensure_lark_oapi():
    """
    确保 lark_oapi 模块可导入，自动添加 Hermes 路径到 sys.path
    
    如果 Hermes 内置的 lark_oapi 不可用，尝试 pip 安装
    """
    try:
        import lark_oapi
        return
    except ImportError:
        pass
    
    # 尝试添加 Hermes 路径
    try:
        repo_path = get_hermes_repo_path()
        if repo_path not in sys.path:
            sys.path.insert(0, repo_path)
        import lark_oapi
        return
    except ImportError:
        pass
    
    # 尝试 pip 安装
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "lark-oapi", "-q"])
        import lark_oapi
        return
    except Exception:
        pass
    
    raise ImportError(
        "无法导入 lark_oapi 模块。请手动安装：pip install lark-oapi"
    )


# ============================================================
# 5. 调试辅助
# ============================================================

def dump_env_info() -> str:
    """输出当前环境信息（用于调试）"""
    lines = [
        "=== s-feishu-card-v1 环境诊断 ===",
        f"平台: {sys.platform}",
        f"Python: {sys.version.split()[0]}",
        f"HERMES_HOME: {os.environ.get('HERMES_HOME', '(未设置)')}",
        f"推断的 hermes_home: {get_hermes_home()}",
        f"Profile 模式: {is_profile_mode()}",
        f"Profile 名称: {get_current_profile_name() or '(无)'}",
        f".env 路径: {get_env_path()}",
        f".env 存在: {get_env_path().exists()}",
        f"Skill 模板路径: {find_skill_template() or '(未找到)'}",
        f"Hermes repo 路径: {get_hermes_repo_path()}",
        "==================================",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    # 直接运行此文件可进行环境诊断
    print(dump_env_info())
