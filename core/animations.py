#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终端动画引擎 - 基于rich实现迪士尼风格动画效果
30fps动态帧率版: 精确补偿渲染耗时，Termux 下稳定流畅
"""

import os
import sys
import time
import random
import math
from contextlib import contextmanager
from typing import Optional, Callable

from rich.console import Console
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import (
    Progress, BarColumn, TextColumn, SpinnerColumn,
    TimeRemainingColumn
)
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.style import Style
from rich.color import Color
from rich import box

console = Console()


# ==================== 性能优化 & Termux 辅助函数 ====================

_terminal_cache = {"size": None, "timestamp": 0.0}


def _terminal_size():
    """获取终端尺寸，带 2 秒缓存，避免频繁系统调用"""
    now = time.time()
    if _terminal_cache["size"] is None or (now - _terminal_cache["timestamp"]) > 2:
        _terminal_cache["size"] = os.get_terminal_size()
        _terminal_cache["timestamp"] = now
    return _terminal_cache["size"]


def _twidth():
    """从缓存获取终端宽度"""
    return _terminal_size().columns


def _theight():
    """从缓存获取终端高度"""
    return _terminal_size().lines


# ==================== 缓动函数 ====================

def ease_in_out(t: float) -> float:
    """三次贝塞尔缓入缓出曲线 (smoothstep)"""
    if t < 0:
        return 0.0
    if t > 1:
        return 1.0
    return t * t * (3.0 - 2.0 * t)


# ==================== 通用帧率运行器 ====================

def frame_runner(callback: Callable[[float], str], fps: float, duration: float):
    """通用高帧率动画运行器。

    每一帧调用 callback(progress) 生成帧字符串，progress 在 0.0~1.0 之间。
    按指定 fps 运行，持续 duration 秒。
    使用 console.clear() + console.print() 保证与 Rich 兼容。
    """
    frame_time = 1.0 / fps
    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        elapsed = time.time() - start
        progress = min(elapsed / duration, 1.0)
        frame_str = callback(progress)
        console.clear()
        console.print(frame_str)
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 页面切换动画 ====================

def page_transition(duration: float = 0.8):
    """页面切换动画 - 清屏 + 快速淡出，30fps 动态帧率。

    简单的清屏过渡效果，不占用过多渲染时间。
    """
    fps = 30
    frame_time = 1.0 / fps
    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1
    console.clear()


# ==================== 打字机效果 ====================

def typewriter(text: str, delay: float = 0.03, style: str = "bold cyan"):
    """打字机逐字弹出动画"""
    d = delay * 0.3
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(d)
    sys.stdout.write("\n")
    sys.stdout.flush()


# ==================== 流光扫动动画 ====================

def sweep_animation(text: str, duration: float = 2.0, style: str = "bold cyan"):
    """渐变流光扫动文字动画 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    gradient = ["cyan", "bright_cyan", "blue", "bright_blue", "magenta", "bright_magenta"]
    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        offset = frame % len(gradient)
        chars = list(text)
        colored = Text()
        for j, ch in enumerate(chars):
            color_idx = (offset + j) % len(gradient)
            colored.append(ch, style=gradient[color_idx])
        console.clear()
        console.print(colored)
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 渐变进度条 ====================

@contextmanager
def gradient_progress(total: int = 100, description: str = "Processing"):
    """渐变彩色进度条上下文管理器"""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=50, style="cyan", complete_style="bright_magenta",
                  finished_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )
    with progress:
        task = progress.add_task(description, total=total)
        yield progress, task


# ==================== 粒子刷屏动画 ====================

