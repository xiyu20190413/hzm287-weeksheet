import json, re, os

RAW = r"C:\Users\IT008\WorkBuddy\2026-08-13-task-21\data\raw_ocr.json"
OUT = r"C:\Users\IT008\WorkBuddy\2026-08-13-task-21\data\schedule.json"
DEFAULT_DURATION = 2  # 小时

WEEK_ORDER = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

WEEK_EN = {"MON": "MON", "TUE": "TUE", "WED": "WED", "THU": "THU", "THR": "THU",
           "THUR": "THU", "FRI": "FRI", "FRY": "FRI", "FRB": "FRI", "SAT": "SAT", "SAL": "SAT", "SUN": "SUN"}
WEEK_DAY = {"DAY1": "MON", "DAY2": "TUE", "DAY3": "WED", "DAY4": "THU",
            "DAY5": "FRI", "DAY6": "SAT", "DAY7": "SUN"}
WEEK_CN = {"星期一": "MON", "周一": "MON", "星期二": "TUE", "周二": "TUE",
           "星期三": "WED", "周三": "WED", "星期四": "THU", "周四": "THU",
           "星期五": "FRI", "周五": "FRI", "星期六": "SAT", "周六": "SAT",
           "星期日": "SUN", "周日": "SUN", "星期天": "SUN", "周天": "SUN"}

DECOR_KW = ["SCHEDULE", "WEEKLY", "今日放送", "STREAMINGTODAY", "TREAMINGTODAY",
            "常规周表", "本周日程", "周间予定表", "直播安排", "LIKC", "LIKO",
            "DATE", "TO THE KOMICHI", "ASSASSIN", "BUNNY", "请支持新投稿", "播完了",
            "CHEDULE", "EKL", "HEDUL", "ＥＫＬ",
            "留言板", "提问箱", "推歌", "电台来信", "MESSAGE"]


def find_week(text):
    t = text.strip()
    m = re.match(r'^(MON|TUE|WED|THUR|THU|THR|FRI|FRY|FRB|SAT|SAL|SUN)\s*[.:：]?\s*(.*)$', t, re.I)
    if m:
        return WEEK_EN[m.group(1).upper()], m.group(2).strip()
    m = re.match(r'^(DAY\s*[1-7])\s*[.:：]?\s*(.*)$', t, re.I)
    if m:
        return WEEK_DAY[m.group(1).upper().replace(" ", "")], m.group(2).strip()
    m = re.match(r'^(星期一|星期二|星期三|星期四|星期五|星期六|星期日|星期天|周一|周二|周三|周四|周五|周六|周日|周天)\s*[.:：]?\s*(.*)$', t)
    if m:
        return WEEK_CN[m.group(1)], m.group(2).strip()
    return None, t


def is_decor(text):
    t = text.strip()
    if len(t) == 1 and t.isascii() and t.isalpha():
        return True
    tu = t.upper().replace(" ", "")
    for kw in DECOR_KW:
        if kw.upper().replace(" ", "") in tu:
            return True
    if re.fullmatch(r'\d{1,2}[./]\d{1,2}', t):
        return True
    if re.search(r'\d{1,2}[./]\d{1,2}\s*[-~]\s*\d{1,2}[./]\d{1,2}', t):
        return True
    if re.fullmatch(r'20\d{2}\s*\d{1,2}[./]\d{1,2}\s*[-~]\s*\d{1,2}[./]\d{1,2}\s*\S*', t):
        return True
    return False


