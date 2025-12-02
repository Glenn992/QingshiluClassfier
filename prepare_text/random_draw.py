#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
random_draw.py
--------------------------------------------------------
随机抽取历史条文工具
1. 文件选择框读入 txt
2. 输入抽取数量（默认 100）
3. 随机抽取 → 桌面 {原文件名}_random<N>.txt
4. 打印实际抽取数量
--------------------------------------------------------
PyCharm 直接点绿色三角即可运行
"""

import tkinter as tk
from tkinter import filedialog, simpledialog
from pathlib import Path
import random
import sys

DESKTOP = Path.home() / "Desktop"

def main():
    # 隐藏主窗口
    root = tk.Tk()
    root.withdraw()

    # 选文件
    path = Path(
        filedialog.askopenfilename(
            title="请选择历史条文文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
    )
    if not path.name:
        print("用户取消选择")
        sys.exit(0)

    # 读入所有非空行
    with path.open(encoding="utf-8") as f:
        lines = [l.rstrip() for l in f if l.strip()]
    total = len(lines)
    if total == 0:
        print("文件无有效内容")
        sys.exit(0)

    # 输入抽取数量
    num = simpledialog.askinteger(
        "抽取数量",
        f"文件共有 {total} 条，请输入要随机抽取的数量：",
        initialvalue=min(100, total),
        minvalue=1,
        maxvalue=total
    )
    if num is None:  # 用户取消
        sys.exit(0)

    # 随机抽 + 去重
    picked = random.sample(lines, num)  # 不重复抽样
    out_file = DESKTOP / f"{path.stem}_random{num}.txt"
    with out_file.open("w", encoding="utf-8") as f:
        f.writelines(f"{l}\n" for l in picked)

    print(f"✅ 已完成：随机抽取 {num} 条 → {out_file.name}")
    print(f"实际抽取数量：{num}")

if __name__ == "__main__":
    main()