#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndWreBox - 安卓扳手盒子 v1.0
"""

import time
import math
import threading
from collections import deque
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import (
    Progress, BarColumn, TextColumn, SpinnerColumn
)
from rich.align import Align
from rich.style import Style
from rich import box
from rich.rule import Rule

from core.shell import shell
from core.config import SNAPDRAGON_PATHS, LOG_COLORS
from core.animations import console, divider, title_panel
from core.i18n import T


class MonitorDashboard:
    """实时监控仪表盘"""

    def __init__(self, refresh_rate: float = 1.0):
        self.refresh_rate = refresh_rate
        self._running = False
        self._live: Live = None
        self._cpu_cores = self._detect_cpu_cores()
        self._history = deque(maxlen=60)  # 60秒历史
        self._lock = threading.Lock()

    def _detect_cpu_cores(self) -> list:
        """检测在线CPU核心"""
        cores = []
        for i in range(8):
            online = shell.read_node(f"/sys/devices/system/cpu/cpu{i}/online")
            if online != "0":
                cores.append(i)
        return cores if cores else list(range(8))

    def _read_cpu_freqs(self) -> dict:
        """读取所有CPU核心频率"""
        freqs = {}
        for cpu in self._cpu_cores:
            freq = shell.read_node_int(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_cur_freq")
            freqs[cpu] = freq // 1000 if freq > 0 else 0  # MHz
        return freqs

    def _read_cpu_usage(self) -> float:
        """读取CPU总使用率 - 修复top解析失败问题"""
        # 使用/proc/stat (最可靠的方式)
        ok, stat, _ = shell.run("cat /proc/stat 2>/dev/null | grep '^cpu '")
        if ok and stat:
            fields = stat.split()
            if len(fields) >= 5:
                # cpu  user nice system idle iowait irq softirq steal
                total = sum(int(f) for f in fields[1:8] if f.isdigit())
                idle = int(fields[4]) if fields[4].isdigit() else 0
                iowait = int(fields[5]) if len(fields) > 5 and fields[5].isdigit() else 0
                if total > 0:
                    return round((1 - (idle + iowait) / total) * 100, 1)
        return 0.0

    def _read_gpu_info(self) -> dict:
        """读取GPU信息"""
        info = {"freq": 0, "usage": 0, "governor": ""}
        info["freq"] = shell.read_node_int("/sys/class/kgsl/kgsl-3d0/gpuclk") // 1000000
        info["usage"] = shell.read_node_int("/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage")
        info["governor"] = shell.read_node("/sys/class/kgsl/kgsl-3d0/devfreq/governor")
        return info

    def _read_temps(self) -> dict:
        """读取温度"""
        temps = {"cpu": 0, "gpu": 0, "battery": 0}
        zones = shell.ls("/sys/class/thermal")
        for zone in zones:
            if zone.startswith("thermal_zone"):
                ttype = shell.read_node(f"/sys/class/thermal/{zone}/type")
                temp = shell.read_node_int(f"/sys/class/thermal/{zone}/temp")
                if temp > 0:
                    temp_c = temp / 1000.0
                    ttype_lower = ttype.lower()
                    if any(k in ttype_lower for k in ["cpu", "ap", "soc", "xpu"]):
                        temps["cpu"] = max(temps["cpu"], temp_c)
                    if "gpu" in ttype_lower:
                        temps["gpu"] = max(temps["gpu"], temp_c)
                    if "batt" in ttype_lower:
                        temps["battery"] = max(temps["battery"], temp_c)
        return temps

    def _read_battery(self) -> dict:
        """读取电池信息"""
        info = {
            "capacity": shell.read_node_int("/sys/class/power_supply/battery/capacity"),
            "current": shell.read_node_int("/sys/class/power_supply/battery/current_now"),
            "voltage": shell.read_node_int("/sys/class/power_supply/battery/voltage_now"),
            "temp": shell.read_node_int("/sys/class/power_supply/battery/temp"),
        }
        # 电流转换为mA
        if abs(info["current"]) > 10000:
            info["current_ma"] = info["current"] // 1000
        else:
            info["current_ma"] = info["current"]
        # 电压转换为mV
        if info["voltage"] > 10000:
            info["voltage_mv"] = info["voltage"] // 1000
        else:
            info["voltage_mv"] = info["voltage"]
        return info

    def _read_memory(self) -> dict:
        """读取内存信息"""
        info = {"total": 0, "free": 0, "available": 0, "used": 0, "percent": 0}
        ok, meminfo, _ = shell.run("cat /proc/meminfo")
        if ok:
            for line in meminfo.split("\n"):
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().replace(" kB", "")
                    try:
                        val_kb = int(val)
                        if key == "MemTotal":
                            info["total"] = val_kb // 1024
                        elif key == "MemFree":
                            info["free"] = val_kb // 1024
                        elif key == "MemAvailable":
                            info["available"] = val_kb // 1024
                    except ValueError:
                        pass
            if info["total"] > 0:
                info["used"] = info["total"] - (info["available"] or info["free"])
                info["percent"] = round(info["used"] / info["total"] * 100, 1)
        return info

    def _temp_color(self, temp: float) -> str:
        """根据温度返回颜色"""
        if temp > 80:
            return "bold red"
        elif temp > 65:
            return "bold yellow"
        elif temp > 45:
            return "cyan"
        else:
            return "dim cyan"

    def _battery_color(self, pct: int) -> str:
        """根据电量返回颜色"""
        if pct <= 15:
            return "bold red"
        elif pct <= 30:
            return "bold yellow"
        else:
            return "green"

    def _usage_color(self, pct: float) -> str:
        """根据使用率返回颜色"""
        if pct > 90:
            return "bold red"
        elif pct > 70:
            return "bold yellow"
        elif pct > 40:
            return "cyan"
        else:
            return "green"

    def _generate_layout(self) -> Layout:
        """生成仪表盘布局"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=2),
        )
        layout["left"].split_column(
            Layout(name="cpu"),
            Layout(name="gpu"),
        )
        layout["right"].split_column(
            Layout(name="temps"),
            Layout(name="battery"),
            Layout(name="memory"),
        )
        return layout

    def _build_header(self) -> Panel:
        """构建头部面板"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = shell.run_raw("cat /proc/uptime | awk '{print $1}'").strip()
        if uptime:
            uptime_s = int(float(uptime))
            hours = uptime_s // 3600
            mins = (uptime_s % 3600) // 60
            uptime_str = f"{hours}h {mins}m"
        else:
            uptime_str = T("N/A")

        model = shell.get_prop("ro.product.model") or T("unknown")
        kernel = shell.run_raw("uname -r").strip()

        text = Text()
        text.append("\U0001f4ca ", style="bold bright_cyan")
        text.append(T("monitor_header"), style="bold bright_cyan")
        text.append("  |  ", style="dim white")
        text.append(f"{model}", style="cyan")
        text.append("  |  ", style="dim white")
        text.append(f"{T('kernel_version')}: {kernel}", style="dim cyan")
        text.append("  |  ", style="dim white")
        text.append(f"{T('monitor_uptime')}: {uptime_str}", style="green")
        text.append("  |  ", style="dim white")
        text.append(now, style="dim white")

        return Panel(
            Align.center(text, vertical="middle"),
            border_style="cyan",
            box=box.ROUNDED,
        )

    def _build_cpu_panel(self) -> Panel:
        """构建CPU面板"""
        cpu_usage = self._read_cpu_usage()
        freqs = self._read_cpu_freqs()

        # CPU使用率进度条
        bar_width = 40
        filled = int(bar_width * cpu_usage / 100)
        bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
        usage_color = self._usage_color(cpu_usage)

        content = f"[{usage_color}]{bar}[/] [{usage_color}]{cpu_usage:.1f}%[/]\n\n"

        # 各核心频率
        for cpu in sorted(freqs.keys()):
            freq = freqs[cpu]
            if freq > 0:
                # 核心类型标记
                if freq >= 2500:
                    label = f"[bold red]CPU{cpu} ({T('cpu_core_type_big')})[/]"
                elif freq >= 1800:
                    label = f"[bold yellow]CPU{cpu} ({T('cpu_core_type_mid')})[/]"
                else:
                    label = f"[dim cyan]CPU{cpu} ({T('cpu_core_type_little')})[/]"

                # 频率条
                max_freq = 3200  # 默认最大频率
                freq_bar_w = 30
                freq_filled = min(int(freq_bar_w * freq / max_freq), freq_bar_w)
                freq_bar = "\u2588" * freq_filled + "\u2591" * (freq_bar_w - freq_filled)
                content += f"  {label} [{usage_color}]{freq_bar}[/] {freq} MHz\n"
            else:
                content += f"  [dim]CPU{cpu}: {T('monitor_offline')}[/]\n"

        return Panel(
            content.strip(),
            title=f"[bold bright_cyan]{T('monitor_cpu_panel')}[/]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _build_gpu_panel(self) -> Panel:
        """构建GPU面板"""
        gpu = self._read_gpu_info()

        if gpu["freq"] > 0:
            bar_width = 40
            max_gpu = 1000
            filled = min(int(bar_width * gpu["freq"] / max_gpu), bar_width)
            bar = "\u2588" * filled + "\u2591" * (bar_width - filled)

            content = f"  [cyan]{T('monitor_freq')}:[/] [{self._usage_color(gpu['usage'])}]{bar}[/] {gpu['freq']} MHz\n"
            content += f"  [cyan]{T('gpu_load')}:[/] {gpu['usage']}%\n"
            content += f"  [cyan]{T('cpu_governor')}:[/] {gpu['governor']}\n"
        else:
            content = f"  [dim]{T('monitor_gpu_unavailable')}[/]"

        return Panel(
            content.strip(),
            title=f"[bold bright_cyan]{T('monitor_gpu_panel')}[/]",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _build_temps_panel(self) -> Panel:
        """构建温度面板"""
        temps = self._read_temps()

        content = ""
        temp_items = [
            (T("thermal_sensor_cpu"), temps["cpu"]),
            (T("thermal_sensor_gpu"), temps["gpu"]),
            (T("thermal_sensor_battery"), temps["battery"]),
        ]

        for name, temp in temp_items:
            if temp > 0:
                color = self._temp_color(temp)
                bar_width = 30
                filled = min(int(bar_width * temp / 100), bar_width)
                bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
                content += f"  [cyan]{name}:[/] [{color}]{bar}[/] [{color}]{temp:.1f}\u00b0C[/]\n"

        if not content:
            content = f"  [dim]{T('monitor_temp_unavailable')}[/]"

        return Panel(
            content.strip(),
            title=f"[bold bright_cyan]{T('monitor_temp_panel')}[/]",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _build_battery_panel(self) -> Panel:
        """构建电池面板"""
        battery = self._read_battery()

        cap = battery["capacity"]
        color = self._battery_color(cap)
        bar_width = 30
        filled = int(bar_width * cap / 100)
        bar = "\u2588" * filled + "\u2591" * (bar_width - filled)

        content = f"  [cyan]{T('monitor_battery_level')}:[/] [{color}]{bar}[/] [{color}]{cap}%[/]\n"

        if battery["current_ma"] != 0:
            direction = T("monitor_charging") if battery["current_ma"] < 0 else T("monitor_discharging")
            content += f"  [cyan]{T('monitor_current')}:[/] {abs(battery['current_ma'])} mA ({direction})\n"
        if battery["voltage_mv"] > 0:
            content += f"  [cyan]{T('monitor_voltage')}:[/] {battery['voltage_mv']} mV\n"
        if battery["temp"] > 0:
            temp_c = battery["temp"] / 10.0
            tcolor = self._temp_color(temp_c)
            content += f"  [cyan]{T('monitor_battery_temp')}:[/] [{tcolor}]{temp_c:.1f}\u00b0C[/]\n"

        return Panel(
            content.strip(),
            title=f"[bold bright_cyan]{T('monitor_battery_panel')}[/]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _build_memory_panel(self) -> Panel:
        """构建内存面板"""
        mem = self._read_memory()

        if mem["total"] > 0:
            bar_width = 30
            filled = int(bar_width * mem["percent"] / 100)
            bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
            color = self._usage_color(mem["percent"])

            content = f"  [cyan]{T('monitor_used')}:[/] [{color}]{bar}[/] [{color}]{mem['percent']:.1f}%[/]\n"
            content += f"  [cyan]{T('monitor_total')}:[/] {mem['total']} MB\n"
            content += f"  [cyan]{T('monitor_used')}:[/] {mem['used']} MB\n"
            content += f"  [cyan]{T('monitor_available')}:[/] {mem['available'] or mem['free']} MB\n"
        else:
            content = f"  [dim]{T('monitor_mem_unavailable')}[/]"

        return Panel(
            content.strip(),
            title=f"[bold bright_cyan]{T('monitor_memory_panel')}[/]",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )

    def _build_footer(self) -> Panel:
        """构建底部面板"""
        # 读取顶层进程
        ok, procs, _ = shell.run("ps -A -o PID,%CPU,NAME --sort=-%CPU 2>/dev/null | head -6")
        lines = procs.strip().split("\n") if ok else []

        content = f"[dim]{T('monitor_top_processes')}:[/] "
        if len(lines) > 1:
            process_lines = []
            for line in lines[1:]:  # 跳过标题
                parts = line.strip().split()
                if len(parts) >= 2:
                    process_lines.append(f"[cyan]{parts[-1][:15]}[/] [yellow]{parts[1]}%[/]")
            content += "  |  ".join(process_lines[:4])

        content += f"\n[dim]{T('monitor_hint')}[/]"

        return Panel(
            content,
            border_style="dim cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        )

    def _build_dashboard(self) -> Layout:
        """构建完整仪表盘"""
        layout = self._generate_layout()
        layout["header"].update(self._build_header())
        layout["cpu"].update(self._build_cpu_panel())
        layout["gpu"].update(self._build_gpu_panel())
        layout["temps"].update(self._build_temps_panel())
        layout["battery"].update(self._build_battery_panel())
        layout["memory"].update(self._build_memory_panel())
        layout["footer"].update(self._build_footer())
        return layout

    def run(self):
        """启动实时监控"""
        self._running = True
        console.clear()

        try:
            with Live(
                self._build_dashboard(),
                console=console,
                refresh_per_second=1 / self.refresh_rate,
                screen=True,
                transient=False,
            ) as live:
                self._live = live
                while self._running:
                    live.update(self._build_dashboard())
                    time.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            self._running = False
            console.clear()
            console.print(f"[bold cyan]{T('monitor_stopped')}[/]")

    def stop(self):
        """停止监控"""
        self._running = False
        if self._live:
            self._live.stop()


def run_monitor():
    """启动监控看板入口"""
    dashboard = MonitorDashboard(refresh_rate=1.0)
    dashboard.run()