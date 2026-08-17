import json, urllib.request, urllib.parse, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESS_FILE = os.path.join(ROOT, "data", ".sessdata")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def sessdata():
    with open(SESS_FILE, encoding="utf-8") as f:
        return f.read().strip()


def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read(), dict(r.headers)


def get_buvid3():
    # 通过 finger/spi 获取 b_3/b_4，拼出 buvid3
    try:
        body, hdrs = http_get("https://api.bilibili.com/x/frontend/finger/spi",
                              {"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
        d = json.loads(body.decode("utf-8"))
        b3 = d.get("data", {}).get("b_3", "")
        b4 = d.get("data", {}).get("b_4", "")
        print("[spi] b_3=", b3, "b_4=", b4)
        # buvid3 常见拼法: b_3 + 'infoc'
        return b3 + "infoc", b3, b4
    except Exception as e:
        print("[spi] 获取失败", e)
        return "", "", ""


def get_mid(opus_id):
    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?id={opus_id}"
    body, _ = http_get(url, {"User-Agent": UA, "Referer": "https://t.bilibili.com/"})
    d = json.loads(body.decode("utf-8"))
    author = d["data"]["item"]["modules"]["module_author"]
    return author["mid"], author.get("name")


def feed_space(mid, cookie):
    url = ("https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"
           f"?host_mid={mid}&timezone_offset=-480")
    body, _ = http_get(url, {"User-Agent": UA, "Referer": f"https://space.bilibili.com/{mid}",
                             "Cookie": cookie})
    return json.loads(body.decode("utf-8"))


def main():
    sd = sessdata()
    buvid3, b3, b4 = get_buvid3()

    streamers = [
        ("灰泽满Hazel", "1158783344706584596"),
        ("四时小路Komichi", "1234580674174779395"),
        ("小松绿Viridis", "1234144339813203972"),
        ("枝堇Sumire", "1234946274659139593"),
        ("羽啾chu2u", "1237388530530910244"),
    ]

    mids = {}
    for name, oid in streamers:
        try:
            mid, aname = get_mid(oid)
            mids[name] = mid
            print(f"[mid] {name} -> mid={mid} (author={aname})")
        except Exception as e:
            print(f"[mid] {name} 失败: {e}")

    print("\n--- 测试 feed/space（SESSDATA + buvid3）---")
    for name, oid in streamers:
        mid = mids.get(name)
        if not mid:
            continue
        cookie = f"SESSDATA={sd}; buvid3={buvid3}"
        try:
            d = feed_space(mid, cookie)
            code = d.get("code")
            items = d.get("data", {}).get("items", [])
            print(f"[feed] {name} mid={mid} code={code} items={len(items)}")
            if code == 0:
                for it in items:
                    mods = it.get("modules", {})
                    tag = mods.get("module_tag", {}).get("text", "")
                    major = mods.get("module_dynamic", {}).get("major", {})
                    mtype = major.get("type", "")
                    draw_items = major.get("draw", {}).get("items", []) if mtype == "MAJOR_TYPE_DRAW" else []
                    desc = ""
                    for di in draw_items:
                        desc += f"[{di.get('width')}x{di.get('height')}]"
                    print(f"    - type={mtype} tag={tag!r} imgs={desc}")
            elif code == -352:
                print("    -> 风控 -352，Cookie 可能不完整")
        except Exception as e:
            print(f"[feed] {name} 异常: {e}")


if __name__ == "__main__":
    main()
