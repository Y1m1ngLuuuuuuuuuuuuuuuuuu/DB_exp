#!/usr/bin/env python3
"""Build a no-audio static demo video preview from report screenshots.

The script always generates:
- report/video/static_demo_frames/frame_XX.png
- report/video/student_course_demo_static.gif
- report/video/student_course_demo_static.html

It also tries to generate an MP4 if an encoder is available. The MP4 step is
best-effort because local ffmpeg installations may be unavailable or broken.
"""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
FIGURES = REPORT / "figures"
OUT_DIR = REPORT / "video"
FRAME_DIR = OUT_DIR / "static_demo_frames"

WIDTH = 1280
HEIGHT = 720
FPS = 1


@dataclass(frozen=True)
class Slide:
    title: str
    subtitle: str
    bullets: tuple[str, ...]
    image: str | None = None
    duration: int = 4


SLIDES: tuple[Slide, ...] = (
    Slide(
        "基于 openGauss 的学生选课成绩管理系统",
        "数据库设计与实现演示 · 无声静态预览",
        (
            "展示重点：ER 模型、关系模型、规范化、触发器、事务与锁",
            "演示数据：4 个学院、100 名学生、30 名教师、50 门课程",
        ),
        "ui/01_login.png",
        4,
    ),
    Slide(
        "登录与角色体系",
        "学生、教师、管理员统一入口",
        (
            "学生使用学号登录，教师使用教师编号登录，管理员使用管理员编号登录",
            "user_account 保存认证信息，角色档案分表保存",
            "角色档案一致性由数据库触发器兜底",
        ),
        "ui/01_login.png",
        4,
    ),
    Slide(
        "管理员首页",
        "系统数据规模与运行概览",
        (
            "展示学生、教师、课程、教学班、选课记录和成绩日志数量",
            "管理端指标来自基础表、聚合查询和视图",
        ),
        "ui/08_admin_dashboard.png",
        4,
    ),
    Slide(
        "概念结构设计",
        "从业务对象抽取实体、属性与联系",
        (
            "核心实体：学生、教师、课程、学期、教室、教学班、选课记录",
            "学生与教学班是 M:N 联系，由 enrollment 转换",
        ),
        "er_conceptual.png",
        5,
    ),
    Slide(
        "逻辑结构设计",
        "关系模式、主键、候选键和外键",
        (
            "course 保存课程定义，course_offering 保存具体教学班",
            "course_schedule 结构化保存上课时间片",
            "course_prerequisite 表达课程先修自关联",
        ),
        "er_logical.png",
        5,
    ),
    Slide(
        "学生端课程概览",
        "选课记录、课表和成绩聚合展示",
        (
            "学生首页汇总已选课程、本学期课程、已完成课程和绩点信息",
            "底层数据来自 enrollment、课程教学表和绩点统计视图",
        ),
        "ui/02_student_dashboard.png",
        4,
    ),
    Slide(
        "课程查询与选课",
        "数据库层保证选课完整性",
        (
            "选课流程调用 select_course_tx()",
            "SELECT ... FOR UPDATE 锁定目标教学班",
            "触发器检查容量、时间冲突、先修课程和同课跨班限制",
        ),
        None,
        4,
    ),
    Slide(
        "范式设计",
        "减少冗余，避免更新异常",
        (
            "基础表不保存 selected_count，已选人数通过视图统计",
            "基础表不保存 gpa_point，绩点通过 grade_policy、grade_scale 和视图计算",
            "上课时间使用 course_schedule 结构化表示",
        ),
        "er_attributes_preview.png",
        4,
    ),
    Slide(
        "教师成绩录入",
        "成绩更新与审计日志保持事务一致",
        (
            "教师只能维护本人负责的教学班成绩",
            "成绩更新事务设置当前操作者与修改原因",
            "trg_score_change_log 自动写入 score_change_log",
        ),
        "ui/06_teacher_dashboard.png",
        4,
    ),
    Slide(
        "事务与并发控制",
        "防止最后一个名额被多人同时抢到",
        (
            "并发测试：success_count = 1",
            "并发测试：failed_count = 1",
            "数据库最终 selected_count_in_db = 1",
        ),
        None,
        4,
    ),
    Slide(
        "运行维护与审计",
        "触发器、视图、测试脚本与权限设计共同支撑系统运行",
        (
            "回滚型 SQL 测试覆盖容量、时间冲突、先修关系和成绩审计",
            "视图封装常用 JOIN 和聚合统计",
            "数据库角色脚本体现最小权限设计",
        ),
        "ui/08_admin_dashboard.png",
        4,
    ),
    Slide(
        "展示收尾",
        "数据库原理2课程知识点落地",
        (
            "设计流程：规划、需求、概念、逻辑、规范化、物理、运行维护",
            "核心机制：ER、关系模型、3NF、约束、触发器、事务、锁、视图",
            "后续方向：生产级权限、备份恢复、监控、教师评价和更大规模压测",
        ),
        None,
        4,
    ),
)