def particle_burst(duration: float = 1.5, density: int = 20):
    """粒子爆炸刷屏效果 (30fps 动态帧率, 自适应终端尺寸)"""
    fps = 30
    frame_time = 1.0 / fps
    chars = "✦✧✶✷✸✹✺✦✧▪▫◆◇○●□■△▲☆★"
    width = min(_twidth(), 80)
    height = min(_theight() - 2, 15)
    density = max(5, density // 2)

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for _ in range(density):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            ch = random.choice(chars)
            style = random.choice(["cyan", "bright_cyan", "blue", "magenta", "bright_magenta"])
            grid[y][x] = f"[{style}]{ch}[/]"

        console.clear()
        frame_str = "\n".join("".join(row) for row in grid)
        console.print(frame_str)
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 弹窗提示框 ====================

def popup_message(title: str, message: str, style: str = "cyan",
                  duration: float = 3.0, fade: bool = True):
    """
    弹出提示框 — fade=True: 自动消失(延长至3秒), fade=False: 需要按键确认
    自适应DPI宽度
    """
    adaptive_w = max(40, min(_twidth() - 4, 80))
    confirm_text = "\n\n[dim]Press any key to continue...[/]" if not fade else ""
    panel = Panel(
        Align.center(f"[bold]{message}[/]{confirm_text}", vertical="middle"),
        title=f"[bold {style}]{title}[/]",
        border_style=style,
        box=box.ROUNDED,
        padding=(1, 3),
        width=adaptive_w,
    )

    if fade:
        console.print()
        console.print(panel)
        time.sleep(duration)
        console.clear()
    else:
        console.print()
        console.print(panel)
        input()


# ==================== 加载动画 ====================

def loading_spinner(message: str, duration: float = 2.0, style: str = "cyan"):
    """旋转加载动画"""
    console.print()
    with console.status(f"[{style}]{message}...[/]", spinner="dots"):
        time.sleep(duration)


def loading_sweep(message: str, duration: float = 2.0):
    """流光加载动画 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    chars = "█▓▒░"
    console.print()
    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        bar = "".join(chars[(frame + j) % len(chars)] for j in range(20))
        sys.stdout.write(f"\r  [{bar}]")
        sys.stdout.flush()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1
    sys.stdout.write("\n")
    sys.stdout.flush()


# ==================== 分隔线 ====================

def divider(char: str = "━", width: int = 60, style: str = "dim cyan"):
    """打印分隔线"""
    console.print(char * width, style=style)


# ==================== 标题面板 ====================

def title_panel(title: str, subtitle: str = ""):
    """带标题和副标题的装饰面板"""
    content = f"[bold bright_cyan]{title}[/]"
    if subtitle:
        content += f"\n[dim cyan]{subtitle}[/]"
    console.print(Panel(
        Align.center(content, vertical="middle"),
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    ))


# ==================== 实时数据刷新 ====================

class LiveDashboard:
    """实时监控仪表盘基类"""

    def __init__(self, refresh_rate: float = 1.0):
        self.refresh_rate = refresh_rate
        self._running = False
        self._live: Optional[Live] = None

    def _generate_layout(self) -> Layout:
        """子类重写此方法生成布局"""
        raise NotImplementedError

    def start(self):
        """启动实时刷新"""
        self._running = True
        self._live = Live(
            self._generate_layout(),
            console=console,
            refresh_per_second=1 / self.refresh_rate,
            screen=True,
        )
        self._live.start()

    def stop(self):
        """停止刷新"""
        self._running = False
        if self._live:
            self._live.stop()

    def update(self):
        """手动更新一次"""
        if self._live and self._running:
            self._live.update(self._generate_layout())

    def run(self):
        """持续运行循环"""
        self.start()
        try:
            while self._running:
                self.update()
                time.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            self.stop()


# ==================== 矩阵雨效果 ====================

def matrix_rain(duration: float = 2.0, density: int = 40):
    """黑客帝国风格矩阵雨动画 (30fps 动态帧率, 自适应终端)"""
    fps = 30
    frame_time = 1.0 / fps
    chars = "ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789"
    width = min(_twidth(), 80)
    height = min(_theight() - 2, 15)
    density = max(5, density // 2)
    columns = [random.randint(0, height - 1) for _ in range(width)]

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        frame_lines = []
        for y in range(height):
            line = ""
            for x in range(width):
                if columns[x] <= y < columns[x] + random.randint(3, 8):
                    if y == columns[x] + random.randint(2, 5):
                        line += "[bold bright_green]" + random.choice(chars) + "[/]"
                    else:
                        line += "[green]" + random.choice(chars) + "[/]"
                else:
                    line += " "
            frame_lines.append(line)
        console.print("\n".join(frame_lines))
        for i in range(len(columns)):
            if random.random() > 0.95:
                columns[i] = 0
            else:
                columns[i] = min(columns[i] + 1, height)
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 脉冲光晕效果 ====================

def pulse_glow(text: str, cycles: int = 3, duration: float = 3.0):
    """脉冲光晕文字效果 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    colors = ["cyan", "bright_cyan", "blue", "bright_blue", "magenta", "bright_magenta", "purple", "cyan"]
    steps_per_cycle = len(colors)
    total_steps = cycles * steps_per_cycle * 2

    start = time.time()
    frame = 0
    step_index = 0
    while time.time() - start < duration and step_index < total_steps:
        frame_start = time.time()
        cycle_idx = step_index // (steps_per_cycle * 2)
        step_in_cycle = step_index % (steps_per_cycle * 2)
        if step_in_cycle < steps_per_cycle:
            color = colors[step_in_cycle]
        else:
            color = colors[steps_per_cycle * 2 - 1 - step_in_cycle]

        console.clear()
        console.print()
        console.print(Align.center(text, style=f"dim {color}"))
        console.print(Align.center(text, style=f"bold {color}"))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        step_index += 1
        frame += 1


# ==================== 霓虹闪烁边框 ====================

def neon_border_panel(content: str, title: str = "", duration: float = 2.0):
    """霓虹闪烁边框面板 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    colors = ["cyan", "magenta", "blue", "bright_cyan", "bright_magenta", "bright_blue"]
    tw = min(_twidth() - 4, 60)

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        color = colors[frame % len(colors)]
        panel = Panel(
            Align.center(content, vertical="middle"),
            title=f"[bold {color}]{title}[/]" if title else None,
            border_style=color,
            box=box.ROUNDED,
            padding=(1, 3),
            width=tw,
        )
        console.clear()
        console.print()
        console.print(panel)
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 数字滚动计数 ====================

def count_up_animation(start: int, end: int, duration: float = 1.5, label: str = "",
                       style: str = "bold cyan"):
    """数字滚动计数动画 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    t_start = time.time()
    frame = 0
    while time.time() - t_start < duration:
        frame_start = time.time()
        elapsed = time.time() - t_start
        progress = min(elapsed / duration, 1.0)
        val = int(start + (end - start) * progress)
        sys.stdout.write(f"\r  {label} [{style}]{val}[/]")
        sys.stdout.flush()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1
    sys.stdout.write("\n")
    sys.stdout.flush()


# ==================== 波浪进度条 ====================

def wave_progress_bar(value: float, width: int = 40, style: str = "cyan"):
    """波浪动画进度条"""
    wave_chars = " ▁▂▃▄▅▆▇█"
    filled = int(width * value / 100)
    bar = ""
    for i in range(width):
        if i < filled:
            wave_idx = int((math.sin(time.time() * 3 + i * 0.5) + 1) * 3.5)
            wave_idx = max(0, min(7, wave_idx))
            bar += f"[{style}]{wave_chars[wave_idx]}[/]"
        else:
            bar += "[dim]░[/]"
    return f"{bar} [{style}]{value:.1f}%[/]"


# ==================== 彩色螺旋 ====================

def spiral_animation(duration: float = 2.0):
    """彩色螺旋动画 (30fps 动态帧率, 自适应尺寸)"""
    fps = 30
    frame_time = 1.0 / fps
    chars = "✦✧✶✷✸✹✺✵✴✳✲✱"
    colors = ["cyan", "bright_cyan", "blue", "bright_blue", "magenta", "bright_magenta"]
    radius = 8
    width = min(_twidth(), 60)
    height = min(_theight() - 2, 20)

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        angle = frame * 0.3
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for r in range(1, radius + 1):
            theta = angle + r * 0.5
            x = int(width // 2 + r * 2.5 * math.cos(theta))
            y = int(height // 2 + r * 1.2 * math.sin(theta))
            if 0 <= x < width and 0 <= y < height:
                ch = random.choice(chars)
                color = colors[r % len(colors)]
                grid[y][x] = f"[{color}]{ch}[/]"
        console.print("\n".join("".join(row) for row in grid))
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 故障效果 ====================

def glitch_text(text: str, duration: float = 2.0, intensity: int = 5):
    """故障风格文字效果 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        result = list(text)
        for _ in range(intensity):
            if random.random() > 0.7:
                idx = random.randint(0, len(text) - 1)
                result[idx] = random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?/~`")
        glitched = "".join(result)
        console.print()
        if random.random() > 0.5:
            offset = random.randint(-2, 2)
            console.print(" " * (40 + offset) + f"[bold red]{glitched}[/]")
            console.print(" " * (40 - offset) + f"[bold cyan]{glitched}[/]")
        else:
            console.print(Align.center(glitched, style="bold cyan"))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1
    console.clear()
    console.print()
    console.print(Align.center(text, style="bold bright_cyan"))
    console.print()


# ==================== 彩虹流光边框 ====================

def rainbow_flow_border(text: str, duration: float = 3.0):
    """彩虹流光边框环绕文字 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    rainbow = ["red", "yellow", "green", "cyan", "blue", "magenta", "bright_red", "bright_yellow"]
    tw = min(_twidth() - 4, 65)

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        color = rainbow[frame % len(rainbow)]
        next_color = rainbow[(frame + 1) % len(rainbow)]
        console.clear()
        console.print()
        panel = Panel(
            Align.center(f"[bold {color}]{text}[/]", vertical="middle"),
            border_style=next_color,
            box=box.ROUNDED,
            padding=(1, 3),
            width=tw,
        )
        console.print(panel)
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 星空背景 ====================

def starfield(duration: float = 2.5, stars: int = 80):
    """星空飞过动画 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    star_chars = "·✦✧✶✷✸✹✺✵✴✳✲✱"
    colors_list = ["bright_cyan", "bright_blue", "bright_magenta", "cyan", "white", "bright_white"]
    width = min(_twidth(), 80)
    height = min(_theight() - 2, 20)
    star_count = max(10, stars // 3)
    star_objs = []
    for _ in range(star_count):
        star_objs.append({
            "x": random.randint(0, width - 2),
            "y": random.randint(0, height - 2),
            "z": random.uniform(0.5, 1.5),
            "char": random.choice(star_chars),
            "color": random.choice(colors_list),
        })

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for s in star_objs:
            s["x"] -= s["z"] * 0.8
            if s["x"] < 0:
                s["x"] = width - 1
                s["y"] = random.randint(0, height - 2)
            x, y = int(s["x"]), int(s["y"])
            if 0 <= x < width and 0 <= y < height:
                if s["z"] > 1.0:
                    grid[y][x] = f"[bold {s['color']}]{s['char']}[/]"
                elif s["z"] > 0.6:
                    grid[y][x] = f"[{s['color']}]{s['char']}[/]"
                else:
                    grid[y][x] = f"[dim {s['color']}]·[/]"
        console.print("\n".join("".join(row) for row in grid))
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 炫彩打字机 ====================

def rainbow_typewriter(text: str, delay: float = 0.03):
    """彩虹色打字机 - 每个字颜色不同"""
    rainbow = ["red", "yellow", "green", "cyan", "blue", "magenta"]
    d = delay * 0.3
    for i, char in enumerate(text):
        color = rainbow[i % len(rainbow)]
        sys.stdout.write(f"[bold {color}]{char}[/]")
        sys.stdout.flush()
        time.sleep(d)
    sys.stdout.write("\n")
    sys.stdout.flush()


# ==================== 爆炸扩散文字 ====================

def explode_text(text: str, duration: float = 2.0):
    """爆炸扩散文字效果 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    colors = ["bright_cyan", "bright_magenta", "bright_yellow", "bright_blue", "bright_green", "bright_red"]

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        elapsed = time.time() - start
        progress = elapsed / duration
        console.clear()
        chars = list(text)
        result = ""
        for i, ch in enumerate(chars):
            offset = int((i - len(chars)/2) * progress * 8)
            color = colors[i % len(colors)]
            if offset == 0:
                result += f"[bold {color}]{ch}[/]"
            else:
                result += f"[dim {color}]{ch}[/]" + " " * abs(offset)
        console.print()
        console.print(Align.center(result))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1
    console.clear()
    console.print()
    console.print(Align.center(text, style="bold bright_cyan"))
    console.print()


# ==================== 加载粒子环 ====================

def particle_ring_loader(message: str, duration: float = 2.0):
    """粒子环旋转加载动画 (30fps 动态帧率, 自适应尺寸)"""
    fps = 30
    frame_time = 1.0 / fps
    width = min(_twidth(), 80)
    height = min(_theight() - 2, 20)

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        console.print()
        radius = min(8, height // 2 - 2)
        chars = "○●◐◑◒◓◔◕"
        cx = width // 2
        cy = height // 2
        frame_lines = []
        for y in range(height):
            line = ""
            for x in range(width):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx*dx + dy*dy)
                if radius - 0.8 < dist < radius + 0.8:
                    angle = math.atan2(dy, dx) + frame * 0.3
                    idx = int((angle / (2*math.pi) * 8) % 8)
                    line += f"[cyan]{chars[idx]}[/]"
                else:
                    line += " "
            frame_lines.append(line)
        console.print("\n".join(frame_lines))
        console.print(Align.center(f"[bold cyan]{message}[/]", style=""))
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 波浪文字 ====================

def wave_text(text: str, duration: float = 3.0, amplitude: float = 1.5):
    """波浪文字动画 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    colors = ["cyan", "blue", "magenta", "bright_cyan", "bright_blue", "bright_magenta"]

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        elapsed = (time.time() - start) * 5
        dynamic_amp = amplitude * (0.8 + 0.5 * math.sin(elapsed * 0.6))
        console.print()
        result = ""
        for i, ch in enumerate(text):
            offset = int(math.sin(elapsed + i * 0.4) * dynamic_amp)
            color = colors[i % len(colors)]
            if offset > 0:
                result += f"[{color}]{ch}[/]" + " " * offset
            elif offset < 0:
                result += " " * abs(offset) + f"[{color}]{ch}[/]"
            else:
                result += f"[bold {color}]{ch}[/]"
        console.print(Align.center(result))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 全屏彩虹粒子爆破 ====================

def rainbow_particle_explosion(duration: float = 2.0):
    """全屏彩虹粒子爆破 - 从中心向四周扩散 (30fps 动态帧率, 自适应尺寸)"""
    fps = 30
    frame_time = 1.0 / fps
    particles = []
    colors = ["red", "yellow", "green", "cyan", "blue", "magenta", "bright_red",
              "bright_yellow", "bright_green", "bright_cyan", "bright_blue", "bright_magenta"]
    chars = "✦✧✶✷✸✹✺✵✴✳✲✱▪▫◆◇○●"
    width = min(_twidth(), 80)
    height = min(_theight() - 2, 20)
    cx = width / 2
    cy = height / 2

    for _ in range(60):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.5, 3.0)
        particles.append({
            "x": cx, "y": cy,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.uniform(0.5, 2.0),
            "max_life": 0,
            "color": random.choice(colors),
            "char": random.choice(chars),
        })
    for p in particles:
        p["max_life"] = p["life"]

    start = time.time()
    frame = 0
    while time.time() - start < duration and particles:
        frame_start = time.time()
        console.clear()
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for p in particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.05
            p["vy"] += 0.02
            if p["life"] <= 0:
                particles.remove(p)
                continue
            x, y = int(p["x"]), int(p["y"])
            if 0 <= x < width and 0 <= y < height:
                alpha = p["life"] / p["max_life"]
                if alpha > 0.7:
                    style = f"bold {p['color']}"
                elif alpha > 0.3:
                    style = p["color"]
                else:
                    style = f"dim {p['color']}"
                grid[y][x] = f"[{style}]{p['char']}[/]"
        console.print("\n".join("".join(row) for row in grid))
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 心跳动画 ====================

def heartbeat(text: str, cycles: int = 5, duration: float = 3.0):
    """心跳脉冲动画 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps

    start = time.time()
    frame = 0
    cycle = 0
    while time.time() - start < duration and cycle < cycles:
        frame_start = time.time()
        # 收缩
        console.clear()
        console.print()
        console.print(Align.center(text, style="dim cyan"))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)

        frame_start = time.time()
        # 膨胀
        console.clear()
        console.print()
        console.print(Align.center(text, style="bold bright_cyan"))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)

        frame_start = time.time()
        # 最大
        console.clear()
        console.print()
        console.print(Align.center(text, style="bold bright_magenta"))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)

        frame_start = time.time()
        # 收缩
        console.clear()
        console.print()
        console.print(Align.center(text, style="bold cyan"))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)

        frame += 1
        cycle += 1


