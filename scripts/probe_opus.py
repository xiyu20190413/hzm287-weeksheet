import urllib.request, json

OPUS = "1158783344706584596"

def fetch(opus_id):
    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?id={opus_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://t.bilibili.com/",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

d = fetch(OPUS)
item = d["data"]["item"]
mods = item["modules"]

print("=== modules keys ===")
print(list(mods.keys()))

md = mods.get("module_dynamic", {})
print("\n=== module_dynamic keys ===")
print(list(md.keys()))

major = md.get("major", {})
print("\n=== major keys ===")
print(list(major.keys()))

print("\n=== major.type ===")
print(major.get("type"))

if "draw" in major:
    draw = major["draw"]
    print("\n=== draw keys ===")
    print(list(draw.keys()))
    items = draw.get("items", [])
    print(f"\n=== draw.items count: {len(items)} ===")
    for i, it in enumerate(items):
        print(f"\n--- item[{i}] keys: {list(it.keys())} ---")
        print(json.dumps(it, ensure_ascii=False)[:600])

desc = md.get("desc")
print("\n=== desc text ===")
print((desc.get("text", "") if desc else "")[:200])
