# 灰泽满＆287 共享周表

以「课表式」展示 VirtuaReal 五位主播本周直播安排的共享网站。横轴为各主播（代表色 + 头像），纵轴为连续时间轴，色块显示直播主题。

**在线访问**：https://xiyu20190413.github.io/hzm287/

## 主播清单

| 主播 | mid | 应援色 |
|------|-----|--------|
| 灰泽满 Hazel | 1298779265 | `#D3D3D3` |
| 四时小路 Komichi | 1512246445 | `#FF2231` |
| 小松绿 Viridis | 1891335475 | `#8EB056` |
| 枝堇 Sumire | 1150976664 | `#B4A6BF` |
| 羽啾 chu2u | 2138961136 | `#D4DA7B` |

## 目录结构

```
├── scripts/            # 抓取、OCR、解析、生成、维护脚本
│   ├── maintain_weekly.py   # 每日维护主逻辑（置顶动态抓取 + 智能识别周表图）
│   ├── parse_schedule.py    # OCR 结果结构化解析
│   ├── generate_html.py     # streamers.json → index.html
│   └── fetch_weeksheet.py   # 初始批量抓取周表图
├── data/               # 数据（唯一数据源 + 维护状态）
│   ├── streamers.json       # 唯一数据源（主播信息 + 周表 schedule）
│   └── maintain_state.json  # 维护对比基准（上次周表图 src）
├── website/            # 前端（生成后的 index.html + 头像）
├── weeksheet_images/   # 抓取到的原始周表图
└── photo/              # 主播头像
```

## 工作原理

1. **抓取**：通过 B站 `feed/space` API 抓取主播**置顶动态**中的所有图片（需 SESSDATA Cookie）。
2. **智能识别周表图**：对每张候选图 OCR，按「星期关键词 + SCHEDULE」命中数打分，最高分者为周表图（**不能用高宽比判断**，横图/竖图都可能是周表或周边）。
3. **OCR 解析**：RapidOCR 识别文字 → `parse_schedule.py` 结构化（星期块锚点 + y 最近邻分配）。
4. **生成页面**：`generate_html.py` 读 `streamers.json` 生成 `website/index.html`。
5. **部署**：推送 `website/` 至 GitHub Pages（仓库 `xiyu20190413/hzm287`）。

## 每日自动维护

`maintain_weekly.py`（由自动化任务每天 8 点运行）：

- 周表图无变化 → 清空该主播 schedule（等待新周表）
- 周表图变化 → 重新 OCR 解析更新
- 本周已更新 → 跳过

## 运行要求

```bash
# Python 3.13 + 依赖
pip install rapidocr_onnxruntime pyyaml

# 需在 data/ 下放置凭证（不入库）：
#   data/.sessdata      B站登录态（SESSDATA）
#   data/.github_token  GitHub 个人访问令牌（repo 权限）
```

> 公司/受限网络下 git push 需强制 HTTP/1.1：`git -c http.version=HTTP/1.1 push`

## 注意

- B站 SESSDATA 通常几个月过期，届时需重新提供。
- `weeksheet_images/` 保留早期 8 位主播的抓取历史，当前仅维护上述 5 位。
