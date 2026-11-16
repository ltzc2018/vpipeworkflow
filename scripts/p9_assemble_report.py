#!/usr/bin/env python3
"""把第 9 轮的量化表格与 LFM3-VL 复核结果装配进报告第 17 节

流程：
  report/section17.md（含 {{TABLES}} / {{VQA}} 占位）
  + logs/p9-tables.md（p9_report_tables.py 产物）
  + out/vqa-p9-*.txt（LFM3-VL-2B 原始回答）
  → report/vpipe-H3-部署与测试报告.md 末尾追加第 17 节

用法: p9_assemble_report.py [--section report/section17.md] [--report ...]
"""
import os
import re
import sys

WS = "/Users/minichen/AI-Models/vpipe-workspace"
LAB = "/Users/minichen/WorkBuddy/2026-11-12-21-10-11/vpipe-lab"

GROUPS = [
    ("a", "A 组 · Ref2VA 768p · 1 图参考 · shift 6.0"),
    ("d", "D 组 · Ref2VA 768p · 1 图参考 · shift 8.0"),
    ("b", "B 组 · Ref2VA 768p · 1 图参考 · shift 12.0"),
    ("c", "C 组 · Ref2VA 768p · 1 图 + 动作视频 + 音轨 · shift 6.0"),
]

QUESTIONS = [
    ("idsharp", "身份 + 画质", "主体是谁？画面清晰还是发糊？"),
    ("scene", "串味", "画面里有没有海边/沙滩/奔跑的人/女性/竹子/熊猫？"),
    ("cam", "运镜", "镜头怎么动？整体往左还是往右？"),
]


def read(path):
    if not os.path.exists(path):
        return ""
    return open(path, errors="ignore").read().strip()


def build_vqa():
    L = ["| 组 | 问题 | LFM3-VL-2B 的回答 |", "|---|---|---|"]
    for g, label in GROUPS:
        for key, qname, qdesc in QUESTIONS:
            t = read(f"{WS}/out/vqa-p9-{g}-{key}.txt")
            t = re.sub(r"\s+", " ", t).strip()
            if not t:
                t = "（无输出）"
            if len(t) > 420:
                t = t[:420] + " …"
            L.append(f"| {label} | {qname}（{qdesc}）| {t} |")
    L.append("")
    L.append("参考动作视频自身的运镜基准（LFM3-VL 的回答）：")
    L.append("")
    t = re.sub(r"\s+", " ", read(f"{WS}/out/vqa-p9-ref-motion.txt")).strip()
    L.append(f"> {t}")
    L.append("")
    L.append("**人工逐帧目检补正**：A 组的「串味」问题，2B 模型两次都输出了无意义的"
             "「1. 有 2. 没有 …」序列，**没有指名道姓**，因此这一条由人工看第 0/40/80/末帧判定："
             "画面只有木质窗台、橘猫、窗外的树林与草地，**没有海边、沙滩、奔跑的人、女性、竹子、熊猫** → **无串味 ✅**。")
    return "\n".join(L)


def main():
    argv = sys.argv[1:]
    section = f"{LAB}/report/section17.md"
    report = f"{LAB}/report/vpipe-H3-部署与测试报告.md"
    if "--section" in argv:
        section = argv[argv.index("--section") + 1]
    if "--report" in argv:
        report = argv[argv.index("--report") + 1]

    txt = read(section)
    tables = read(f"{LAB}/logs/p9-tables.md")
    txt = txt.replace("{{TABLES}}", tables)
    txt = txt.replace("{{VQA}}", build_vqa())

    body = open(report, encoding="utf-8").read()
    if "## 17. 第九轮" in body:
        body = body.split("## 17. 第九轮")[0].rstrip() + "\n"
    if not body.endswith("\n"):
        body += "\n"
    body += "\n---\n\n" + txt.strip() + "\n"
    with open(report, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"第 17 节已装配进 {report}（{len(body.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