# ==================== 烟花效果 ====================

def firework(duration: float = 2.0, bursts: int = 5):
    """终端烟花效果 (30fps 动态帧率, 自适应尺寸, 减少爆发密度)"""
    fps = 30
    frame_time = 1.0 / fps
    chars = "✧✶✷✸✹✺✦✵✴✳✲✱▪▫◆◇○●·•"
    colors_list = ["bright_cyan", "bright_magenta", "bright_blue", "bright_yellow", "bright_green"]
    width = min(_twidth(), 80)
    height = min(_theight() - 2, 18)
    particles = []

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        if random.random() > 0.85 and len(particles) < 60:
            cx = random.randint(width // 5, width * 4 // 5)
            cy = random.randint(2, height // 2)
            color = random.choice(colors_list)
            for _ in range(8):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(0.5, 2.0)
                particles.append({
                    "x": cx, "y": cy, "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed, "life": 12,
                    "color": color, "char": random.choice(chars)
                })

        console.clear()
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for p in particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] <= 0:
                particles.remove(p)
                continue
            x, y = int(p["x"]), int(p["y"])
            if 0 <= x < width and 0 <= y < height:
                if p["life"] > 8:
                    style = f"bold {p['color']}"
                else:
                    style = f"dim {p['color']}"
                grid[y][x] = f"[{style}]{p['char']}[/]"

        console.print("\n".join("".join(row) for row in grid))
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 渐变彩虹边框面板 ====================

def rainbow_panel(title: str, content: str, width: int = 60):
    """彩虹渐变边框面板"""
    colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]
    tw = min(width, _twidth() - 4)
    i = int(time.time() * 3) % len(colors)
    color = colors[i]
    panel = Panel(
        Align.center(content, vertical="middle"),
        title=f"[bold {color}]{title}[/]",
        border_style=color,
        box=box.ROUNDED,
        padding=(1, 2),
        width=tw,
    )
    console.print(panel)


