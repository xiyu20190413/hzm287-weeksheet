import urllib.request, json, os

STREAMERS = [
    ("灰泽满Hazel",  "1158783344706584596", 4, "D3D3D3"),
    ("克罗雅Kloa",   "1234796895672467464", 2, "D3D3D3"),
    ("莉蔻Liko",     "1224599578206011408", 4, "DF7623"),
    ("十六萤Izayoi",  "1159457766274760752", 1, "C7E6D1"),
    ("四时小路Komichi","1234580674174779395", 3, "FF2231"),
    ("小松绿Viridis", "1234144339813203972", 1, "8EB056"),
    ("枝堇Sumire",   "1234946274659139593", 4, "B4A6BF"),
    ("羽啾chu2u",    "1234802363167932438", 1, "D4DA7B"),
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def fetch_detail(opus_id):
    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?id={opus_id}"
    return json.loads(get(url).decode("utf-8"))

def download(url, path):
    data = get(url)
    with open(path, "wb") as f:
        f.write(data)

outdir = os.path.join(os.path.dirname(__file__), "..", "weeksheet_images")
outdir = os.path.abspath(outdir)
os.makedirs(outdir, exist_ok=True)

for name, oid, pos, color in STREAMERS:
    try:
        d = fetch_detail(oid)
        items = d["data"]["item"]["modules"]["module_dynamic"]["major"]["draw"]["items"]
        idx = pos - 1
        it = items[idx]
        src = it["src"]
        if src.startswith("http://"):
            src = "https://" + src[len("http://"):]
        ext = os.path.splitext(src.split("?")[0])[1] or ".png"
        fname = f"{name}{ext}"
        download(src, os.path.join(outdir, fname))
        print(f"[OK] {name}: 图{pos}=items[{idx}] {it['width']}x{it['height']} -> {fname}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")

print(f"\n保存目录: {outdir}")