def font_path() -> str | None:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


FONT_FILE = font_path()


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if FONT_FILE:
        index = 1 if bold and FONT_FILE.endswith(".ttc") else 0
        return ImageFont.truetype(FONT_FILE, size=size, index=index)
    return ImageFont.load_default()


TITLE_FONT = load_font(44, bold=True)
SUBTITLE_FONT = load_font(24)
BODY_FONT = load_font(24)
SMALL_FONT = load_font(17)


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> float:
    return draw.textlength(text, font=font)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        if current and text_width(draw, trial, font) > max_width:
            lines.append(current)
            current = char
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str, outline: str | None = None) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline)


def fit_image(path: Path, box_size: tuple[int, int]) -> Image.Image | None:
    if not path.exists():
        return None
    img = Image.open(path).convert("RGB")
    img.thumbnail(box_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", box_size, "#FFFFFF")
    x = (box_size[0] - img.width) // 2
    y = (box_size[1] - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def draw_bullets(draw: ImageDraw.ImageDraw, bullets: Iterable[str], x: int, y: int, max_width: int) -> int:
    cursor = y
    for bullet in bullets:
        wrapped = wrap_text(draw, bullet, BODY_FONT, max_width - 34)
        draw.ellipse((x, cursor + 10, x + 9, cursor + 19), fill="#0071E3")
        for idx, line in enumerate(wrapped):
            draw.text((x + 24, cursor), line, font=BODY_FONT, fill="#1D1D1F")
            cursor += 33
            if idx < len(wrapped) - 1:
                cursor += 1
        cursor += 12
    return cursor


def render_slide(slide: Slide, index: int, total: int) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), "#F5F5F7")
    draw = ImageDraw.Draw(img)

    # Soft background bands
    draw.rounded_rectangle((50, 44, WIDTH - 50, HEIGHT - 44), radius=34, fill="#FFFFFF", outline="#E5E7EB")
    draw.rectangle((50, 44, WIDTH - 50, 118), fill="#FFFFFF")

    draw.text((82, 72), f"{index:02d}", font=SMALL_FONT, fill="#6E6E73")
    draw.text((122, 58), slide.title, font=TITLE_FONT, fill="#1D1D1F")
    draw.text((124, 112), slide.subtitle, font=SUBTITLE_FONT, fill="#6E6E73")

    image_area = (676, 156, 1118, 420)
    text_x = 118
    text_width_px = 500

    if slide.image:
        source = FIGURES / slide.image
        fitted = fit_image(source, (image_area[2] - image_area[0], image_area[3] - image_area[1]))
        rounded_rect(draw, (646, 142, 1148, 448), 24, "#F9FAFB", "#E5E7EB")
        if fitted:
            mask = Image.new("L", fitted.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, fitted.width, fitted.height), radius=18, fill=255)
            img.paste(fitted, image_area[:2], mask)
        else:
            draw.text((690, 268), "截图未找到", font=BODY_FONT, fill="#6E6E73")
    else:
        rounded_rect(draw, (646, 142, 1148, 448), 24, "#F9FAFB", "#E5E7EB")
        draw.text((710, 236), "静态讲解页", font=TITLE_FONT, fill="#1D1D1F")
        draw.text((714, 296), "用于录屏前确认节奏", font=SUBTITLE_FONT, fill="#6E6E73")

    rounded_rect(draw, (92, 162, 596, 512), 22, "#F9FAFB", "#E5E7EB")
    draw_bullets(draw, slide.bullets, text_x, 206, text_width_px)

    # Footer
    draw.line((92, 614, WIDTH - 92, 614), fill="#E5E7EB", width=1)
    draw.text((92, 634), "学生选课成绩管理系统 · 数据库原理2大作业演示", font=SMALL_FONT, fill="#6E6E73")
    progress_w = int((WIDTH - 184) * index / total)
    draw.rounded_rectangle((92, 676, WIDTH - 92, 684), radius=4, fill="#E5E7EB")
    draw.rounded_rectangle((92, 676, 92 + progress_w, 684), radius=4, fill="#0071E3")
    draw.text((WIDTH - 210, 634), f"{index}/{total}", font=SMALL_FONT, fill="#6E6E73")
    return img