# ==================== 3D旋转文字 ====================

def rotate_3d_text(text: str, duration: float = 3.0):
    """伪3D旋转文字效果 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        frames_since = (time.time() - start) * 4
        scale = abs(math.sin(frames_since))
        stretched = ""
        for ch in text:
            stretched += ch + " " * int((1 - scale) * 3)
        console.print()
        console.print(Align.center(stretched, style="bold cyan"))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1
    console.clear()
    console.print()
    console.print(Align.center(text, style="bold bright_cyan"))
    console.print()


# ==================== 渐变进度条V2 ====================

@contextmanager
def gradient_progress_v2(total: int, description: str, colors: list = None):
    """渐变进度条V2 - 支持自定义颜色列表"""
    if colors is None:
        colors = ["cyan", "blue", "magenta", "bright_cyan", "bright_blue", "bright_magenta"]

    progress = Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[bold]{task.description}"),
        BarColumn(bar_width=50, style="dim cyan", complete_style=colors[0],
                  finished_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )
    with progress:
        task = progress.add_task(f"[{colors[0]}]{description}[/]", total=total)
        yield progress, task


# ==================== 滚动横幅 ====================

def scrolling_banner(text: str, width: int = 60, duration: float = 3.0):
    """滚动横幅文字 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    tw = min(width, _twidth() - 4)
    padded = " " * (tw // 2) + text + " " * (tw // 2)

    start = time.time()
    frame = 0
    offset = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        visible = padded[offset:offset + tw]
        console.print()
        console.print(f"  ┌{'─' * tw}┐")
        console.print(f"  │ {visible:<{tw}} │")
        console.print(f"  └{'─' * tw}┘")
        console.print()
        offset = (offset + 1) % (len(padded) - tw + 1)
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 渐变LOGO ====================

def gradient_logo(text: str, duration: float = 2.0):
    """渐变色LOGO展示 - 颜色从顶部向下流动 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    gradient = ["bright_cyan", "cyan", "bright_blue", "blue", "bright_magenta", "magenta", "purple", "bright_cyan"]

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        console.clear()
        lines = text.split("\n")
        for i, line in enumerate(lines):
            color = gradient[(i + frame) % len(gradient)]
            console.print(Align.center(line, style=f"bold {color}"))
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 进度条动画包装器 ====================

def animated_loading(message: str, duration: float = 2.0):
    """简化加载动画: 旋转spinner + 进度条 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    bar_width = 30

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        elapsed = time.time() - start
        progress = min(elapsed / duration, 1.0)
        filled = int(bar_width * progress)
        bar = "█" * filled + "░" * (bar_width - filled)
        spinner = frames[frame % len(frames)]
        sys.stdout.write(f"\r  {spinner} {message} [{bar}] {progress*100:.0f}%")
        sys.stdout.flush()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1
    sys.stdout.write(f"\r  ✓ {message} - Complete!                    \n\n")
    sys.stdout.flush()


# ==================== 雪花飘落 → AndWreBox Logo ====================

# 5x7 像素字体位图，用于 AndWreBox Logo 渲染
_FONT_5X7 = {
    'A': [" *** ", "*   *", "*   *", "*****", "*   *", "*   *", "*   *"],
    'N': ["*   *", "**  *", "* * *", "*  **", "*   *", "*   *", "*   *"],
    'D': ["**** ", "*   *", "*   *", "*   *", "*   *", "*   *", "**** "],
    'W': ["*   *", "*   *", "*   *", "* * *", "** **", "*   *", "*   *"],
    'R': ["**** ", "*   *", "*   *", "**** ", "*  * ", "*   *", "*   *"],
    'E': ["*****", "*    ", "*    ", "**** ", "*    ", "*    ", "*****"],
    'B': ["**** ", "*   *", "*   *", "**** ", "*   *", "*   *", "**** "],
    'O': [" *** ", "*   *", "*   *", "*   *", "*   *", "*   *", " *** "],
    'X': ["*   *", "*   *", " * * ", "  *  ", " * * ", "*   *", "*   *"],
}


def _build_logo_pixels(logo_text: str, logo_x: int, logo_y: int,
                       char_w: int = 5, char_h: int = 7, spacing: int = 1):
    """根据 5x7 字体构建 Logo 像素坐标列表。

    返回 [(x, y), ...] 列表，每个元素是终端上的一个像素坐标。
    """
    pixels = []
    for i, ch in enumerate(logo_text):
        bitmap = _FONT_5X7.get(ch, ["     "] * char_h)
        ox = logo_x + i * (char_w + spacing)
        for row_idx, row in enumerate(bitmap):
            for col_idx, pixel in enumerate(row):
                if pixel == '*':
                    pixels.append((ox + col_idx, logo_y + row_idx))
    return pixels


def snowfall(duration: float = 4.0, density: int = 80):
    """全屏雪花飘落动画 —— 雪花最终汇聚成 "AndWreBox" 文字。

    两阶段动画：
      Phase 1 (0–60% 时长): 雪花覆盖整个终端自由飘落
      Phase 2 (60–100% 时长): 雪花逐渐汇聚到屏幕中央，逐字形成 "AndWreBox"
      Hold + Fade: 保持 1 秒后渐隐退出

    参数:
        duration: 动画总时长（秒），不含最后的 hold 阶段。默认 4.0。
        density:  雪花密度。默认 80。
    """
    fps = 30
    frame_time = 1.0 / fps
    width = _twidth()
    height = _theight()

    # ── 构建 Logo 像素映射 ──
    logo_text = "AndWreBox"
    char_w, char_h = 5, 7
    spacing = 1
    total_w = len(logo_text) * char_w + (len(logo_text) - 1) * spacing
    total_h = char_h

    # 终端太小 → 退化到纯雪花模式
    logo_fits = (width >= total_w + 4 and height >= total_h + 4)
    if logo_fits:
        logo_x = (width - total_w) // 2
        logo_y = (height - total_h) // 2
        logo_pixels = _build_logo_pixels(logo_text, logo_x, logo_y, char_w, char_h, spacing)
    else:
        logo_pixels = []

    # ── 创建雪花粒子 ──
    total_flakes = max(density, len(logo_pixels)) if logo_pixels else density
    snow_chars = ["*", "·", "•", "✦", "✧", "❄", "❅", "❆"]

    flakes = []
    for i in range(total_flakes):
        flake = {
            "x": random.uniform(0, max(width - 1, 1)),
            "y": random.uniform(-5, max(height - 1, 1)),
            "speed": random.uniform(0.5, 2.5),
            "char": random.choice(snow_chars),
            "target": logo_pixels[i % len(logo_pixels)] if logo_pixels else (0, 0),
        }
        flakes.append(flake)

    phase1_end = duration * 0.6
    total_runtime = duration + 1.0  # 额外 1 秒用于 hold + fade

    start = time.time()
    while time.time() - start < total_runtime:
        frame_start = time.time()
        elapsed = time.time() - start

        grid = [[" " for _ in range(width)] for _ in range(height)]

        if elapsed <= phase1_end:
            # ═══════════════════════════════════════
            # Phase 1: 自由飘落，覆盖全屏
            # ═══════════════════════════════════════
            for flake in flakes:
                flake["y"] += flake["speed"] * 0.8
                flake["x"] += random.uniform(-0.3, 0.3)

                if flake["y"] >= height:
                    flake["y"] = random.uniform(-5, 0)
                    flake["x"] = random.uniform(0, max(width - 1, 1))

                if flake["x"] < 0:
                    flake["x"] = max(width - 1, 0)
                elif flake["x"] >= width:
                    flake["x"] = 0

                x, y = int(flake["x"]), int(flake["y"])
                if 0 <= x < width and 0 <= y < height:
                    if flake["speed"] > 1.6:
                        style = "bold bright_white"
                    elif flake["speed"] > 1.0:
                        style = "bright_white"
                    else:
                        style = "white"
                    grid[y][x] = f"[{style}]{flake['char']}[/]"

        elif elapsed <= duration:
            # ═══════════════════════════════════════
            # Phase 2: 汇聚形成 AndWreBox
            # ═══════════════════════════════════════
            p2 = (elapsed - phase1_end) / (duration - phase1_end)
            eased = ease_in_out(p2)

            for i, flake in enumerate(flakes):
                tx, ty = flake["target"]

                # 逐帧拉近到目标，力度随 eased 增大
                force = 0.03 + eased * 0.35
                flake["x"] += (tx - flake["x"]) * force
                flake["y"] += (ty - flake["y"]) * force

                # 逐渐衰减的随机漂移，让汇聚过程更自然
                drift_strength = (1.0 - eased) * 1.5
                flake["x"] += math.sin(elapsed * 4.0 + i * 0.3) * drift_strength * 0.3
                flake["y"] += math.cos(elapsed * 3.0 + i * 0.5) * drift_strength * 0.2

                x, y = int(flake["x"]), int(flake["y"])
                if 0 <= x < width and 0 <= y < height:
                    if eased > 0.7:
                        style = "bold bright_cyan"
                    elif eased > 0.4:
                        style = "bright_cyan"
                    else:
                        style = "bright_white"
                    # 使用单宽度 * 字符，确保 Logo 对齐
                    grid[y][x] = f"[{style}]*[/]"

        else:
            # ═══════════════════════════════════════
            # Hold + Fade: 保持 0.7s 后渐隐
            # ═══════════════════════════════════════
            hold_t = (elapsed - duration) / 1.0
            # fade 在 0.7s 后开始，0.3s 内完成
            fade = 1.0 - max(0.0, (hold_t - 0.7) / 0.3)

            for flake in flakes:
                tx, ty = flake["target"]
                x, y = int(tx), int(ty)
                if 0 <= x < width and 0 <= y < height:
                    if fade > 0.8:
                        style = "bold bright_cyan"
                    elif fade > 0.5:
                        style = "bright_cyan"
                    elif fade > 0.2:
                        style = "dim bright_cyan"
                    else:
                        style = "dim cyan"
                    # 使用单宽度 * 字符，确保 Logo 对齐
                    grid[y][x] = f"[{style}]*[/]"

        frame_str = "\n".join("".join(row) for row in grid)
        console.clear()
        console.print(frame_str)
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)

    console.clear()


