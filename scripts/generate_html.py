import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "streamers.json")
HTML = os.path.join(ROOT, "website", "index.html")


def generate():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    # 生成 STREAMERS 的 JS 数据（去掉 opus_id/img_pos 等维护字段）
    frontend = []
    for s in data["streamers"]:
        frontend.append({
            "name": s["name"], "color": s["color"], "avatar": s["avatar"],
            "live": s["live"], "space": s["space"], "schedule": s["schedule"],
        })
    js = "const STREAMERS = " + json.dumps(frontend, ensure_ascii=False) + ";"

    with open(HTML, encoding="utf-8") as f:
        html = f.read()

    html, n = re.subn(r'const STREAMERS = \[.*?\];', js, html, flags=re.S)
    if n != 1:
        raise SystemExit(f"generate_html: 未找到 STREAMERS 数据块（替换 {n} 处）")

    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {HTML}")


if __name__ == "__main__":
    generate()