def save_html(frame_paths: list[Path], durations: list[int]) -> Path:
    encoded = []
    for path in frame_paths:
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        encoded.append(f"data:image/png;base64,{b64}")
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>学生选课成绩管理系统静态演示视频</title>
  <style>
    body {{ margin: 0; background: #111827; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif; }}
    .wrap {{ min-height: 100vh; display: grid; place-items: center; gap: 12px; padding: 24px; box-sizing: border-box; }}
    img {{ max-width: min(96vw, 1280px); max-height: 86vh; border-radius: 18px; box-shadow: 0 20px 80px rgba(0,0,0,.38); background: #fff; }}
    .bar {{ width: min(96vw, 1280px); display: flex; justify-content: space-between; color: #cbd5e1; font-size: 14px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <img id="slide" src="{encoded[0]}" alt="demo slide" />
    <div class="bar"><span>无声静态预览</span><span id="counter">1 / {len(encoded)}</span></div>
  </div>
  <script>
    const slides = {encoded!r};
    const durations = {durations!r};
    let i = 0;
    const img = document.getElementById('slide');
    const counter = document.getElementById('counter');
    function next() {{
      i = (i + 1) % slides.length;
      img.src = slides[i];
      counter.textContent = `${{i + 1}} / ${{slides.length}}`;
      setTimeout(next, durations[i] * 1000);
    }}
    setTimeout(next, durations[0] * 1000);
  </script>
</body>
</html>
"""
    out = OUT_DIR / "student_course_demo_static.html"
    out.write_text(html, encoding="utf-8")
    return out


def save_gif(frames: list[Image.Image], durations: list[int]) -> Path:
    out = OUT_DIR / "student_course_demo_static.gif"
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=[d * 1000 for d in durations],
        loop=0,
        optimize=True,
    )
    return out


def try_mp4_with_imageio(frame_paths: list[Path], durations: list[int]) -> Path | None:
    try:
        import imageio.v2 as imageio  # type: ignore
    except Exception:
        return None

    out = OUT_DIR / "student_course_demo_static.mp4"
    try:
        writer = imageio.get_writer(out, fps=FPS, codec="libx264", quality=8, macro_block_size=16)
        for path, duration in zip(frame_paths, durations):
            frame = imageio.imread(path)
            for _ in range(max(1, duration * FPS)):
                writer.append_data(frame)
        writer.close()
        return out if out.exists() else None
    except Exception as exc:
        print(f"MP4 imageio export skipped: {exc}")
        return None


def try_mp4_with_avconvert(gif_path: Path) -> Path | None:
    avconvert = shutil.which("avconvert")
    if not avconvert:
        return None
    out = OUT_DIR / "student_course_demo_static.mp4"
    cmd = [
        avconvert,
        "--source",
        str(gif_path),
        "--preset",
        "Preset1280x720",
        "--output",
        str(out),
        "--replace",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return out if out.exists() else None
    except Exception as exc:
        print(f"MP4 avconvert export skipped: {exc}")
        return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if FRAME_DIR.exists():
        for old in FRAME_DIR.glob("frame_*.png"):
            old.unlink()
    FRAME_DIR.mkdir(parents=True, exist_ok=True)

    frames: list[Image.Image] = []
    frame_paths: list[Path] = []
    durations: list[int] = []
    total = len(SLIDES)

    for idx, slide in enumerate(SLIDES, start=1):
        frame = render_slide(slide, idx, total)
        path = FRAME_DIR / f"frame_{idx:02d}.png"
        frame.save(path)
        frames.append(frame)
        frame_paths.append(path)
        durations.append(slide.duration)

    gif_path = save_gif(frames, durations)
    html_path = save_html(frame_paths, durations)
    mp4_path = try_mp4_with_imageio(frame_paths, durations) or try_mp4_with_avconvert(gif_path)

    print(f"frames: {FRAME_DIR}")
    print(f"gif: {gif_path}")
    print(f"html: {html_path}")
    if mp4_path:
        print(f"mp4: {mp4_path}")
    else:
        print("mp4: not generated; install imageio/imageio-ffmpeg or repair ffmpeg if MP4 is required")


if __name__ == "__main__":
    main()