# ==================== 雨滴下落 ====================

def rain_drops(duration: float = 3.0, density: int = 30):
    """雨滴下落动画 - 纯下落，无溅射，30fps 动态帧率。

    使用 console.clear() + 单次 console.print() 避免 Rich 终端状态损坏。
    """
    fps = 30
    frame_time = 1.0 / fps
    width = min(_twidth(), 80)
    height = min(_theight() - 2, 20)
    density = max(5, density // 2)

    drops = []
    for _ in range(density):
        drops.append({
            "x": random.uniform(0, width - 1),
            "y": random.uniform(0, height - 1),
            "speed": random.uniform(0.8, 2.0),
        })

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for drop in drops:
            drop["y"] += drop["speed"] * 0.5
            if drop["y"] >= height:
                drop["y"] = 0
                drop["x"] = random.uniform(0, width - 1)
            x, y = int(drop["x"]), int(drop["y"])
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = "[bright_cyan]|[/]"

        frame_str = "\n".join("".join(row) for row in grid)
        console.clear()
        console.print(frame_str)
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 平滑滚动文字 ====================

def smooth_scroll(text: str, duration: float = 3.0, width: int = 60):
    """平滑滚动文字，使用缓动曲线 (30fps 动态帧率)"""
    fps = 30
    frame_time = 1.0 / fps
    tw = min(width, _twidth() - 4)
    padded = " " * (tw // 2) + text + " " * (tw // 2)
    max_offset = len(padded) - tw
    if max_offset <= 0:
        max_offset = 1

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        elapsed = time.time() - start
        raw_t = elapsed / duration
        t = ease_in_out(raw_t)
        offset = int(t * max_offset)
        visible = padded[offset:offset + tw]

        console.clear()
        console.print()
        console.print(f"  ┌{'─' * tw}┐")
        console.print(f"  │ [bold cyan]{visible:<{tw}}[/] │")
        console.print(f"  └{'─' * tw}┘")
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 颜色循环边框 ====================

def color_cycle_border(panel_text: str, duration: float = 2.0, title: str = ""):
    """快速颜色循环边框 (30fps 动态帧率, 自适应宽度)"""
    fps = 30
    frame_time = 1.0 / fps
    colors = ["cyan", "magenta", "blue", "bright_cyan", "bright_magenta",
              "bright_blue", "green", "bright_green", "yellow", "bright_yellow",
              "red", "bright_red", "purple", "bright_white"]
    tw = min(_twidth() - 4, 65)

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        color = colors[frame % len(colors)]
        panel = Panel(
            Align.center(panel_text, vertical="middle"),
            title=f"[bold {color}]{title}[/]" if title else None,
            border_style=color,
            box=box.ROUNDED,
            padding=(1, 3),
            width=tw,
        )
        console.clear()
        console.print()
        console.print(panel)
        sys.stdout.flush()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 渐变滑动标题 ====================

def gradient_slide_title(text: str, duration: float = 3.0, width: int = 60):
    """渐变标题 - 居中显示，渐变色彩淡入，30fps 动态帧率。

    使用 console.clear() + console.print() 确保与 Rich 终端状态同步。
    """
    fps = 30
    frame_time = 1.0 / fps
    tw = min(width, _twidth() - 4)

    gradient_colors = [
        "red", "yellow", "green", "cyan", "blue", "magenta",
        "bright_red", "bright_yellow", "bright_green", "bright_cyan",
        "bright_blue", "bright_magenta",
    ]

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        progress = min((time.time() - start) / duration, 1.0)

        console.clear()
        console.print()

        colored = Text()
        for i, ch in enumerate(text):
            color_idx = (i + frame) % len(gradient_colors)
            if progress < 0.3:
                alpha_style = "dim"
            elif progress < 0.7:
                alpha_style = ""
            else:
                alpha_style = "bold"
            style = f"{alpha_style} {gradient_colors[color_idx]}"
            colored.append(ch, style=style)

        console.print(Align.center(colored))
        console.print()
        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1


# ==================== 彩虹滚动横幅 ====================

def rainbow_scroll_banner(text: str, duration: float = 3.0, width: int = 60):
    """简洁横幅 - 居中显示单色文字，30fps 动态帧率。

    使用 console.clear() + console.print() 确保与 Rich 终端状态同步。
    """
    fps = 30
    frame_time = 1.0 / fps

    colors = ["cyan", "bright_cyan", "blue", "bright_blue", "magenta", "bright_magenta"]

    start = time.time()
    frame = 0
    while time.time() - start < duration:
        frame_start = time.time()
        color = colors[frame % len(colors)]

        console.clear()
        console.print()
        console.print(Align.center(text, style=f"bold {color}"))
        console.print()

        render_time = time.time() - frame_start
        if render_time < frame_time:
            time.sleep(frame_time - render_time)
        frame += 1