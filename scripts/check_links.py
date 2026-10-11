# -*- coding: utf-8 -*-
"""
站点自检：检查所有页面的本地链接、资源引用与页内锚点是否存在，
并做一遍基础的 HTML 结构检查。内容维护后建议运行一次。

用法:
    python scripts/check_links.py
"""
import os
import re
import sys
from html.parser import HTMLParser

# Windows 控制台默认可能是 GBK，强制用 UTF-8 输出，避免中文与符号报错
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
# 这些标签允许省略闭合标签
OPTIONAL_END = {"li", "p", "td", "th", "tr", "option", "thead", "tbody", "tfoot", "dt", "dd"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = set()
        self.refs = []          # (标签, 属性, 值, 行号)
        self.title = None
        self._in_title = False
        self.has_lang = False
        self.has_viewport = False
        self.images_without_alt = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.has_lang = True
        if tag == "meta" and a.get("name") == "viewport":
            self.has_viewport = True
        if a.get("id"):
            self.ids.add(a["id"])
        for name in ("href", "src"):
            if a.get(name):
                self.refs.append((tag, name, a[name], self.getpos()[0]))
        if tag == "img" and "alt" not in a:
            self.images_without_alt.append(self.getpos()[0])
        if tag == "title":
            self._in_title = True
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append("第 %d 行：多余的 </%s>" % (self.getpos()[0], tag))
            return
        # 容忍可省略结束标签的情况
        while self.stack and self.stack[-1][0] != tag:
            open_tag, line = self.stack[-1]
            if open_tag in OPTIONAL_END:
                self.stack.pop()
                continue
            self.errors.append(
                "第 %d 行：</%s> 与第 %d 行的 <%s> 不匹配" % (self.getpos()[0], tag, line, open_tag)
            )
            self.stack.pop()
            return
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self._in_title and self.title is None:
            self.title = data.strip()


def strip_query(value):
    return value.split("#", 1)[0].split("?", 1)[0]


def main():
    html_files = sorted(
        os.path.join(dp, f)
        for dp, dn, fn in os.walk(ROOT)
        for f in fn
        if f.endswith(".html") and ".git" not in dp
    )

    problems = []
    warnings = []
    anchors = {}

    # 第一遍：收集每个页面的 id
    for path in html_files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        anchors[rel] = set(re.findall(r'\bid="([^"]+)"', text))

    print("检查 %d 个 HTML 页面 ...\n" % len(html_files))

    for path in html_files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()

        parser = Checker()
        parser.feed(text)

        if not parser.has_lang:
            warnings.append("%s：<html> 缺少 lang 属性" % rel)
        if not parser.has_viewport:
            problems.append("%s：缺少 viewport meta，移动端会缩放异常" % rel)
        if not parser.title:
            warnings.append("%s：缺少 <title>" % rel)
        for line in parser.images_without_alt:
            warnings.append("%s 第 %d 行：<img> 缺少 alt 属性" % (rel, line))
        for err in parser.errors:
            problems.append("%s %s" % (rel, err))
        for tag, line in parser.stack:
            if tag not in OPTIONAL_END:
                problems.append("%s 第 %d 行：<%s> 未闭合" % (rel, line, tag))

        for tag, attr, value, line in parser.refs:
            if value.startswith(("http://", "https://", "mailto:", "tel:", "data:", "javascript:")):
                continue

            if value.startswith("#"):
                target = value[1:]
                if target and target not in anchors.get(rel, set()):
                    problems.append("%s 第 %d 行：页内锚点 #%s 不存在" % (rel, line, target))
                continue

            page_part, _, frag = value.partition("#")
            clean = strip_query(page_part)
            if not clean:
                continue

            target_path = os.path.normpath(os.path.join(os.path.dirname(path), clean))
            if not os.path.exists(target_path):
                problems.append("%s 第 %d 行：<%s %s=\"%s\"> 指向的文件不存在" % (rel, line, tag, attr, value))
                continue

            if frag and clean.endswith(".html"):
                target_rel = os.path.relpath(target_path, ROOT).replace("\\", "/")
                if frag not in anchors.get(target_rel, set()):
                    problems.append(
                        "%s 第 %d 行：链接 %s 的锚点 #%s 在目标页面中不存在" % (rel, line, value, frag)
                    )

    # 反向检查：图片目录里有没有没被引用的文件
    used = set()
    for path in html_files:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        used.update(re.findall(r'(?:src|href)="(assets/[^"#?]+)"', text))
        # meta content 里也可能引用资源（如 og:image）
        used.update(re.findall(r'content="(assets/[^"#?]+)"', text))
    img_dir = os.path.join(ROOT, "assets", "img")
    if os.path.isdir(img_dir):
        for name in sorted(os.listdir(img_dir)):
            rel_asset = "assets/img/" + name
            if rel_asset not in used:
                warnings.append("未被任何页面引用：%s" % rel_asset)

    print("=" * 68)
    if problems:
        print("发现 %d 个问题：" % len(problems))
        for item in problems:
            print("  ✗ " + item)
    else:
        print("✓ 未发现断链、锚点缺失或 HTML 结构问题")

    if warnings:
        print()
        print("提示 %d 条（不影响功能）：" % len(warnings))
        for item in warnings:
            print("  · " + item)
    print("=" * 68)

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