def parse_content(text):
    """返回 (entries, topic)；entries = [(start, end_or_None)]"""
    t = text.strip()

    def ampm_repl(m):
        is_pm = m.group(1).lower() == "pm"
        hh, mm = int(m.group(2)), int(m.group(3))
        if is_pm and hh < 12:
            hh += 12
        if not is_pm and hh == 12:
            hh = 0
        return f"{hh:02d}:{mm:02d}"

    t = re.sub(r'([AaPp][Mm])\s*[:：]?\s*(\d{1,2})\s*[:：]\s*(\d{2})', ampm_repl, t)
    t = re.sub(r'(?<!\d)(\d)\s+(\d{1,2}\s*[:：]\s*\d{2})(?!\d)', lambda m: m.group(1) + m.group(2), t)
    t = re.sub(r'(\d{1,2})\s*[:：]\s*(\d{2})', lambda m: m.group(1) + ":" + m.group(2), t)

    tokens = []
    for m in re.finditer(r'(\d{1,2}):+(\d{2})', t):
        hh, mm = int(m.group(1)), int(m.group(2))
        tokens.append((m.start(), m.end(), f"{hh:02d}:{mm:02d}"))
    entries = []
    i = 0
    while i < len(tokens):
        if i + 1 < len(tokens):
            between = t[tokens[i][1]:tokens[i + 1][0]]
            if re.fullmatch(r'[-~一至–—]*', between):
                entries.append((tokens[i][2], tokens[i + 1][2]))
                i += 2
                continue
        entries.append((tokens[i][2], None))
        i += 1

    topic = t
    for m in re.finditer(r'(\d{1,2}):+(\d{2})', topic):
        topic = topic.replace(m.group(0), " ", 1)
    topic = re.sub(r'\b[AaPp][Mm]\b', " ", topic)
    topic = re.sub(r'[-~–—]', " ", topic)
    topic = re.sub(r'(?<![0-9A-Za-z\u4e00-\u9fff])[一至](?![0-9A-Za-z\u4e00-\u9fff])', " ", topic)
    topic = re.sub(r'\s+', " ", topic).strip()
    topic = topic.strip("：:/-~ ")
    return entries, topic


def add_hours(t, hours=DEFAULT_DURATION):
    hh, mm = map(int, t.split(":"))
    total = (hh * 60 + mm + hours * 60) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


def build_entries(day_blocks):
    timed, pure = [], []
    for b in day_blocks:
        entries, topic = parse_content(b["text"])
        cy = (b["y0"] + b["y1"]) / 2
        if entries:
            for s, e in entries:
                timed.append({"start": s, "end": e if e else add_hours(s), "topic": topic, "y": cy})
        elif topic:
            pure.append({"topic": topic, "y": cy})
    for p in pure:
        if not timed:
            timed.append({"start": None, "end": None, "topic": p["topic"], "y": p["y"]})
            continue
        best = min(timed, key=lambda t: abs(t["y"] - p["y"]))
        if not best["topic"]:
            best["topic"] = p["topic"]
        else:
            timed.append({"start": None, "end": None, "topic": p["topic"], "y": p["y"]})
    out = [{"start": t["start"], "end": t["end"], "topic": t["topic"], "y": t["y"]} for t in timed]
    out.sort(key=lambda e: e["start"] if e["start"] else "99:99")
    return out


def fix_missing_week(sched):
    """补齐漏识别的星期：空 day 夹在两个非空 day 之间，且前一个 day 有两场时，挪 y 最靠下的一场过来"""
    for i, w in enumerate(WEEK_ORDER):
        if sched.get(w):
            continue
        prev = WEEK_ORDER[i - 1] if i > 0 else None
        nxt = WEEK_ORDER[i + 1] if i < 6 else None
        if not (prev and nxt and sched.get(prev) and sched.get(nxt)):
            continue
        if len(sched[prev]) >= 2:
            sched[prev].sort(key=lambda e: e.get("y", 0))
            moved = sched[prev].pop()
            sched[w] = [moved]
    return sched


def parse_row_aligned(blocks, max_x=None):
    """星期块为锚点，内容块按 y 中心最近邻分配；max_x 用于过滤右侧装饰区（如留言板）"""
    weeks, contents = [], []
    for b in blocks:
        week, rest = find_week(b["text"])
        if week:
            weeks.append((week, b, rest))
        elif not is_decor(b["text"]):
            if max_x and b["x0"] > max_x:
                continue
            contents.append(b)
    weeks_sorted = sorted(weeks, key=lambda w: w[1]["y0"])
    day_map, order = {}, []
    for w, b, rest in weeks_sorted:
        if w not in day_map:
            day_map[w] = []
            order.append(w)
        if rest and not is_decor(rest):
            day_map[w].append({"text": rest, "x0": b["x0"], "x1": b["x1"], "y0": b["y0"], "y1": b["y1"]})
    for c in contents:
        cy = (c["y0"] + c["y1"]) / 2
        candidates = [w for w in weeks_sorted if w[1]["y0"] <= cy]
        if candidates:
            best = max(candidates, key=lambda w: w[1]["y0"])
        else:
            best = min(weeks_sorted, key=lambda w: w[1]["y0"])
        day_map[best[0]].append(c)
    result = {}
    for w in order:
        result[w] = build_entries(day_map[w])
    return result


