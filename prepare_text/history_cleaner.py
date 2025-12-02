#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
history_cleaner.py
--------------------------------------------------------
清洗历史条文工具（Python 3.12+）
1. 去除条文前缀符号后的序号，保留唯一○
   例：○1○123  文本 → ○文本
2. 全局去重，仅保留首次出现
3. 输出最终条文数
4. 跳过隐藏/临时文件
5. 结果保存到 ~/Desktop/{原文件名}_cleaned.txt
--------------------------------------------------------
Usage:
    python3 history_cleaner.py  <文件或文件夹路径>
"""

import re
import sys
import logging
from pathlib import Path

# ---------- 日志配置 ----------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)
log = logging.getLogger("HistoryCleaner")

# ---------- 常量 ----------
DESKTOP = Path.home() / "Desktop"
SKIP_PREFIXES = (".", "~")      # 跳过隐藏/临时文件
MIN_SIZE = 30                   # 小于 30 Byte 的文件直接忽略

# ---------- 功能函数 ----------
def clean_line(line: str) -> str:
    """
    1. 把连续的 ○数字 全部删掉，只保留一个 ○
    2. 如果结果开头没有 ○，再补一个
    例：
        ○1○123 文本  -> ○文本
        123 文本      -> ○123 文本
    """
    # 第一步：把所有 ○数字 片段一次性干掉
    line = re.sub(r'○\d+', '', line.lstrip())
    # 第二步：把可能出现的连续多个 ○ 压成一个
    line = re.sub(r'○+', '○', line)
    line = line.strip()
    # 兜底：开头无 ○ 就补一个
    if not line.startswith('○'):
        line = '○' + line
    return line
def read_and_clean(file_path: Path) -> list[str]:
    """
    读取文件，逐行清洗，返回清洗后的条文列表
    空行自动跳过
    """
    try:
        with file_path.open(encoding="utf-8") as f:
            lines = [clean_line(l) for l in f if l.strip()]
        log.info("已读取 %s，原始行数 %d", file_path.name, len(lines))
        return lines
    except Exception as e:
        log.error("读取文件失败 %s: %s", file_path, e)
        return []

import unicodedata

# ---------- 归一化 ----------
def normalize(line: str) -> str:
    line = line.strip()
    line = "".join(c for c in line if not unicodedata.category(c).startswith("C"))

    def f(c):
        code = ord(c)
        # 全角 ASCII 区 -> 半角
        if 0xFF01 <= code <= 0xFF5E:
            half = code - 0xFEE0          # 正确偏移
            return chr(half)
        if code == 0x3000:                # 全角空格
            return " "
        return c

    line = "".join(f(c) for c in line)
    return unicodedata.normalize("NFKC", line)

# ---------- 去重（归一化键版） ----------
def dedup(lines: list[str]) -> tuple[list[str], int]:
    """
    按归一化后的 key 去重，顺序不变；
    返回 (去重后原始行列表, 被剔除的重复条数)
    """
    seen = set()
    deduped = []
    dup_count = 0
    for raw in lines:
        key = normalize(raw)
        if key not in seen:
            seen.add(key)
            deduped.append(raw)
        else:
            dup_count += 1
    return deduped, dup_count

def should_skip(path: Path) -> bool:
    """
    判断是否需要跳过该文件
    """
    if path.is_dir():
        return True
    if path.name.startswith(SKIP_PREFIXES):
        log.info("跳过隐藏/临时文件: %s", path.name)
        return True
    if path.stat().st_size < MIN_SIZE:
        log.info("跳过过小文件: %s (%d Byte)", path.name, path.stat().st_size)
        return True
    return False

def process_single_file(file_path: Path) -> None:
    """
    处理单个文件：清洗 -> 去重 -> 写结果到桌面
    """
    if should_skip(file_path):
        return

    lines = read_and_clean(file_path)
    if not lines:
        log.warning("文件 %s 无有效内容，已跳过", file_path.name)
        return

    deduped, dup_count = dedup(lines)
    out_file = DESKTOP / f"{file_path.stem}_cleaned.txt"

    try:
        with out_file.open("w", encoding="utf-8") as f:
            for line in deduped:
                f.write(line + "\n")
        log.info(
            "✅ 完成：%s -> %s，原始 %d 条，去重 %d 条，最终 %d 条",
            file_path.name,
            out_file.name,
            len(lines),
            dup_count,
            len(deduped),
        )
    except Exception as e:
        log.error("写入结果失败 %s: %s", out_file, e)

def main(root_path: Path) -> None:
    """
    批量处理目录下所有文本文件，或直接处理单个文件
    """
    if not root_path.exists():
        log.error("路径不存在: %s", root_path)
        sys.exit(1)

    if root_path.is_file():
        files = [root_path]
    else:
        files = [p for p in root_path.iterdir() if p.is_file()]

    if not files:
        log.warning("未找到任何文件: %s", root_path)
        sys.exit(0)

    log.info("共发现 %d 个文件，开始处理…", len(files))
    for file_path in files:
        process_single_file(file_path)
    log.info("全部处理完成，结果已保存到桌面！")

# ---------- 入口 ----------
if __name__ == "__main__":
    # 无参数时弹出文件选择框
    if len(sys.argv) == 1:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                title="请选择要清洗的条文文件",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if not path:
                sys.exit(0)
            main(Path(path))
        except ImportError:
            print("用法: python3 history_cleaner.py  <文件或文件夹路径>")
            sys.exit(1)
    else:
        main(Path(sys.argv[1]))