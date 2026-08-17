import sys, os, json, glob
sys.stdout.reconfigure(encoding="utf-8")
from rapidocr_onnxruntime import RapidOCR

IMG_DIR = r"C:\Users\IT008\WorkBuddy\2026-08-13-task-21\weeksheet_images"
OUT = r"C:\Users\IT008\WorkBuddy\2026-08-13-task-21\data\raw_ocr.json"

STREAMERS = {
    "灰泽满Hazel": "D3D3D3",
    "克罗雅Kloa": "D3D3D3",
    "莉蔻Liko": "DF7623",
    "十六萤Izayoi": "C7E6D1",
    "四时小路Komichi": "FF2231",
    "小松绿Viridis": "8EB056",
    "枝堇Sumire": "B4A6BF",
    "羽啾chu2u": "D4DA7B",
}

engine = RapidOCR()
results = {}

for name, color in STREAMERS.items():
    matches = glob.glob(os.path.join(IMG_DIR, name + ".*"))
    if not matches:
        print(f"[MISS] {name}")
        continue
    img = matches[0]
    result, _ = engine(img)
    blocks = []
    print(f"\n===== {name} ({color}) 共 {len(result or [])} 块 =====")
    for box, text, score in (result or []):
        xs = [float(p[0]) for p in box]
        ys = [float(p[1]) for p in box]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        blocks.append({"text": str(text), "x0": x0, "y0": y0, "x1": x1, "y1": y1, "score": score})
        print(f"  [{score}] ({x0:.0f},{y0:.0f})~({x1:.0f},{y1:.0f})  {text}")
    results[name] = {"color": color, "blocks": blocks}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n原始结果已保存到 {OUT}")