def parse_grid_two_rows(blocks, split_y):
    """横版表格：上排/下排各若干列，列头是星期，内容按 y 分排 + x 中点分列归属"""
    weeks, contents = [], []
    for b in blocks:
        week, rest = find_week(b["text"])
        if week:
            weeks.append((week, b))
        elif not is_decor(b["text"]):
            contents.append(b)
    result = {}
    for row_weeks in [[w for w in weeks if w[1]["y0"] < split_y],
                      [w for w in weeks if w[1]["y0"] >= split_y]]:
        if not row_weeks:
            continue
        is_first = row_weeks[0][1]["y0"] < split_y
        row_contents = [c for c in contents if (c["y0"] < split_y) == is_first]
        row_sorted = sorted(row_weeks, key=lambda w: w[1]["x0"])
        xs = [w[1]["x0"] for w in row_sorted]
        for i, (w, wb) in enumerate(row_sorted):
            x_lo = (xs[i - 1] + xs[i]) / 2 if i > 0 else -10 ** 9
            x_hi = (xs[i] + xs[i + 1]) / 2 if i + 1 < len(xs) else 10 ** 9
            col = [c for c in row_contents if x_lo <= c["x0"] < x_hi]
            result[w] = build_entries(col)
    return result


def parse_two_column(blocks, split_x):
    left = [b for b in blocks if (b["x0"] + b["x1"]) / 2 < split_x]
    right = [b for b in blocks if (b["x0"] + b["x1"]) / 2 >= split_x]
    result = parse_row_aligned(left)
    result.update(parse_row_aligned(right))
    return result


PARSERS = {
    "灰泽满Hazel": lambda b: parse_row_aligned(b),
    "四时小路Komichi": lambda b: parse_row_aligned(b),
    "小松绿Viridis": lambda b: parse_row_aligned(b),
    "枝堇Sumire": lambda b: parse_row_aligned(b),
    "羽啾chu2u": lambda b: parse_two_column(b, 900),
}

COLORS = {
    "灰泽满Hazel": "D3D3D3", "四时小路Komichi": "FF2231", "小松绿Viridis": "8EB056",
    "枝堇Sumire": "B4A6BF", "羽啾chu2u": "D4DA7B",
}


def main():
    with open(RAW, encoding="utf-8") as f:
        raw = json.load(f)
    streamers = []
    for name, color in COLORS.items():
        blocks = raw[name]["blocks"]
        sched = PARSERS[name](blocks)
        sched = fix_missing_week(sched)
        full = {}
        for w in WEEK_ORDER:
            full[w] = [{k: v for k, v in e.items() if k != "y"} for e in sched.get(w, [])]
        streamers.append({"name": name, "color": "#" + color, "schedule": full})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"site_name": "灰泽满＆287共享周表", "default_duration_hours": DEFAULT_DURATION,
                   "streamers": streamers}, f, ensure_ascii=False, indent=2)

    print("=" * 70)
    print("网站名：灰泽满＆287共享周表")
    for s in streamers:
        print(f"\n【{s['name']}】 {s['color']}")
        for w in WEEK_ORDER:
            for it in s["schedule"][w]:
                tm = f"{it['start']}~{it['end']}" if it["start"] else "待定/无时间"
                tp = it["topic"] if it["topic"] else "—"
                print(f"  {w}: {tm}  {tp}")
    print(f"\n已输出 {OUT}")


if __name__ == "__main__":
    main()
