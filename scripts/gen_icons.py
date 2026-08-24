"""
生成 PWA 图标：蓝底白字「西」，两种尺寸。
运行：.venv/bin/python scripts/gen_icons.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG_COLOR = (74, 144, 217)   # #4a90d9
FG_COLOR = (255, 255, 255)  # white
TEXT = "西"

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """尝试加载支持中文的字体，失败则退回默认字体。"""
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def make_icon(size: int, out_path: Path) -> None:
    img = Image.new("RGB", (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = _load_font(int(size * 0.6))

    # 居中绘制文字
    bbox = draw.textbbox((0, 0), TEXT, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), TEXT, font=font, fill=FG_COLOR)

    img.save(out_path, "PNG")
    print(f"生成 {out_path} ({size}x{size})")


if __name__ == "__main__":
    STATIC_DIR.mkdir(exist_ok=True)
    make_icon(192, STATIC_DIR / "icon-192.png")
    make_icon(512, STATIC_DIR / "icon-512.png")
