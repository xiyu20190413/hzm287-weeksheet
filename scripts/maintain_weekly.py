import json, os, sys, re, urllib.request, datetime, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from parse_schedule import parse_row_aligned, parse_two_column, fix_missing_week, WEEK_ORDER
from rapidocr_onnxruntime import RapidOCR

DATA = os.path.join(ROOT, "data", "streamers.json")
STATE = os.path.join(ROOT, "data", "maintain_state.json")
LOG = os.path.join(ROOT, "data", "maintain_log.md")
TOKEN_FILE = os.path.join(ROOT, "data", ".github_token")
SESS_FILE = os.path.join(ROOT, "data", ".sessdata")
WEBSITE = os.path.join(ROOT, "website")
TMP_IMG = os.path.join(WEBSITE, "photo", "_tmp_week.png")
TMP_PROBE = os.path.join(ROOT, "data", "_tmp_probe.png")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
GITHUB_REPO = "xiyu20190413/hzm287"
TWO_COLUMN = {"羽啾chu2u"}

# 周表图识别关键词：星期英文/中文 + DAY 标记 + 周表标记
DAY_KW = ["MON", "TUE", "WED", "THU", "THR", "THUR", "FRI", "FRY", "SAT", "SUN",
          "DAY1", "DAY2", "DAY3", "DAY4", "DAY5", "DAY6", "DAY7",
          "周一", "周二", "周三", "周四", "周五", "周六", "周日",
          "星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日", "星期天"]
SCHED_KW = ["SCHEDULE", "周表", "排班", "直播安排", "日程", "直播表", "本周日程"]

# 右侧装饰区（如留言板）过滤阈值：x0 超过该值的块视为装饰，不进 schedule
MAX_X = {"四时小路Komichi": 700}


