import sys, os
sys.stdout.reconfigure(encoding="utf-8")
from rapidocr_onnxruntime import RapidOCR

IMG = r"C:\Users\IT008\WorkBuddy\2026-08-13-task-21\weeksheet_images\灰泽满Hazel.png"

print("初始化 OCR 引擎（首次加载模型，约 5-20 秒）...")
engine = RapidOCR()
print("开始识别...\n")

result, elapse = engine(IMG)

if not result:
    print("!! 未识别到任何文字")
else:
    print(f"共识别到 {len(result)} 个文本块：\n")
    for box, text, score in result:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        print(f"[{score}] ({x0},{y0})~({x1},{y1})  {text}")

print(f"\n耗时: {elapse}")
