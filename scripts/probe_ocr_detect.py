import json, urllib.request, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

sd = open(os.path.join(ROOT, "data", ".sessdata"), encoding="utf-8").read().strip()

KW = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN",
      "周一", "周二", "周三", "周四", "周五", "周六", "周日",
      "星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日",
      "周表", "排班", "SCHEDULE", "直播表", "本周"]


def get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def get_json(url, headers):
    return json.loads(get(url, headers).decode("utf-8"))


def buvid3():
    d = get_json("https://api.bilibili.com/x/frontend/finger/spi",
                 {"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
    return d["data"]["b_3"] + "infoc"


def pinned_draw(mid):
    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={mid}&timezone_offset=-480"
    d = get_json(url, {"User-Agent": UA, "Referer": f"https://space.bilibili.com/{mid}",
                       "Cookie": f"SESSDATA={sd}; buvid3={buvid3()}"})
    for it in d.get("data", {}).get("items", []):
        mods = it.get("modules", {}) or {}
        tag = (mods.get("module_tag") or {}).get("text", "")
        major = mods.get("module_dynamic", {}).get("major", {}) or {}
        if major.get("type") == "MAJOR_TYPE_DRAW" and tag == "置顶":
            return major.get("draw", {}).get("items", [])
    return []


def download(src, path):
    if src.startswith("http://"):
        src = "https://" + src[7:]
    with open(path, "wb") as f:
        f.write(get(src, {"User-Agent": UA, "Referer": "https://www.bilibili.com/"}))


from rapidocr_onnxruntime import RapidOCR

engine = RapidOCR()
mids = {"灰泽满Hazel": 1298779265, "四时小路Komichi": 1512246445, "小松绿Viridis": 1891335475,
        "枝堇Sumire": 1150976664, "羽啾chu2u": 2138961136}

for name, mid in mids.items():
    items = pinned_draw(mid)
    print(f"\n=== {name} (置顶) 共{len(items)}图 ===")
    for i, di in enumerate(items):
        w, h = int(di["width"]), int(di["height"])
        src = di["src"]
        tmp = os.path.join(ROOT, "data", f"_probe_{i}.png")
        try:
            download(src, tmp)
            result, _ = engine(tmp)
            texts = [str(t) for _, t, _ in (result or [])]
            joined = " ".join(texts)
            hits = [k for k in KW if k.upper() in joined.upper()]
            print(f"  [{i}] {w}x{h} 关键词命中{hits} 文本片段: {joined[:80]!r}")
            os.remove(tmp)
        except Exception as e:
            print(f"  [{i}] {w}x{h} 下载/OCR失败: {e}")