def http_get(url, referer, cookie=None):
    headers = {"User-Agent": UA, "Referer": referer}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def get_sessdata():
    try:
        with open(SESS_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def get_buvid3():
    d = json.loads(http_get("https://api.bilibili.com/x/frontend/finger/spi",
                            "https://www.bilibili.com/").decode("utf-8"))
    return d["data"]["b_3"] + "infoc"


def fetch_pinned_items(mid):
    """抓取主播置顶动态里的所有图片（list of {src,width,height}）；失败或无置顶返回 None"""
    sd = get_sessdata()
    if not sd:
        return None
    try:
        b3 = get_buvid3()
        url = (f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
               f"?host_mid={mid}&timezone_offset=-480")
        d = json.loads(http_get(url, f"https://space.bilibili.com/{mid}",
                                f"SESSDATA={sd}; buvid3={b3}").decode("utf-8"))
        if d.get("code") != 0:
            return None
        for it in d.get("data", {}).get("items", []):
            mods = it.get("modules", {}) or {}
            tag = (mods.get("module_tag") or {}).get("text", "")
            major = mods.get("module_dynamic", {}).get("major", {}) or {}
            if major.get("type") == "MAJOR_TYPE_DRAW" and tag == "置顶":
                return major.get("draw", {}).get("items", [])
        return None
    except Exception:
        return None


def fetch_img_src(opus_id, img_pos):
    """旧方案：按固定 opus_id + 图片位置抓取（作为置顶动态失败时的回退）"""
    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?id={opus_id}"
    d = json.loads(http_get(url, "https://t.bilibili.com/").decode("utf-8"))
    items = d["data"]["item"]["modules"]["module_dynamic"]["major"]["draw"]["items"]
    return items[img_pos - 1]["src"]


def download_img(src, path):
    if src.startswith("http://"):
        src = "https://" + src[len("http://"):]
    with open(path, "wb") as f:
        f.write(http_get(src, "https://www.bilibili.com/"))


def ocr_blocks(engine, img_path):
    result, _ = engine(img_path)
    blocks = []
    for box, text, score in (result or []):
        xs = [float(p[0]) for p in box]
        ys = [float(p[1]) for p in box]
        blocks.append({"text": str(text), "x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys)})
    return blocks


def blocks_to_schedule(blocks, name):
    if name in TWO_COLUMN:
        sched = parse_two_column(blocks, 900)
    else:
        sched = parse_row_aligned(blocks, max_x=MAX_X.get(name))
    sched = fix_missing_week(sched)
    out = {}
    for w in WEEK_ORDER:
        out[w] = [[e.get("start"), e.get("end"), e.get("topic", "")] for e in sched.get(w, [])]
    return out


def score_schedule(text):
    tu = text.upper()
    day_hits = sum(1 for k in DAY_KW if k in tu)
    sched_hits = sum(1 for k in SCHED_KW if k.upper() in tu)
    return day_hits, sched_hits


def detect_schedule(items, engine):
    """从置顶动态多张图中，用 OCR 关键词识别真正的周表图；返回 (src, blocks) 或 (None, None)"""
    best_src, best_blocks, best_day = None, None, 0
    for it in items:
        try:
            w = int(it.get("width") or 0)
            h = int(it.get("height") or 0)
        except (TypeError, ValueError):
            w = h = 0
        if w and h and w < 300 and h < 300:
            continue  # 跳过极小图（头像/角标）
        src = it["src"]
        try:
            download_img(src, TMP_PROBE)
            blocks = ocr_blocks(engine, TMP_PROBE)
        except Exception:
            continue
        text = " ".join(b["text"] for b in blocks)
        day, sched = score_schedule(text)
        if day > best_day:
            best_src, best_blocks, best_day = src, blocks, day
    if best_day < 2:  # 至少命中 2 个星期关键词才算周表
        return None, None
    return best_src, best_blocks


def current_week_key():
    y, w, _ = datetime.date.today().isocalendar()
    return f"{y}-W{w:02d}"


def push_github():
    try:
        with open(TOKEN_FILE, encoding="utf-8") as f:
            token = f.read().strip()
    except OSError as e:
        print(f"[push] 读取 token 失败: {e}")
        return
    remote = f"https://{GITHUB_REPO.split('/')[0]}:{token}@github.com/{GITHUB_REPO}.git"
    for cmd in [
        ["git", "add", "-A"],
        ["git", "commit", "-m", f"weekly update {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"],
    ]:
        r = subprocess.run(cmd, cwd=WEBSITE, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            print(f"[push] {cmd[0]} 失败: {r.stdout} {r.stderr}")
            return
    # 强制 HTTP/1.1：公司网络下 HTTP/2 会超时导致 git 静默退出 49
    r = subprocess.run(["git", "-c", "http.version=HTTP/1.1", "push", remote, "main"],
                       cwd=WEBSITE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 and "up-to-date" not in (r.stdout + r.stderr):
        last = (r.stderr or "").strip().splitlines()
        print(f"[push] push 失败（可能网络问题，下次运行会重试）: {last[-1] if last else '未知'}")
        return
    print("[push] 已推送到 GitHub")


def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    state = {}
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            state = json.load(f)

    week_key = current_week_key()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    logs = []
    changed = False

    engine = RapidOCR()

    for s in data["streamers"]:
        name = s["name"]
        st = state.get(name, {})
        mid = s.get("mid")
        blocks = None  # 检测阶段已 OCR 出的周表 blocks（复用避免重复 OCR）

        # 0) 本周已更新：直接跳过（不抓取、不 OCR，避免重复计算）
        if st.get("week_key") == week_key:
            logs.append(f"- [{now}] {name}：跳过（本周已更新）")
            continue

        # 1) 优先用置顶动态自动抓取 + 智能识别周表图
        items = fetch_pinned_items(mid) if mid else None
        if items:
            src, blocks = detect_schedule(items, engine)
            if src is None:
                logs.append(f"- [{now}] {name}：置顶动态未识别到周表图")
                continue
        else:
            # 回退：固定 opus_id + img_pos（SESSDATA 失效或网络异常时）
            try:
                src = fetch_img_src(s["opus_id"], s["img_pos"])
                logs.append(f"- [{now}] {name}：提示（置顶动态不可用，回退固定位置抓取）")
            except Exception as e:
                logs.append(f"- [{now}] {name}：抓取失败（{e}）")
                continue

        # 2) 首次运行：仅建立基线
        if not st:
            state[name] = {"img_src": src, "week_key": None}
            logs.append(f"- [{now}] {name}：首次建立基线")
            continue

        # 4) 周表图无变化 → 清空（等待新周表）
        if st.get("img_src") == src:
            if any(s["schedule"].get(w) for w in WEEK_ORDER):
                s["schedule"] = {w: [] for w in WEEK_ORDER}
                state[name] = st
                logs.append(f"- [{now}] {name}：清空（周表无改变）")
                changed = True
            else:
                logs.append(f"- [{now}] {name}：无改变（已空，继续等待）")
        # 5) 周表图变化 → 解析更新
        else:
            try:
                if blocks is None:
                    download_img(src, TMP_IMG)
                    blocks = ocr_blocks(engine, TMP_IMG)
                s["schedule"] = blocks_to_schedule(blocks, name)
                st["img_src"] = src
                st["week_key"] = week_key
                state[name] = st
                logs.append(f"- [{now}] {name}：更新（检测到新周表）")
                changed = True
            except Exception as e:
                logs.append(f"- [{now}] {name}：更新失败（{e}）")

    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(logs) + "\n")

    for l in logs:
        print(l)

    if changed:
        import generate_html
        generate_html.generate()
    # 无论是否有新变化，都尝试推送（确保之前网络失败的推送能补上）
    push_github()


if __name__ == "__main__":
    main()
