# -*- coding: utf-8 -*-
"""
生成站点所需的 SVG 素材（纯抽象几何图形，不含任何真实校徽/院徽/照片）。
用法: python scripts/gen_assets.py
"""
import os
import sys

# Windows 控制台默认可能是 GBK，强制用 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
os.makedirs(IMG, exist_ok=True)

# (深色, 亮色) 渐变对，全部落在站点品牌色域内
PALETTE = [
    ("#062a52", "#1462ad"),
    ("#0a3b6f", "#0f9b8e"),
    ("#062a52", "#c8102e"),
    ("#0f4c8a", "#1e7ad1"),
    ("#0b3b6f", "#c9a227"),
    ("#12294a", "#0f9b8e"),
    ("#0a3b6f", "#e01f3d"),
    ("#103a63", "#5b8def"),
    ("#062a52", "#1462ad"),
]


def write(name, content):
    path = os.path.join(IMG, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print("  +", os.path.relpath(path, ROOT))


def defs(c1, c2, uid):
    return f"""  <defs>
    <linearGradient id="g{uid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="r{uid}" cx="78%" cy="16%" r="72%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <pattern id="p{uid}" width="34" height="34" patternUnits="userSpaceOnUse">
      <path d="M34 0H0V34" fill="none" stroke="#ffffff" stroke-opacity="0.10" stroke-width="1"/>
    </pattern>
  </defs>"""


def cover(name, index, w, h):
    """生成一张抽象封面：渐变 + 网格 + 几何形状（无文字，避免字体依赖）。"""
    c1, c2 = PALETTE[index % len(PALETTE)]
    uid = f"{w}x{h}-{index}"
    s = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="示意图">\n'
    s += defs(c1, c2, uid) + "\n"
    s += f'  <rect width="{w}" height="{h}" fill="url(#g{uid})"/>\n'
    s += f'  <rect width="{w}" height="{h}" fill="url(#p{uid})"/>\n'
    s += f'  <rect width="{w}" height="{h}" fill="url(#r{uid})"/>\n'

    # 每张图用不同的几何构成，保证视觉上不重复
    kind = index % 6
    if kind == 0:
        s += f'  <circle cx="{w*0.74:.0f}" cy="{h*0.34:.0f}" r="{h*0.34:.0f}" fill="#ffffff" fill-opacity="0.13"/>\n'
        s += f'  <circle cx="{w*0.74:.0f}" cy="{h*0.34:.0f}" r="{h*0.21:.0f}" fill="#ffffff" fill-opacity="0.16"/>\n'
        s += f'  <path d="M0 {h*0.78:.0f} Q {w*0.34:.0f} {h*0.52:.0f} {w*0.66:.0f} {h*0.8:.0f} T {w} {h*0.66:.0f} V {h} H 0 Z" fill="#000000" fill-opacity="0.16"/>\n'
    elif kind == 1:
        s += f'  <path d="M{w*0.52:.0f} {h} L{w*0.82:.0f} 0 L{w} 0 L{w} {h} Z" fill="#ffffff" fill-opacity="0.10"/>\n'
        for i in range(4):
            x = w * 0.12 + i * w * 0.09
            s += f'  <rect x="{x:.0f}" y="{h*0.6 - i*14:.0f}" width="{w*0.045:.0f}" height="{h*0.4 + i*14:.0f}" rx="6" fill="#ffffff" fill-opacity="{0.10 + i*0.05:.2f}"/>\n'
        s += f'  <circle cx="{w*0.2:.0f}" cy="{h*0.26:.0f}" r="{h*0.09:.0f}" fill="#ffffff" fill-opacity="0.22"/>\n'
    elif kind == 2:
        s += f'  <path d="M0 0 L{w*0.46:.0f} 0 L0 {h*0.72:.0f} Z" fill="#ffffff" fill-opacity="0.12"/>\n'
        s += f'  <path d="M{w} {h} L{w*0.54:.0f} {h} L{w} {h*0.28:.0f} Z" fill="#000000" fill-opacity="0.18"/>\n'
        s += f'  <circle cx="{w*0.62:.0f}" cy="{h*0.44:.0f}" r="{h*0.16:.0f}" fill="none" stroke="#ffffff" stroke-opacity="0.34" stroke-width="3"/>\n'
        s += f'  <circle cx="{w*0.62:.0f}" cy="{h*0.44:.0f}" r="{h*0.07:.0f}" fill="#ffffff" fill-opacity="0.3"/>\n'
    elif kind == 3:
        for i in range(5):
            r = h * (0.12 + i * 0.11)
            s += f'  <circle cx="{w*0.30:.0f}" cy="{h*0.74:.0f}" r="{r:.0f}" fill="none" stroke="#ffffff" stroke-opacity="{0.26 - i*0.04:.2f}" stroke-width="2"/>\n'
        s += f'  <rect x="{w*0.62:.0f}" y="{h*0.18:.0f}" width="{w*0.24:.0f}" height="{h*0.24:.0f}" rx="14" fill="#ffffff" fill-opacity="0.16"/>\n'
        s += f'  <rect x="{w*0.70:.0f}" y="{h*0.30:.0f}" width="{w*0.24:.0f}" height="{h*0.24:.0f}" rx="14" fill="#ffffff" fill-opacity="0.24"/>\n'
    elif kind == 4:
        s += f'  <path d="M0 {h*0.54:.0f} L{w} {h*0.2:.0f} L{w} {h*0.42:.0f} L0 {h*0.76:.0f} Z" fill="#ffffff" fill-opacity="0.14"/>\n'
        s += f'  <path d="M0 {h*0.76:.0f} L{w} {h*0.42:.0f} L{w} {h*0.56:.0f} L0 {h*0.9:.0f} Z" fill="#000000" fill-opacity="0.14"/>\n'
        s += f'  <circle cx="{w*0.16:.0f}" cy="{h*0.24:.0f}" r="{h*0.11:.0f}" fill="#ffffff" fill-opacity="0.2"/>\n'
    else:
        for gx in range(6):
            for gy in range(4):
                cx = w * 0.1 + gx * w * 0.16
                cy = h * 0.16 + gy * h * 0.22
                op = 0.10 + ((gx + gy) % 4) * 0.055
                s += f'  <circle cx="{cx:.0f}" cy="{cy:.0f}" r="{h*0.035:.0f}" fill="#ffffff" fill-opacity="{op:.2f}"/>\n'
        s += f'  <path d="M{w*0.58:.0f} {h} L{w*0.86:.0f} 0 L{w} 0 L{w} {h} Z" fill="#000000" fill-opacity="0.15"/>\n'

    s += "</svg>\n"
    write(name, s)


def logo():
    """抽象标识（占位）：镜头 + 笔尖，非任何真实校徽。"""
    s = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="宣传报道部标识（占位图形）">
  <defs>
    <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f4c8a"/>
      <stop offset="55%" stop-color="#1462ad"/>
      <stop offset="100%" stop-color="#062a52"/>
    </linearGradient>
    <linearGradient id="la" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0%" stop-color="#c8102e"/>
      <stop offset="100%" stop-color="#e01f3d"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="62" height="62" rx="18" fill="url(#lg)"/>
  <circle cx="27" cy="27" r="13.5" fill="none" stroke="#ffffff" stroke-opacity="0.92" stroke-width="3.4"/>
  <circle cx="27" cy="27" r="5.6" fill="#ffffff" fill-opacity="0.95"/>
  <circle cx="27" cy="27" r="2.2" fill="#0a3b6f"/>
  <path d="M40 44 L53 24 L57.5 27 L44.5 47 Z" fill="url(#la)"/>
  <path d="M40.6 44.9 L44.4 46.9 L38.6 48.9 Z" fill="#ffffff" fill-opacity="0.9"/>
  <path d="M14 47.5 h17" stroke="#ffffff" stroke-opacity="0.5" stroke-width="3" stroke-linecap="round"/>
</svg>
"""
    write("logo.svg", s)


def favicon():
    s = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <linearGradient id="fg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f4c8a"/>
      <stop offset="100%" stop-color="#062a52"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="16" fill="url(#fg)"/>
  <circle cx="27" cy="27" r="13" fill="none" stroke="#ffffff" stroke-opacity="0.92" stroke-width="3.6"/>
  <circle cx="27" cy="27" r="5.4" fill="#e01f3d"/>
  <path d="M41 45 L54 25 L58 28 L45 48 Z" fill="#ffffff" fill-opacity="0.9"/>
</svg>
"""
    write("favicon.svg", s)


def og_image():
    """社交分享大图（1200x630 PNG）。有中文字体则绘制文字，否则退化为纯图形。"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  ! 未安装 Pillow，跳过 og-cover.png")
        return

    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#062a52")
    px = img.load()
    # 对角渐变底
    c1 = (6, 42, 82)
    c2 = (20, 98, 173)
    for y in range(H):
        for x in range(0, W, 4):
            t = (x / W * 0.55 + y / H * 0.45)
            col = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
            for dx in range(4):
                if x + dx < W:
                    px[x + dx, y] = col

    d = ImageDraw.Draw(img, "RGBA")
    # 装饰圆形
    d.ellipse([880, -140, 1420, 400], fill=(224, 31, 61, 46))
    d.ellipse([-160, 380, 320, 860], fill=(255, 255, 255, 22))
    d.ellipse([950, 400, 1180, 630], fill=(255, 255, 255, 20))
    # 网格
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 14), width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 14), width=1)
    # 左侧强调条
    d.rectangle([0, 0, 10, H], fill=(200, 16, 46, 255))

    def font(size, bold=True):
        cands = [
            r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\Deng.ttf",
        ]
        for c in cands:
            if os.path.exists(c):
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    continue
        return None

    f_small = font(30, False)
    f_title = font(78, True)
    f_sub = font(36, False)
    f_foot = font(28, False)

    if f_title:
        d.text((86, 96), "湖南科技大学 · 建筑与设计学院", font=f_small, fill=(160, 196, 232, 255))
        d.text((82, 150), "宣传报道部", font=f_title, fill=(255, 255, 255, 255))
        d.line([(86, 268), (230, 268)], fill=(224, 31, 61, 255), width=6)
        d.text((86, 300), "以笔为尺丈量校园 · 以镜为窗记录时代", font=f_sub, fill=(206, 226, 246, 255))
        d.text((86, 500), "新闻采编 / 摄影摄像 / 新媒体运营 / 视觉设计", font=f_sub, fill=(160, 196, 232, 255))
        d.text((86, 566), "示例占位图 · 上线前请替换为官方素材", font=f_foot, fill=(150, 176, 204, 255))
    else:
        print("  ! 未找到中文字体，og-cover.png 仅生成图形层")

    out = os.path.join(IMG, "og-cover.png")
    img.save(out, "PNG", optimize=True)
    print("  +", os.path.relpath(out, ROOT))


def main():
    print("生成 SVG 封面 ...")
    for i in range(1, 4):
        cover(f"cover-news-{i}.svg", i - 1, 800, 500)
    for i in range(1, 10):
        cover(f"cover-work-{i}.svg", i + 2, 800, 600)
    print("生成标识与图标 ...")
    logo()
    favicon()
    print("生成社交分享图 ...")
    og_image()
    print("完成。")


if __name__ == "__main__":
    main()
