import json, urllib.request, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

sd = open(os.path.join(ROOT, "data", ".sessdata"), encoding="utf-8").read().strip()


def get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def buvid3():
    d = get("https://api.bilibili.com/x/frontend/finger/spi",
            {"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
    return d["data"]["b_3"] + "infoc"


def pinned_draw(mid):
    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={mid}&timezone_offset=-480"
    d = get(url, {"User-Agent": UA, "Referer": f"https://space.bilibili.com/{mid}",
                  "Cookie": f"SESSDATA={sd}; buvid3={buvid3()}"})
    for it in d.get("data", {}).get("items", []):
        mods = it.get("modules", {}) or {}
        tag = (mods.get("module_tag") or {}).get("text", "")
        major = mods.get("module_dynamic", {}).get("major", {}) or {}
        if major.get("type") == "MAJOR_TYPE_DRAW" and tag == "置顶":
            return major.get("draw", {}).get("items", [])
    return []


mids = {"灰泽满Hazel": 1298779265, "四时小路Komichi": 1512246445, "小松绿Viridis": 1891335475,
        "枝堇Sumire": 1150976664, "羽啾chu2u": 2138961136}

for name, mid in mids.items():
    items = pinned_draw(mid)
    print(f"=== {name} (置顶) 共{len(items)}图 ===")
    for i, di in enumerate(items):
        w, h = int(di["width"]), int(di["height"])
        print(f"  [{i}] {w}x{h} 高宽比={h/max(w,1):.2f} {di['src']}")
