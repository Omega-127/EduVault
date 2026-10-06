"""Generate a high-quality EduVault hero demo GIF."""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "eduvault-demo.gif"

# Render at 2x, export at 1x for crisp edges
EXPORT_W, EXPORT_H = 1280, 720
SCALE = 2
PALETTE_COLORS = 256
W, H = EXPORT_W * SCALE, EXPORT_H * SCALE

BG = (17, 24, 39)
SURFACE = (31, 41, 55)
SURFACE_ALT = (37, 47, 63)
BORDER = (55, 65, 81)
ACCENT = (16, 185, 129)
ACCENT_DARK = (6, 78, 59)
TEXT = (249, 250, 251)
MUTED = (156, 163, 175)
USER_BUBBLE = (16, 185, 129)
USER_TEXT = (17, 24, 39)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ["Segoe UI Semibold.ttf", "segoeuib.ttf"] if bold else ["Segoe UI.ttf", "segoeui.ttf"]
    ) + (["Arial Bold.ttf", "arialbd.ttf"] if bold else ["Arial.ttf", "arial.ttf"])
    windir = os.environ.get("WINDIR", r"C:\Windows")
    fonts_dir = Path(windir) / "Fonts"
    for name in names:
        path = fonts_dir / name
        if path.exists():
            return ImageFont.truetype(str(path), size * SCALE)
    return ImageFont.load_default()


FONT_BRAND = load_font(20, True)
FONT_MD = load_font(17)
FONT_SM = load_font(15)
FONT_AVATAR = load_font(13, True)
FONT_XS = load_font(13)
FONT_MONO = load_font(12)

QUESTION = "What is the minimum attendance required for end-semester exams?"
ANSWER_LINES = [
    "According to Academic Regulations 2024, candidates need",
    "75% aggregate attendance to appear for end-semester examinations.",
    "Medical condonation (65–74%) requires approved records within 7 days.",
]
CITATION = "Academic_Regulations_2024.pdf  ·  Section 4.2  ·  Page 18"
SIM = "0.89"


def rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
    width: int = 0,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_centered_label(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    """Center text using the actual glyph ink box, not font ascent metrics."""
    x1, y1, x2, y2 = box
    box_cx = (x1 + x2) / 2
    box_cy = (y1 + y2) / 2

    # Measure ink relative to origin; bbox includes left/top bearings
    left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
    ink_cx = (left + right) / 2
    ink_cy = (top + bottom) / 2

    # Place so ink center lands on box center (tiny down bias for caps)
    tx = box_cx - ink_cx
    ty = box_cy - ink_cy + (0.5 * SCALE)
    draw.text((tx, ty), label, font=font, fill=fill)


def draw_frame(
    q_chars: int,
    answer_chars: int = 0,
    show_cite: bool = False,
    typing_phase: int | None = None,
    cursor_on: bool = False,
) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    for x in range(0, W, 64 * SCALE):
        d.line([(x, 0), (x, H)], fill=(22, 30, 46), width=1)
    for y in range(0, H, 64 * SCALE):
        d.line([(0, y), (W, y)], fill=(22, 30, 46), width=1)

    pad = 56 * SCALE
    win = (pad, 48 * SCALE, W - pad, H - 48 * SCALE)
    rounded_rect(d, win, 20 * SCALE, SURFACE, BORDER, 2 * SCALE)

    # Title bar
    tb = (win[0], win[1], win[2], win[1] + 52 * SCALE)
    d.rectangle(tb, fill=SURFACE_ALT)
    d.line([(tb[0], tb[3]), (tb[2], tb[3])], fill=BORDER, width=2)
    for i, color in enumerate([(239, 68, 68), (245, 158, 11), (16, 185, 129)]):
        cx = tb[0] + 22 * SCALE + i * 22 * SCALE
        cy = tb[1] + 18 * SCALE
        d.ellipse((cx, cy, cx + 14 * SCALE, cy + 14 * SCALE), fill=color)

    d.text((tb[0] + 88 * SCALE, tb[1] + 14 * SCALE), "EduVault", font=FONT_BRAND, fill=TEXT)
    d.text((tb[0] + 220 * SCALE, tb[1] + 18 * SCALE), "Chat session", font=FONT_XS, fill=MUTED)

    status_x = tb[2] - 180 * SCALE
    d.ellipse(
        (status_x, tb[1] + 22 * SCALE, status_x + 8 * SCALE, tb[1] + 30 * SCALE),
        fill=ACCENT,
    )
    d.text((status_x + 16 * SCALE, tb[1] + 16 * SCALE), "Grounded RAG", font=FONT_XS, fill=MUTED)

    content_top = tb[3] + 28 * SCALE
    avatar_size = 40 * SCALE

    # User bubble — fixed width from full question so it doesn't jump while typing
    q_shown = QUESTION[:q_chars]
    if cursor_on and q_chars < len(QUESTION):
        q_shown += "|"

    full_bbox = d.textbbox((0, 0), QUESTION, font=FONT_MD)
    qw = full_bbox[2] - full_bbox[0] + 36 * SCALE
    qh = full_bbox[3] - full_bbox[1] + 28 * SCALE
    ux2 = win[2] - 32 * SCALE - avatar_size - 12 * SCALE
    ux1 = ux2 - qw
    uy1 = content_top
    uy2 = uy1 + qh
    rounded_rect(d, (ux1, uy1, ux2, uy2), 14 * SCALE, USER_BUBBLE)
    d.text((ux1 + 18 * SCALE, uy1 + 14 * SCALE), q_shown, font=FONT_MD, fill=USER_TEXT)

    # User avatar — text truly centered
    avatar = (ux2 + 12 * SCALE, uy1, ux2 + 12 * SCALE + avatar_size, uy1 + avatar_size)
    rounded_rect(d, avatar, 10 * SCALE, SURFACE_ALT, BORDER, 2)
    draw_centered_label(d, avatar, "ST", FONT_AVATAR, TEXT)

    ay = uy2 + 32 * SCALE
    bot_avatar = (
        win[0] + 32 * SCALE,
        ay,
        win[0] + 32 * SCALE + avatar_size,
        ay + avatar_size,
    )
    rounded_rect(d, bot_avatar, 10 * SCALE, ACCENT_DARK, ACCENT, 2)
    draw_centered_label(d, bot_avatar, "EV", FONT_AVATAR, ACCENT)

    bx1 = bot_avatar[2] + 16 * SCALE
    bx2 = win[2] - 48 * SCALE

    if typing_phase is not None and answer_chars == 0:
        ty = ay + 14 * SCALE
        for i in range(3):
            # Smooth bounce via sine-ish stepped heights
            phase = (typing_phase + i * 2) % 6
            bounce = [0, 3, 6, 3, 0, 0][phase] * SCALE
            cx = bx1 + 8 * SCALE + i * 18 * SCALE
            d.ellipse(
                (cx, ty - bounce, cx + 10 * SCALE, ty - bounce + 10 * SCALE),
                fill=ACCENT,
            )
        return downscale(img)

    if answer_chars > 0:
        # Stream across lines using a flat char index (no join-space ambiguity)
        lines: list[str] = []
        consumed = 0
        for src in ANSWER_LINES:
            if consumed >= answer_chars:
                break
            take = min(len(src), answer_chars - consumed)
            lines.append(src[:take])
            consumed += take
            if take < len(src):
                break

        line_h = 30 * SCALE
        cite_h = 52 * SCALE if show_cite else 0
        box_h = 24 * SCALE + max(1, len(lines)) * line_h + cite_h
        rounded_rect(d, (bx1, ay, bx2, ay + box_h), 14 * SCALE, BG, BORDER, 2 * SCALE)

        ty = ay + 18 * SCALE
        for line in lines:
            d.text((bx1 + 20 * SCALE, ty), line, font=FONT_SM, fill=TEXT)
            ty += line_h

        if show_cite:
            cy1 = ty + 4 * SCALE
            cy2 = cy1 + 36 * SCALE
            rounded_rect(
                d, (bx1 + 20 * SCALE, cy1, bx1 + 520 * SCALE, cy2), 8 * SCALE, ACCENT_DARK
            )
            d.text((bx1 + 32 * SCALE, cy1 + 10 * SCALE), CITATION, font=FONT_MONO, fill=ACCENT)
            d.text((bx1 + 540 * SCALE, cy1 + 10 * SCALE), SIM, font=FONT_MONO, fill=MUTED)

    return downscale(img)


def downscale(img: Image.Image) -> Image.Image:
    return img.resize((EXPORT_W, EXPORT_H), Image.Resampling.LANCZOS)


def build_frames() -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    durations: list[int] = []

    answer_len = sum(len(line) for line in ANSWER_LINES)

    # Type question — every 2 chars keeps motion smooth without decode lag
    for n in range(0, len(QUESTION) + 1, 2):
        frames.append(
            draw_frame(n, 0, cursor_on=(n < len(QUESTION) and (n // 2) % 2 == 0))
        )
        durations.append(36 if n < len(QUESTION) else 180)
    if len(QUESTION) % 2 != 0:
        frames.append(draw_frame(len(QUESTION), 0))
        durations.append(180)

    # Brief thinking dots
    for phase in range(8):
        frames.append(draw_frame(len(QUESTION), 0, typing_phase=phase))
        durations.append(50)

    # Stream answer in larger chunks — still reads as typing, fewer frames
    step = 5
    for n in range(step, answer_len + 1, step):
        frames.append(draw_frame(len(QUESTION), n))
        durations.append(30)
    if answer_len % step != 0:
        frames.append(draw_frame(len(QUESTION), answer_len))
        durations.append(30)

    frames.append(draw_frame(len(QUESTION), answer_len))
    durations.append(160)

    frames.append(draw_frame(len(QUESTION), answer_len, show_cite=True))
    durations.append(1200)

    return frames, durations


def quantize_frames(frames: list[Image.Image]) -> list[Image.Image]:
    """Single master palette to reduce flicker and banding."""
    sample = Image.new("RGB", (EXPORT_W, EXPORT_H * min(8, len(frames))))
    step = max(1, len(frames) // 8)
    for i, idx in enumerate(range(0, len(frames), step)[:8]):
        sample.paste(frames[idx], (0, i * EXPORT_H))

    palette_ref = sample.quantize(
        colors=PALETTE_COLORS, method=Image.Quantize.MEDIANCUT
    )
    # NONE dither keeps UI chrome sharper and playback lighter
    return [
        frame.quantize(palette=palette_ref, dither=Image.Dither.NONE)
        for frame in frames
    ]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rgb_frames, durations = build_frames()
    frames = quantize_frames(rgb_frames)

    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(
        f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB, "
        f"{len(frames)} frames, {EXPORT_W}x{EXPORT_H})"
    )


if __name__ == "__main__":
    main()
