#!/usr/bin/env python3
"""飞书日历工具 - Hermes Agent 通用日历操作脚本

通过飞书 API (tenant_access_token) 管理共享日历的日程增删改查。
状态持久化到同目录下的 calendar_state.json。
"""

import argparse, json, os, sys, datetime, time, requests
from urllib.parse import quote

API_BASE = "https://open.feishu.cn/open-apis"
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar_state.json")


# ========== 基础工具 ==========

def load_credentials():
    """加载飞书凭证: 环境变量 > HERMES_HOME/.env"""
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    if app_id and app_secret:
        return app_id, app_secret
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    env_file = os.path.join(hermes_home, ".env")
    if not os.path.exists(env_file):
        _error(f"找不到 .env: {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            k, _, v = line.partition("=")
            if k == "FEISHU_APP_ID":
                app_id = v.strip().strip('"\'')
            elif k == "FEISHU_APP_SECRET":
                app_secret = v.strip().strip('"\'')
    if not app_id or not app_secret:
        _error("FEISHU_APP_ID 或 FEISHU_APP_SECRET 未配置")
    return app_id, app_secret


def get_token(app_id, app_secret):
    r = requests.post(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
    )
    data = r.json()
    if data.get("code") != 0:
        _error(f"获取 token 失败: {data.get('msg')}")
    return data["tenant_access_token"]


def hdr(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def cal_url(cal_id):
    return f"{API_BASE}/calendar/v4/calendars/{quote(cal_id, safe='')}"


def _output(d):
    print(json.dumps(d, ensure_ascii=False))


def _error(msg):
    _output({"ok": False, "error": msg})
    sys.exit(1)


# ========== 状态管理 ==========

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"initialized": False}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _require_init():
    state = load_state()
    if not state.get("initialized"):
        _error("日历未初始化，请先执行 init")
    return state


# ========== chat_id 查找 ==========

def find_chat_id():
    """多来源查找 chat_id"""
    for key in ("FEISHU_DM_CHAT_ID", "FEISHU_CHAT_ID"):
        v = os.environ.get(key)
        if v:
            return v
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    for env_path in (
        os.path.join(hermes_home, ".env"),
        os.path.join(hermes_home, "profiles", os.environ.get("HERMES_PROFILE", "default"), ".env"),
    ):
        if not os.path.exists(env_path):
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("FEISHU_DM_CHAT_ID="):
                    return line.split("=", 1)[1].strip()
    return None


# ========== 命令实现 ==========

def cmd_status():
    state = load_state()
    _output({
        "initialized": state.get("initialized", False),
        "calendar_id": state.get("calendar_id"),
        "calendar_name": state.get("calendar_name"),
    })


def cmd_init(name, chat_id=None):
    state = load_state()
    if state.get("initialized"):
        _output({"ok": True, "message": "已初始化", "calendar_id": state["calendar_id"]})
        return

    app_id, app_secret = load_credentials()
    token = get_token(app_id, app_secret)
    h = hdr(token)

    # 1. 创建日历
    r = requests.post(
        f"{API_BASE}/calendar/v4/calendars",
        headers=h,
        json={
            "summary": name,
            "description": "Hermes Agent 管理的日历",
            "color": -1,
        },
    )
    data = r.json()
    if data.get("code") != 0:
        _error(f"创建日历失败: {data.get('msg')}")
    cal = data["data"]["calendar"]
    cal_id = cal["calendar_id"]

    # 2. 获取用户 open_id
    cid = chat_id or find_chat_id()
    if not cid:
        _error("需要 chat_id。请通过 --chat-id 参数提供，或在 .env 中配置 FEISHU_DM_CHAT_ID")
    r = requests.get(f"{API_BASE}/im/v1/chats/{cid}/members", headers=h, params={"page_size": 20})
    data = r.json()
    if data.get("code") != 0:
        _error(f"获取聊天成员失败: {data.get('msg')}")
    members = data.get("data", {}).get("items", [])
    if not members:
        _error("聊天中没有成员")
    user_id = members[0]["member_id"]
    user_name = members[0].get("name", "")

    # 3. ACL 授权
    r = requests.post(
        f"{cal_url(cal_id)}/acls",
        headers=h,
        json={"scope": {"type": "user", "user_id": user_id}, "role": "reader"},
    )
    data = r.json()
    if data.get("code") != 0:
        _error(f"ACL 授权失败: {data.get('msg')}")

    # 4. 保存状态
    save_state({
        "initialized": True,
        "calendar_id": cal_id,
        "calendar_name": name,
        "user_open_id": user_id,
        "user_name": user_name,
        "created_at": datetime.datetime.now().isoformat(),
    })
    _output({
        "ok": True,
        "calendar_id": cal_id,
        "calendar_name": name,
        "user_name": user_name,
        "message": f"日历 '{name}' 创建成功。请前往飞书日历搜索 '{name}' 并订阅。",
    })


def cmd_list(days=7):
    state = _require_init()
    app_id, app_secret = load_credentials()
    token = get_token(app_id, app_secret)
    h = hdr(token)

    now = datetime.datetime.now()
    r = requests.get(
        f"{cal_url(state['calendar_id'])}/events",
        headers=h,
        params={
            "start_time": str(int(now.timestamp())),
            "end_time": str(int((now + datetime.timedelta(days=days)).timestamp())),
            "page_size": 50,
        },
    )
    data = r.json()
    if data.get("code") != 0:
        _error(f"查询日程失败: {data.get('msg')}")
    events = []
    for e in data.get("data", {}).get("items", []):
        if e.get("status") == "cancelled":
            continue
        events.append({
            "event_id": e.get("event_id"),
            "title": e.get("summary"),
            "description": e.get("description", ""),
            "location": e.get("location", ""),
            "start": e.get("start_time"),
            "end": e.get("end_time"),
            "status": e.get("status"),
            "link": e.get("app_link", ""),
        })
    _output({"ok": True, "days": days, "count": len(events), "events": events})


def cmd_create(title, when, end=None, minutes=None, desc=None, location=None):
    state = _require_init()
    app_id, app_secret = load_credentials()
    token = get_token(app_id, app_secret)
    h = hdr(token)

    start_dt = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
    if end:
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M")
    elif minutes:
        end_dt = start_dt + datetime.timedelta(minutes=minutes)
    else:
        end_dt = start_dt + datetime.timedelta(hours=1)

    body = {
        "summary": title,
        "start_time": {"timestamp": str(int(start_dt.timestamp())), "timezone": "Asia/Shanghai"},
        "end_time": {"timestamp": str(int(end_dt.timestamp())), "timezone": "Asia/Shanghai"},
        "color": -1,
        "need_notification": True,
    }
    if desc:
        body["description"] = desc
    if location:
        body["location"] = location

    r = requests.post(f"{cal_url(state['calendar_id'])}/events", headers=h, json=body)
    data = r.json()
    if data.get("code") != 0:
        _error(f"创建日程失败: {data.get('msg')}")
    evt = data.get("data", {}).get("event", data.get("data", {}))
    _output({
        "ok": True,
        "event_id": evt.get("event_id"),
        "title": evt.get("summary"),
        "message": f"日程 '{title}' 创建成功",
    })


def cmd_delete(event_id):
    state = _require_init()
    app_id, app_secret = load_credentials()
    token = get_token(app_id, app_secret)
    h = hdr(token)

    r = requests.delete(
        f"{cal_url(state['calendar_id'])}/events/{quote(event_id, safe='')}",
        headers=h,
    )
    data = r.json()
    if data.get("code") != 0:
        _error(f"删除日程失败: {data.get('msg')}")
    _output({"ok": True, "message": "日程已删除"})


def cmd_reset(confirm=False):
    """重置日历状态，删除日历并清空状态文件。"""
    state = load_state()
    if not state.get("initialized"):
        _output({"ok": True, "message": "未初始化，无需重置"})
        return
    if not confirm:
        _output({
            "ok": False,
            "error": "reset 需要确认。请加 --confirm 参数。这会删除日历及所有日程。",
        })
        return
    app_id, app_secret = load_credentials()
    token = get_token(app_id, app_secret)
    h = hdr(token)
    r = requests.delete(cal_url(state["calendar_id"]), headers=h)
    data = r.json()
    if data.get("code") != 0:
        _error(f"删除日历失败: {data.get('msg')}")
    save_state({"initialized": False})
    _output({"ok": True, "message": "日历已删除，状态已重置"})


# ========== 入口 ==========

def main():
    parser = argparse.ArgumentParser(description="飞书日历工具")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status")

    pi = sub.add_parser("init")
    pi.add_argument("--name", required=True, help="日历名称")
    pi.add_argument("--chat-id", help="飞书 DM chat_id")

    pl = sub.add_parser("list")
    pl.add_argument("--days", type=int, default=7, help="未来 N 天（默认 7）")

    pc = sub.add_parser("create")
    pc.add_argument("--title", required=True, help="标题")
    pc.add_argument("--when", required=True, help="开始时间 YYYY-MM-DD HH:MM")
    pc.add_argument("--end", help="结束时间 YYYY-MM-DD HH:MM")
    pc.add_argument("--minutes", type=int, help="持续分钟数")
    pc.add_argument("--desc", help="描述")
    pc.add_argument("--location", help="地点")

    pd = sub.add_parser("delete")
    pd.add_argument("--event-id", required=True, help="事件 ID")

    pr = sub.add_parser("reset")
    pr.add_argument("--confirm", action="store_true", help="确认重置")

    args = parser.parse_args()

    dispatch = {
        "status": lambda: cmd_status(),
        "init": lambda: cmd_init(args.name, args.chat_id),
        "list": lambda: cmd_list(args.days),
        "create": lambda: cmd_create(args.title, args.when, args.end, args.minutes, args.desc, args.location),
        "delete": lambda: cmd_delete(args.event_id),
        "reset": lambda: cmd_reset(args.confirm),
    }

    if args.cmd in dispatch:
        dispatch[args.cmd]()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
